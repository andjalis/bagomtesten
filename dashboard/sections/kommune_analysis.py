"""Kommune / Lokalt Nedslag section — per-municipality interactive analysis."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout
from dashboard.sections.gaming_analysis import _render_candidate_cards


from dashboard.data import load_candidates_data, load_questions, load_kommune_stats, load_candidate_gaming
from dashboard.sections.gaming_analysis import _render_candidate_cards


def render_kommune_analysis():
    """Render interactive analysis for a single selected municipality from precomputed data."""
    st.header("📍 Lokalt nedslag (kommune-søgning)")
    st.caption("Vælg en specifik kommune for at analysere, hvordan testen falder ud lokalt.")

    k_stats = load_kommune_stats()
    if k_stats.empty:
        st.info("Ingen kommunedata tilgængelig.")
        return

    all_munis = sorted(k_stats["Kommune"].dropna().unique())
    selected_muni = st.selectbox(
        "Vælg kommune", options=all_munis,
        index=all_munis.index("København") if "København" in all_munis else 0,
    )

    st.divider()

    muni_row = k_stats[k_stats["Kommune"] == selected_muni]
    if muni_row.empty:
        st.info(f"Ingen simuleret data for {selected_muni}.")
        return

    muni_row = muni_row.iloc[0]

    # Stats cards
    num_sims = muni_row.get("Total_Tests", 0)
    most_rec_party = muni_row.get("Top_Party", "N/A")
    top_block = muni_row.get("Vinder_Blok", "N/A")

    col1, col3, col4 = st.columns(3)
    with col1:
        st.metric("Simulerede testkørsler", f"{num_sims:,}".replace(",", "."))
    with col3:
        st.metric("Top-anbefalet parti", most_rec_party)
    with col4:
        st.metric("Vinder-Blok", top_block)

    st.divider()

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_right:
        st.subheader("📊 Blok-fordeling lokalt")
        st.caption("Procentvis andel af anbefalinger rullet op på rød og blå blok.")

        # Simply show the block distribution since we have that precalculated
        red_pct = muni_row.get("Red_Pct", 0)
        blue_pct = muni_row.get("Blue_Pct", 0)
        undet_pct = 100 - red_pct - blue_pct

        fig_party = go.Figure(data=[
            go.Bar(
                x=["Rød Blok", "Blå Blok", "Andet"],
                y=[red_pct, blue_pct, undet_pct],
                texttemplate="%{y:.1f}%", textposition="outside",
                textfont=dict(color="#94a3b8", size=11),
                marker_color=["#ef4444", "#3b82f6", "#64748b"],
            )
        ])
        fig_party.update_layout(**base_layout(
            title="",
            xaxis=dict(title="", tickangle=-45),
            yaxis=dict(title="Andel af anbefalinger (%)", range=[0, 100]),
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
        ))
        st.plotly_chart(fig_party, use_container_width=True)

    with col_left:
        st.subheader("🥇 Hvem dominerede testen her?")
        st.caption("Kandidater der oftest tonede frem på skærmen som absolutte top-match for testtagerne.")

        top_candidates, _ = load_candidate_gaming()
        if not top_candidates.empty:
            muni_candidates = top_candidates[top_candidates["municipality"] == selected_muni]
            if not muni_candidates.empty:
                _render_candidate_cards(muni_candidates, key_prefix="kommune")
            else:
                st.info("Ingen kandidater at vise for denne kommune.")
        else:
            st.info("Utilstrækkelig data til at bygge kandidatkort for denne kommune.")
