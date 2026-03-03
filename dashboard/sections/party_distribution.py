"""Party distribution section — bar chart + donut chart of top-1 recommendations."""

import pandas as pd
import plotly.express as px
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout


from dashboard.data import load_party_rankings

def render_party_distribution():
    """Render bar chart + donut chart of top-1 party distribution from precomputed JSON."""
    st.subheader("📊 Fordeling af anbefalede partier")
    st.caption("Testens top-1 anbefalinger bygget på samtlige simuleringer.")

    col_left, col_right = st.columns([3, 2], gap="large")

    party_counts = load_party_rankings()
    if party_counts.empty:
        st.warning("Data mangler. Kør bygge-scriptet.")
        return
        
    party_counts.rename(columns={"Party": "Parti", "Count": "Antal"}, inplace=True)

    with col_left:
        fig_party = px.bar(
            party_counts, x="Parti", y="Antal",
            color="Parti", color_discrete_map=PARTY_COLORS,
            title="Top-1 anbefalet parti pr. test",
        )
        fig_party.update_traces(
            hovertemplate="<b>%{x}</b><br>Anbefalinger: %{y}<extra></extra>"
        )
        fig_party.update_layout(**base_layout(
            showlegend=False,
            xaxis=dict(title="", tickangle=-45),
            yaxis=dict(title="", showticklabels=False, showgrid=False),
            margin=dict(l=0, r=0, t=50, b=0),
        ))
        st.plotly_chart(fig_party, use_container_width=True)

    with col_right:
        fig_pie = px.pie(
            party_counts, values="Antal", names="Parti",
            color="Parti", color_discrete_map=PARTY_COLORS,
            title="Procentvis dominans", hole=0.5,
        )
        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent",
            textfont=dict(color="#e2e8f0", size=12),
            marker=dict(line=dict(width=0)),
            hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        )
        fig_pie.update_layout(**base_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=50, b=0),
        ))
        st.plotly_chart(fig_pie, use_container_width=True)
