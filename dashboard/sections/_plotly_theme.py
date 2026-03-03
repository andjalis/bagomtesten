"""
_plotly_theme.py — Shared Plotly layout defaults for the dark-mode dashboard.

Provides a consistent, readable theme for all charts: light text on dark
backgrounds, subtle grid lines, and the Inter font family.
"""

# ── Rank color palette (1st through 6th place) ───────────────────────────────
RANK_COLORS = {
    "Nr. 1": "#f97316",  # Vibrant orange
    "Nr. 2": "#94a3b8",  # Silver
    "Nr. 3": "#b45309",  # Bronze
    "Nr. 4": "#60a5fa",  # Light blue
    "Nr. 5": "#a78bfa",  # Lavender
    "Nr. 6": "#f472b6",  # Pink
}

# ── Dark-mode Plotly layout ───────────────────────────────────────────────────
_PLOTLY_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color="#cbd5e1", size=13),
    hoverlabel=dict(
        bgcolor="#1e293b",
        font_size=13,
        font_family="Inter, system-ui, sans-serif",
        font_color="#e2e8f0",
        bordercolor="#334155",
    ),
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        title_font=dict(size=12, color="#94a3b8"),
        tickfont=dict(color="#94a3b8", size=11),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.04)",
        zeroline=False,
        showline=False,
        title_font=dict(size=12, color="#94a3b8"),
        tickfont=dict(color="#94a3b8", size=11),
    ),
    legend=dict(
        font=dict(color="#94a3b8", size=12),
    ),
    margin=dict(t=60, b=40, l=0, r=0),
)


def base_layout(**overrides) -> dict:
    """Return a copy of the shared Plotly layout dict merged with overrides."""
    import copy
    layout = copy.deepcopy(_PLOTLY_LAYOUT)
    for k, v in overrides.items():
        if isinstance(v, dict) and k in layout and isinstance(layout[k], dict):
            layout[k].update(v)
        else:
            layout[k] = v
    return layout
