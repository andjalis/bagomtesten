"""Blok analysis section — Red vs Blue block stacked bar chart."""

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from dashboard.sections._plotly_theme import base_layout


from dashboard.data import load_kommune_stats

def render_blok_analysis_global():
    """Render horizontal stacked bar chart showing Red vs Blue block split across all municipalities."""
    st.subheader("🔴 Rød vs. blå blok anbefalinger pr. kommune")
    st.caption("Andelen af top-anbefalinger, der tilfalder hhv. rød og blå blok, simuleret for kommunen.")

    stats = load_kommune_stats()
    if stats.empty:
        st.warning("Data mangler. Kør bygge-scriptet.")
        return
        
    stats["Andet_Pct"] = 100 - stats["Red_Pct"] - stats["Blue_Pct"]
    stats_sorted = stats.sort_values("Red_Pct", ascending=True)

    fig_blok = go.Figure()

    fig_blok.add_trace(go.Bar(
        y=stats_sorted["Kommune"], x=stats_sorted["Red_Pct"],
        orientation="h", name="Rød Blok", marker=dict(color="#ef4444"),
    ))
    fig_blok.add_trace(go.Bar(
        y=stats_sorted["Kommune"], x=stats_sorted["Blue_Pct"],
        orientation="h", name="Blå Blok", marker=dict(color="#60a5fa"),
    ))
    fig_blok.add_trace(go.Bar(
        y=stats_sorted["Kommune"], x=stats_sorted["Andet_Pct"],
        orientation="h", name="Andet", marker=dict(color="#475569"),
    ))

    fig_blok.update_layout(**base_layout(
        barmode="stack",
        height=max(400, len(stats_sorted) * 25),
        xaxis=dict(title="Andel af anbefalinger (%)"),
        yaxis=dict(title="", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    ))

    st.plotly_chart(fig_blok, use_container_width=True)
