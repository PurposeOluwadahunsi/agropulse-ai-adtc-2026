

import streamlit as st
def apply_sidebar_button_fix() -> None:
    """Hide the raw Streamlit button text in sidebar — HTML divs handle visuals."""
    import streamlit as st
    st.markdown("""
    <style>
    /* Hide sidebar nav button text HTML divs provide the visual */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        height: 0 !important;
        padding: 0 !important;
        margin: -2px 0 0 0 !important;
        font-size: 0 !important;
        box-shadow: none !important;
        min-height: 0 !important;
        line-height: 0 !important;
    }
    /* Style expanders in sidebar */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 4px !important;
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 0.4rem 0.75rem !important;
        margin: 2px 0 !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background: rgba(255,255,255,0.1) !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderContent {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }
    /* Main area buttons stay styled */
    .block-container .stButton > button {
        background: var(--green-700) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 2px 6px rgba(45,106,79,0.3) !important;
    }
    .block-container .stButton > button:hover {
        background: var(--green-900) !important;
    }
    </style>
    """, unsafe_allow_html=True)
def apply_sidebar_button_fix() -> None:
    """No-op kept for backward compatibility — navigation now uses st.radio."""
    pass

def apply_styles() -> None:
    st.markdown("""
    <style>
    /* ── TOKENS ─────────────────────────────────────────────── */
    :root {
        --green-900: #1A3C2E;
        --green-700: #2D6A4F;
        --green-500: #4A7C59;
        --green-300: #74B08A;
        --green-100: #D6EAD8;
        --green-50:  #EEF7EF;
        --bg:        #F8F6F1;
        --surface:   #FFFFFF;
        --border:    #E5E7EB;
        --border-md: #D1D5DB;
        --text-900:  #111827;
        --text-700:  #374151;
        --text-500:  #6B7280;
        --text-300:  #9CA3AF;
        --amber:     #D97706;
        --amber-bg:  #FFFBEB;
        --amber-border: #FCD34D;
        --red-900:   #7F1D1D;
        --red-700:   #991B1B;
        --red-500:   #DC2626;
        --red-bg:    #FEF2F2;
        --red-border:#FECACA;
        --blue-700:  #1D4ED8;
        --blue-bg:   #EFF6FF;
        --blue-border:#BFDBFE;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
        --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
    }

    /* ── GLOBAL ─────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     system-ui, sans-serif;
        background: var(--bg);
        color: var(--text-900);
    }
    .block-container {
        padding: 1.5rem 2rem 3rem 2rem !important;
        max-width: 1160px !important;
    }
    h1,h2,h3,h4 { color: var(--text-900); font-weight: 600; }
    a { color: var(--green-700); }

    /* ── SIDEBAR ────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: var(--green-900) !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * { color: #E5F0E8 !important; }
    [data-testid="stSidebar"] .sidebar-logo {
        padding: 1.5rem 1.25rem 0.75rem;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] .sidebar-logo h2 {
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFFFFF !important;
        margin: 0;
        letter-spacing: -0.2px;
    }
    [data-testid="stSidebar"] .sidebar-logo p {
        font-size: 0.72rem;
        color: rgba(255,255,255,0.55) !important;
        margin: 0.15rem 0 0;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .nav-section-label {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255,255,255,0.35) !important;
        padding: 1rem 1.25rem 0.3rem;
        display: block;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.55rem 1.25rem;
        font-size: 0.875rem;
        color: rgba(255,255,255,0.75) !important;
        cursor: pointer;
        border-radius: 0;
        transition: background 0.15s;
        text-decoration: none;
    }
    .nav-item:hover, .nav-item.active {
        background: rgba(255,255,255,0.08);
        color: #FFFFFF !important;
    }
    .nav-item.active { border-left: 3px solid var(--green-300); }
    .sidebar-status {
        padding: 1rem 1.25rem;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin-top: auto;
    }
    .status-dot {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.65) !important;
        padding: 0.2rem 0;
    }
    .status-dot::before {
        content: '';
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #4ADE80;
        flex-shrink: 0;
    }
    .status-dot.warn::before { background: #FBBF24; }
    .status-dot.off::before  { background: #6B7280; }

    /* ── HERO ───────────────────────────────────────────────── */
    .ap-hero {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-sm);
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
    }
    .ap-hero-left h1 {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--green-900);
        margin: 0 0 0.15rem;
        letter-spacing: -0.4px;
    }
    .ap-hero-left .tagline {
        font-size: 0.875rem;
        color: var(--green-500);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0 0 0.5rem;
    }
    .ap-hero-left .description {
        font-size: 0.875rem;
        color: var(--text-500);
        max-width: 520px;
        line-height: 1.55;
        margin: 0;
    }
    .ap-hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        align-items: flex-start;
        padding-top: 0.25rem;
    }
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.65rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        background: var(--green-50);
        color: var(--green-700);
        border: 1px solid var(--green-100);
        white-space: nowrap;
    }
    .badge-pill.blue {
        background: var(--blue-bg);
        color: var(--blue-700);
        border-color: var(--blue-border);
    }

    /* ── SECTION HEADER ─────────────────────────────────────── */
    .section-header {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--text-500);
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
        margin: 1.5rem 0 1rem;
    }

    /* ── DASHBOARD CARDS ────────────────────────────────────── */
    .dash-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        height: 100%;
    }
    .dash-card .card-icon {
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
        display: block;
    }
    .dash-card .card-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-500);
        margin-bottom: 0.25rem;
    }
    .dash-card .card-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--text-900);
        line-height: 1.2;
    }
    .dash-card .card-value.green  { color: var(--green-700); }
    .dash-card .card-value.amber  { color: var(--amber); }
    .dash-card .card-value.red    { color: var(--red-700); }
    .dash-card .card-value.blue   { color: var(--blue-700); }
    .dash-card .card-desc {
        font-size: 0.75rem;
        color: var(--text-500);
        margin-top: 0.2rem;
    }

    /* ── CONSULTATION PANEL ─────────────────────────────────── */
    .consult-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.25rem;
        box-shadow: var(--shadow-sm);
    }
    .consult-card .consult-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-500);
        margin-bottom: 0.75rem;
    }
    .stTextArea textarea {
        border: 1.5px solid var(--border-md) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
        background: var(--bg) !important;
        color: var(--text-900) !important;
        padding: 0.75rem !important;
        resize: vertical !important;
    }
    .stTextArea textarea:focus {
        border-color: var(--green-500) !important;
        box-shadow: 0 0 0 3px rgba(74,124,89,0.12) !important;
        outline: none !important;
    }

    /* ── SAMPLE QUERY CHIPS ─────────────────────────────────── */
    .sample-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-500);
        margin: 0.75rem 0 0.4rem;
    }
    .sample-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
        margin-bottom: 0.25rem;
    }

    /* ── ANALYZE BUTTON ─────────────────────────────────────── */
    .stButton > button {
        background: var(--green-700) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.6rem 1.5rem !important;
        width: 100% !important;
        letter-spacing: 0.1px;
        box-shadow: 0 2px 6px rgba(45,106,79,0.3) !important;
        transition: background 0.15s !important;
    }
    .stButton > button:hover {
        background: var(--green-900) !important;
        box-shadow: 0 3px 10px rgba(45,106,79,0.4) !important;
    }

    /* ── ASSESSMENT CARDS ───────────────────────────────────── */
    .assessment-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.75rem;
    }
    .assessment-card.critical {
        border-left: 4px solid var(--red-500);
    }
    .assessment-card.moderate {
        border-left: 4px solid var(--amber);
    }
    .assessment-card.low {
        border-left: 4px solid var(--green-500);
    }
    .assessment-card.info {
        border-left: 4px solid var(--blue-700);
    }
    .assessment-card .ac-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-500);
        margin-bottom: 0.35rem;
    }
    .assessment-card .ac-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-900);
    }
    .assessment-card .ac-body {
        font-size: 0.875rem;
        color: var(--text-700);
        line-height: 1.6;
        margin-top: 0.25rem;
    }

    /* ── SEVERITY BADGES ────────────────────────────────────── */
    .sev-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .sev-critical { background: var(--red-bg);   color: var(--red-700);  border: 1px solid var(--red-border); }
    .sev-moderate { background: var(--amber-bg); color: var(--amber);    border: 1px solid var(--amber-border); }
    .sev-low      { background: var(--green-50); color: var(--green-700);border: 1px solid var(--green-100); }
    .sev-unknown  { background: #F9FAFB;         color: var(--text-500); border: 1px solid var(--border); }

    /* ── CONFIDENCE BAR ─────────────────────────────────────── */
    .conf-container {
        margin: 0.5rem 0 0.25rem;
    }
    .conf-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.35rem;
    }
    .conf-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-700);
    }
    .conf-pct {
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--text-900);
    }
    .conf-track {
        height: 6px;
        background: var(--border);
        border-radius: 3px;
        overflow: hidden;
    }
    .conf-fill {
        height: 100%;
        border-radius: 3px;
        background: var(--green-500);
        transition: width 0.4s ease;
    }
    .conf-fill.high     { background: var(--green-500); }
    .conf-fill.moderate { background: var(--amber); }
    .conf-fill.low      { background: var(--red-500); }

    /* ── SYMPTOM TAGS ───────────────────────────────────────── */
    .symptom-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        background: var(--green-50);
        color: var(--green-700);
        border: 1px solid var(--green-100);
        border-radius: 4px;
        padding: 0.2rem 0.55rem;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 0.15rem 0.15rem 0 0;
    }

    /* ── EVIDENCE PANEL ─────────────────────────────────────── */
    .evidence-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.75rem;
    }
    .evidence-card .ev-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-500);
        margin-bottom: 0.6rem;
    }
    .source-card {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.65rem 0.75rem;
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        margin-bottom: 0.4rem;
    }
    .source-card .src-icon {
        font-size: 1rem;
        flex-shrink: 0;
        margin-top: 0.05rem;
    }
    .source-card .src-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-900);
        line-height: 1.3;
    }
    .source-card .src-meta {
        font-size: 0.72rem;
        color: var(--text-500);
        margin-top: 0.1rem;
    }
    .source-card .src-conf {
        margin-left: auto;
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--green-700);
        white-space: nowrap;
        padding-top: 0.05rem;
    }
    .reasoning-box {
        background: var(--blue-bg);
        border: 1px solid var(--blue-border);
        border-radius: var(--radius-sm);
        padding: 0.75rem 1rem;
        font-size: 0.85rem;
        color: var(--text-700);
        line-height: 1.6;
        font-style: italic;
    }

    /* ── EMERGENCY ALERT ────────────────────────────────────── */
    .emergency-alert {
        background: var(--red-bg);
        border: 1px solid var(--red-border);
        border-left: 4px solid var(--red-500);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    .emergency-alert .ea-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--red-700);
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 0.4rem;
    }
    .emergency-alert .ea-body {
        font-size: 0.82rem;
        color: var(--red-900);
        line-height: 1.55;
    }

    /* ── VET ALERT ──────────────────────────────────────────── */
    .vet-alert {
        background: var(--amber-bg);
        border: 1px solid var(--amber-border);
        border-left: 4px solid var(--amber);
        border-radius: var(--radius-md);
        padding: 0.85rem 1.1rem;
        margin-bottom: 0.75rem;
        font-size: 0.84rem;
        color: #78350F;
        line-height: 1.5;
    }
    .vet-alert strong { color: #92400E; }

    /* ── ACTION PLAN ────────────────────────────────────────── */
    .action-plan {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.75rem;
    }
    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border);
        font-size: 0.875rem;
        color: var(--text-700);
        line-height: 1.5;
    }
    .action-item:last-child { border-bottom: none; }
    .action-num {
        min-width: 22px;
        height: 22px;
        background: var(--green-700);
        color: #fff;
        border-radius: 50%;
        font-size: 0.68rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 0.1rem;
    }

    /* ── HISTORY TABLE ──────────────────────────────────────── */
    .hist-table { width: 100%; border-collapse: collapse; }
    .hist-row {
        display: grid;
        grid-template-columns: 145px 1fr 90px 72px 60px;
        gap: 0.5rem;
        padding: 0.6rem 0.75rem;
        border-bottom: 1px solid var(--border);
        font-size: 0.8rem;
        color: var(--text-700);
        align-items: center;
        background: var(--surface);
    }
    .hist-row:first-child {
        background: var(--bg);
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-500);
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        border-bottom: 2px solid var(--border);
    }
    .hist-row:last-child { border-bottom: none; }
    .hist-wrap {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    /* ── STAT BLOCKS ────────────────────────────────────────── */
    .stat-block {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        text-align: center;
    }
    .stat-block .stat-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--green-700);
        line-height: 1;
    }
    .stat-block .stat-lbl {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-500);
        margin-top: 0.3rem;
    }

    /* ── AI RESPONSE ────────────────────────────────────────── */
    .ai-response {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 4px solid var(--blue-700);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        font-size: 0.875rem;
        color: var(--text-700);
        line-height: 1.7;
        margin-bottom: 0.75rem;
    }
    .ai-response .ai-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--blue-700);
        margin-bottom: 0.6rem;
    }

    /* ── EMPTY STATE ────────────────────────────────────────── */
    .empty-state {
        border: 2px dashed var(--border-md);
        border-radius: var(--radius-md);
        padding: 2.5rem 2rem;
        text-align: center;
        color: var(--text-500);
    }
    .empty-state .es-icon { font-size: 2rem; margin-bottom: 0.75rem; display: block; }
    .empty-state .es-title { font-size: 0.95rem; font-weight: 600; color: var(--text-700); margin-bottom: 0.3rem; }
    .empty-state .es-body  { font-size: 0.82rem; color: var(--text-500); }

    /* ── ABOUT PAGE ─────────────────────────────────────────── */
    .about-section {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.5rem 1.75rem;
        box-shadow: var(--shadow-sm);
        margin-bottom: 1rem;
    }
    .about-section h3 {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--green-900);
        margin: 0 0 0.6rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--border);
    }
    .about-section p, .about-section li {
        font-size: 0.875rem;
        color: var(--text-700);
        line-height: 1.65;
    }
    .about-section ul { padding-left: 1.1rem; margin: 0.3rem 0; }
    .tech-badge {
        display: inline-block;
        background: var(--green-50);
        color: var(--green-700);
        border: 1px solid var(--green-100);
        border-radius: 4px;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.15rem 0.15rem 0 0;
    }
    .rai-box {
        background: var(--amber-bg);
        border: 1px solid var(--amber-border);
        border-radius: var(--radius-sm);
        padding: 0.9rem 1.1rem;
        font-size: 0.84rem;
        color: #78350F;
        line-height: 1.6;
    }

    /* ── PROGRESS STEPS ─────────────────────────────────────── */
    .progress-step {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.5rem 0;
        font-size: 0.875rem;
        color: var(--text-700);
    }
    .progress-step .step-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--green-500);
        flex-shrink: 0;
    }

    /* ── TIMING FOOTER ──────────────────────────────────────── */
    .timing-footer {
        font-size: 0.72rem;
        color: var(--text-300);
        padding-top: 0.4rem;
        line-height: 1.8;
    }

    /* ── HIDE STREAMLIT CHROME ──────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer     { visibility: hidden; }
    header     { visibility: hidden; }
    [data-testid="stDecoration"] { display: none; }
    .stSpinner > div {
        border-top-color: var(--green-500) !important;
    }

    </style>
    """, unsafe_allow_html=True)
    