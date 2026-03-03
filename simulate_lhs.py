"""
simulate_lhs.py — Nationwide LHS simulation of DR Kandidattest.

Generates 100,000 systematically distributed answer combinations per
municipality (storkreds) using Latin Hypercube Sampling (LHS), calculates
linear match % against all local candidates, and saves the Top-5 results
to results.csv — the same format read by the Streamlit dashboard.

Why LHS over pure random?
    Latin Hypercube Sampling guarantees that each answer option (0–3) is
    represented equally across all 25 questions, ensuring uniform coverage
    of the political answer space. This is critical for unbiased analysis.

Usage:
    python simulate_lhs.py                     # 100,000 runs per storkreds
    python simulate_lhs.py --runs 10000        # Custom run count
    python simulate_lhs.py --seed 99           # Custom random seed
"""

import argparse
import json
import time

import numpy as np
import pandas as pd
from tqdm import tqdm

from config import CSV_HEADER, normalize_party_name
from scraper.sampling import generate_lhs_combinations, answer_hash

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_RUNS = 100_000
TOP_K = 5          # Save top-K candidates per run
CHUNK_SIZE = 5_000  # Process in chunks to keep memory usage low
OUTPUT_FILE = "results.csv"


def load_candidates(path: str = "all_candidates.json") -> dict[str, list]:
    """Load scraped candidates and group them by municipality (storkreds).

    Only candidates with all 25 answers are included in the simulation.

    Returns:
        Dict mapping storkreds name → list of candidate dicts with keys:
        name, party, answers (list of 25 ints).
    """
    with open(path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    mun_map: dict[str, list] = {}
    for c in candidates:
        if c.get("has_answers") and c.get("answers") and len(c["answers"]) == 25:
            mun = c.get("municipality", "Ukendt")
            if mun not in mun_map:
                mun_map[mun] = []

            # The scraped party field is "{name}{party}" concatenated — strip name prefix.
            raw_party = c.get("party", "Ukendt")
            name = c["name"]
            if raw_party.startswith(name):
                raw_party = raw_party[len(name):].strip()

            mun_map[mun].append({
                "name": name,
                "party": normalize_party_name(raw_party) if raw_party else "Ukendt",
                "answers": c["answers"],
            })
    return mun_map


def calc_matches(user_chunk: np.ndarray, candidate_matrix: np.ndarray) -> np.ndarray:
    """Vectorised linear match % calculation (DR's algorithm).

    Args:
        user_chunk:       shape (N, 25) — user answer vectors
        candidate_matrix: shape (M, 25) — candidate answer vectors

    Returns:
        match_pct: shape (N, M) — integer match percentages [0, 100]
    """
    # Broadcast: (N, 1, 25) vs (1, M, 25)
    u = user_chunk[:, np.newaxis, :]
    c = candidate_matrix[np.newaxis, :, :]

    # DR formula: (1 - total_abs_diff / max_possible_diff) * 100
    diff = np.abs(u - c)
    n_answered = user_chunk.shape[1]   # all 25 answered (no skips in LHS)
    max_diff = n_answered * 3
    total_diff = diff.sum(axis=2)      # shape (N, M)

    return np.round((1 - total_diff / max_diff) * 100).astype(int)


def simulate_municipality(
    mun_name: str,
    candidates: list[dict],
    user_answers: list[list[int]],
) -> list[tuple]:
    """Simulate all runs for one municipality and return CSV rows.

    Args:
        mun_name:     Municipality / storkreds name.
        candidates:   List of candidate dicts (name, party, answers).
        user_answers: List of 100k answer vectors (each 25 ints).

    Returns:
        List of tuples matching CSV_HEADER column order.
    """
    C = np.array([c["answers"] for c in candidates])  # (M, 25)
    cand_names = [c["name"] for c in candidates]
    cand_parties = [c["party"] for c in candidates]
    n_runs = len(user_answers)
    rows: list[tuple] = []

    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    for start in range(0, n_runs, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, n_runs)
        chunk = np.array(user_answers[start:end])       # (chunk, 25)
        match_pct = calc_matches(chunk, C)              # (chunk, M)

        for i in range(end - start):
            run_id = f"lhs_{mun_name}_{start + i}"
            ans_list = chunk[i].tolist()
            ahash = answer_hash(ans_list)
            ans_str = json.dumps(ans_list)
            pcts = match_pct[i]

            # Top-K candidates sorted by descending match %
            top_indices = np.argsort(-pcts)[:min(TOP_K, len(candidates))]
            for rank, c_idx in enumerate(top_indices, 1):
                rows.append((
                    run_id, ahash, ans_str, mun_name,
                    rank, cand_names[c_idx], cand_parties[c_idx], pcts[c_idx], ts,
                ))

    return rows


def main():
    parser = argparse.ArgumentParser(description="Simulate DR Kandidattest with LHS answers.")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS,
                        help=f"Number of simulated runs per municipality (default: {DEFAULT_RUNS})")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for LHS (default: 42, ensures reproducibility)")
    args = parser.parse_args()

    # ── Load Data ─────────────────────────────────────────────────────────────
    print("Indlæser kandidater fra all_candidates.json...")
    mun_map = load_candidates()
    print(f"Fandt {len(mun_map)} storkredse med kandidater.\n")

    # ── Generate LHS answer combinations ──────────────────────────────────────
    print(f"Genererer {args.runs:,} LHS svar-kombinationer (seed={args.seed})...")
    user_answers = generate_lhs_combinations(args.runs, seed=args.seed)
    print(f"LHS genereret. Starter simulation...\n")

    # ── Write CSV header ───────────────────────────────────────────────────────
    pd.DataFrame(columns=CSV_HEADER).to_csv(OUTPUT_FILE, index=False)

    # ── Simulate per municipality ──────────────────────────────────────────────
    global_start = time.time()
    total_rows = 0

    for mun_name, candidates in tqdm(mun_map.items(), desc="Storkredse", unit="storkreds"):
        rows = simulate_municipality(mun_name, candidates, user_answers)
        if rows:
            pd.DataFrame(rows, columns=CSV_HEADER).to_csv(
                OUTPUT_FILE, mode="a", header=False, index=False
            )
            total_rows += len(rows)

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - global_start
    print(f"\n{'='*60}")
    print(f"SIMULATION FÆRDIG")
    print(f"Storkredse:          {len(mun_map)}")
    print(f"Kørsler per storkreds: {args.runs:,}")
    print(f"Totale rækker skrevet: {total_rows:,}")
    print(f"Tid: {elapsed/60:.1f} min")
    print(f"Gemt til: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
