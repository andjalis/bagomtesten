"""Gaming analysis section — candidate cards and rank breakdown chart."""

import pandas as pd
import plotly.express as px
import streamlit as st

from config import PARTY_COLORS, ANSWER_LABELS, ANSWER_COLORS
from dashboard.sections._plotly_theme import base_layout, RANK_COLORS


from dashboard.data import load_candidates_data, load_questions, load_candidate_gaming

def render_gaming_analysis():
    """Render the 'Who games the test?' section with candidate cards and rank chart."""
    st.subheader("🚨 Hvem 'gamer' testen?")
    st.markdown(
        "Vi kan afsløre systematisk over-anbefaling ved at kigge på, hvor ofte "
        "en kandidat toner frem på skærmen som testens absolutte bedste match, "
        "sammenlignet med det gennemsnitlige forventede udfald ved tilfældige svar."
    )

    top_candidates, rank_breakdown = load_candidate_gaming()
    if top_candidates.empty or rank_breakdown.empty:
        st.warning("Data mangler. Kør bygge-scriptet.")
        return

    col_left, col_right = st.columns([2, 3])

    with col_left:
        _render_candidate_cards(top_candidates)

    with col_right:
        _render_rank_chart(rank_breakdown)


def _render_candidate_cards(top_candidates: pd.DataFrame, key_prefix: str = "gaming"):
    """Render sortable candidate cards in the left column from precomputed data."""
    st.markdown("**Testens mest anbefalede kandidater**")

    sort_method = st.selectbox(
        "Sortér lister efter:",
        ["Oftest anbefalet som 1. valg", "Flest visninger totalt i resultaterne"],
        index=0,
        label_visibility="collapsed",
        key=f"{key_prefix}_sort_candidates",
    )

    sort_map = {
        "Oftest anbefalet som 1. valg": (["count"], [False]),
        "Flest visninger totalt i resultaterne": (["total_count", "count"], [False, False]),
    }
    cols, asc = sort_map[sort_method]
    display_candidates = top_candidates.sort_values(cols, ascending=asc).head(8)

    c_df = load_candidates_data()
    q_dict = load_questions()

    for _, row in display_candidates.iterrows():
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


def _render_rank_chart(rank_breakdown: pd.DataFrame):
    """Render the stacked bar chart showing candidate placement distribution from precomputed data."""
    st.markdown("**Placering for top 15 kandidater (nr. 1 til nr. 6)**")

    total_freq = rank_breakdown.groupby("candidate_name")["Antal"].sum().to_dict()
    rank_breakdown["Total"] = rank_breakdown["candidate_name"].map(total_freq)
    
    # Only show top 15 in the chart
    top15_names = pd.Series(total_freq).sort_values(ascending=False).head(15).index.tolist()
    rank_breakdown = rank_breakdown[rank_breakdown["candidate_name"].isin(top15_names)]
    
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
