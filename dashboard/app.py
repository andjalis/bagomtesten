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

    # Build party logo badges HTML — clickable WITHOUT page refresh via JS & hidden Streamlit buttons
    party_badges_html = ""
    for party_name, letter in PARTY_LETTERS.items():
        color = PARTY_COLORS.get(party_name, "#374151")
        party_badges_html += (
            f'<span class="party-badge" data-party="{party_name}" '
            f'style="background-color: {color}; cursor: pointer; color: white;" '
            f'title="Se analyse af {party_name}">{letter}</span>'
        )

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

    # ── Hidden Streamlit integration ──
    # Generate hidden buttons that the JS will click. This forces a fast, in-place Streamlit 
    # rerun without a full browser refresh, maintaining a seamless SPA experience.
    for party_name in PARTY_LETTERS.keys():
        if st.button(f"Hidden_{party_name}", key=f"btn_nav_{party_name}"):
            st.query_params["parti"] = party_name

    # ── JS logic: Badge click handler, Hide Streamlit buttons, Auto-switch to Partier tab ──
    import streamlit.components.v1 as components
    components.html("""
    <script>
    // 1. Hide the ugly Streamlit buttons we just created for the routing
    const allBtns = window.parent.document.querySelectorAll('.stButton p');
    for (const p of allBtns) {
        if (p.innerText.startsWith('Hidden_')) {
            const container = p.closest('.stElementContainer');
            if (container) {
                container.style.display = 'none';
                container.style.margin = '0';
                container.style.padding = '0';
            }
        }
    }

    // 2. Define the function that triggers the hidden Streamlit buttons
    function clickStreamlitBadge(partyName) {
        const btns = window.parent.document.querySelectorAll('.stButton p');
        for (const p of btns) {
            if (p.innerText === "Hidden_" + partyName) {
                p.closest('button').click();
                break;
            }
        }
    }

    // 2b. Attach click listeners to all party badges in the parent document
    // (Streamlit strips inline onclick from st.markdown, so we attach here)
    const badges = window.parent.document.querySelectorAll('.party-badge[data-party]');
    badges.forEach(badge => {
        badge.addEventListener('click', () => {
            clickStreamlitBadge(badge.getAttribute('data-party'));
        });
    });

    // 3. Tab-switching logic if URL param is present
    const urlParams = new URLSearchParams(window.parent.location.search);
    if (urlParams.has('parti')) {
        function clickPartierTab() {
            const tabs = window.parent.document.querySelectorAll('[role="tab"]');
            for (const tab of tabs) {
                if (tab.textContent.includes('Partier')) {
                    if (tab.getAttribute('aria-selected') !== 'true') {
                        tab.click();
                    }
                    return true;
                }
            }
            return false;
        }
        
        if (!clickPartierTab()) {
            let attempts = 0;
            const interval = setInterval(() => {
                if (clickPartierTab() || attempts > 50) {
                    clearInterval(interval);
                }
                attempts++;
            }, 100);
        }
    }
    </script>
    """, height=0, width=0)

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
