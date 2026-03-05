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

from config import REFRESH_INTERVAL, normalize_parties_df, PARTY_COLORS
from dashboard.css import DASHBOARD_CSS
from dashboard.data import load_global_kpis
from dashboard.sections import (
    render_party_distribution,
    render_partier_unified,
    render_data_foundation,
    render_blok_analysis_global,
    render_kpi_hero,
    render_party_pairs,
    render_valgkreds_section,
)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DR Kandidattest — Bias-dashboard",
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
    # ── Logos & Header ────────────────────────────────────────────────────────
    n_storkredse = kpis.get("storkredse", 0)
    n_candidates = kpis.get("total_candidates", 0)

    # Party letter mapping for logo badges
    PARTY_LETTERS = {
        "Socialdemokratiet": "A",
        "Radikale Venstre": "B",
        "Konservative": "C",
        "Socialistisk Folkeparti": "F",
        "Liberal Alliance": "I",
        "Moderaterne": "M",
        "Dansk Folkeparti": "O",
        "Venstre": "V",
        "Danmarksdemokraterne": "Æ",
        "Enhedslisten": "Ø",
        "Alternativet": "Å",
        "Borgernes Parti": "Q",
    }

    # Build party logo badges HTML
    party_badges_html = ""
    for party_name, letter in PARTY_LETTERS.items():
        color = PARTY_COLORS.get(party_name, "#374151")
        party_badges_html += f'<span class="party-badge" style="background-color: {color};" title="{party_name}">{letter}</span>'

    st.markdown(f"""
    <div class="main-header">
        <div class="header-logos">
            <span style="font-weight:900; font-size:1.6rem; color:#e4002b; letter-spacing:-1px; font-family:'Helvetica Neue',Arial,sans-serif;">DR</span>
            <span class="header-logo-divider">×</span>
            <span style="font-weight:700; font-size:1.3rem; color:#94a3b8; letter-spacing:0.5px; font-family:'Helvetica Neue',Arial,sans-serif;">ALTINGET</span>
        </div>
        <h1>Kandidattest: Bias & algoritme</h1>
        <p>LHS-simulering af {n_storkredse} storkredse • {n_candidates} kandidater med svar • FV26</p>
        <div class="party-badge-row">{party_badges_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Render Sections (Tabs) ────────────────────────────────────────────────
    tab_overordnet, tab_partier, tab_valgkreds, tab_method = st.tabs(
        ["Overordnet", "Partier", "Valgkreds", "Metode og data"]
    )

    with tab_overordnet:
        render_party_distribution()
        st.divider()

        render_party_pairs()
        st.divider()

        render_blok_analysis_global()
        st.divider()

    with tab_partier:
        render_partier_unified()

    with tab_valgkreds:
        render_valgkreds_section()

    with tab_method:
        render_data_foundation()
