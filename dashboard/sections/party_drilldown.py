"""Party drill-down section — per-party detailed analysis tab."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout


def render_party_drilldown(df: pd.DataFrame, top1: pd.DataFrame):
    """Render the party-specific drilldown tab."""
    from dashboard.data import load_candidates_data, load_questions
    from dashboard.sections.gaming_analysis import _render_candidate_cards

    st.header("🔍 Dyk ned i et specifikt parti")
    st.caption("Detaljeret profil af ét bestemt parti: geografi, top-kandidater fra testen og partidisciplin.")

    parties = sorted(top1["party"].unique().tolist())
    if not parties:
        st.info("Ingen partidata.")
        return

    # Store in session state to maintain selection across reruns if needed
    party = st.selectbox("Vælg Parti for Dybdegående Analyse:", parties, index=parties.index("Alternativet") if "Alternativet" in parties else 0)
    p_color = PARTY_COLORS.get(party, "#3b82f6")

    st.divider()
    
    st.divider()
    
    # 1. Top Section - Map
    st.subheader("📍 Geografisk Styrke (Top-1 Pct)")
    total_runs_per_mun = df[df["candidate_rank"] == 1]["municipality"].value_counts()
    party_runs_per_mun = top1[top1["party"] == party]["municipality"].value_counts()

    win_rate = (party_runs_per_mun / total_runs_per_mun * 100).fillna(0).reset_index()
    win_rate.columns = ["Storkreds", "Win_Rate_Pct"]
    win_rate = win_rate.sort_values("Win_Rate_Pct", ascending=False)

    fig_map = px.bar(
        win_rate, x="Storkreds", y="Win_Rate_Pct",
        title=f"Hvor stor en andel af alle nr. 1 anbefalinger går til {party} lokalt?",
        color_discrete_sequence=[p_color],
    )
    fig_map.update_traces(
        hovertemplate="<b>%{x}</b><br>Ud af alle top-1 resultater her ryddede partiet <b>%{y:.1f}%</b><extra></extra>"
    )
    fig_map.update_layout(**base_layout(
        xaxis=dict(title="", tickangle=-45),
        yaxis=dict(title="Anbefalet (%)", showgrid=True),
        margin=dict(l=0, r=0, t=50, b=0),
    ))
    st.plotly_chart(fig_map, use_container_width=True)

    st.divider()
    
    # 2. Top-5 Candidates
    st.subheader(f"🥇 Mest Anbefalede Kandidater i {party}")
    st.caption("Disse kandidater tonede oftest frem på skærmen som absolut top-match for testtagerne.")
    
    party_top1 = top1[top1["party"] == party]
    party_df = df[df["party"] == party]
    
    if not party_top1.empty:
        # We reuse the candidate card renderer, but it sorts all inside. 
        # So we just pass the filtered data.
        _render_candidate_cards(party_df, party_top1)
    else:
        st.info("Ingen 'nr. 1' anbefalinger for partiet at vise kandidater ud fra.")

    st.divider()

    # -- 3. Intra-party Analysis --
    c_df = load_candidates_data()
    if c_df.empty:
        st.warning("Kan ikke analysere internt i partiet (mangler all_candidates.json).")
        return

    p_c_df = c_df[c_df["party"] == party].copy()
    if p_c_df.empty or len(p_c_df) < 2:
        st.info(f"Ikke nok kandidater (har kun {len(p_c_df)}) til at lave intern variansanalyse for {party}.")
        return

    q_cols = [f"Q{i+1}" for i in range(25)]
    q_dict = load_questions()

    st.subheader(f"🤝 Intern enighed ({len(p_c_df)} kandidater fra {party})")
    st.caption("Viser hvor enige kandidaterne i partiet er om de enkelte spørgsmål. Grøn betyder stor enighed (lav varians), rød betyder stor splittelse.")

    variances = p_c_df[q_cols].var().sort_values()
    
    # Create a horizontal bar chart / heatmap-like view for variances
    var_df = pd.DataFrame({"Spørgsmål": variances.index, "Varians": variances.values})
    var_df["Spørgsmål_Tekst"] = var_df["Spørgsmål"].apply(lambda q: f"{q.replace('Q', '')}. {q_dict.get(int(q.replace('Q', '')), '')[:60]}...")
    var_df["Enighed"] = 3.0 - var_df["Varians"] # Invert so higher is better agreement (max variance is typically around 1-2)
    # Normalize color scale
    var_df["Color_Val"] = var_df["Varians"]
    
    fig_var = px.bar(
        var_df, x="Varians", y="Spørgsmål_Tekst",
        orientation="h",
        color="Varians",
        color_continuous_scale="RdYlGn_r", # Reversed: low variance (green) to high variance (red)
        title="",
    )
    fig_var.update_layout(**base_layout(
        xaxis=dict(title="Intern uenighed (Varians)", showgrid=True),
        yaxis=dict(title="", autorange="reversed"),
        height=600,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False
    ))
    fig_var.update_traces(
        hovertemplate="<b>%{y}</b><br>Varians: %{x:.2f}<extra></extra>"
    )
    st.plotly_chart(fig_var, use_container_width=True)

    st.divider()

    # -- 4. Partisoldat vs Oprører --
    st.subheader("👤 Partisoldat vs. oprører")
    st.caption(f"Hvilke folketingskandidater for {party} ligger hhv. tættest på og længst fra partiets gennemsnitlige holdninger (testens midte)?")

    mean_vec = p_c_df[q_cols].mean()
    distances = (p_c_df[q_cols] - mean_vec).abs().sum(axis=1)
    p_c_df["Afvigelse"] = distances

    soldat = p_c_df.loc[distances.idxmin()]
    oprorer = p_c_df.loc[distances.idxmax()]

    col3, col4 = st.columns(2)
    
    def render_persona(persona_row, title, css_class, desc_prefix):
        img_src = persona_row.get('candidate_image', '')
        if pd.isna(img_src) or not img_src:
            img_src = "https://via.placeholder.com/64/374151/FFFFFF/?text=?"
            
        st.markdown(f"""
        <div class="persona-card {css_class}">
            <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 15px;">
                <img src="{img_src}" style="width: 64px; height: 64px; border-radius: 50%; object-fit: cover; border: 2px solid var(--border-subtle);" />
                <div>
                    <div class="persona-title">{title}</div>
                    <div class="persona-name">{persona_row['candidate_name']}</div>
                    <div class="persona-meta">Stiller op i {persona_row['municipality']}</div>
                </div>
            </div>
            <div class="persona-detail">
                {desc_prefix}: Afviger totalt med <strong>{persona_row['Afvigelse']:.1f} point</strong> fra parti-linjen over 25 spørgsmål.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander(f"Se {persona_row['candidate_name']}s enigheds-map vs. {party}"):
            # Build divergence map
            dev_records = []
            for q_idx in range(1, 26):
                q_col = f"Q{q_idx}"
                if q_col in persona_row:
                    cand_val = persona_row[q_col]
                    party_mean_val = mean_vec[q_col]
                    deviation = cand_val - party_mean_val # Directional deviation
                    
                    short_q = f"Q{q_idx}. {q_dict.get(q_idx, '')[:45]}..."
                    dev_records.append({
                        "Spørgsmål": short_q,
                        "Afvigelse": deviation,
                        "AbsAfvigelse": abs(deviation),
                        "Svar": cand_val,
                        "PartiGns": party_mean_val
                    })
                    
            dev_df = pd.DataFrame(dev_records)
            dev_df = dev_df.sort_values("AbsAfvigelse", ascending=True)
            
            fig_dev = px.bar(
                dev_df, x="Afvigelse", y="Spørgsmål",
                orientation="h",
                color="AbsAfvigelse",
                color_continuous_scale="RdYlGn_r", # Red for high deviation, green for low
                title="",
            )
            from config import ANSWER_LABELS
            # Add custom hover text
            hover_texts = []
            for i, row in dev_df.iterrows():
                ans_str = ANSWER_LABELS.get(row["Svar"], "Ukendt")
                hover_texts.append(f"<b>Kandidatens svar:</b> {ans_str}<br><b>Partiets gns:</b> {row['PartiGns']:.1f}<br><b>Afvigelse:</b> {row['AbsAfvigelse']:.1f} pt")
            
            fig_dev.update_traces(
                customdata=hover_texts,
                hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>"
            )
            
            # Center the x-axis around 0
            max_dev = max(1.5, dev_df["AbsAfvigelse"].max() * 1.1)
            
            fig_dev.update_layout(**base_layout(
                xaxis=dict(title="Afvigelse fra parti-linjen (point)", range=[-max_dev, max_dev], showgrid=True, zeroline=True, zerolinecolor="#64748b", zerolinewidth=2),
                yaxis=dict(title="", showgrid=False),
                height=600,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False
            ))
            st.plotly_chart(fig_dev, use_container_width=True, key=f"dev_map_{persona_row['candidate_name']}")

    with col3:
        render_persona(soldat, "Partisoldaten", "persona-soldat", "Stemmer mest trofast")

    with col4:
        render_persona(oprorer, "Oprøreren", "persona-oprorer", "Største afviger")
