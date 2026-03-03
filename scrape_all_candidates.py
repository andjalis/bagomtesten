"""
scrape_all_candidates.py — Scrape ALL candidates from DR Kandidattest.

Iterates through candidate IDs 1–950 at:
  https://www.dr.dk/nyheder/politik/folketingsvalg/din-stemmeseddel/kandidater/{id}

For each candidate, extracts:
  - Name, party, municipality/storkreds
  - 25 answers (0=Uenig, 1=Lidt uenig, 2=Lidt enig, 3=Enig)

Uses progressive scroll extraction to handle lazy-loaded DOM elements.
Saves progress after each candidate to all_candidates.json.
"""

import asyncio
import json
import os
import re
import time
from playwright.async_api import async_playwright, Page

OUTPUT_FILE = "all_candidates.json"
BASE_URL = "https://www.dr.dk/nyheder/politik/folketingsvalg/din-stemmeseddel/kandidater"
MAX_ID = 950
CONCURRENCY = 10  # Number of parallel browser tabs


async def extract_candidate_info(page: Page, candidate_id: int) -> dict | None:
    """Navigate to a candidate page and extract all info."""
    url = f"{BASE_URL}/{candidate_id}"
    
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        if resp and resp.status == 404:
            return None
    except Exception:
        return None
    
    await asyncio.sleep(1.5)
    
    # Dismiss cookie banner if present
    try:
        btn = page.locator("button.drcc-button.submitAll, button:has-text('Tillad alle')").first
        if await btn.is_visible(timeout=2000):
            await btn.click()
            await asyncio.sleep(0.5)
    except Exception:
        pass
    
    # Check if this is a valid candidate page (has name + answers)
    try:
        info = await page.evaluate("""
            () => {
                // Extract candidate name
                const nameEl = document.querySelector('h2[class*="CandidateBaseInfo_name"]');
                const name = nameEl ? nameEl.textContent.trim() : null;
                if (!name) return null;
                
                // Extract party and municipality
                const infoEl = document.querySelector('div[class*="CandidateBaseInfo_candidateInfo"]');
                let party = '';
                let municipality = '';
                
                if (infoEl) {
                    const text = infoEl.textContent.trim();
                    const parts = text.split('|').map(s => s.trim());
                    if (parts.length >= 1) party = parts[0];
                    if (parts.length >= 2) municipality = parts[1];
                }
                
                return { name, party, municipality };
            }
        """)
        
        if not info or not info.get("name"):
            return None
            
    except Exception:
        return None
    
    # Check if candidate has answered the test
    has_answers = False
    try:
        has_answers = await page.evaluate("""
            () => {
                const text = document.body.innerText;
                return text.includes('/25') && (text.includes('svar') || text.includes('Uenig'));
            }
        """)
    except Exception:
        pass
    
    if not has_answers:
        return {
            "id": candidate_id,
            "name": info["name"],
            "party": info.get("party", ""),
            "municipality": info.get("municipality", ""),
            "answers": None,
            "url": f"{BASE_URL}/{candidate_id}",
            "has_answers": False,
        }
    
    # Expand the list
    try:
        vis_alle_btn = page.locator("button[aria-label='Vis alle svar'], button:has-text('Vis alle')").first
        if await vis_alle_btn.is_visible(timeout=3000):
            await vis_alle_btn.click()
            await asyncio.sleep(1.5)
    except Exception:
        pass
    
    # Progressive scroll extraction (proven method from KBH scraping)
    all_answers = [None] * 25
    
    for scroll_idx in range(25):
        try:
            results = await page.evaluate("""
                () => {
                    const markers = Array.from(document.querySelectorAll('div, span, button')).filter(el => 
                        el.textContent && el.textContent.match(/svar$/i) && el.textContent.length < 40
                    );
                    
                    const batch = [];
                    for (const marker of markers) {
                        const mRect = marker.getBoundingClientRect();
                        const markerCenter = mRect.x + mRect.width / 2;
                        
                        // Find question number (X/25)
                        let container = marker.parentElement;
                        let qNum = null;
                        for (let i = 0; i < 8; i++) {
                            if (!container) break;
                            const t = container.textContent;
                            const match = t.match(/(\\d+)\\/25/);
                            if (match) {
                                qNum = parseInt(match[1], 10);
                                break;
                            }
                            container = container.parentElement;
                        }
                        
                        // Find chosen label
                        container = marker.parentElement;
                        let labels = [];
                        for (let i = 0; i < 6; i++) {
                            if (!container) break;
                            labels = Array.from(container.querySelectorAll('label[aria-label]'));
                            if (labels.length >= 4) break;
                            container = container.parentElement;
                        }
                        
                        let answerVal = null;
                        if (labels.length >= 4) {
                            const validLabels = labels.filter(l => 
                                ["Uenig", "Lidt uenig", "Lidt enig", "Enig"].includes(l.getAttribute('aria-label'))
                            );
                            
                            let closestLabel = null;
                            let minDistance = 9999;
                            
                            const validSiblingLabels = validLabels.filter(l => 
                                Math.abs(l.getBoundingClientRect().y - mRect.y) < 150
                            );
                            
                            for (const label of validSiblingLabels) {
                                const lRect = label.getBoundingClientRect();
                                const lCenter = lRect.x + lRect.width / 2;
                                const dist = Math.abs(markerCenter - lCenter);
                                if (dist < minDistance) {
                                    minDistance = dist;
                                    closestLabel = label.getAttribute('aria-label');
                                }
                            }
                            
                            if (closestLabel) {
                                const map = {"Uenig": 0, "Lidt uenig": 1, "Lidt enig": 2, "Enig": 3};
                                answerVal = map[closestLabel];
                            }
                        }
                        
                        if (qNum !== null && answerVal !== null) {
                            batch.push({q: qNum - 1, a: answerVal});
                        }
                    }
                    return batch;
                }
            """)
            
            if results:
                for r in results:
                    q_idx = r['q']
                    if 0 <= q_idx < 25:
                        all_answers[q_idx] = r['a']
            
            if sum(1 for a in all_answers if a is not None) == 25:
                break
                
            await page.evaluate("window.scrollBy(0, 400)")
            await asyncio.sleep(0.25)
            
        except Exception:
            pass
    
    found = sum(1 for a in all_answers if a is not None)
    
    return {
        "id": candidate_id,
        "name": info["name"],
        "party": info.get("party", ""),
        "municipality": info.get("municipality", ""),
        "answers": all_answers if found > 0 else None,
        "answers_found": found,
        "url": f"{BASE_URL}/{candidate_id}",
        "has_answers": found == 25,
    }


async def main():
    # Load existing progress
    existing = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for c in data:
                existing[c["id"]] = c
    
    print(f"Existing progress: {len(existing)} candidates already scraped.")
    
    # Find which IDs still need scraping
    todo_ids = [i for i in range(1, MAX_ID + 1) if i not in existing]
    print(f"Remaining to scrape: {len(todo_ids)} IDs")
    
    if not todo_ids:
        print("All done!")
        return
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        
        # Create multiple pages for parallel scraping
        contexts = []
        pages = []
        for _ in range(CONCURRENCY):
            ctx = await browser.new_context(
                viewport={"width": 1440, "height": 1080},
                locale="da-DK",
            )
            p = await ctx.new_page()
            contexts.append(ctx)
            pages.append(p)
        
        idx = 0
        total = len(todo_ids)
        start_time = time.time()
        found_count = 0
        no_answers_count = 0
        
        while idx < total:
            # Launch a batch of CONCURRENCY tasks
            batch = []
            for page_idx in range(CONCURRENCY):
                if idx + page_idx < total:
                    cid = todo_ids[idx + page_idx]
                    batch.append(extract_candidate_info(pages[page_idx], cid))
            
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for r in results:
                if isinstance(r, Exception):
                    continue
                if r is not None:
                    existing[r["id"]] = r
                    if r.get("has_answers"):
                        found_count += 1
                    elif r.get("name"):
                        no_answers_count += 1
            
            idx += CONCURRENCY
            
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total - idx) / rate if rate > 0 else 0
            
            print(
                f"[{idx}/{total}] "
                f"Found: {found_count} with answers, {no_answers_count} without | "
                f"Speed: {rate:.1f} IDs/sec | ETA: {eta/60:.1f} min"
            )
            
            # Save progress after every batch
            all_candidates = sorted(existing.values(), key=lambda x: x["id"])
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_candidates, f, indent=2, ensure_ascii=False)
        
        for ctx in contexts:
            await ctx.close()
        await browser.close()
    
    # Final summary
    all_candidates = sorted(existing.values(), key=lambda x: x["id"])
    with_answers = [c for c in all_candidates if c.get("has_answers")]
    without = [c for c in all_candidates if c.get("name") and not c.get("has_answers")]
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"Total candidate pages found: {len([c for c in all_candidates if c.get('name')])}")
    print(f"With 25 answers: {len(with_answers)}")
    print(f"Without answers: {len(without)}")
    print(f"Saved to {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
