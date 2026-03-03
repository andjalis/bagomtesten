"""Kommune / Lokalt Nedslag section — per-municipality interactive analysis."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout
from dashboard.sections.gaming_analysis import _render_candidate_cards


def render_kommune_analysis(df: pd.DataFrame, top1: pd.DataFrame):
    """Render interactive analysis for a single selected municipality."""
    st.header("📍 Lokalt nedslag (kommune-søgning)")
    st.caption("Vælg en specifik kommune for at analysere, hvordan testen falder ud lokalt.")

    if top1.empty or "municipality" not in top1.columns:
        st.info("Ingen kommunedata tilgængelig.")
        return

    all_munis = sorted(top1["municipality"].dropna().unique())
    selected_muni = st.selectbox(
        "Vælg kommune", options=all_munis,
        index=all_munis.index("København") if "København" in all_munis else 0,
    )

    st.divider()

    muni_top1 = top1[top1["municipality"] == selected_muni]

    if muni_top1.empty:
        st.info(f"Ingen simuleret data for {selected_muni}.")
        return

    # Stats cards
    num_sims = len(muni_top1)
    unique_candidates = muni_top1["candidate_name"].nunique()
    most_rec_party = muni_top1["party"].mode()[0] if not muni_top1.empty else "N/A"

    col1, col3, col4 = st.columns(3)
    with col1:
        st.metric("Simulerede testkørsler", f"{num_sims:,}".replace(",", "."))
    with col3:
        st.metric("Top-anbefalet parti", most_rec_party)
    with col4:
        st.metric("Unikke kandidater vist", unique_candidates)

    st.divider()

    col_left, col_right = st.columns([3, 2], gap="large")

    with col_right:
        st.subheader("📊 Parti-anbefalinger lokalt")
        st.caption("Hvilke partier endte oftest som testens nr. 1 anbefaling her?")

        party_counts = muni_top1["party"].value_counts().reset_index()
        party_counts.columns = ["Parti", "Antal"]
        party_counts["Procent"] = (party_counts["Antal"] / len(muni_top1)) * 100

        fig_party = go.Figure(data=[
            go.Bar(
                x=party_counts["Parti"],
                y=party_counts["Procent"],
                texttemplate="%{y:.1f}%", textposition="outside",
                textfont=dict(color="#94a3b8", size=11),
                marker_color=[PARTY_COLORS.get(p, "#94a3b8") for p in party_counts["Parti"]],
            )
        ])
        fig_party.update_layout(**base_layout(
            title="",
            xaxis=dict(title="", tickangle=-45),
            yaxis=dict(title="Andel af anbefalinger (%)", range=[0, min(100, party_counts["Procent"].max() * 1.2)]),
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
        ))
        st.plotly_chart(fig_party, use_container_width=True)

    with col_left:
        st.subheader("🥇 Hvem dominerede testen her?")
        st.caption("Kandidater der oftest tonede frem på skærmen som absolutte top-match for testtagerne.")

        muni_df = df[df["municipality"] == selected_muni]
        if not muni_df.empty and not muni_top1.empty:
            _render_candidate_cards(muni_df, muni_top1)
        else:
            st.info("Utilstrækkelig data til at bygge kandidatkort for denne kommune.")
