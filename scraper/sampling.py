"""
sampling.py — Latin Hypercube Sampling for DR Kandidattest.

Generates systematically distributed answer combinations across the
25-question × 4-option space to maximize coverage of the political spectrum.

Why LHS?
    Pure random sampling tends to cluster in certain regions of the answer space.
    Latin Hypercube Sampling guarantees that each quarter of each dimension
    (i.e. each answer option for each question) is sampled equally, pushing
    combinations into all corners of the political space. This is critical
    for bias detection: if we miss certain answer patterns, we might miss
    the algorithmic bias entirely.
"""

import hashlib
import json

import numpy as np
from scipy.stats import qmc

from config import ANSWER_MAP, NUM_QUESTIONS, NUM_OPTIONS


def generate_lhs_combinations(n_samples: int, seed: int = 42) -> list[list[int]]:
    """Generate n_samples answer combinations using Latin Hypercube Sampling.

    Each combination is a list of 25 integers in [0, 3].

    Args:
        n_samples: Number of unique answer vectors to generate.
        seed: Random seed for reproducibility. Two runs with the same
              seed and n_samples produce identical combinations, enabling
              the scraper to skip already-completed work.

    Returns:
        List of answer vectors (each a list of 25 ints).
    """
    sampler = qmc.LatinHypercube(d=NUM_QUESTIONS, seed=seed)
    raw = sampler.random(n=n_samples)  # shape (n_samples, 25), values in [0, 1)

    scaled = np.floor(raw * NUM_OPTIONS).astype(int)
    scaled = np.clip(scaled, 0, NUM_OPTIONS - 1)

    return scaled.tolist()


def answer_hash(answers: list[int]) -> str:
    """Create a deterministic 16-char hex hash of an answer combination.

    Used as a unique key to prevent duplicate runs in the database.
    """
    return hashlib.sha256(json.dumps(answers).encode()).hexdigest()[:16]


def answers_to_labels(answers: list[int]) -> list[str]:
    """Convert integer answers to their Danish aria-label strings."""
    return [ANSWER_MAP[a] for a in answers]


if __name__ == "__main__":
    combos = generate_lhs_combinations(10)
    for i, c in enumerate(combos):
        labels = answers_to_labels(c)
        h = answer_hash(c)
        print(f"Combo {i+1} [{h}]: {labels[:5]}... (showing first 5)")
