"""
csv_io.py — CSV read/write helpers for the DR Kandidattest scraper.

Handles creation and appending of the flat results CSV file that the
Streamlit dashboard reads for visualization.
"""

import csv
from config import CSV_PATH, CSV_HEADER


def ensure_csv():
    """Create the CSV file with a header row if it doesn't already exist."""
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def append_csv(rows: list[dict]):
    """Append one or more result rows to the CSV file.

    Each row dict should have keys matching CSV_HEADER.
    """
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        for row in rows:
            writer.writerow(row)
