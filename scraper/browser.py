"""
browser.py — Playwright page-interaction functions for DR Kandidattest.

Each function operates on a single Playwright Page object and handles
one atomic step of the test flow: dismissing cookies, selecting a
municipality, answering a question, navigating to results, or
extracting candidate data from the results page.
"""

import asyncio
import logging
import random
import re

from playwright.async_api import Page

from config import ANSWER_MAP, MIN_DELAY, MAX_DELAY

log = logging.getLogger("scraper")


# ── Timing ────────────────────────────────────────────────────────────────────

async def human_delay(low: float = MIN_DELAY, high: float = MAX_DELAY):
    """Wait a random human-like duration to avoid bot detection."""
    await asyncio.sleep(random.uniform(low, high))


# ── Cookie Banner ─────────────────────────────────────────────────────────────

async def dismiss_cookie_banner(page: Page):
    """Try to dismiss cookie/consent banners if they appear.

    DR uses several possible button selectors for cookie consent.
    We iterate through known selectors and click the first visible one.
    """
    try:
        for selector in [
            "button.drcc-button.submitAll",
            "button[aria-label='Tillad alle']",
            "button:has-text('Tillad alle')",
            "button:has-text('Accepter')",
            "button:has-text('Acceptér')",
            "button:has-text('OK')",
            "[data-testid='cookie-accept']",
            ".cookie-consent button",
        ]:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                await human_delay(0.3, 0.6)
                log.info("Dismissed cookie banner")
                return
    except Exception:
        pass  # No banner found — that's fine


# ── Municipality Selection ────────────────────────────────────────────────────

async def select_municipality(page: Page, municipality: str):
    """Select a municipality from the React-Select dropdown.

    The DR test uses react-select; we focus the input, type the
    municipality name, then click the first matching option.
    """
    select_input = page.locator("#react-select-1-input")
    await select_input.click()
    await human_delay(0.3, 0.5)

    await select_input.fill(municipality)
    await human_delay(0.5, 0.8)

    option = page.locator("[id*='react-select-1-option']").first
    await option.wait_for(state="visible", timeout=5000)
    await option.click()
    await human_delay(0.3, 0.5)


# ── Start Test ────────────────────────────────────────────────────────────────

async def start_test(page: Page):
    """Click 'Tag testen' to begin answering questions."""
    btn = page.locator(".dre-button:has-text('Tag testen')")
    await btn.wait_for(state="visible", timeout=10000)
    await btn.click()
    await human_delay(0.8, 1.2)


# ── Answer a Question ─────────────────────────────────────────────────────────

async def answer_question(page: Page, question_num: int, answer_idx: int) -> dict | None:
    """Answer a single question and return question metadata if extractable.

    Args:
        page: Active Playwright page.
        question_num: 1-indexed question number (1–25).
        answer_idx: Answer index (0=Uenig, 1=Lidt uenig, 2=Lidt enig, 3=Enig).

    Returns:
        A dict with keys {number, text, category} if the question text
        could be extracted, otherwise None.
    """
    label_text = ANSWER_MAP[answer_idx]

    # Wait for the specific answer button
    answer_btn = page.locator(f"label[aria-label='{label_text}']").nth(question_num - 1)
    await answer_btn.wait_for(state="visible", timeout=10000)

    # Try to extract question text before clicking
    question_info = None
    try:
        progress_text = await page.locator("text=/\\d+\\/25/").first.text_content(timeout=3000)

        question_heading = page.locator("h1, h2, h3").filter(has_not_text="Kandidattest")
        q_texts = await question_heading.all_text_contents()
        if q_texts:
            # Filter out cookie-banner text and non-question headings
            q_text = next(
                (t for t in q_texts
                 if len(t) > 10
                 and "Kandidattest" not in t
                 and "DR passer" not in t
                 and "Vores og vores partneres" not in t
                 and "1/25" not in t
                 and "data" not in t.lower() or "dr passer på dine data" not in t.lower()),
                q_texts[-1] if q_texts else "Ukendt spørgsmål",
            )
            category = ""
            if "|" in (progress_text or ""):
                category = progress_text.split("|")[-1].strip()
            question_info = {
                "number": question_num,
                "text": q_text.strip(),
                "category": category,
            }
    except Exception:
        pass

    await answer_btn.click()
    await human_delay()
    return question_info


# ── Navigate to Results ───────────────────────────────────────────────────────

async def navigate_to_results(page: Page):
    """Navigate from the last answered question to the results page.

    After question 25, we try multiple strategies to reach the results:
    1. Click the forward-arrow navigation button.
    2. Click any "Se resultat" variant button.
    3. Wait for "% enighed" text as a fallback.
    """
    try:
        next_arrow = page.locator("button:has-text('>')").last
        if await next_arrow.is_visible(timeout=2000):
            await next_arrow.click()
            await human_delay(0.8, 1.2)
    except Exception:
        pass

    for text in ["Se resultat", "Se dit resultat", "Se resultater"]:
        try:
            result_btn = page.locator(
                f"button:has-text('{text}'), .dre-button:has-text('{text}'), a:has-text('{text}')"
            )
            if await result_btn.first.is_visible(timeout=3000):
                await result_btn.first.click()
                await human_delay(1.0, 2.0)
                return
        except Exception:
            continue

    # Fallback: wait for results content to appear
    try:
        await page.wait_for_selector("text=/\\d+%\\s*enighed/", timeout=10000)
    except Exception:
        for _ in range(3):
            try:
                btn = page.locator(".dre-button").first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await human_delay(0.8, 1.2)
            except Exception:
                pass


# ── Extract Results ───────────────────────────────────────────────────────────

async def extract_results(page: Page) -> list[dict]:
    """Extract the top 6 candidate results from the results page.

    Uses JavaScript evaluation to parse candidate cards from the DOM.
    Falls back to regex text extraction if JS fails.

    Returns:
        List of dicts with keys: rank, name, party, match_pct, url, image.
    """
    candidates = []

    await page.wait_for_selector("text=/\\d+%\\s*enighed/", timeout=15000)
    await human_delay(0.5, 1.0)

    try:
        data = await page.evaluate("""
            () => {
                const candidates = [];
                const links = document.querySelectorAll('a[href*="kandidat"]');
                let validCount = 0;
                if (links.length > 0) {
                    links.forEach((link) => {
                        const h2 = link.querySelector('h2');
                        const pElements = link.querySelectorAll('p');
                        const img = link.querySelector('img');

                        let matchPct = 0;
                        const allText = link.textContent;
                        const pctMatch = allText.match(/(\\d+)%\\s*enighed/);
                        if (pctMatch) matchPct = parseInt(pctMatch[1]);

                        if (h2) {
                            validCount++;
                            const partyP = Array.from(pElements).find(p => !p.textContent.includes('%'));
                            candidates.push({
                                rank: validCount,
                                name: h2.textContent.trim(),
                                party: partyP ? partyP.textContent.trim() : '',
                                match_pct: matchPct,
                                url: link.href || '',
                                image: img ? img.src : ''
                            });
                        }
                    });
                }

                // Fallback: CandidateBaseInfo cards
                if (candidates.length === 0) {
                    const cards = document.querySelectorAll('[class*="CandidateBaseInfo"], [class*="candidate"]');
                    cards.forEach((card, i) => {
                        const h2 = card.querySelector('h2');
                        const p = card.querySelector('p');
                        const img = card.querySelector('img');
                        const allText = card.textContent;
                        const pctMatch = allText.match(/(\\d+)%\\s*enighed/);
                        if (h2) {
                            candidates.push({
                                rank: i + 1,
                                name: h2.textContent.trim(),
                                party: p ? p.textContent.trim() : '',
                                match_pct: pctMatch ? parseInt(pctMatch[1]) : 0,
                                url: card.href || '',
                                image: img ? img.src : ''
                            });
                        }
                    });
                }
                return candidates.slice(0, 6);
            }
        """)
        candidates = data
    except Exception as e:
        log.error(f"JS extraction failed: {e}")
        try:
            text = await page.text_content("body")
            matches = re.findall(r"(\d+)%\s*enighed", text)
            for i, m in enumerate(matches[:6]):
                candidates.append({
                    "rank": i + 1,
                    "name": f"Unknown_{i+1}",
                    "party": "Unknown",
                    "match_pct": int(m),
                    "url": "",
                    "image": "",
                })
        except Exception:
            pass

    return candidates
