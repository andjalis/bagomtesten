"""Party drill-down section — per-party detailed analysis tab (includes unified view with comparison)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import PARTY_COLORS
from dashboard.sections._plotly_theme import base_layout


from dashboard.data import load_candidates_data, load_questions, load_kommune_stats, load_candidate_gaming
from dashboard.sections.gaming_analysis import _render_candidate_cards

def render_party_drilldown():
    """Render the party-specific drilldown tab from precomputed data."""
    st.header("🔍 Dyk ned i et specifikt parti")
    st.caption("Detaljeret profil af ét bestemt parti: geografi, top-kandidater fra testen og partidisciplin.")

    parties = list(PARTY_COLORS.keys())

    # Store in session state to maintain selection across reruns if needed
    party = st.selectbox("Vælg parti for dybdegående analyse:", parties, index=parties.index("Alternativet") if "Alternativet" in parties else 0)
    p_color = PARTY_COLORS.get(party, "#3b82f6")

    st.divider()
    
    # 1. Top Section - Map
    st.subheader("📍 Geografisk styrke (top-1 pct.)")
    
    k_stats = load_kommune_stats()
    if not k_stats.empty:
        # Approximate win rate from precalculated block percentages and top party
        # Note: real version would have exact party % in JSON if we needed perfect accuracy, 
        # but for this specific "which municipality does the party shine in" we can infer or 
        # just show the municipalities where this party won it all.
        
        # Let's filter to municipalities where this party is the top winner.
        party_muns = k_stats[k_stats["Top_Party"] == party]
        
        if not party_muns.empty:
            st.markdown(f"**{party}** er det bedst matchende parti i følgende kommuner:")
            party_muns = party_muns.copy()
            party_muns["Dominerende Blok Pct"] = party_muns.apply(lambda r: r["Red_Pct"] if r["Vinder_Blok"] == "Rød Blok" else r["Blue_Pct"], axis=1)
            party_muns = party_muns.sort_values("Dominerende Blok Pct", ascending=False)
            
            fig_map = px.bar(
                party_muns, x="Kommune", y="Dominerende Blok Pct",
                title=f"Kommuner vundet af {party} (Farvet efter blok-størrelse)",
                color_discrete_sequence=[p_color],
            )
            fig_map.update_layout(**base_layout(
                xaxis=dict(title="", tickangle=-45),
                yaxis=dict(title="Top Blok (%)", showgrid=True),
                margin=dict(l=0, r=0, t=50, b=0),
            ))
            st.plotly_chart(fig_map, use_container_width=True, key=f"drilldown_local_map_{party}")
        else:
            st.info(f"{party} var ikke det mest anbefalede parti i nogen kommune samlet set.")
    
    st.divider()
    
    # 2. Top-5 Candidates
    st.subheader(f"🥇 Mest anbefalede kandidater i {party}")
    st.caption("Disse kandidater tonede oftest frem på skærmen som absolut top-match for testtagerne.")
    
    top_candidates, _ = load_candidate_gaming()
    
    if not top_candidates.empty:
        party_top = top_candidates[top_candidates["party"] == party]
        if not party_top.empty:
            _render_candidate_cards(party_top, key_prefix="drilldown")
        else:
            st.info("Ingen kandidater at vise for dette parti i top-listerne.")
    else:
        st.info("Data mangler.")

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
        xaxis=dict(title="Intern uenighed (varians)", showgrid=True),
        yaxis=dict(title="", autorange="reversed"),
        height=600,
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False
    ))
    fig_var.update_traces(
        hovertemplate="<b>%{y}</b><br>Varians: %{x:.2f}<extra></extra>"
    )
    st.plotly_chart(fig_var, use_container_width=True, key=f"drilldown_variance_bar_{party}")

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

    st.divider()

    # -- 5. Fiktiv Besvarelsesoversigt (Partiets Samlede Svar) --
    st.subheader(f"📋 Fiktiv profil: Hvad svarer {party} samlet set?")
    st.caption("Hvis partiet var én samlet kandidat, baseret på gennemsnittet af alle deres kandidaters svar, ville profilen se sådan ud:")

    from config import ANSWER_LABELS

    # Create summary records
    summary_records = []
    party_means = mean_vec.copy() 
    
    # Sort questions 1-25 
    for i in range(1, 26):
        q_col = f"Q{i}"
        val = party_means[q_col]
        
        # Round to nearest valid answer (0, 1, 2, 3)
        rounded_val = int(round(val))
        
        ans_text = ANSWER_LABELS.get(rounded_val, "Ukendt")
        
        # Add visual indicator based on answer
        indicator = ""
        if rounded_val == 3: indicator = "🟩 Enig"
        elif rounded_val == 2: indicator = "🟨 Lidt enig"
        elif rounded_val == 1: indicator = "🟧 Lidt uenig"
        elif rounded_val == 0: indicator = "🟥 Uenig"

        q_text = q_dict.get(i, f"Spørgsmål {i}")
        
        summary_records.append({
            "Q_Num": i,
            "Spørgsmål": q_text,
            "Gns. Værdi (0-3)": f"{val:.1f}",
            "Fiktivt Svar": indicator,
        })
        
    summary_df = pd.DataFrame(summary_records).set_index("Q_Num")
    
    # Render as a clean dataframe
    st.dataframe(
        summary_df,
        use_container_width=True,
        height=600,
        column_config={
            "Spørgsmål": st.column_config.TextColumn("Spørgsmål", width="large"),
            "Gns. Værdi (0-3)": st.column_config.TextColumn("Matematisk gns.", width="small"),
            "Fiktivt Svar": st.column_config.TextColumn("Afrundet svar", width="medium"),
        }
    )


def render_partier_unified():
    """Unified Partier tab: party drilldown + inline comparison using a shared party selector."""
    from dashboard.data import load_party_rankings

    st.header("🔍 Parti-analyse")
    st.caption("Vælg et parti for at se dets detaljerede profil — og sammenlign det med et andet parti.")

    parties = list(PARTY_COLORS.keys())

    # ── Shared party selector ──
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        party = st.selectbox(
            "Vælg parti til dybdegående analyse:",
            parties,
            index=parties.index("Alternativet") if "Alternativet" in parties else 0,
            key="unified_party_main",
        )
    with col_sel2:
        compare_party = st.selectbox(
            "Sammenlign med:",
            [p for p in parties if p != party],
            index=([p for p in parties if p != party].index("Venstre")
                   if "Venstre" in [p for p in parties if p != party] else 0),
            key="unified_party_compare",
        )

    p_color = PARTY_COLORS.get(party, "#3b82f6")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION A — DRILLDOWN (inline, same as render_party_drilldown but using shared selector)
    # ═══════════════════════════════════════════════════════════════════════════

    # 1. Geographic strength
    st.subheader("📍 Geografisk styrke (top-1 pct.)")

    k_stats = load_kommune_stats()
    if not k_stats.empty:
        party_muns = k_stats[k_stats["Top_Party"] == party]
        if not party_muns.empty:
            st.markdown(f"**{party}** er det bedst matchende parti i følgende kommuner:")
            party_muns = party_muns.copy()
            party_muns["Dominerende Blok Pct"] = party_muns.apply(
                lambda r: r["Red_Pct"] if r["Vinder_Blok"] == "Rød Blok" else r["Blue_Pct"], axis=1
            )
            party_muns = party_muns.sort_values("Dominerende Blok Pct", ascending=False)

            fig_map = px.bar(
                party_muns, x="Kommune", y="Dominerende Blok Pct",
                title=f"Kommuner vundet af {party} (farvet efter blok-størrelse)",
                color_discrete_sequence=[p_color],
            )
            fig_map.update_layout(**base_layout(
                xaxis=dict(title="", tickangle=-45),
                yaxis=dict(title="Top Blok (%)", showgrid=True),
                margin=dict(l=0, r=0, t=50, b=0),
            ))
            st.plotly_chart(fig_map, use_container_width=True, key=f"unified_local_map_{party}")
        else:
            st.info(f"{party} var ikke det mest anbefalede parti i nogen kommune samlet set.")

    st.divider()

    # 2. Top candidates
    st.subheader(f"🥇 Mest anbefalede kandidater i {party}")
    st.caption("Disse kandidater tonede oftest frem på skærmen som absolut top-match for testtagerne.")

    top_candidates, _ = load_candidate_gaming()
    if not top_candidates.empty:
        party_top = top_candidates[top_candidates["party"] == party]
        if not party_top.empty:
            _render_candidate_cards(party_top, key_prefix="unified_drill")
        else:
            st.info("Ingen kandidater at vise for dette parti i top-listerne.")
    else:
        st.info("Data mangler.")

    st.divider()

    # 3. Intra-party analysis
    c_df = load_candidates_data()
    q_dict = load_questions()
    q_cols = [f"Q{i+1}" for i in range(25)]

    if not c_df.empty:
        p_c_df = c_df[c_df["party"] == party].copy()
        if len(p_c_df) >= 2:
            st.subheader(f"🤝 Intern enighed ({len(p_c_df)} kandidater fra {party})")
            st.caption("Viser hvor enige kandidaterne i partiet er om de enkelte spørgsmål.")

            variances = p_c_df[q_cols].var().sort_values()
            var_df = pd.DataFrame({"Spørgsmål": variances.index, "Varians": variances.values})
            var_df["Spørgsmål_Tekst"] = var_df["Spørgsmål"].apply(
                lambda q: f"{q.replace('Q', '')}. {q_dict.get(int(q.replace('Q', '')), '')[:60]}..."
            )
            var_df["Color_Val"] = var_df["Varians"]

            fig_var = px.bar(
                var_df, x="Varians", y="Spørgsmål_Tekst",
                orientation="h", color="Varians",
                color_continuous_scale="RdYlGn_r", title="",
            )
            fig_var.update_layout(**base_layout(
                xaxis=dict(title="Intern uenighed (varians)", showgrid=True),
                yaxis=dict(title="", autorange="reversed"),
                height=600,
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
            ))
            fig_var.update_traces(hovertemplate="<b>%{y}</b><br>Varians: %{x:.2f}<extra></extra>")
            st.plotly_chart(fig_var, use_container_width=True, key=f"unified_variance_{party}")

            st.divider()

            # 4. Partisoldat vs. oprører
            st.subheader("👤 Partisoldat vs. oprører")
            st.caption(f"Hvilke kandidater for {party} ligger hhv. tættest på og længst fra partiets gennemsnit?")

            mean_vec = p_c_df[q_cols].mean()
            distances = (p_c_df[q_cols] - mean_vec).abs().sum(axis=1)
            p_c_df["Afvigelse"] = distances

            soldat = p_c_df.loc[distances.idxmin()]
            oprorer = p_c_df.loc[distances.idxmax()]

            col3, col4 = st.columns(2)

            def _render_persona_unified(persona_row, title, css_class, desc_prefix):
                img_src = persona_row.get("candidate_image", "")
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
                    dev_records = []
                    for q_idx in range(1, 26):
                        q_col = f"Q{q_idx}"
                        if q_col in persona_row:
                            cand_val = persona_row[q_col]
                            party_mean_val = mean_vec[q_col]
                            deviation = cand_val - party_mean_val
                            short_q = f"Q{q_idx}. {q_dict.get(q_idx, '')[:45]}..."
                            dev_records.append({
                                "Spørgsmål": short_q, "Afvigelse": deviation,
                                "AbsAfvigelse": abs(deviation), "Svar": cand_val, "PartiGns": party_mean_val
                            })
                    dev_df = pd.DataFrame(dev_records).sort_values("AbsAfvigelse", ascending=True)

                    fig_dev = px.bar(
                        dev_df, x="Afvigelse", y="Spørgsmål", orientation="h",
                        color="AbsAfvigelse", color_continuous_scale="RdYlGn_r", title="",
                    )
                    from config import ANSWER_LABELS
                    hover_texts = []
                    for _, row in dev_df.iterrows():
                        ans_str = ANSWER_LABELS.get(row["Svar"], "Ukendt")
                        hover_texts.append(f"<b>Kandidatens svar:</b> {ans_str}<br><b>Partiets gns:</b> {row['PartiGns']:.1f}<br><b>Afvigelse:</b> {row['AbsAfvigelse']:.1f} pt")
                    fig_dev.update_traces(customdata=hover_texts, hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>")
                    max_dev = max(1.5, dev_df["AbsAfvigelse"].max() * 1.1)
                    fig_dev.update_layout(**base_layout(
                        xaxis=dict(title="Afvigelse fra parti-linjen (point)", range=[-max_dev, max_dev], showgrid=True, zeroline=True, zerolinecolor="#64748b", zerolinewidth=2),
                        yaxis=dict(title="", showgrid=False), height=600,
                        margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False,
                    ))
                    st.plotly_chart(fig_dev, use_container_width=True, key=f"unified_dev_{persona_row['candidate_name']}")

            with col3:
                _render_persona_unified(soldat, "Partisoldaten", "persona-soldat", "Stemmer mest trofast")
            with col4:
                _render_persona_unified(oprorer, "Oprøreren", "persona-oprorer", "Største afviger")

            st.divider()

            # 5. Fictional profile
            st.subheader(f"📋 Fiktiv profil: Hvad svarer {party} samlet set?")
            st.caption("Hvis partiet var én samlet kandidat, baseret på gennemsnittet af alle deres kandidaters svar:")
            from config import ANSWER_LABELS
            summary_records = []
            party_means = mean_vec.copy()
            for i in range(1, 26):
                q_col = f"Q{i}"
                val = party_means[q_col]
                rounded_val = int(round(val))
                indicator = ""
                if rounded_val == 3: indicator = "🟩 Enig"
                elif rounded_val == 2: indicator = "🟨 Lidt enig"
                elif rounded_val == 1: indicator = "🟧 Lidt uenig"
                elif rounded_val == 0: indicator = "🟥 Uenig"
                q_text = q_dict.get(i, f"Spørgsmål {i}")
                summary_records.append({"Q_Num": i, "Spørgsmål": q_text, "Gns. Værdi (0-3)": f"{val:.1f}", "Fiktivt Svar": indicator})
            summary_df = pd.DataFrame(summary_records).set_index("Q_Num")
            st.dataframe(summary_df, use_container_width=True, height=600, column_config={
                "Spørgsmål": st.column_config.TextColumn("Spørgsmål", width="large"),
                "Gns. Værdi (0-3)": st.column_config.TextColumn("Matematisk gns.", width="small"),
                "Fiktivt Svar": st.column_config.TextColumn("Afrundet svar", width="medium"),
            })

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION B — COMPARISON (party vs compare_party, using the shared selectors)
    # ═══════════════════════════════════════════════════════════════════════════

    color1 = PARTY_COLORS.get(party, "#ef4444")
    color2 = PARTY_COLORS.get(compare_party, "#3b82f6")

    st.header(f"⚖️ {party} vs. {compare_party}")
    st.caption("Side-om-side sammenligning af de to valgte partier.")

    # Key figures
    party_rankings = load_party_rankings()
    if not party_rankings.empty:
        st.subheader("📊 Nøgletal")
        count1 = party_rankings[party_rankings["Party"] == party]["Count"].iloc[0] if not party_rankings[party_rankings["Party"] == party].empty else 0
        count2 = party_rankings[party_rankings["Party"] == compare_party]["Count"].iloc[0] if not party_rankings[party_rankings["Party"] == compare_party].empty else 0
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric(f"{party} — top-1 visninger", f"{count1:,}".replace(",", "."))
        with col_s2:
            st.metric(f"{compare_party} — top-1 visninger", f"{count2:,}".replace(",", "."))
        st.divider()

    # Radar chart
    if not c_df.empty:
        st.subheader("🎯 Svarprofil-sammenligning")
        st.caption("Gennemsnitligt svarmønster på tværs af alle 25 spørgsmål for begge partier.")

        mean1 = c_df[c_df["party"] == party][q_cols].mean()
        mean2 = c_df[c_df["party"] == compare_party][q_cols].mean()

        diffs = (mean1 - mean2).abs().sort_values(ascending=False)
        top_diff_qs = diffs.head(5).index.tolist()

        short_labels = []
        for q in q_cols:
            q_num = int(q.replace("Q", ""))
            text = q_dict.get(q_num, q)
            short_labels.append(f"Q{q_num}: {text[:20]}...")

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=mean1.values, theta=short_labels, fill="toself", name=party,
            line_color=color1, opacity=0.8
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=mean2.values, theta=short_labels, fill="toself", name=compare_party,
            line_color=color2, opacity=0.8
        ))

        radar_layout = base_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 3], tickvals=[0, 1, 2, 3],
                                ticktext=["Uenig", "Lidt uenig", "Lidt enig", "Enig"],
                                tickfont=dict(color="#cbd5e1")),
                angularaxis=dict(tickfont=dict(size=10, color="#94a3b8"), rotation=90, direction="clockwise"),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
            margin=dict(l=50, r=50, t=40, b=40),
            height=600,
        )
        if "xaxis" in radar_layout: del radar_layout["xaxis"]
        if "yaxis" in radar_layout: del radar_layout["yaxis"]
        fig_radar.update_layout(**radar_layout)

        st.plotly_chart(fig_radar, use_container_width=True, key="unified_comparison_radar")

        # Biggest differences
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
                            <span style="color:{color1}; font-weight:700;">{party}: {val1:.1f}</span>
                            <span style="color:{color2}; font-weight:700;">{compare_party}: {val2:.1f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

