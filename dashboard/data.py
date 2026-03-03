"""
dashboard.data — Data loading and caching layer for the dashboard.
Refactored to serve pre-computed lightweight JSON files instead of 
parsing massive CSVs on-the-fly, to ensure safe memory footprints.
"""

import json
import sqlite3
import time
import os
from pathlib import Path
import pandas as pd
import streamlit as st

# Environment detection for Render.com Persistent Disk
IS_RENDER = os.environ.get('RENDER') == 'true'
BASE_DIR = Path(__file__).resolve().parent.parent

if IS_RENDER:
    # On Render, raw data/history.db lives on the persistent disk mounted at /data
    PERSISTENT_DIR = Path('/data')
else:
    PERSISTENT_DIR = BASE_DIR / 'data'

# The precomputed JSON files are checked into Git, so they are ALWAYS in the project directory
PRECOMPUTED_DIR = BASE_DIR / 'data' / 'precomputed'
DB_PATH = str(PERSISTENT_DIR / 'history.db')

def _load_json(filename: str):
    path = PRECOMPUTED_DIR / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ──  Precomputed Data Getters ────────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=3600)
def load_global_kpis() -> dict:
    """Load lightweight summary KPIs (storkredse, bias_index, etc.)."""
    data = _load_json("global_kpis.json")
    if not data:
        # Fallback values if compiler hasn't run
        return {"storkredse": 10, "total_candidates": 714, "total_simulations": 0, "bias_index": 0}
    return data

@st.cache_data(show_spinner=False, ttl=3600)
def load_party_rankings() -> pd.DataFrame:
    """Load pre-aggregated top-1 party frequencies."""
    path = PRECOMPUTED_DIR / "party_rankings.json"
    if not path.exists(): return pd.DataFrame()
    return pd.read_json(path, orient="records")

@st.cache_data(show_spinner=False, ttl=3600)
def load_party_match_distributions() -> pd.DataFrame:
    """Load a stratified sample of match percentages for violin plots."""
    path = PRECOMPUTED_DIR / "party_match_distributions.json"
    if not path.exists(): return pd.DataFrame()
    return pd.read_json(path, orient="records")

@st.cache_data(show_spinner=False, ttl=3600)
def load_party_pairs() -> pd.DataFrame:
    """Load pre-aggregated matrix of Rank 1 vs Rank 2 party combinations."""
    path = PRECOMPUTED_DIR / "party_pairs.json"
    if not path.exists(): return pd.DataFrame()
    return pd.read_json(path, orient="records")

@st.cache_data(show_spinner=False, ttl=3600)
def load_question_impact() -> pd.DataFrame:
    """Load pre-calculated effect sizes of each question on top_match_pct."""
    path = PRECOMPUTED_DIR / "question_impact.json"
    if not path.exists(): return pd.DataFrame()
    return pd.read_json(path, orient="records")

@st.cache_data(show_spinner=False, ttl=3600)
def load_candidate_gaming() -> tuple:
    """Load stats for the most recommended candidates and their rank distribution."""
    data = _load_json("candidate_gaming.json")
    if not data: return pd.DataFrame(), pd.DataFrame()
    return pd.DataFrame(data["top_candidates"]), pd.DataFrame(data["rank_breakdown"])

@st.cache_data(show_spinner=False, ttl=3600)
def load_kommune_stats() -> pd.DataFrame:
    """Load geographical red/blue block distribution."""
    path = PRECOMPUTED_DIR / "kommune_stats.json"
    if not path.exists(): return pd.DataFrame()
    return pd.read_json(path, orient="records")


# ── Legacy Functions (Still used, optimized) ─────────────────────────────────

@st.cache_data(show_spinner=False, ttl=3600)
def load_candidates_data() -> pd.DataFrame:
    """Load the pre-scraped candidates and their 25 answers into a DataFrame.
    Expands the answers list into Q1-Q25 columns for variance analysis.
    Used for intra-party alignment analysis (Partisoldat vs Oprører)."""
    try:
        path = BASE_DIR / "all_candidates.json"
        if not path.exists():
            return pd.DataFrame()
            
        with open(path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
            
        rows = []
        for c in candidates:
            if c.get("has_answers") and c.get("answers") and len(c["answers"]) == 25:
                raw_party = c.get("party", "Ukendt")
                name = c["name"]
                if raw_party.startswith(name):
                    raw_party = raw_party[len(name):].strip()
                
                row = {
                    "candidate_name": name,
                    "party": raw_party,
                    "municipality": c.get("municipality", c.get("storkreds", "Ukendt")),
                    "candidate_image": c.get("image", ""),
                }
                # Expand answers into Q1..Q25
                for i, ans in enumerate(c["answers"]):
                    row[f"Q{i+1}"] = ans
                rows.append(row)
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error loading candidates: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def load_questions() -> dict:
    """Load question texts from the database."""
    try:
        db = _find_db()
        if not db:
            return {}
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT question_number, question_text FROM questions")
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}
    except Exception as e:
        print(f"Error loading questions: {e}")
        return {}


@st.cache_data(show_spinner=False, ttl=3600)
def load_run_answers() -> pd.DataFrame:
    """Load user answer data from the scraped history database.
    Returns a DataFrame with run_id, Q1..Q25 columns.
    This is lightweight (~10K rows from SQLite)."""
    try:
        db = _find_db()
        if not db:
            return pd.DataFrame()
        conn = sqlite3.connect(db)
        df = pd.read_sql_query(
            "SELECT run_id, " + ", ".join(f"Q{i+1}" for i in range(25)) + " FROM run_answers",
            conn,
        )
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading run answers: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def load_db_top1() -> pd.DataFrame:
    """Load top-1 match results from the scraped history database.
    Returns a DataFrame with run_id, candidate_name, party, match_pct.
    This is lightweight (~10K rows from SQLite)."""
    try:
        db = _find_db()
        if not db:
            return pd.DataFrame()
        conn = sqlite3.connect(db)
        df = pd.read_sql_query(
            "SELECT run_id, candidate_name, party, match_pct FROM results WHERE rank = 1",
            conn,
        )
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading db top1: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=60)
def load_db_stats() -> dict:
    """Load scraper run statistics from SQLite."""
    try:
        db = _find_db()
        if not db:
            return {"total": 0, "done": 0, "failed": 0, "failed_recent": 0, "running": 0, "speed_per_hour": 0}
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM runs")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status='done'")
        done = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status='failed'")
        failed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status='running'")
        running = cursor.fetchone()[0]
        
        one_hour_ago = time.time() - 3600
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status='done' AND completed_at > ?", (one_hour_ago,))
        speed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM runs WHERE status='failed' AND completed_at > ?", (one_hour_ago,))
        failed_recent = cursor.fetchone()[0]
        
        conn.close()
        return {
            "total": total,
            "done": done,
            "failed": failed,
            "failed_recent": failed_recent,
            "running": running,
            "speed_per_hour": speed
        }
    except Exception as e:
        return {"total": 0, "done": 0, "failed": 0, "failed_recent": 0, "running": 0, "speed_per_hour": 0}


def _find_db() -> str | None:
    """Find the history.db file, checking multiple fallback locations."""
    candidates = [
        PERSISTENT_DIR / 'history.db',
        BASE_DIR / 'history.db',
        Path('history.db'),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None

