"""Party-pair analysis — heatmap showing 'If X is #1, who is usually #2?'"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout


def render_party_pairs(df: pd.DataFrame):
    """Render heatmap of party co-occurrence: when party X is #1, who's #2?"""
    st.subheader("🤝 Parti-par analyse")
    st.caption(
        "Når et parti anbefales som nr. 1, hvilket parti er så oftest nr. 2? "
        "Afslører naturlige parti-klynger i testens algoritme."
    )

    # Get rank 1 and rank 2 per run
    rank1 = df[df["candidate_rank"] == 1][["run_id", "party"]].rename(columns={"party": "Nr1"})
    rank2 = df[df["candidate_rank"] == 2][["run_id", "party"]].rename(columns={"party": "Nr2"})

    pairs = rank1.merge(rank2, on="run_id", how="inner")
    if pairs.empty:
        st.info("Utilstrækkelig data til parti-par analyse.")
        return

    # Build co-occurrence matrix (row = Nr1, col = Nr2, value = count)
    all_parties = sorted(list(PARTY_COLORS.keys()))
    cross = pd.crosstab(pairs["Nr1"], pairs["Nr2"])

    # Normalize per row (percentage of times Nr2 appears when Nr1 is first)
    cross_pct = cross.div(cross.sum(axis=1), axis=0) * 100

    # Reindex to include all parties
    cross_pct = cross_pct.reindex(index=all_parties, columns=all_parties, fill_value=0)

    # Remove self-pairs (diagonal) — a party can't be both #1 and #2
    # (they can be if different candidates from same party, but let's keep it)

    fig = go.Figure(data=go.Heatmap(
        z=cross_pct.values,
        x=cross_pct.columns.tolist(),
        y=cross_pct.index.tolist(),
        colorscale=[
            [0, "#0f172a"],
            [0.2, "#1e293b"],
            [0.4, "#334155"],
            [0.6, "#6366f1"],
            [0.8, "#818cf8"],
            [1.0, "#a5b4fc"],
        ],
        colorbar=dict(
            title="% af gange",
            title_font=dict(color="#94a3b8"),
            tickfont=dict(color="#94a3b8"),
            ticksuffix="%",
        ),
        xgap=2, ygap=2,
        hovertemplate="Når <b>%{y}</b> er Nr. 1:<br><b>%{x}</b> er Nr. 2 i <b>%{z:.1f}%</b> af tilfældene<extra></extra>",
    ))

    fig.update_layout(**base_layout(
        xaxis=dict(title="Nr. 2 Anbefaling", tickangle=-45, side="bottom"),
        yaxis=dict(
            title="Nr. 1 Anbefaling",
            autorange="reversed",
            showgrid=False,
        ),
        height=600,
        margin=dict(l=150, r=0, t=20, b=120),
    ))
    st.plotly_chart(fig, use_container_width=True)

    # Insight: strongest pair
    mask = cross_pct.values.copy()
    for i in range(len(all_parties)):
        mask[i][i] = 0  # Ignore self-pairs
    max_idx = mask.argmax()
    row_idx, col_idx = divmod(max_idx, len(all_parties))
    strongest_1 = all_parties[row_idx]
    strongest_2 = all_parties[col_idx]
    strongest_pct = mask[row_idx][col_idx]

    st.markdown(f"""
    <div class="insight-row">
        <div class="insight-chip" style="border-color: {PARTY_COLORS.get(strongest_1, '#818cf8')};">
            <span class="insight-icon">🔗</span>
            <span>Stærkeste par: <strong>{strongest_1}</strong> → <strong>{strongest_2}</strong> ({strongest_pct:.1f}% af nr. 2 placeringerne)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
