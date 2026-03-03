"""Question Impact (Effect Size) section — showing which questions change the outcome most."""

import plotly.express as px
import streamlit as st

from dashboard.data import load_question_impact
from dashboard.sections._plotly_theme import base_layout

def render_question_impact():
    """Render a horizontal bar chart of question effect sizes."""
    st.subheader("🎯 Spørgsmåls-Indflydelse (Effect Size)")
    st.caption("Viser hvilke spørgsmål, der i gennemsnit skaber størst udsving i testens anbefalinger.")

    impact_df = load_question_impact()
    if impact_df.empty:
        st.warning("Data mangler. Kør bygge-scriptet `build_dashboard_data.py`.")
        return

    # Sort ascending for plotly horizontal bar
    impact_df = impact_df.sort_values("Indflydelse (Effect Size)", ascending=True)

    fig = px.bar(
        impact_df,
        x="Indflydelse (Effect Size)",
        y="Spørgsmål",
        orientation="h",
        color="Indflydelse (Effect Size)",
        color_continuous_scale="Viridis",
        hover_data={"Tekst": True, "Indflydelse (Effect Size)": ":.1f"}
    )

    fig.update_layout(**base_layout(
        xaxis=dict(title="Max Variations-point pr. spørgsmål"),
        yaxis=dict(title=""),
        coloraxis_showscale=False,
        height=max(400, len(impact_df) * 25),
        margin=dict(l=0, r=0, t=10, b=0),
    ))

    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Indflydelse: %{x:.1f} point<br><i>%{customdata[0]}</i><extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)
