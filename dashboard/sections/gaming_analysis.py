"""Gaming analysis section — candidate cards and rank breakdown chart."""

import pandas as pd
import plotly.express as px
import streamlit as st

from config import PARTY_COLORS, ANSWER_LABELS, ANSWER_COLORS
from dashboard.sections._plotly_theme import base_layout, RANK_COLORS


def render_gaming_analysis(df: pd.DataFrame, top1: pd.DataFrame):
    """Render the 'Who games the test?' section with candidate cards and rank chart."""
    st.subheader("🚨 Hvem 'gamer' testen?")
    st.markdown(
        "Vi kan afsløre systematisk over-anbefaling ved at kigge på, hvor ofte "
        "en kandidat toner frem på skærmen som testens absolutte bedste match, "
        "sammenlignet med det gennemsnitlige forventede udfald ved tilfældige svar."
    )

    col_left, col_right = st.columns([2, 3])

    with col_left:
        _render_candidate_cards(df, top1)

    with col_right:
        _render_rank_chart(df)


def _render_candidate_cards(df: pd.DataFrame, top1: pd.DataFrame):
    """Render sortable candidate cards in the left column."""
    from dashboard.data import load_candidates_data, load_questions

    st.markdown("**Testens mest anbefalede kandidater**")

    sort_method = st.selectbox(
        "Sortér lister efter:",
        ["Oftest anbefalet som 1. valg", "Flest visninger totalt i resultaterne"],
        index=0,
        label_visibility="collapsed",
        key=f"sort_cand_{id(top1)}",
    )

    top1_stats = (
        top1.groupby(["candidate_name", "party", "candidate_image"])
        .agg(count=("run_id", "count"), municipality=("municipality", "first"))
        .reset_index()
    )

    total_appearances = df.groupby("candidate_name").size().reset_index(name="total_count")
    top1_stats = pd.merge(top1_stats, total_appearances, on="candidate_name", how="left")

    sort_map = {
        "Oftest anbefalet som 1. valg": (["count"], [False]),
        "Flest visninger totalt i resultaterne": (["total_count", "count"], [False, False]),
    }
    cols, asc = sort_map[sort_method]
    top_candidates = top1_stats.sort_values(cols, ascending=asc).head(8)

    c_df = load_candidates_data()
    q_dict = load_questions()

    for _, row in top_candidates.iterrows():
        p_color = PARTY_COLORS.get(row["party"], "#374151")
        img_src = (
            row["candidate_image"]
            if pd.notna(row["candidate_image"]) and row["candidate_image"]
            else "https://via.placeholder.com/64/374151/FFFFFF/?text=?"
        )

        if sort_method == "Flest visninger totalt i resultaterne":
            main_label = "Visninger i alt"
            main_val = f"{row['total_count']}"
            sub_val = f"Førstevalg: {row['count']} gange"
        else:
            main_label = "Førstevalg"
            main_val = f"{row['count']}"
            sub_val = f"I alt vist: {row.get('total_count', 0)} gange"

        st.markdown(f"""
        <div class="cand-card">
            <img src="{img_src}" class="cand-img" />
            <div class="cand-info">
                <p class="cand-name">{row["candidate_name"]}</p>
                <p class="cand-party">{row["party"]} • {row["municipality"]}</p>
            </div>
            <div class="cand-count">
                <span class="cand-label" style="color: {p_color};">{main_label}</span>
                <strong>{main_val}</strong>
                <span class="cand-sub">{sub_val}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cand_match = c_df[c_df["candidate_name"] == row["candidate_name"]]
        if not cand_match.empty:
            ans_row = cand_match.iloc[0]
            with st.expander(f"Se {row['candidate_name']}s testbesvarelse"):
                for q_idx in range(1, 26):
                    q_col = f"Q{q_idx}"
                    if q_col in ans_row:
                        ans_val = ans_row[q_col]
                        ans_str = ANSWER_LABELS.get(ans_val, "Ukendt")
                        color = ANSWER_COLORS.get(ans_str, "#e2e8f0")

                        st.markdown(f"""
                        <div class="answer-row">
                            <div class="answer-q-num">Spørgsmål {q_idx}</div>
                            <div class="answer-q-text">{q_dict.get(q_idx, '')}</div>
                            <div class="answer-val" style="color: {color};">Svar: {ans_str}</div>
                        </div>
                        """, unsafe_allow_html=True)


def _render_rank_chart(df: pd.DataFrame):
    """Render the stacked bar chart showing candidate placement distribution."""
    st.markdown("**Placering for top 15 kandidater (nr. 1 til nr. 6)**")

    top15_names = df["candidate_name"].value_counts().head(15).index.tolist()
    df_top15 = df[df["candidate_name"].isin(top15_names)]

    rank_breakdown = (
        df_top15.groupby(["candidate_name", "party", "candidate_rank"])
        .size().reset_index(name="Antal")
    )

    total_freq = df_top15.groupby("candidate_name").size().to_dict()
    rank_breakdown["Total"] = rank_breakdown["candidate_name"].map(total_freq)
    rank_breakdown = rank_breakdown.sort_values(["Total", "candidate_name"], ascending=[False, True])
    rank_breakdown["Placering"] = rank_breakdown["candidate_rank"].apply(lambda x: f"Nr. {int(x)}")

    fig = px.bar(
        rank_breakdown, x="candidate_name", y="Antal",
        color="Placering", color_discrete_map=RANK_COLORS,
        title="Placering i søgekriteriet for algoritmens favoritter",
        category_orders={"Placering": [f"Nr. {i}" for i in range(1, 7)]},
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y} anbefalinger som %{fullData.name}<extra></extra>"
    )

    # Color x-axis labels by party
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
        margin=dict(b=100, l=0, r=0, t=50),
        barmode="stack",
        legend_title_text="",
    ))
    st.plotly_chart(fig, use_container_width=True)
