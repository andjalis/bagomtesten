"""
dashboard.data — Data loading and caching layer for the dashboard.
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
DATA_DIR = '/data' if IS_RENDER else '.'
DB_PATH = os.path.join(DATA_DIR, 'history.db')
CSV_PATH = os.path.join(DATA_DIR, 'results.csv')

def _get_db_path() -> str:
    # Use /data/history.db if it exists, else fallback to local
    return DB_PATH if os.path.exists(DB_PATH) else 'history.db'

def _get_csv_path() -> str:
    return CSV_PATH if os.path.exists(CSV_PATH) else 'results.csv'


@st.cache_data(show_spinner=False, ttl=3600)
def load_csv() -> pd.DataFrame:
    """Load the latest simulation answers from CSV and attach candidate images."""
    try:
        # Heavily optimized for Render's 512MB RAM tier
        usecols = [
            "run_id",
            "municipality",
            "candidate_rank",
            "candidate_name",
            "party",
            "match_pct"
        ]
        dtypes = {
            "municipality": "category",
            "candidate_rank": "int8",
            "candidate_name": "category",
            "party": "category",
            "match_pct": "int8"
        }
        
        # Severely limit rows on Render to prevent OOM
        nrows = 1_000_000 if IS_RENDER else None
        
        df = pd.read_csv(_get_csv_path(), usecols=usecols, dtype=dtypes, nrows=nrows, low_memory=False)
        
        conn = sqlite3.connect(_get_db_path())
        media_df = pd.read_sql_query("SELECT candidate_name, candidate_image FROM candidate_media", conn)
        conn.close()
        
        # Merge if media was found
        if not media_df.empty:
            media_df = media_df.drop_duplicates(subset=["candidate_name"])
            df = df.merge(media_df, on="candidate_name", how="left")
            
        if 'candidate_image' not in df.columns:
            df['candidate_image'] = ""
            
        df['candidate_image'] = df['candidate_image'].fillna("")
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def load_simulation_meta() -> dict:
    """Load metadata for the simulation hero banner."""
    try:
        conn = sqlite3.connect(_get_db_path())
        df = pd.read_sql_query("SELECT COUNT(DISTINCT municipality) as storkredse, COUNT(DISTINCT answer_hash) as user_variants FROM runs WHERE status='done'", conn)
        conn.close()
        
        storkredse = int(df['storkredse'].iloc[0]) if not df.empty else 10
        user_variants = int(df['user_variants'].iloc[0]) if not df.empty else 100000
        
        return {
            "storkredse": storkredse,
            "total_candidates": 714, # known from LHS
        }
    except Exception as e:
        print(f"Error loading simulation meta: {e}")
        return {"storkredse": 10, "total_candidates": 714}


@st.cache_data(show_spinner=False, ttl=3600)
def load_candidates_data() -> pd.DataFrame:
    """Load the pre-scraped candidates and their 25 answers into a DataFrame.
    Used for intra-party alignment analysis (Partisoldat vs Oprører)."""
    try:
        with open("all_candidates.json", "r", encoding="utf-8") as f:
            candidates = json.load(f)
            
        rows = []
        for c in candidates:
            if c.get("has_answers") and c.get("answers") and len(c["answers"]) == 25:
                raw_party = c.get("party", "Ukendt")
                name = c["name"]
                if raw_party.startswith(name):
                    raw_party = raw_party[len(name):].strip()
                
                rows.append({
                    "name": name,
                    "party": raw_party,
                    "answers": c["answers"]
                })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error loading candidates: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=60)
def load_db_top1() -> pd.DataFrame:
    """Load rank-1 results directly from the history database for correlation analysis."""
    try:
        conn = sqlite3.connect(_get_db_path())
        df = pd.read_sql_query("SELECT run_id, party, match_pct FROM results WHERE rank=1", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading top1 from DB: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=60)
def load_db_stats() -> dict:
    """Load scraper run statistics from SQLite."""
    try:
        conn = sqlite3.connect(_get_db_path())
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


@st.cache_data(show_spinner=False, ttl=3600)
def load_run_answers() -> pd.DataFrame:
    """Load answer vectors for all completed runs.
    Parses the JSON answer arrays stored in runs.answers_json into
    25 separate columns (Q1-Q25) for correlation and pattern analysis."""
    try:
        conn = sqlite3.connect(_get_db_path())
        df = pd.read_sql_query("SELECT id, answers_json, status FROM runs WHERE status='done'", conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
            
        answers_list = df['answers_json'].apply(json.loads).tolist()
        answers_df = pd.DataFrame(answers_list, columns=[f"Q{i+1}" for i in range(1, 26)])
        answers_df['run_id'] = df['id']
        return answers_df
    except Exception as e:
        print(f"Error loading run answers: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner=False, ttl=3600)
def load_questions() -> dict:
    """Load question texts from the database.
    Returns: Dict mapping question_number (int) -> question_text (str)."""
    try:
        conn = sqlite3.connect(_get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT question_number, question_text FROM questions")
        results = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in results}
    except Exception as e:
        print(f"Error loading questions: {e}")
        return {}
