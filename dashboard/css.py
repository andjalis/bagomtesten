"""
dashboard.css — Redesigned CSS for the Streamlit dashboard.

Modern dark-mode theme using Inter font, with proper contrast ratios,
readable active tabs, and consistent visual language.
"""

DASHBOARD_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Design Tokens ── */
    :root {
        --bg-base: #0f172a;
        --bg-surface: #1e293b;
        --bg-elevated: #334155;
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-accent: rgba(99, 102, 241, 0.3);

        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;

        --accent: #818cf8;
        --accent-hover: #6366f1;
        --accent-subtle: rgba(99, 102, 241, 0.1);

        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.25);
        --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.3);

        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-full: 9999px;
    }

    /* ── Base App Shell ── */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        background: var(--bg-base) !important;
        color: var(--text-primary);
    }

    /* ── Typography ── */
    h1, h2, h3, h4, h5, h6,
    .st-emotion-cache-10trblm {
        font-family: 'Inter', -apple-system, sans-serif !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
        font-weight: 700 !important;
    }

    h1 { font-weight: 800 !important; }

    p, li, span, div {
        color: var(--text-primary);
    }

    /* ── Tabs — Segmented Control ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: none !important;
        margin-bottom: 32px;
        background: var(--bg-surface);
        padding: 6px;
        border-radius: var(--radius-full);
        border: 1px solid var(--border-subtle);
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem;
        font-weight: 500;
        padding: 10px 20px;
        border-radius: var(--radius-full);
        color: var(--text-secondary) !important;
        border: none !important;
        background-color: transparent !important;
        box-shadow: none;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background-color: var(--bg-elevated) !important;
    }

    /* CRITICAL: Active tab must be readable */
    .stTabs [aria-selected="true"] {
        background-color: var(--accent) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: var(--shadow-sm);
    }

    /* Tab highlight bar override */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* ── Main Header ── */
    .main-header {
        text-align: center;
        padding: 48px 0 32px 0;
        margin-bottom: 12px;
    }
    .main-header h1 {
        font-size: 3.2rem !important;
        font-weight: 800 !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        margin-bottom: 12px;
        line-height: 1.1;
        letter-spacing: -0.03em;
    }
    .main-header p {
        color: var(--text-secondary) !important;
        font-size: 1.15rem;
        font-weight: 400;
        letter-spacing: 0.01em;
    }

    /* ── Candidate Cards ── */
    .cand-card {
        background: var(--bg-surface);
        border-radius: var(--radius-md);
        padding: 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 20px;
        border: 1px solid var(--border-subtle);
        transition: all 0.2s ease;
    }
    .cand-card:hover {
        border-color: var(--border-accent);
        background: rgba(30, 41, 59, 0.8);
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    .cand-img {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        object-fit: cover;
        background: var(--bg-elevated);
        border: 2px solid var(--border-subtle);
    }
    .cand-info { flex: 1; }
    .cand-name {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        margin: 0 0 4px 0;
        font-size: 1.1rem;
        color: var(--text-primary);
    }
    .cand-party {
        margin: 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 400;
    }
    .cand-count {
        text-align: right;
        min-width: 90px;
    }
    .cand-count strong {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.8rem;
        display: block;
        line-height: 1;
        margin-bottom: 4px;
        color: var(--text-primary);
    }
    .cand-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        display: block;
        font-weight: 600;
        margin-bottom: 2px;
    }
    .cand-sub {
        font-size: 0.8rem;
        color: var(--text-muted);
        display: block;
    }

    /* ── Answer Rows (expander content) ── */
    .answer-row {
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .answer-q-num {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 3px;
        font-weight: 500;
    }
    .answer-q-text {
        font-size: 1rem;
        color: var(--text-primary);
        margin-bottom: 5px;
        font-weight: 500;
    }
    .answer-val {
        font-weight: 600;
    }

    /* ── Info Cards (Methodology Tab) ── */
    .info-card {
        background: var(--bg-surface);
        padding: 32px;
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-subtle);
        height: 100%;
    }
    .info-card-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.4rem;
        margin: 0 0 16px 0;
        color: var(--text-primary);
    }
    .info-card-text {
        font-size: 1rem;
        line-height: 1.75;
        color: var(--text-secondary);
    }
    .info-card-text ul {
        margin: 12px 0 0 0;
        padding-left: 20px;
    }
    .info-card-text li {
        margin-bottom: 10px;
    }
    .info-card-text strong {
        color: var(--text-primary);
    }

    /* ── Persona Cards (Partisoldat / Oprører) ── */
    .persona-card {
        padding: 28px;
        background: var(--bg-surface);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-subtle);
        height: 100%;
    }
    .persona-title {
        font-weight: 700;
        font-size: 1.2rem;
        margin-bottom: 8px;
    }
    .persona-soldat .persona-title { color: #34d399; }
    .persona-oprorer .persona-title { color: #f87171; }
    .persona-name {
        font-weight: 700;
        font-size: 1.6rem;
        color: var(--text-primary);
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .persona-meta {
        color: var(--text-secondary);
        font-size: 1rem;
    }
    .persona-detail {
        margin-top: 16px;
        font-size: 1rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    .persona-detail strong {
        color: var(--text-primary);
    }

    /* ── Streamlit Native Element Overrides ── */
    [data-testid="stDataFrame"] {
        background: var(--bg-surface);
        border-radius: var(--radius-md);
        padding: 16px;
        border: 1px solid var(--border-subtle);
    }

    .stSelectbox, .stRadio {
        margin-bottom: 20px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: var(--bg-surface);
        border-radius: var(--radius-md);
        padding: 20px;
        border: 1px solid var(--border-subtle);
    }

    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        background: var(--bg-surface) !important;
    }

    /* Dividers */
    hr {
        border-color: var(--border-subtle) !important;
        margin: 28px 0 !important;
    }

    /* Caption text */
    .stCaption, [data-testid="stCaption"] {
        color: var(--text-muted) !important;
    }

    /* Scrollbar styling for dark mode */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--bg-elevated);
        border-radius: 3px;
    }

    /* ── KPI Hero Grid ── */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    .kpi-card {
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
        border-color: rgba(255, 255, 255, 0.15);
    }
    .kpi-card.kpi-accent {
        background: linear-gradient(145deg, var(--bg-surface) 0%, rgba(99, 102, 241, 0.08) 100%);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .kpi-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 500;
        margin-bottom: 8px;
        letter-spacing: 0.01em;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.1;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.02em;
    }
    .kpi-value.kpi-party {
        font-size: 1.4rem;
        line-height: 1.2;
        letter-spacing: -0.01em;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: var(--text-muted);
        min-height: 20px;
    }
    .kpi-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── Insight Chips ── */
    .insight-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin: 20px 0;
    }
    .insight-chip {
        display: flex;
        align-items: center;
        gap: 8px;
        background: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-left-width: 4px;
        padding: 10px 16px;
        border-radius: var(--radius-sm);
        font-size: 0.9rem;
        color: var(--text-primary);
    }
    .insight-icon {
        font-size: 1.2rem;
    }

    /* ── Method Section Components ── */
    .method-step {
        padding: 8px 0;
    }
    .method-step h4 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.15rem !important;
        color: var(--accent) !important;
        margin: 28px 0 12px 0 !important;
        letter-spacing: -0.01em;
    }
    .method-step h4:first-child {
        margin-top: 0 !important;
    }
    .method-step p {
        line-height: 1.8;
        color: var(--text-secondary);
        margin-bottom: 12px;
    }
    .method-step ul, .method-step ol {
        margin: 8px 0 16px 0;
        padding-left: 24px;
        color: var(--text-secondary);
    }
    .method-step li {
        margin-bottom: 8px;
        line-height: 1.7;
        color: var(--text-secondary);
    }
    .method-step strong {
        color: var(--text-primary);
    }
    .method-step code {
        background: var(--bg-elevated);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.9em;
        color: var(--accent);
    }

    .formula-box {
        background: linear-gradient(145deg, var(--bg-surface) 0%, rgba(99, 102, 241, 0.06) 100%);
        border: 1px solid var(--border-accent);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius-sm);
        padding: 20px 24px;
        margin: 16px 0 20px 0;
        font-family: 'Courier New', Courier, monospace;
        font-size: 1.05rem;
        color: var(--text-primary);
        line-height: 1.8;
        letter-spacing: 0.02em;
    }

    .method-highlight {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: var(--radius-md);
        padding: 20px 24px;
        margin: 16px 0;
        color: var(--text-secondary);
        line-height: 1.7;
    }
    .method-highlight strong {
        color: var(--accent);
    }

    /* ── Header Logos ── */
    .header-logos {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        margin-bottom: 20px;
    }
    .header-logo {
        height: 32px;
        opacity: 0.85;
        filter: brightness(0) invert(0.85);
        transition: opacity 0.2s ease;
    }
    .header-logo:hover {
        opacity: 1;
    }
    .header-logo-divider {
        font-size: 1.2rem;
        color: var(--text-muted);
        font-weight: 300;
    }

    /* ── Party Badge Row ── */
    .party-badge-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-top: 20px;
        flex-wrap: wrap;
    }
    .party-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        color: #fff;
        font-weight: 700;
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s ease;
        cursor: default;
        box-shadow: var(--shadow-sm);
    }
    .party-badge:hover {
        transform: scale(1.15);
        box-shadow: var(--shadow-md);
    }

    /* ═══════════════════════════════════════════════════════
       ── Mobile & Tablet Responsive ──
       ═══════════════════════════════════════════════════════ */

    /* ── Tablet (≤900px) ── */
    @media (max-width: 900px) {
        .main-header h1 {
            font-size: 2.2rem !important;
        }
        .kpi-grid {
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
        }
        .kpi-value {
            font-size: 1.8rem;
        }
    }

    /* ── Mobile (≤640px) ── */
    @media (max-width: 640px) {

        /* Header */
        .main-header {
            padding: 24px 8px 16px 8px;
        }
        .main-header h1 {
            font-size: 1.5rem !important;
            letter-spacing: -0.02em;
            line-height: 1.2;
            word-break: break-word;
        }
        .main-header p {
            font-size: 0.85rem !important;
            line-height: 1.5;
        }

        /* Tabs — allow wrapping on small screens */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            padding: 4px;
            border-radius: 12px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.8rem;
            padding: 7px 12px;
        }

        /* KPI Cards — 2-column grid on phones */
        .kpi-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        .kpi-card {
            padding: 14px;
        }
        .kpi-value {
            font-size: 1.5rem;
        }
        .kpi-value.kpi-party {
            font-size: 1.1rem;
        }
        .kpi-label {
            font-size: 0.78rem;
        }
        .kpi-sub {
            font-size: 0.75rem;
        }

        /* Metrics */
        [data-testid="stMetric"] {
            padding: 12px;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }

        /* Candidate cards — stack on mobile */
        .cand-card {
            flex-wrap: wrap;
            padding: 14px;
            gap: 12px;
        }
        .cand-img {
            width: 44px;
            height: 44px;
        }
        .cand-name {
            font-size: 0.95rem;
        }
        .cand-party {
            font-size: 0.8rem;
        }
        .cand-count {
            min-width: 70px;
        }
        .cand-count strong {
            font-size: 1.4rem;
        }

        /* Info cards — remove fixed height, tighter padding */
        .info-card {
            padding: 18px;
            height: auto;
        }
        .info-card-title {
            font-size: 1.1rem;
        }
        .info-card-text {
            font-size: 0.9rem;
            line-height: 1.65;
        }

        /* Insight chips — full width */
        .insight-row {
            flex-direction: column;
            gap: 8px;
        }
        .insight-chip {
            font-size: 0.82rem;
            padding: 8px 12px;
        }

        /* Method section */
        .method-step h4 {
            font-size: 1rem !important;
        }
        .method-step p,
        .method-step li {
            font-size: 0.9rem;
            line-height: 1.65;
        }

        /* Persona cards */
        .persona-card {
            padding: 16px;
        }
        .persona-name {
            font-size: 1.3rem;
        }

        /* Global h2/h3 sizing */
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
        h4 { font-size: 1rem !important; }

        /* Reduce Streamlit default padding on mobile */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
        }

        /* Make plotly charts not overflow horizontally */
        .stPlotlyChart {
            overflow-x: auto !important;
        }

        /* Expanders */
        [data-testid="stExpander"] summary {
            font-size: 0.9rem;
        }

        /* Dataframes — horizontal scroll */
        [data-testid="stDataFrame"] {
            overflow-x: auto;
        }
    }

</style>
"""

