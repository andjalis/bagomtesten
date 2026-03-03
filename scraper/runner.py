"""
scraper.py — CLI entry point and async orchestrator for DR Kandidattest scraping.

This module handles:
    - CLI argument parsing (--runs-per-municipality, --seed, --workers, --start-municipality)
    - Generating LHS answer combinations via sampling.py
    - Dynamic AIMD concurrency scaling (ramp up on success, halve on rate-limit)
    - Delegating actual browser interaction to browser.py
    - Persisting results via db.py and csv_io.py

Scraping strategy:
    Municipalities are processed sequentially. For each municipality, we
    generate enough LHS combinations to reach the target (default: 10,000),
    accounting for already-completed runs. Once a municipality reaches its
    target, we move to the next one.

Error handling strategy:
    - Each worker retries up to MAX_RETRIES times before giving up on a combo.
    - Failed combos are re-queued for later retry.
    - Browser crashes trigger a full browser restart (not a script exit).
    - The orchestrator never exits due to transient errors.

Architecture:
    scraper.py  →  browser.py   (Playwright page interactions)
                →  sampling.py  (Latin Hypercube Sampling)
                →  db.py        (SQLite state management)
                →  csv_io.py    (flat CSV output)
                →  config.py    (shared constants)
"""

import asyncio
import argparse
import json
import logging
import random
import time
import traceback

from playwright.async_api import async_playwright, BrowserContext, Browser

from scraper import db
from scraper.browser import (
    dismiss_cookie_banner,
    select_municipality,
    start_test,
    answer_question,
    navigate_to_results,
    extract_results,
    human_delay,
)
from config import (
    BASE_URL,
    CSV_PATH,
    MUNICIPALITIES,
    USER_AGENTS,
    NUM_QUESTIONS,
)
from scraper.csv_io import ensure_csv, append_csv
from scraper.sampling import generate_lhs_combinations, answer_hash, answers_to_labels

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scraper")

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_RETRIES = 3           # Max retries per combo before giving up
RETRY_DELAY_BASE = 10.0   # Base delay between retries (doubled each attempt)
BROWSER_RESTART_DELAY = 5.0  # Seconds to wait before restarting browser
DEFAULT_RUNS_PER_MUN = 10000  # Target tests per municipality


# ── Single Test Runner ────────────────────────────────────────────────────────

async def run_test(
    context: BrowserContext,
    answers: list[int],
    run_id: int,
    worker_id: int,
    municipality: str,
) -> tuple[bool, bool]:
    """Run a single test instance in a browser context.

    Returns:
        (success, is_rate_limited) — tuple of booleans.
    """
    page = None
    try:
        page = await context.new_page()
    except Exception as e:
        log.error(f"[W{worker_id}] Run #{run_id} — Could not create page: {e}")
        return False, False

    ahash = answer_hash(answers)
    labels = answers_to_labels(answers)

    try:
        log.info(f"[W{worker_id}] Run #{run_id} starting — hash={ahash}, Kommune={municipality}")

        await page.goto(BASE_URL, wait_until="networkidle", timeout=45000)
        await human_delay(0.5, 1.0)

        await dismiss_cookie_banner(page)
        await select_municipality(page, municipality)
        await start_test(page)

        # Answer all 25 questions
        questions = []
        for i in range(NUM_QUESTIONS):
            q_info = await answer_question(page, i + 1, answers[i])
            if q_info:
                questions.append(q_info)
            log.info(f"[W{worker_id}] Run #{run_id} — Q{i+1}/25: {labels[i]}")

        if questions:
            try:
                await db.save_questions(questions)
            except Exception as e:
                log.warning(f"[W{worker_id}] Run #{run_id} — Could not save questions (non-fatal): {e}")

        await navigate_to_results(page)
        candidates = await extract_results(page)

        if not candidates:
            raise ValueError("No candidates extracted from results page")

        log.info(
            f"[W{worker_id}] Run #{run_id} — Got {len(candidates)} candidates. "
            f"Top: {candidates[0]['name']} ({candidates[0]['party']}) "
            f"@ {candidates[0]['match_pct']}%"
        )

        # Persist to database
        await db.save_results(run_id, candidates)
        await db.mark_complete(run_id)

        # Persist to CSV
        csv_rows = [
            {
                "run_id": run_id,
                "answer_hash": ahash,
                "answers": json.dumps(answers),
                "municipality": municipality,
                "candidate_rank": c["rank"],
                "candidate_name": c["name"],
                "party": c["party"],
                "match_pct": c["match_pct"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for c in candidates
        ]
        append_csv(csv_rows)

        log.info(f"[W{worker_id}] Run #{run_id} COMPLETE ✓")
        return True, False

    except Exception as e:
        err_str = str(e).lower()
        log.error(f"[W{worker_id}] Run #{run_id} FAILED: {e}")
        try:
            await db.mark_failed(run_id, str(e))
        except Exception:
            pass

        is_rl = any(
            term in err_str
            for term in ["timeout", "429", "access denied", "cloudflare", "too many requests"]
        )
        return False, is_rl

    finally:
        try:
            if page and not page.is_closed():
                await page.close()
        except Exception:
            pass  # Page may already be closed if browser crashed


# ── Browser Management ────────────────────────────────────────────────────────

class BrowserManager:
    """Manages the Playwright browser lifecycle with crash recovery."""

    def __init__(self, playwright):
        self._pw = playwright
        self._browser: Browser | None = None
        self._lock = asyncio.Lock()

    async def launch(self) -> Browser:
        """Launch a new browser instance."""
        async with self._lock:
            if self._browser and self._browser.is_connected():
                return self._browser
            log.info("Launching new Chromium browser instance...")
            self._browser = await self._pw.chromium.launch(headless=True)
            return self._browser

    async def get_browser(self) -> Browser:
        """Get the current browser, restarting if it has crashed."""
        async with self._lock:
            if self._browser and self._browser.is_connected():
                return self._browser
        # Browser died — restart
        log.warning("Browser disconnected! Restarting...")
        await asyncio.sleep(BROWSER_RESTART_DELAY)
        return await self.launch()

    async def close(self):
        """Gracefully close the browser."""
        async with self._lock:
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None


# ── Municipality Worker Pool ──────────────────────────────────────────────────

async def scrape_municipality(
    bm: BrowserManager,
    municipality: str,
    combos: list[list[int]],
    max_workers: int,
) -> tuple[int, int, int]:
    """Scrape a batch of combos for a single municipality.

    Returns:
        (completed, failed_permanent, retried) counts.
    """
    completed = 0
    failed_permanent = 0
    retried = 0

    # Build task queue: (combo, retry_count)
    task_queue: list[tuple[list[int], int]] = [(c, 0) for c in combos]
    total_new = len(task_queue)

    if total_new == 0:
        return 0, 0, 0

    # AIMD state
    current_workers = 1
    worker_counter = 0
    active_tasks: set[asyncio.Task] = set()
    retry_queue: list[tuple[list[int], int]] = []
    queue_idx = 0

    async def worker_task(combo: list[int], w_id: int, attempt: int) -> tuple[bool, float, bool, list[int], int]:
        """Execute a single test and return (success, duration, is_rate_limited, combo, attempt)."""
        start_time = time.time()
        h = answer_hash(combo)

        # Double-check for duplicates (another worker may have completed it)
        if await db.is_duplicate(h, municipality):
            return True, 0.0, False, combo, attempt

        ua = random.choice(USER_AGENTS)

        try:
            run_id = await db.register_run(h, combo, municipality)
        except Exception as e:
            log.error(f"[W{w_id}] Failed to register run: {e}")
            return False, 0.0, False, combo, attempt

        context = None
        try:
            browser = await bm.get_browser()
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                locale="da-DK",
                user_agent=ua,
            )
            success, is_rl = await run_test(context, combo, run_id, w_id, municipality)
        except Exception as e:
            log.error(f"[W{w_id}] Worker-level error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            success, is_rl = False, "timeout" in str(e).lower()
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

        return success, time.time() - start_time, is_rl, combo, attempt

    def get_next_combo() -> tuple[list[int], int] | None:
        """Get next combo from either retry queue or main queue."""
        nonlocal queue_idx
        if retry_queue:
            return retry_queue.pop(0)
        if queue_idx < len(task_queue):
            item = task_queue[queue_idx]
            queue_idx += 1
            return item
        return None

    # Controller loop
    log.info(f"  Starting workers for {municipality} (Max: {max_workers}, Tasks: {total_new})...")
    consecutive_failures = 0

    while True:
        # Harvest completed tasks
        done_tasks = [t for t in active_tasks if t.done()]
        for t in done_tasks:
            active_tasks.remove(t)
            try:
                success, duration, is_rl, combo, attempt = t.result()

                if is_rl:
                    current_workers = max(1, current_workers // 2)
                    pause = random.uniform(30.0, 90.0)
                    log.warning(
                        f"⚠️  Rate limit hit! Scaled down to {current_workers} workers. "
                        f"Pausing for {pause:.0f}s..."
                    )
                    if attempt < MAX_RETRIES:
                        retry_queue.append((combo, attempt + 1))
                        retried += 1
                    else:
                        failed_permanent += 1
                        log.error(f"Combo {answer_hash(combo)} permanently failed after {MAX_RETRIES} retries")
                    await asyncio.sleep(pause)
                    consecutive_failures = 0

                elif success:
                    if duration > 0:
                        completed += 1
                        consecutive_failures = 0
                        if duration > 75.0:
                            current_workers = max(1, current_workers - 1)
                            log.warning(f"Degraded perf ({duration:.1f}s). Scaled to {current_workers}")
                        elif current_workers < max_workers and len(active_tasks) >= current_workers - 1:
                            current_workers += 1
                            log.info(f"Solid perf ({duration:.1f}s). Ramping to {current_workers}")

                    remaining = (len(task_queue) - queue_idx) + len(retry_queue)
                    log.info(
                        f"📊 [{municipality}] {completed}/{total_new} done | "
                        f"{len(active_tasks)} active | {remaining} remaining | "
                        f"{failed_permanent} failed"
                    )

                else:
                    consecutive_failures += 1
                    if attempt < MAX_RETRIES:
                        delay = RETRY_DELAY_BASE * (2 ** attempt)
                        log.warning(
                            f"Retrying combo {answer_hash(combo)} "
                            f"(attempt {attempt + 1}/{MAX_RETRIES}, delay {delay:.0f}s)"
                        )
                        retry_queue.append((combo, attempt + 1))
                        retried += 1
                    else:
                        failed_permanent += 1
                        log.error(
                            f"❌ Combo {answer_hash(combo)} permanently failed "
                            f"after {MAX_RETRIES} attempts"
                        )

                    if consecutive_failures >= 5:
                        log.warning(
                            f"🔄 {consecutive_failures} consecutive failures — "
                            f"restarting browser and pausing 15s..."
                        )
                        await bm.close()
                        await asyncio.sleep(15.0)
                        await bm.launch()
                        current_workers = max(1, current_workers // 2)
                        consecutive_failures = 0

            except Exception as e:
                log.error(f"Worker task crashed fatally: {e}\n{traceback.format_exc()}")

        # Fill pool
        while len(active_tasks) < current_workers:
            next_item = get_next_combo()
            if next_item is None:
                break
            combo, attempt = next_item
            worker_counter += 1

            jitter = random.uniform(1.0, 3.0) if attempt == 0 else random.uniform(
                RETRY_DELAY_BASE * (2 ** (attempt - 1)),
                RETRY_DELAY_BASE * (2 ** attempt),
            )
            t = asyncio.create_task(worker_task(combo, worker_counter, attempt))
            active_tasks.add(t)
            await asyncio.sleep(min(jitter, 5.0))

        if not active_tasks:
            break

        await asyncio.sleep(1.0)

    return completed, failed_permanent, retried


# ── Main Orchestrator ─────────────────────────────────────────────────────────

async def main(
    runs_per_mun: int = DEFAULT_RUNS_PER_MUN,
    seed: int = 42,
    max_workers: int = 15,
    start_municipality: str | None = None,
):
    """Iterate through municipalities sequentially, scraping runs_per_mun
    tests for each one (accounting for existing completed runs).

    The municipality order starts with start_municipality (default: København)
    and then continues through the rest of MUNICIPALITIES.
    """
    log.info("=" * 60)
    log.info("=== DR Kandidattest Scraper — Sequential Municipality Mode ===")
    log.info(f"Target: {runs_per_mun} tests per municipality")
    log.info("=" * 60)

    await db.init_db()
    ensure_csv()

    # Clean up incomplete runs from previous crashed sessions
    stale_count = await db.cleanup_stale_runs()
    if stale_count:
        log.warning(f"🧹 Cleaned up {stale_count} stale 'running' runs from previous session")

    # Build municipality order: start_municipality first, then the rest
    start_mun = start_municipality or "København"
    if start_mun not in MUNICIPALITIES:
        log.error(f"Municipality '{start_mun}' not found in MUNICIPALITIES list!")
        log.info(f"Available: {', '.join(MUNICIPALITIES)}")
        return

    mun_order = [start_mun] + [m for m in MUNICIPALITIES if m != start_mun]

    # Grand totals
    grand_completed = 0
    grand_failed = 0
    grand_retried = 0

    async with async_playwright() as pw:
        bm = BrowserManager(pw)
        await bm.launch()

        for mun in mun_order:
            existing = await db.count_done_for_municipality(mun)
            needed = runs_per_mun - existing

            log.info("")
            log.info("─" * 60)
            log.info(f"🏘️  Municipality: {mun}")
            log.info(f"   Existing: {existing} | Target: {runs_per_mun} | Needed: {max(0, needed)}")
            log.info("─" * 60)

            if needed <= 0:
                log.info(f"✅ {mun} already has {existing} runs (≥ {runs_per_mun}). Skipping!")
                continue

            # Generate LHS combos for this municipality
            # Use a seed derived from the base seed + municipality name for reproducibility
            mun_seed = seed + hash(mun) % 100000
            combos = generate_lhs_combinations(needed + 500, seed=mun_seed)  # +500 buffer for duplicates

            # Filter out combos already done for THIS municipality
            filtered_combos = []
            for combo in combos:
                if len(filtered_combos) >= needed:
                    break
                h = answer_hash(combo)
                if not await db.is_duplicate(h, mun):
                    filtered_combos.append(combo)

            if not filtered_combos:
                log.info(f"No new combinations to run for {mun}. Increasing seed or buffer may help.")
                continue

            log.info(f"📋 Queued {len(filtered_combos)} new combinations for {mun}")

            completed, failed, retried_count = await scrape_municipality(
                bm, mun, filtered_combos, max_workers
            )

            grand_completed += completed
            grand_failed += failed
            grand_retried += retried_count

            final_count = await db.count_done_for_municipality(mun)
            log.info(
                f"🏁 {mun} session done: +{completed} completed, {failed} failed. "
                f"Total for {mun}: {final_count}/{runs_per_mun}"
            )

        await bm.close()

    stats = await db.get_stats()
    log.info("")
    log.info("=" * 60)
    log.info("=== ALL MUNICIPALITIES COMPLETE ===")
    log.info(f"DB totals: {stats['total']} runs | {stats['done']} done | {stats['failed']} failed")
    log.info(f"This session: {grand_completed} completed | {grand_failed} permanently failed | {grand_retried} retries")
    log.info(f"Results saved to {CSV_PATH}")
    log.info("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DR Kandidattest Scraper")
    parser.add_argument(
        "--runs-per-municipality", type=int, default=DEFAULT_RUNS_PER_MUN,
        help=f"Target number of tests per municipality (default: {DEFAULT_RUNS_PER_MUN})"
    )
    parser.add_argument("--seed", type=int, default=42, help="Base random seed for LHS (default: 42)")
    parser.add_argument("--workers", type=int, default=15, help="Max concurrent workers (default: 15)")
    parser.add_argument(
        "--start-municipality", type=str, default="København",
        help="Municipality to start with (default: København)"
    )
    args = parser.parse_args()

    asyncio.run(main(
        runs_per_mun=args.runs_per_municipality,
        seed=args.seed,
        max_workers=args.workers,
        start_municipality=args.start_municipality,
    ))
