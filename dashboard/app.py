"""
dashboard.app — Streamlit entry point for DR Kandidattest bias analysis.

This is the page layout skeleton. All data loading, CSS, and chart rendering
are delegated to dedicated modules:
    - dashboard.css              → Custom CSS styles
    - dashboard.data             → Cached data loading functions
    - dashboard.sections         → Chart rendering sub-package
    - config                     → Shared constants (colors, labels, paths)

Run with:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `config` and `dashboard.*` resolve
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import time

import streamlit as st

from config import REFRESH_INTERVAL, normalize_parties_df
from dashboard.css import DASHBOARD_CSS
from dashboard.data import load_global_kpis
from dashboard.sections import (
    render_party_distribution,
    render_gaming_analysis,
    render_question_impact,
    render_party_drilldown,
    render_data_foundation,
    render_kommune_analysis,
    render_blok_analysis_global,
    render_kpi_hero,
    render_party_pairs,
    render_party_comparison,
)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DR Kandidattest — Bias Dashboard",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────────────────────
kpis = load_global_kpis()

if not kpis or kpis.get("total_simulations", 0) == 0:
    st.divider()
    st.info(
        "🔄 Ingen simulationsdata fundet. Kør data-compilen med `python tools/build_dashboard_data.py` for at generere JSON-views.",
        icon="📊",
    )
    time.sleep(REFRESH_INTERVAL)
    st.rerun()

else:
    # ── Header ────────────────────────────────────────────────────────────────────
    n_storkredse = kpis.get("storkredse", 0)
    n_candidates = kpis.get("total_candidates", 0)

    st.markdown(f"""
    <div class="main-header">
        <h1>Kandidattest: Bias & Algoritme</h1>
        <p>LHS-simulering af {n_storkredse} storkredse • {n_candidates} kandidater med svar • FV26</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric KPI Hero (Above Tabs) ──
    render_kpi_hero(kpis)
    st.divider()

    # ── Render Sections (Tabs) ────────────────────────────────────────────────
    tab_global, tab_party, tab_compare, tab_kommune, tab_method = st.tabs(
        ["🌍 Global Analyse", "🔍 Parti-Drilldown", "⚖️ Sammenlign Partier", "📍 Lokalt Nedslag", "⚙️ Metode & Data"]
    )

    with tab_global:
        render_party_distribution()
        st.divider()

        render_gaming_analysis()
        st.divider()

        render_party_pairs()
        st.divider()

        render_question_impact()
        st.divider()

        render_blok_analysis_global()
        st.divider()

    with tab_party:
        render_party_drilldown()
        
    with tab_compare:
        render_party_comparison()

    with tab_kommune:
        render_kommune_analysis()

    with tab_method:
        render_data_foundation()
