"""ui/navigation.py — Sidebar nav: styled real buttons in collapsible groups.
No hidden/invisible elements — every button is real, visible, and clickable.
"""
from __future__ import annotations
import streamlit as st
from ui.state import get_stats

MAIN_ITEMS = [
    ("⌂", "Dashboard", "home"),
    ("+", "AI Consultation", "consultation"),
    ("◎", "Voice Input", "voice"),
    ("▶", "Demo Mode", "demo"),
]
INTELLIGENCE_ITEMS = [
    ("★", "Smart Operations", "smart"),
    ("◈", "Analytics", "analytics"),
    ("≡", "History", "history"),
    ("∑", "Statistics", "statistics"),
]
OPERATIONS_ITEMS = [
    ("◐", "Livestock", "livestock"),
    ("▼", "Mortality", "mortality"),
    ("▣", "Feed Inventory", "feed"),
    ("✚", "Medication", "medication"),
    ("◑", "Vaccinations", "vaccination"),
    ("○", "Egg Production", "eggs"),
]
OTHER_ITEMS = [
    ("◉", "Knowledge Base", "knowledge"),
    ("?", "About", "about"),
]


def get_active_page() -> str:
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "home"
    return st.session_state["active_page"]


def set_active_page(page: str) -> None:
    st.session_state["active_page"] = page


def _apply_nav_css() -> None:
    st.markdown("""
    <style>
    /* Real, visible, clickable buttons styled as nav rows */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.78) !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 0.875rem !important;
        font-weight: 400 !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        width: 100% !important;
        margin: 1px 0 !important;
        transition: background 0.12s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.09) !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: none !important;
    }
    /* Active page button */
    [data-testid="stSidebar"] .nav-active .stButton > button {
        background: rgba(255,255,255,0.14) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-left: 3px solid #74B08A !important;
        border-radius: 0 6px 6px 0 !important;
    }
    /* Expander styled to match sidebar */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 6px !important;
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border: none !important;
        padding: 0.5rem 0.75rem !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background: rgba(255,255,255,0.09) !important;
    }
    [data-testid="stSidebar"] .streamlit-expanderContent {
        border: none !important;
        background: transparent !important;
        padding: 0.25rem 0 0 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def _nav_row(icon: str, label: str, page: str) -> None:
    active = get_active_page() == page
    wrapper_class = "nav-active" if active else "nav-inactive"
    st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
    if st.button(f"{icon}  {label}", key=f"nav_{page}", use_container_width=True):
        set_active_page(page)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        _apply_nav_css()

        st.markdown(
            '<div class="sidebar-logo"><h2>AgroPulse AI</h2>'
            '<p>Smart Farm Operations</p></div>',
            unsafe_allow_html=True,
        )

        active = get_active_page()

        # Main — always visible, no group wrapper
        for icon, label, page in MAIN_ITEMS:
            _nav_row(icon, label, page)

        # Farm Intelligence — collapsible
        with st.expander(
            "Farm Intelligence",
            expanded=active in [p for _, _, p in INTELLIGENCE_ITEMS],
        ):
            for icon, label, page in INTELLIGENCE_ITEMS:
                _nav_row(icon, label, page)

        # Farm Operations — collapsible
        with st.expander(
            "Farm Operations",
            expanded=active in [p for _, _, p in OPERATIONS_ITEMS],
        ):
            for icon, label, page in OPERATIONS_ITEMS:
                _nav_row(icon, label, page)

        # Other — always visible
        for icon, label, page in OTHER_ITEMS:
            _nav_row(icon, label, page)

        stats = get_stats() or {}
        total = stats.get("total_queries", 0)
        st.markdown(
            f'<div class="sidebar-status">'
            f'<div class="status-dot">Offline Mode Active</div>'
            f'<div class="status-dot">AI Model Ready</div>'
            f'<div class="status-dot">Database Online</div>'
            f'<div style="margin-top:0.5rem;font-size:0.72rem;color:rgba(255,255,255,0.35);">'
            f'{total} consultation{"s" if total != 1 else ""} recorded</div></div>',
            unsafe_allow_html=True,
        )