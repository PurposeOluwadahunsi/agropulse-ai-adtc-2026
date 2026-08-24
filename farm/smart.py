"""farm/smart.py — Smart Farm Operations UI panels."""
from __future__ import annotations
import streamlit as st
from typing import Any
from ui.components import section_header, render_stat
import farm.db as db
from farm.performance import compute_performance
from farm.recommendations import (
    get_recommendations, feed_planner,
    mortality_intelligence, egg_intelligence,
)


def _card(label: str, value: str, desc: str, rec: str, cls: str = "low") -> None:
    rec_html = (
        f'<div style="margin-top:0.4rem;font-size:0.78rem;color:var(--green-700);font-weight:600;">→ {rec}</div>'
        if rec else ""
    )
    st.markdown(
        f'<div class="assessment-card {cls}">'
        f'<div class="ac-label">{label}</div>'
        f'<div class="ac-value" style="font-size:1rem;">{value}</div>'
        f'<div class="ac-body" style="font-size:0.8rem;">{desc}</div>'
        f'{rec_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_daily_summary(history: list[dict]) -> None:
    from farm.performance import compute_performance
    from core.biosecurity import compute_biosecurity_score
    from ui.analytics import _average_risk

    section_header("Today's Farm Summary")
    perf    = compute_performance(history)
    bio     = compute_biosecurity_score(history)
    avg_r   = _average_risk(history)
    total_b = db.ls_total_birds()
    today_m = db.mort_today()
    today_e = db.egg_today()
    low_f   = db.feed_low_stock()
    overdue = len(db.vacc_overdue())

    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
    c1.metric("Live Birds", f"{total_b:,}")
    c2.metric("Mortality Today", str(today_m))
    c3.metric("Eggs Today", str(today_e))
    c4.metric("Feed Alerts", f"{len(low_f)} low")
    c5.metric("Vacc Due", str(overdue))
    c6.metric("Performance", f"{perf.score}/100")
    c7.metric("Biosecurity", f"{bio.score}/100")
    c8.metric("Farm Risk", f"{avg_r}/100")


def render_performance_panel(history: list[dict]) -> None:
    section_header("Farm Performance Score")
    perf = compute_performance(history)

    colour = {
        "Excellent": "var(--green-700)",
        "Good": "var(--green-500)",
        "Fair": "var(--amber)",
        "Needs Attention": "var(--red-700)",
    }.get(perf.status, "var(--text-900)")
    cls = "low" if perf.score >= 70 else "moderate" if perf.score >= 50 else "critical"

    reasons_html = "".join(
        f'<div style="padding:0.2rem 0;font-size:0.82rem;color:var(--text-700);">&#8226; {r}</div>'
        for r in perf.reasons
    )
    recs_html = "".join(
        f'<div style="padding:0.2rem 0;font-size:0.82rem;color:var(--green-700);">&#10003; {r}</div>'
        for r in perf.recommendations
    )

    st.markdown(
        f'<div class="assessment-card {cls}">'
        f'<div class="ac-label">Overall Farm Performance</div>'
        f'<div style="display:flex;align-items:baseline;gap:0.75rem;margin:0.3rem 0;">'
        f'<div style="font-size:2rem;font-weight:800;color:{colour};line-height:1;">'
        f'{perf.score}<span style="font-size:1rem;font-weight:400;color:var(--text-500);">/100</span></div>'
        f'<span class="sev-badge {perf.status_css}">{perf.status}</span></div>'
        f'<div style="margin-top:0.5rem;">{reasons_html}</div>'
        f'<div style="margin-top:0.5rem;">{recs_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_smart_operations(history: list[dict]) -> None:
    section_header("Smart Farm Operations")

    # Feed status
    low_feed = db.feed_low_stock()
    all_feed = db.feed_all()
    if not all_feed:
        feed_val, feed_desc, feed_cls = "No Data", "No feed records found.", "info"
        feed_rec = "Add feed inventory records."
    elif low_feed:
        feed_val = f"{len(low_feed)} Low"
        feed_desc = f"{', '.join(f['name'] for f in low_feed)} running low."
        feed_cls = "critical"
        feed_rec = "Restock within 48 hours."
    else:
        feed_val, feed_desc, feed_cls = "Good", "All feed stocks adequate.", "low"
        feed_rec = "No immediate action required."

    # Vaccination
    overdue = db.vacc_overdue()
    upcoming = db.vacc_upcoming()
    if overdue:
        vacc_val = f"{len(overdue)} Overdue"
        vacc_desc = f"{', '.join(v['vaccine'] for v in overdue)} overdue."
        vacc_cls = "critical"
        vacc_rec = "Complete vaccinations immediately."
    elif upcoming:
        vacc_val = f"{len(upcoming)} Due Soon"
        vacc_desc = f"{len(upcoming)} vaccination(s) due in 14 days."
        vacc_cls = "moderate"
        vacc_rec = "Schedule vaccinations."
    else:
        vacc_val, vacc_desc, vacc_cls = "Up to Date", "No vaccinations due.", "low"
        vacc_rec = "Maintain schedule."

    # Mortality
    today_m = db.mort_today()
    rate = db.mort_rate()
    if today_m >= 10 or rate >= 5:
        mort_val = "High"
        mort_desc = f"{today_m} today, {rate}% monthly rate."
        mort_cls = "critical"
        mort_rec = "Run AI consultation immediately."
    elif today_m > 0:
        mort_val, mort_desc, mort_cls = "Moderate", f"{today_m} deaths today.", "moderate"
        mort_rec = "Monitor closely."
    else:
        mort_val, mort_desc, mort_cls = "Normal", "No deaths recorded today.", "low"
        mort_rec = "Continue monitoring."

    # Egg production
    ei = egg_intelligence()
    egg_val = ei["trend"]
    egg_desc = f"Today: {ei['today']} | 7-day avg: {ei['week_avg']}"
    egg_cls = "low" if ei["week_diff"] >= 0 else "moderate"
    egg_rec = ei["recommendation"]

    # Biosecurity
    from core.biosecurity import compute_biosecurity_score
    bio = compute_biosecurity_score(history)
    bio_cls = "low" if bio.score >= 80 else "moderate" if bio.score >= 60 else "critical"

    c1, c2, c3 = st.columns(3)
    with c1:
        _card("Feed Status", feed_val, feed_desc, feed_rec, feed_cls)
        _card("Vaccination Status", vacc_val, vacc_desc, vacc_rec, vacc_cls)
    with c2:
        _card("Mortality Status", mort_val, mort_desc, mort_rec, mort_cls)
        _card("Egg Production", egg_val, egg_desc, egg_rec, egg_cls)
    with c3:
        _card(
            "Biosecurity",
            f"{bio.score}/100",
            bio.status,
            bio.recommendations[0] if bio.recommendations else "",
            bio_cls,
        )


def render_feed_planner() -> None:
    section_header("Smart Feed Planner")
    plan = feed_planner()
    if not plan["items"]:
        st.markdown(
            '<div class="empty-state"><div class="es-title">No Feed Data</div>'
            '<div class="es-body">Add feed records with daily usage to enable the Smart Feed Planner.</div></div>',
            unsafe_allow_html=True,
        )
        return
    for item in plan["items"]:
        cls = "critical" if item["days_remaining"] <= 3 else "moderate" if item["days_remaining"] <= 7 else "low"
        st.markdown(
            f'<div class="assessment-card {cls}">'
            f'<div class="ac-label">{item["name"]} — {item["feed_type"]}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:0.5rem;">'
            f'<div><div style="font-size:0.68rem;color:var(--text-500);text-transform:uppercase;">Remaining</div>'
            f'<div style="font-weight:700;font-size:1rem;color:var(--text-900);">{item["days_remaining"]} days</div></div>'
            f'<div><div style="font-size:0.68rem;color:var(--text-500);text-transform:uppercase;">Depletes</div>'
            f'<div style="font-weight:700;font-size:1rem;color:var(--text-900);">{item["depletion_date"]}</div></div>'
            f'<div><div style="font-size:0.68rem;color:var(--text-500);text-transform:uppercase;">Reorder By</div>'
            f'<div style="font-weight:700;font-size:1rem;color:var(--text-900);">{item["reorder_date"]}</div></div>'
            f'<div><div style="font-size:0.68rem;color:var(--text-500);text-transform:uppercase;">Suggested Buy</div>'
            f'<div style="font-weight:700;font-size:1rem;color:var(--text-900);">{item["suggested_kg"]} kg</div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


def render_mortality_intelligence() -> None:
    section_header("Mortality Intelligence")
    mi = mortality_intelligence()
    cls = "critical" if mi["trend"] == "Increasing" else "low" if mi["trend"] == "Decreasing" else "info"
    st.markdown(
        f'<div class="assessment-card {cls}">'
        f'<div class="ac-label">Mortality Trend</div>'
        f'<div class="ac-value">{mi["trend"]}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-top:0.5rem;">'
        f'<div><div style="font-size:0.68rem;color:var(--text-500);">Today</div>'
        f'<div style="font-weight:700;color:var(--text-900);">{mi["today"]}</div></div>'
        f'<div><div style="font-size:0.68rem;color:var(--text-500);">This Week</div>'
        f'<div style="font-weight:700;color:var(--text-900);">{mi["week"]}</div></div>'
        f'<div><div style="font-size:0.68rem;color:var(--text-500);">Next Week Est.</div>'
        f'<div style="font-weight:700;color:var(--text-900);">{mi["forecast"]}</div></div>'
        f'</div>'
        f'<div style="margin-top:0.5rem;font-size:0.82rem;color:var(--green-700);font-weight:600;">→ {mi["recommendation"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_smart_recommendations(history: list[dict]) -> None:
    section_header("Smart Recommendations")
    recs = get_recommendations(history)
    if not recs:
        st.markdown(
            '<div class="assessment-card low"><div class="ac-body" style="color:var(--green-700);font-weight:600;">'
            'No active recommendations. Farm operations appear normal.</div></div>',
            unsafe_allow_html=True,
        )
        return
    for r in recs:
        cls = r.priority
        st.markdown(
            f'<div class="assessment-card {cls}">'
            f'<div class="ac-label">{r.title}</div>'
            f'<div class="ac-body">{r.body}</div>'
            f'<div style="margin-top:0.4rem;font-size:0.82rem;font-weight:600;color:var(--green-700);">→ {r.action}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_daily_assistant_summary(history: list[dict]) -> None:
    """Sprint 12 — Plain-language daily summary card."""
    from farm.insights import get_daily_summary
    section_header("Today's Farm Summary")
    summary = get_daily_summary(history)
    cls = {"stable": "low", "attention": "moderate", "critical": "critical"}.get(summary.overall_status, "info")
    items = "".join(
        f'<div style="padding:0.25rem 0;font-size:0.85rem;color:var(--text-700);">&#8226; {line}</div>'
        for line in summary.lines
    )
    st.markdown(
        f'<div class="assessment-card {cls}">'
        f'<div class="ac-label">Daily Assistant Summary</div>'
        f'<div style="margin-top:0.4rem;">{items}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_ai_insight_panel(history: list[dict]) -> None:
    """Sprint 12 — Concise AI insight paragraph."""
    from farm.insights import get_ai_insight
    section_header("AI Insight")
    insight = get_ai_insight(history)
    st.markdown(
        f'<div class="assessment-card info" style="border-left-color:var(--blue-700);">'
        f'<div class="ac-label" style="color:var(--blue-700);">What AgroPulse Has Learned</div>'
        f'<div class="ac-body" style="font-style:italic;color:var(--text-700);">{insight}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_whats_changed(history: list[dict]) -> None:
    """Sprint 12 — Changes since last visit, using session state snapshot."""
    from farm.insights import get_whats_changed, build_snapshot
    section_header("What Changed Since Last Visit")
    prev = st.session_state.get("farm_snapshot")
    changes = get_whats_changed(history, prev)
    items = "".join(
        f'<div style="padding:0.25rem 0;font-size:0.84rem;color:var(--text-700);">&#8226; {c}</div>'
        for c in changes
    )
    st.markdown(f'<div class="assessment-card info">{items}</div>', unsafe_allow_html=True)
    st.session_state["farm_snapshot"] = build_snapshot(history)


def render_vaccination_calendar() -> None:
    section_header("Vaccination Calendar")
    all_v = db.vacc_all()
    overdue = [v for v in all_v if v["status"] == "missed"]
    pending = [v for v in all_v if v["status"] == "pending"]
    done = [v for v in all_v if v["status"] == "completed"]

    t1, t2, t3 = st.tabs([f"Overdue ({len(overdue)})", f"Upcoming ({len(pending)})", f"Completed ({len(done)})"])

    def _vacc_table(items: list, empty_msg: str) -> None:
        if not items:
            st.markdown(
                f'<div style="padding:1rem;color:var(--text-500);font-size:0.84rem;">{empty_msg}</div>',
                unsafe_allow_html=True,
            )
            return
        for v in items:
            cls = {"missed": "critical", "pending": "moderate", "completed": "low"}.get(v["status"], "info")
            st.markdown(
                f'<div class="assessment-card {cls}" style="margin-bottom:0.4rem;">'
                f'<div style="display:flex;justify-content:space-between;">'
                f'<div><div class="ac-value" style="font-size:0.95rem;">{v["vaccine"]}</div>'
                f'<div style="font-size:0.78rem;color:var(--text-500);">'
                f'{v["bird_group"] or "All birds"} | Scheduled: {v["scheduled_date"]}</div></div>'
                f'<span class="sev-badge sev-{cls}">{v["status"].upper()}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    with t1:
        _vacc_table(overdue, "No overdue vaccinations.")
    with t2:
        _vacc_table(pending, "No upcoming vaccinations.")
    with t3:
        _vacc_table(done, "No completed vaccinations yet.")