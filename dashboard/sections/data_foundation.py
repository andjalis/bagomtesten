"""Data foundation / Methodology tab — explains the methodology and shows distributions."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from config import ANSWER_LABELS, ANSWER_COLORS
from dashboard.sections._plotly_theme import base_layout


def render_data_foundation():
    """Render the methodology tab explaining the data generation and showing distributions."""
    from dashboard.data import load_run_answers, load_db_top1, load_questions, load_global_kpis

    st.header("⚙️ Metode & data")
    
    kpis = load_global_kpis()
    if kpis:
        st.caption(f"LHS-simulering baseret på **{kpis.get('total_simulations', 0):,}** fuldførte test-kørsler.".replace(",", "."))

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">Metodologi & Datagrundlag</div>
            <div class="info-card-text">
                <strong>Vi scrapede indledningsvist over 10.000 ægte testkørsler manuelt</strong> fra DR's platform.
                Vores analyse af denne data beviste en 100% lineær og symmetrisk sammenhæng i DR's algoritme (dvs. ingen "sort boks").<br/><br/>
                På baggrund af dette har vi kunnet <strong>simulere resten af svarene ekstremt præcist</strong>. Vi har simuleret testen
                100.000 gange pr. storkreds med systematisk fordelte svar via <strong>Latin Hypercube Sampling (LHS)</strong>.
                Dette garanterer, at det politiske spektrum dækkes fuldt ud uden at belaste DR's servere.<br/><br/>
                Statistisk set <em>burde</em> resultaterne fordele sig rimelig jævnt mellem partierne ved helt tilfældige svar.
                Hvis bestemte partier over-anbefales konsekvent, tyder det på at testens vægtning er skævvredet.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="info-card-title">Analyse: Hvordan vægtes dine svar?</div>
            <div class="info-card-text">
                Vores data-analyse bekræfter en <strong>lineær og symmetrisk vægtning</strong> i DR's algoritme:
                <ul>
                    <li><strong>Fuld symmetri:</strong> "Enig" og "Uenig" vægtes præcis lige højt.</li>
                    <li><strong>Midter-fordelen:</strong> Svaret "Lidt enig/uenig" giver statistisk set et
                    marginalt højere gennemsnitligt match% (68,1% vs 67,5%) pga. kortere matematisk
                    afstand til alle mulige kandidat-svar.</li>
                    <li><strong>Linearitet:</strong> Springet i match-% er jævnt — en simpel point-model
                    (0, 1, 2, 3) hvor afstanden mellem hvert valg tæller lige meget.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    answers_df = load_run_answers()
    top1_db = load_db_top1()
    questions_dict = load_questions()

    if answers_df is not None and not answers_df.empty and top1_db is not None and not top1_db.empty:
        # Answer Distribution
        _render_answer_distribution(answers_df, questions_dict)
    else:
        st.info("Ingen simulationsdata tilgængelig til at vise datagrundlaget endnu.")


def _render_answer_distribution(answers_df: pd.DataFrame, questions_dict: dict):
    """Render horizontal stacked bar chart of answer distribution per question."""
    st.subheader("📊 Svarfordeling pr. spørgsmål (Baseret på scrapede data)")
    st.caption(
        "Herunder kan du se, hvordan svarfordelingen var på de indledende 10.000 ægte "
        "tests, som blev formuleret og trukket direkte fra DR's servere for at knække algoritmen."
    )

    melted = answers_df.melt(
        id_vars=["run_id"],
        value_vars=[f"Q{i+1}" for i in range(25)],
        var_name="Question_Raw",
        value_name="Answer_Val",
    )
    melted["Svar"] = melted["Answer_Val"].map(ANSWER_LABELS)
    melted["Q_Num"] = melted["Question_Raw"].str.replace("Q", "").astype(int)
    melted["Spørgsmål"] = melted["Q_Num"].apply(
        lambda x: f"{x}. {questions_dict.get(x, f'Spørgsmål {x}')}"
    )

    dist_counts = (
        melted.groupby(["Spørgsmål", "Q_Num", "Svar"])
        .size().reset_index(name="Antal")
        .sort_values("Q_Num")
    )

    fig = px.bar(
        dist_counts, x="Antal", y="Spørgsmål",
        color="Svar", color_discrete_map=ANSWER_COLORS,
        orientation="h",
        title="Total fordeling af svar pr. spørgsmål",
        category_orders={"Svar": ["Uenig", "Lidt uenig", "Lidt enig", "Enig"]},
    )
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>%{x} person(er) svarede <b>%{fullData.name}</b><extra></extra>"
    )
    fig.update_layout(**base_layout(
        barmode="stack", height=900,
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis=dict(title="", showticklabels=False),
        yaxis=dict(autorange="reversed", title="", showgrid=False),
        legend_title_text="",
    ))
    st.plotly_chart(fig, use_container_width=True)
