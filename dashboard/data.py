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

from config import DB_PATH, ANSWER_LABELS

# Environment detection for Render.com Persistent Disk
IS_RENDER = os.environ.get('RENDER') == 'true'
BASE_DIR = Path(__file__).resolve().parent.parent

# The precomputed JSON files are checked into Git, so they are ALWAYS in the project directory
PRECOMPUTED_DIR = BASE_DIR / 'data' / 'precomputed'

def _get_active_db_path() -> str:
    if IS_RENDER:
        render_db = Path('/data/history.db')
        if render_db.exists():
            return str(render_db)
    return str(DB_PATH)

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
    """Load stats for the most recommended candidates and their rank distribution.
    Ensures 'candidate_name' is present in top_candidates."""
    data = _load_json("candidate_gaming.json")
    if not data: return pd.DataFrame(), pd.DataFrame()
    
    top_cands = pd.DataFrame(data["top_candidates"])
    rank_break = pd.DataFrame(data["rank_breakdown"])
    
    # Normalize naming
    if not top_cands.empty:
        if "name" in top_cands.columns and "candidate_name" not in top_cands.columns:
            top_cands = top_cands.rename(columns={"name": "candidate_name"})
            
    return top_cands, rank_break

@st.cache_data(show_spinner=False, ttl=3600)
def load_kommune_stats() -> pd.DataFrame:
    """Load geographical red/blue block distribution."""
    path = PRECOMPUTED_DIR / "kommune_stats.json"
    if not path.exists(): return pd.DataFrame()
    return pd.read_json(path, orient="records")


# ── Legacy Functions (Still used, optimized) ─────────────────────────────────

@st.cache_data(show_spinner=False, ttl=300)
def load_run_answers() -> pd.DataFrame:
    """Load user answer data from precomputed sample to prevent OS-level DB locks.
    Optimized for performance."""
    try:
        data = _load_json("answers_sample.json")
        if not data:
            return pd.DataFrame()
            
        answers = []
        valid_ids = []
        for row in data:
            try:
                aj = row.get("answers_json")
                if isinstance(aj, str):
                    ans_list = json.loads(aj)
                else:
                    ans_list = aj
                if isinstance(ans_list, list) and len(ans_list) == 25:
                    answers.append(ans_list)
                    valid_ids.append(row["run_id"])
            except:
                continue
        
        if not answers: return pd.DataFrame()
        
        df_ans = pd.DataFrame(answers, columns=[f"Q{i+1}" for i in range(25)])
        df_ans.insert(0, 'run_id', valid_ids)
        return df_ans
    except Exception as e:
        print(f"Error loading run answers from JSON: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=3600)
def load_db_top1() -> pd.DataFrame:
    """Load top-1 match results. Bypassed to prevent DB locks."""
    return pd.DataFrame()

# ── Load Candidates Data ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=3600)
def load_candidates_data() -> pd.DataFrame:
    """Load the pre-scraped candidates and their 25 answers into a DataFrame.
    Normalizes 'name' to 'candidate_name' for dashboard compatibility."""
    try:
        path = BASE_DIR / "all_candidates.json"
        if not path.exists():
            return pd.DataFrame()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        if "name" in df.columns:
            df = df.rename(columns={"name": "candidate_name"}, errors="ignore")
            
        # Optional: clean up party names if they contain the candidate name
        if "candidate_name" in df.columns and "party" in df.columns:
            # Vectorized cleanup for speed
            df["party"] = df.apply(lambda x: str(x["party"]).replace(str(x["candidate_name"]), "").strip(), axis=1)

        # Expand answers list into Q1..Q25
        for i in range(25):
            df[f"Q{i+1}"] = df["answers"].apply(lambda x: x[i] if (isinstance(x, list) and len(x) > i) else None)
        return df
    except Exception as e:
        print(f"Error loading candidates: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=3600)
def load_questions() -> dict:
    """Load question ID to Text mapping from precomputed JSON."""
    path = PRECOMPUTED / "questions.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        # JSON keys are strings, convert to int
        return {int(k): v for k, v in raw.items()}
    return {}

@st.cache_data(show_spinner=False, ttl=60)
def load_db_stats() -> dict:
    """Load scraper run statistics. Bypassed to prevent DB locks."""
    return {"total": 0, "done": 0, "failed": 0, "failed_recent": 0, "running": 0, "speed_per_hour": 0}
