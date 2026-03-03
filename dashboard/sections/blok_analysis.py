"""Blok analysis section — Red vs Blue block stacked bar chart."""

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from dashboard.sections._plotly_theme import base_layout


def render_blok_analysis_global(top1: pd.DataFrame):
    """Render horizontal stacked bar chart showing Red vs Blue block split across all municipalities."""
    st.subheader("🔴 Rød vs. blå blok anbefalinger pr. kommune")
    st.caption("Andelen af top-anbefalinger, der tilfalder hhv. rød og blå blok, simuleret for kommunen.")

    kom_stats = top1.groupby("municipality").agg(count=("run_id", "count")).reset_index()
    min_sims = kom_stats["count"].max() * 0.05 if not kom_stats.empty else 0
    kom_valid = kom_stats[kom_stats["count"] >= min_sims].copy()
    if kom_valid.empty:
        kom_valid = kom_stats

    red_block = ["Socialdemokratiet", "Enhedslisten", "Socialistisk Folkeparti", "Alternativet", "Radikale Venstre"]
    blue_block = ["Venstre", "Konservative", "Liberal Alliance", "Danmarksdemokraterne", "Dansk Folkeparti", "Moderaterne"]

    def get_block(party):
        if party in red_block:
            return "Rød"
        if party in blue_block:
            return "Blå"
        return "Andet"

    top1_blocks = top1.copy()
    top1_blocks["blok"] = top1_blocks["party"].apply(get_block)

    blok_counts = top1_blocks.groupby(["municipality", "blok"]).size().unstack(fill_value=0)
    blok_pct = blok_counts.div(blok_counts.sum(axis=1), axis=0) * 100
    blok_pct = blok_pct.loc[kom_valid["municipality"]]

    if "Rød" in blok_pct.columns:
        blok_pct_sorted = blok_pct.sort_values("Rød", ascending=True)

        fig_blok = go.Figure()

        if "Rød" in blok_pct_sorted.columns:
            fig_blok.add_trace(go.Bar(
                y=blok_pct_sorted.index, x=blok_pct_sorted["Rød"],
                orientation="h", name="Rød Blok", marker=dict(color="#ef4444"),
            ))
        if "Blå" in blok_pct_sorted.columns:
            fig_blok.add_trace(go.Bar(
                y=blok_pct_sorted.index, x=blok_pct_sorted["Blå"],
                orientation="h", name="Blå Blok", marker=dict(color="#60a5fa"),
            ))
        if "Andet" in blok_pct_sorted.columns:
            fig_blok.add_trace(go.Bar(
                y=blok_pct_sorted.index, x=blok_pct_sorted["Andet"],
                orientation="h", name="Andet", marker=dict(color="#475569"),
            ))

        fig_blok.update_layout(**base_layout(
            barmode="stack",
            height=max(400, len(blok_pct_sorted) * 25),
            xaxis=dict(title="Andel af anbefalinger (%)"),
            yaxis=dict(title="", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        ))

        st.plotly_chart(fig_blok, use_container_width=True)
