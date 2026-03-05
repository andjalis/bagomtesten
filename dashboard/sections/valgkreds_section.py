"""Valgkreds section — combined local analysis with party distribution, block split, candidates, and rank chart."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout, RANK_COLORS
from dashboard.sections.gaming_analysis import _render_candidate_cards

from dashboard.data import load_candidates_data, load_questions, load_kommune_stats, load_candidate_gaming, load_party_rankings


def render_valgkreds_section():
    """Render the full Valgkreds tab with party distribution, block split, candidates, and rank chart."""
    st.header("📍 Valgkreds-analyse")
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

    # ── Top stats ──
    num_sims = muni_row.get("Total_Tests", 0)
    most_rec_party = muni_row.get("Top_Party", "N/A")
    top_block = muni_row.get("Vinder_Blok", "N/A")

    col1, col3, col4 = st.columns(3)
    with col1:
        st.metric("Simulerede testkørsler", f"{num_sims:,}".replace(",", "."))
    with col3:
        st.metric("Topanbefalet parti", most_rec_party)
    with col4:
        st.metric("Vinderblok", top_block)

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # ROW 1: Party distribution + Block distribution (top overview)
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("📊 Fordeling af anbefalede partier")
    st.caption(f"Valgkreds-specifik fordeling for {selected_muni}.")

    party_counts = load_party_rankings()

    if not party_counts.empty:
        party_counts_display = party_counts.rename(columns={"Party": "Parti", "Count": "Antal"})

        # Sub-row 1: Party bar + Donut
        col_bar, col_donut = st.columns([3, 2], gap="large")

        with col_bar:
            fig_party = px.bar(
                party_counts_display, x="Parti", y="Antal",
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
            st.plotly_chart(fig_party, use_container_width=True, key="valgkreds_party_bar")

        with col_donut:
            fig_pie = px.pie(
                party_counts_display, values="Antal", names="Parti",
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
            st.plotly_chart(fig_pie, use_container_width=True, key="valgkreds_party_pie")

    st.divider()

    # Sub-row 2: Block distribution (lokalt)
    st.subheader("📊 Blok-fordeling lokalt")
    st.caption("Procentvis andel af anbefalinger rullet op på rød og blå blok.")

    red_pct = muni_row.get("Red_Pct", 0)
    blue_pct = muni_row.get("Blue_Pct", 0)
    undet_pct = 100 - red_pct - blue_pct

    fig_blok = go.Figure(data=[
        go.Bar(
            x=["Rød Blok", "Blå Blok", "Andet"],
            y=[red_pct, blue_pct, undet_pct],
            texttemplate="%{y:.1f}%", textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
            marker_color=["#ef4444", "#3b82f6", "#64748b"],
        )
    ])
    fig_blok.update_layout(**base_layout(
        title="",
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Andel af anbefalinger (%)", range=[0, 100]),
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
    ))
    st.plotly_chart(fig_blok, use_container_width=True, key="valgkreds_blok_bar")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # ROW 2: Candidates (left) + Rank chart (right), side by side
    # ══════════════════════════════════════════════════════════════════════════
    col_left, col_right = st.columns([2, 3], gap="large")

    with col_left:
        st.subheader("🥇 Hvem dominerede testen her?")
        st.caption("Kandidater der oftest tonede frem på skærmen som absolutte top-match for testtagerne.")

        top_candidates, _ = load_candidate_gaming()
        if not top_candidates.empty:
            muni_candidates = top_candidates[top_candidates["municipality"] == selected_muni]
            if not muni_candidates.empty:
                _render_candidate_cards(muni_candidates, key_prefix="valgkreds")
            else:
                st.info("Ingen kandidater at vise for denne kommune.")
        else:
            st.info("Utilstrækkelig data til at bygge kandidatkort for denne kommune.")

    with col_right:
        st.subheader("📊 Placering for top 15-kandidater (nr. 1 til nr. 6)")
        _, rank_breakdown = load_candidate_gaming()
        if not rank_breakdown.empty:
            _render_rank_chart_local(rank_breakdown, selected_muni)
        else:
            st.info("Ingen placeringsdata at vise.")


def _render_rank_chart_local(rank_breakdown: pd.DataFrame, municipality: str):
    """Render a compact rank chart for the selected municipality (or global if no local data)."""
    total_freq = rank_breakdown.groupby("candidate_name")["Antal"].sum().to_dict()
    rank_breakdown = rank_breakdown.copy()
    rank_breakdown["Total"] = rank_breakdown["candidate_name"].map(total_freq)

    top15_names = pd.Series(total_freq).sort_values(ascending=False).head(15).index.tolist()
    rank_breakdown = rank_breakdown[rank_breakdown["candidate_name"].isin(top15_names)]

    rank_breakdown = rank_breakdown.sort_values(["Total", "candidate_name"], ascending=[False, True])
    rank_breakdown["Placering"] = rank_breakdown["candidate_rank"].apply(lambda x: f"Nr. {int(x)}")

    fig = px.bar(
        rank_breakdown, x="candidate_name", y="Antal",
        color="Placering", color_discrete_map=RANK_COLORS,
        title="",
        category_orders={"Placering": [f"Nr. {i}" for i in range(1, 7)]},
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y} anbefalinger som %{fullData.name}<extra></extra>"
    )

    cand_parties = (
        rank_breakdown[["candidate_name", "party"]]
        .drop_duplicates()
        .set_index("candidate_name")["party"]
        .to_dict()
    )
    tickvals = list(cand_parties.keys())
    ticktext = [
        f"<b style='color:{PARTY_COLORS.get(cand_parties[c], '#94a3b8')}'>{c}</b>"
        for c in tickvals
    ]

    fig.update_layout(**base_layout(
        xaxis=dict(tickangle=-45, tickmode="array", tickvals=tickvals, ticktext=ticktext, title=""),
        yaxis=dict(title="", showticklabels=False, showgrid=False),
        margin=dict(b=100, l=0, r=0, t=20),
        barmode="stack",
        legend_title_text="",
        height=400,
    ))
    st.plotly_chart(fig, use_container_width=True, key=f"valgkreds_rank_bar_{municipality}")
