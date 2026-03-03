import pandas as pd
import sqlite3
import os
import streamlit as st
import glob

# Detect if we are running on Render (Render sets RENDER environment variable to 'true')
IS_RENDER = os.environ.get('RENDER') == 'true'

# Define paths based on environment
DATA_DIR = '/data' if IS_RENDER else '.'
DB_PATH = os.path.join(DATA_DIR, 'history.db')
CSV_PATH = os.path.join(DATA_DIR, 'results.csv')

@st.cache_data(ttl=3600)
def load_all_simulations():
    """Load all simulations from CSV"""
    if not os.path.exists(CSV_PATH):
        # Fallback to local directory if not found in /data (e.g., during local testing or missing files)
        fallback_csv = 'results.csv'
        if os.path.exists(fallback_csv):
            return pd.read_csv(fallback_csv)
        st.error(f"Data-filen '{CSV_PATH}' blev ikke fundet.")
        st.info("Kig under fanen 'Læs fil-status' for hjælp.")
        return pd.DataFrame()
    return pd.read_csv(CSV_PATH)

@st.cache_data(ttl=3600)
def load_kpi_metadata():
    """Load latest metadata row from DB"""
    try:
        # Use DB_PATH or fallback to local
        path_to_use = DB_PATH if os.path.exists(DB_PATH) else 'history.db'
        conn = sqlite3.connect(path_to_use)
        df = pd.read_sql("SELECT * FROM metadata ORDER BY id DESC LIMIT 1", conn)
        conn.close()
        if len(df) == 0:
            return None
        return df.iloc[0].to_dict()
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return None
