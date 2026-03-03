"""Party comparison section — interactive side-by-side analysis of two parties."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout


def render_party_comparison(df: pd.DataFrame, top1: pd.DataFrame):
    """Render interactive side-by-side comparison of two selected parties."""
    from dashboard.data import load_candidates_data, load_questions

    st.header("⚖️ Sammenlign partier")
    st.caption("Vælg to partier for at sammenligne deres fordeling, match-procenter og svarprofiler side om side.")

    parties = sorted(top1["party"].unique().tolist())
    if len(parties) < 2:
        st.info("Ikke nok partidata til at foretage en sammenligning.")
        return

    col1, col2 = st.columns(2)
    with col1:
        p1 = st.selectbox("Vælg parti A:", parties, index=parties.index("Socialdemokratiet") if "Socialdemokratiet" in parties else 0)
    with col2:
        p2 = st.selectbox("Vælg parti B:", parties, index=parties.index("Venstre") if "Venstre" in parties else 1)

    if p1 == p2:
        st.warning("Vælg to forskellige partier for at se en sammenligning.")
        return

    color1 = PARTY_COLORS.get(p1, "#ef4444")
    color2 = PARTY_COLORS.get(p2, "#3b82f6")

    st.divider()

    st.divider()

    # -- 1. Nøgletal --
    st.subheader("📊 Nøgletal")
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric(f"{p1} - Top-1 visninger", f"{len(top1[top1['party'] == p1]):,}".replace(",", "."))
    with col_stat2:
        st.metric(f"{p2} - Top-1 visninger", f"{len(top1[top1['party'] == p2]):,}".replace(",", "."))

    st.divider()

    # -- 2. Svar-Profil Sammenligning (Radar Chart) --
    c_df = load_candidates_data()
    q_dict = load_questions()

    if not c_df.empty:
        st.subheader("🎯 Svar-profil sammenligning")
        st.caption("Sammenligner det gennemsnitlige svarmønster på tværs af alle 25 spørgsmål for kandidater fra de to valgte partier.")
        
        q_cols = [f"Q{i+1}" for i in range(25)]
        mean1 = c_df[c_df["party"] == p1][q_cols].mean()
        mean2 = c_df[c_df["party"] == p2][q_cols].mean()
        
        # Calculate largest differences
        diffs = (mean1 - mean2).abs().sort_values(ascending=False)
        top_diff_qs = diffs.head(5).index.tolist()
        
        # Shorten question names for radar chart
        short_labels = []
        for q in q_cols:
            q_num = int(q.replace("Q", ""))
            text = q_dict.get(q_num, q)
            short_labels.append(f"Q{q_num}: {text[:20]}...")

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=mean1.values, theta=short_labels, fill='toself', name=p1,
            line_color=color1, opacity=0.8
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=mean2.values, theta=short_labels, fill='toself', name=p2,
            line_color=color2, opacity=0.8
        ))
        
        # Custom dark theme radar
        radar_layout = base_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 3], tickvals=[0, 1, 2, 3], ticktext=["Uenig", "Lidt uenig", "Lidt enig", "Enig"], tickfont=dict(color="#cbd5e1")),
                angularaxis=dict(tickfont=dict(size=10, color="#94a3b8"), rotation=90, direction="clockwise"),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
            margin=dict(l=50, r=50, t=40, b=40),
            height=600,
        )
        # Update layout, removing incompatible axis dicts from base_layout
        if "xaxis" in radar_layout: del radar_layout["xaxis"]
        if "yaxis" in radar_layout: del radar_layout["yaxis"]
        fig_radar.update_layout(**radar_layout)
        
        st.plotly_chart(fig_radar, use_container_width=True)

        # Highlight biggest differences
        st.markdown("**Størst uenighed mellem de to partier:**")
        cols = st.columns(min(len(top_diff_qs), 3))
        for i, col in enumerate(cols):
            if i < len(top_diff_qs):
                q = top_diff_qs[i]
                q_num = int(q.replace("Q", ""))
                q_text = q_dict.get(q_num, q)
                val1 = mean1[q]
                val2 = mean2[q]
                
                with col:
                    st.markdown(f"""
                    <div style="background: var(--bg-elevated); padding: 15px; border-radius: var(--radius-md); height: 100%;">
                        <p style="font-size:0.8rem; color:var(--text-muted); margin:0;">Spørgsmål {q_num}</p>
                        <p style="font-weight:600; font-size:0.95rem; margin:5px 0 10px 0;">{q_text}</p>
                        <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                            <span style="color:{color1}; font-weight:700;">{p1}: {val1:.1f}</span>
                            <span style="color:{color2}; font-weight:700;">{p2}: {val2:.1f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
