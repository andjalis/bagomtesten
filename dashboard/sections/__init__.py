"""
dashboard.sections — Chart rendering sub-package.

Re-exports all public render_* functions so the main app can import them
from a single location: `from dashboard.sections import render_party_distribution, ...`
"""

from dashboard.sections.party_distribution import render_party_distribution
from dashboard.sections.gaming_analysis import render_gaming_analysis
from dashboard.sections.correlation import render_correlation_analysis
from dashboard.sections.party_drilldown import render_party_drilldown
from dashboard.sections.blok_analysis import render_blok_analysis_global
from dashboard.sections.kommune_analysis import render_kommune_analysis
from dashboard.sections.data_foundation import render_data_foundation

from dashboard.sections.kpi_hero import render_kpi_hero
from dashboard.sections.party_pairs import render_party_pairs
from dashboard.sections.party_comparison import render_party_comparison

__all__ = [
    "render_party_distribution",
    "render_gaming_analysis",
    "render_correlation_analysis",
    "render_party_drilldown",
    "render_blok_analysis_global",
    "render_kommune_analysis",
    "render_data_foundation",
    "render_kpi_hero",
    "render_party_pairs",
    "render_party_comparison",
]
