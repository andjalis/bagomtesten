"""
config.py — Single source of truth for all shared constants and helpers.

This module centralizes configuration used by both the scraper engine
and the Streamlit dashboard, ensuring consistency across the application.
"""

from pathlib import Path

# ── File Paths ────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
DB_PATH = PROJECT_DIR / "history.db"
CSV_PATH = PROJECT_DIR / "results.csv"
LOG_PATH = PROJECT_DIR / "scraper.log"

# ── Scraper Settings ─────────────────────────────────────────────────────────
BASE_URL = "https://www.dr.dk/nyheder/politik/folketingsvalg/kandidattest"
NUM_QUESTIONS = 25
NUM_OPTIONS = 4
MIN_DELAY = 0.5   # Minimum human-like delay (seconds)
MAX_DELAY = 1.3   # Maximum human-like delay (seconds)
REFRESH_INTERVAL = 10  # Dashboard auto-refresh interval (seconds)

# ── Answer Mapping & Colors (Editorial Soft Tones) ───────────────────────────
# Integer index → Danish label text (matches aria-label on DR's site)
ANSWER_MAP = {
    0: "Uenig",
    1: "Lidt uenig",
    2: "Lidt enig",
    3: "Enig",
}
ANSWER_LABELS = ANSWER_MAP  # Alias used by dashboard

# Muted, premium palette for answer distributions (avoiding pure red/green)
ANSWER_COLORS = {
    "Uenig": "#e29578",       # Soft terracotta
    "Lidt uenig": "#ffddd2",  # Blush
    "Lidt enig": "#edf6f9",   # Softest sage
    "Enig": "#83c5be",        # Muted seafoam/sage
}

# ── Municipalities ────────────────────────────────────────────────────────────
# Diverse selection of Danish municipalities for location randomization.
# Using different municipalities ensures geographic spread in the test data
# and mimics organic traffic patterns to avoid bot detection.
MUNICIPALITIES = [
    "København", "Aarhus", "Odense", "Aalborg", "Esbjerg", "Vejle",
    "Randers", "Viborg", "Kolding", "Silkeborg", "Herning", "Horsens",
    "Roskilde", "Slagelse", "Holbæk", "Svendborg", "Sønderborg", "Hjørring",
    "Guldborgsund", "Frederikshavn", "Holstebro", "Ringkøbing-Skjern",
    "Frederiksberg", "Gentofte", "Gladsaxe", "Ishøj", "Albertslund", "Bornholm",
]

# ── User-Agents ───────────────────────────────────────────────────────────────
# Rotated randomly per worker to simulate diverse browser fingerprints.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

# ── CSV Header ────────────────────────────────────────────────────────────────
CSV_HEADER = [
    "run_id",
    "answer_hash",
    "answers",
    "municipality",
    "candidate_rank",
    "candidate_name",
    "party",
    "match_pct",
    "timestamp",
]

# ── Official Party Colors (Desaturated NYT-style) ─────────────────────────
# Hex codes based on official branding but slightly muted for an editorial feel.
PARTY_COLORS = {
    "Radikale Venstre": "#6b4c7a",       # Slightly softer purple
    "Konservative": "#8a9a5b",           # Softer olive
    "Socialistisk Folkeparti": "#cfaaaf",# Washed rose
    "Borgernes Parti": "#86b9b0",        # Muted teal
    "Liberal Alliance": "#6dafb9",       # Desaturated light blue
    "Moderaterne": "#a58dbb",            # Soft lavender
    "Dansk Folkeparti": "#d4c17b",       # Muted mustard
    "Venstre": "#3a4f6d",                # Slate blue
    "Danmarksdemokraterne": "#8598c2",   # Dusty blue
    "Enhedslisten": "#c9824f",           # Burnt orange/terracotta
    "Alternativet": "#578a53",           # Muted forest green
    "Socialdemokratiet": "#a3433a",      # Brick red
}

# ── Party Name Normalization ──────────────────────────────────────────────────
# DR's site sometimes uses abbreviated or variant party names.
# This mapping ensures all variants resolve to the canonical name used
# as key in PARTY_COLORS above.
PARTY_ALIASES = {
    "Radikale": "Radikale Venstre",
    "Det Konservative Folkeparti": "Konservative",
    "Det konservative folkeparti": "Konservative",
    "SF": "Socialistisk Folkeparti",
    "Socialistisk folkeparti": "Socialistisk Folkeparti",
    "Enhedsliste": "Enhedslisten",
    "Borgernes parti": "Borgernes Parti",
}


def normalize_party_name(name: str) -> str:
    """Return the canonical party name, resolving common aliases."""
    return PARTY_ALIASES.get(name, name)


def normalize_parties_df(df):
    """Normalize the 'party' column of a DataFrame in-place and return it."""
    if "party" in df.columns:
        df["party"] = df["party"].replace(PARTY_ALIASES)
    return df
