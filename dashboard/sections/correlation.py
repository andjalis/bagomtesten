"""Correlation analysis section — answer pattern heatmap per party."""

import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout


def render_correlation_analysis():
    """Render the heatmap of average answer patterns per party."""
    from dashboard.data import load_run_answers, load_db_top1, load_questions

    answers_df = load_run_answers()
    if answers_df is None or answers_df.empty:
        st.info("Ingen svardata tilgængelig endnu for korrelationsanalyse.")
        return

    top1_db = load_db_top1()
    if top1_db is None or top1_db.empty:
        st.info("Ingen resultater i databasen tilgængelige for korrelationsanalyse.")
        return

    merged = answers_df.merge(top1_db, on="run_id", how="inner")
    if merged.empty:
        return

    questions_dict = load_questions()

    st.divider()

    # ── Heatmap: average answer per party ──
    st.subheader("🔗 Svarmønstrens korrelation med anbefalede partier")
    question_cols = [f"Q{i+1}" for i in range(25)]
    party_means = merged.groupby("party")[question_cols].mean()

    all_parties = list(PARTY_COLORS.keys())
    party_means = party_means.reindex(all_parties)

    if len(party_means.dropna(how="all")) > 0:
        q_labels = []
        for i in range(25):
            raw = questions_dict.get(i + 1, f"Q{i+1}")
            short = raw[:55] + "..." if len(raw) > 55 else raw
            q_labels.append(f"{i+1}. {short}")

        fig_hm = go.Figure(data=go.Heatmap(
            z=party_means.values, x=q_labels, y=party_means.index.tolist(),
            colorscale="RdYlGn", zmin=0, zmax=3,
            colorbar=dict(
                title="Gns. svar",
                tickvals=[0, 1, 2, 3],
                ticktext=["Uenig", "Lidt uenig", "Lidt enig", "Enig"],
                title_font=dict(color="#94a3b8"),
                tickfont=dict(color="#94a3b8"),
            ),
            xgap=1, ygap=1,
        ))
        fig_hm.update_traces(
            hovertemplate="<b>%{x}</b><br>Parti: %{y}<br>Gns. svar: %{z:.2f}<extra></extra>"
        )

        fig_hm.update_layout(**base_layout(
            title="Gennemsnitligt svarmønster pr. anbefalet parti",
            xaxis=dict(title="", tickangle=-45),
            yaxis=dict(
                title="",
                autorange="reversed",
                type="category",
                tickmode="linear",
                dtick=1,
                categoryorder="array",
                categoryarray=all_parties,
                showgrid=False,
            ),
            height=700,
            margin=dict(l=150, t=50, b=100, r=0),
        ))
        st.plotly_chart(fig_hm, use_container_width=True, key="correlation_heatmap")
    else:
        st.info("Ingen partier at vise data for endnu.")
