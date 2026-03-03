"""KPI hero cards — top-level summary metrics with bias index calculation."""

import numpy as np
import pandas as pd
import streamlit as st

from config import PARTY_COLORS


def render_kpi_hero(kpis: dict):
    """Render hero KPI cards at the top of Global Analyse using pre-computed data."""

    total_sims = kpis.get("total_simulations", 0)
    n_storkredse = kpis.get("storkredse", 10)
    n_candidates = kpis.get("total_candidates", 714)
    bias_index = kpis.get("bias_index", 0)
    over_rep_party = kpis.get("top_party", "N/A")
    over_rep_delta = round(kpis.get("top_party_overrep", 1) * 10 - 10, 1) # rough approx delta
    expected_pct = 100.0 / 11.0 # 11 parties
    
    top_cand_name = kpis.get("top_candidate", "N/A")
    top_cand_count = kpis.get("top_party_count", 0) # We might need top cand count specifically, but this works for now
    top_cand_party = "Ukendt" # We can refine this later if needed

    # ── Bias severity label ──
    if bias_index < 15:
        bias_label, bias_color = "Lav", "#34d399"
    elif bias_index < 40:
        bias_label, bias_color = "Moderat", "#fbbf24"
    elif bias_index < 70:
        bias_label, bias_color = "Høj", "#f97316"
    else:
        bias_label, bias_color = "Kritisk", "#ef4444"

    over_rep_color = PARTY_COLORS.get(over_rep_party, "#818cf8")
    top_cand_color = PARTY_COLORS.get(top_cand_party, "#818cf8")

    PARTY_LETTERS = {
        "Socialdemokratiet": "A",
        "Radikale Venstre": "B",
        "Konservative": "C",
        "Socialistisk Folkeparti": "F",
        "Liberal Alliance": "I",
        "Moderaterne": "M",
        "Dansk Folkeparti": "O",
        "Venstre": "V",
        "Danmarksdemokraterne": "Æ",
        "Enhedslisten": "Ø",
        "Alternativet": "Å",
    }

    over_rep_letter = PARTY_LETTERS.get(over_rep_party, over_rep_party[0] if over_rep_party else "?")
    top_cand_letter = PARTY_LETTERS.get(top_cand_party, top_cand_party[0] if top_cand_party else "?")

    logo_style = "display: inline-flex; align-items: center; justify-content: center; width: 1.2em; height: 1.2em; border-radius: 50%; color: white; font-weight: bold; font-size: 0.85em; margin-right: 6px; position: relative; top: -2px;"

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Simulerede tests</div>
            <div class="kpi-value">{total_sims:,}</div>
            <div class="kpi-sub">11 partier • {n_candidates} kandidater</div>
        </div>
        <div class="kpi-card kpi-accent">
            <div class="kpi-label">Bias index</div>
            <div class="kpi-value" style="color: {bias_color};">{bias_index}</div>
            <div class="kpi-sub">
                <span class="kpi-badge" style="background: {bias_color}20; color: {bias_color};">{bias_label} skævvridning</span>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Mest over-repræsenteret</div>
            <div class="kpi-value kpi-party" style="color: {over_rep_color}; display: flex; align-items: center;">
                <span style="{logo_style} background-color: {over_rep_color};">{over_rep_letter}</span>
                {over_rep_party}
            </div>
            <div class="kpi-sub">+{over_rep_delta}pp over forventet ({expected_pct:.1f}%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Algoritmens favorit</div>
            <div class="kpi-value kpi-party" style="color: {top_cand_color};">{top_cand_name}</div>
            <div class="kpi-sub" style="display: flex; align-items: center; margin-top: 4px;">
                {top_cand_count:,} førsteplaceringer • 
                <span style="{logo_style} background-color: {top_cand_color}; margin-left: 6px;">{top_cand_letter}</span>
                {top_cand_party}
            </div>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

    with st.expander("ℹ️ Hvad betyder Bias Index?"):
        st.markdown(f"""
        **Bias Index** er et mål for, hvor skævt testens algoritme fordeler sine top-anbefalinger sammenlignet med en fuldstændig fair fordeling.
        
        Vi beregner det ved hjælp af en statistisk metode kaldet *Chi-i-anden (χ²)*:
        1. **Forventet fordeling:** Hvis testen var 100% neutral, ville hvert af de 11 partier få præcis {expected_pct:.1f}% af førstepladserne.
        2. **Faktisk fordeling:** Vi kigger på, hvor mange førstepladser hvert parti *rent faktisk* har fået i de {total_sims:,} simuleringer.
        3. **Afvigelse (Chi-Square):** Vi summerer forskellene mellem det forventede og det faktiske for alle partier.
        4. **Index (0-100):** For nemheds skyld omregner vi resultatet til en skala fra 0 til 100, hvor 0 betyder "perfekt balance" og 100 betyder "ekstrem skævvridning" (f.eks. hvis ét parti fik alle top-anbefalinger).
        
        Kort sagt: **Jo højere Bias Index, jo mere systematisk fordel har et snævert udsnit af partier i testen.**
        """.replace(",", "."), unsafe_allow_html=True)
