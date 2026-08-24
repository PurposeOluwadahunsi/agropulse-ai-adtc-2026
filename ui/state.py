"""
ui/state.py

Centralised session state for AgroPulse AI.

All st.session_state keys are defined and initialised here.
Import init_state() and call it once at the top of app.py.
Access state through the helper functions below.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


# ─────────────────────────────────────────────
# Keys
# ─────────────────────────────────────────────

SESSION_ID       = "session_id"
LAST_RESULT      = "last_result"       # dict | None
IS_ANALYZING     = "is_analyzing"      # bool
HISTORY          = "history"           # list[dict]
STATS            = "stats"             # dict | None
LOGBOOK          = "logbook"           # Logbook instance
STARTUP_DONE     = "startup_done"      # bool


def init_state() -> None:
    """
    Initialise all session state keys with default values.
    Safe to call on every Streamlit rerun — only sets keys
    that are not already present.
    """
    defaults: dict[str, Any] = {
        SESSION_ID:   None,
        LAST_RESULT:  None,
        IS_ANALYZING: False,
        HISTORY:      [],
        STATS:        None,
        LOGBOOK:      None,
        STARTUP_DONE: False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ─────────────────────────────────────────────
# Typed accessors
# ─────────────────────────────────────────────

def get_session_id() -> str | None:
    return st.session_state.get(SESSION_ID)

def set_session_id(sid: str) -> None:
    st.session_state[SESSION_ID] = sid

def get_last_result() -> dict[str, Any] | None:
    return st.session_state.get(LAST_RESULT)

def set_last_result(result: dict[str, Any]) -> None:
    st.session_state[LAST_RESULT] = result

def get_history() -> list[dict[str, Any]]:
    return st.session_state.get(HISTORY, [])

def set_history(entries: list[dict[str, Any]]) -> None:
    st.session_state[HISTORY] = entries

def get_stats() -> dict[str, Any] | None:
    return st.session_state.get(STATS)

def set_stats(stats: dict[str, Any]) -> None:
    st.session_state[STATS] = stats

def get_logbook():
    return st.session_state.get(LOGBOOK)

def set_logbook(lb) -> None:
    st.session_state[LOGBOOK] = lb

def is_startup_done() -> bool:
    return st.session_state.get(STARTUP_DONE, False)

def mark_startup_done() -> None:
    st.session_state[STARTUP_DONE] = True