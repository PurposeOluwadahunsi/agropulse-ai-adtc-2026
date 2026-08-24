from __future__ import annotations
from typing import Any
import streamlit as st
from core.outbreak   import detect_outbreaks, get_weekly_case_count
from core.biosecurity import compute_biosecurity_score
from ui.risk import compute_risk_score

def render_outbreak_panel(entries: list[dict[str, Any]]) -> None:
    from ui.components import section_header
    section_header("Outbreak Intelligence")
    report = detect_outbreaks(entries)

    if not report.alerts:
        st.markdown('<div class="assessment-card low"><div class="ac-label">Outbreak Status</div><div class="ac-body" style="color:var(--green-700);font-weight:600;">No disease clusters detected in the last 7 days.</div></div>', unsafe_allow_html=True)
        return

    for alert in report.alerts:
        cls  = "critical" if alert.alert_level == "critical" else "moderate"
        recs = "".join(f'<div style="padding:0.2rem 0;font-size:0.82rem;color:var(--text-700);">&#8226; {r}</div>' for r in alert.recommendations)
        st.markdown(
            f'<div class="assessment-card {cls}">'
            f'<div class="ac-label">Possible {alert.disease} Cluster</div>'
            f'<div class="ac-value" style="font-size:1rem;">{alert.case_count} similar consultations detected &nbsp;|&nbsp; {alert.similarity} similarity</div>'
            f'<div style="margin-top:0.5rem;font-size:0.78rem;color:var(--text-500);">Last seen: {alert.latest_timestamp} &nbsp;|&nbsp; Window: {report.window_days} days</div>'
            f'<div style="margin-top:0.6rem;"><div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-500);margin-bottom:0.3rem;">Recommendations</div>{recs}</div>'
            f'</div>', unsafe_allow_html=True)


def render_biosecurity_panel(entries: list[dict[str, Any]]) -> None:
    from ui.components import section_header
    section_header("Farm Biosecurity Assessment")
    rep = compute_biosecurity_score(entries)

    score_colour = {"Good": "var(--green-700)", "Needs Improvement": "var(--amber)", "At Risk": "var(--red-700)", "Critical Risk": "var(--red-700)"}.get(rep.status, "var(--text-900)")
    reasons_html = "".join(f'<div style="padding:0.2rem 0;font-size:0.82rem;color:var(--text-700);">&#8226; {r}</div>' for r in rep.reasons)
    recs_html    = "".join(f'<div style="padding:0.2rem 0;font-size:0.82rem;color:var(--text-700);">&#10003; {r}</div>' for r in rep.recommendations[:4])
    cls          = "critical" if rep.score < 60 else "moderate" if rep.score < 80 else "low"

    st.markdown(
        f'<div class="assessment-card {cls}">'
        f'<div class="ac-label">Biosecurity Score</div>'
        f'<div style="display:flex;align-items:baseline;gap:0.75rem;margin:0.3rem 0;">'
        f'<div style="font-size:2rem;font-weight:800;color:{score_colour};line-height:1;">{rep.score}<span style="font-size:1rem;font-weight:400;color:var(--text-500);">/100</span></div>'
        f'<span class="sev-badge {rep.status_css}">{rep.status}</span></div>'
        f'<div style="margin-top:0.5rem;"><div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-500);margin-bottom:0.3rem;">Reasons</div>{reasons_html}</div>'
        f'<div style="margin-top:0.5rem;"><div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--text-500);margin-bottom:0.3rem;">Recommendations</div>{recs_html}</div>'
        f'</div>', unsafe_allow_html=True)


def render_health_timeline(entries: list[dict[str, Any]]) -> None:
    from ui.components import section_header, sev_badge
    section_header("Farm Health Timeline")

    if not entries:
        st.markdown('<div class="empty-state"><div class="es-title">No timeline data</div><div class="es-body">Run your first consultation to begin the timeline.</div></div>', unsafe_allow_html=True)
        return

    shown = entries[:10]
    for i, e in enumerate(shown):
        disease  = e.get("disease_hit") or "No match"
        severity = e.get("severity") or ""
        ts       = e.get("timestamp", "—")
        ms       = e.get("response_ms")
        vet      = e.get("vet_needed", 0)
        badge    = sev_badge(severity) if severity else ""

        # Compute risk score proxy from entry
        risk_score = _entry_risk(e)
        connector  = "" if i == len(shown) - 1 else '<div style="width:2px;height:20px;background:var(--border);margin:0 0 0 11px;"></div>'

        st.markdown(
            f'<div style="display:flex;gap:0.75rem;align-items:flex-start;">'
            f'<div style="min-width:24px;display:flex;flex-direction:column;align-items:center;">'
            f'<div style="width:12px;height:12px;border-radius:50%;background:{"var(--red-500)" if severity=="critical" else "var(--amber)" if severity=="moderate" else "var(--green-500)"};margin-top:4px;flex-shrink:0;"></div>'
            f'{connector}</div>'
            f'<div class="assessment-card info" style="flex:1;margin-bottom:0.4rem;padding:0.7rem 0.9rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div style="font-size:0.78rem;font-weight:600;color:var(--text-900);">{disease}</div>'
            f'{badge}</div>'
            f'<div style="font-size:0.72rem;color:var(--text-500);margin-top:0.2rem;">{ts} &nbsp;|&nbsp; Risk: {risk_score}/100{"&nbsp;|&nbsp; Vet referral" if vet else ""}</div>'
            f'</div></div>',
            unsafe_allow_html=True)


def render_trend_analytics(entries: list[dict[str, Any]], stats: dict[str, Any]) -> None:
    from ui.components import section_header, render_stat
    section_header("Disease Trend Analytics")

    total      = stats.get("total_queries", 0)
    breakdown  = stats.get("disease_breakdown", {})
    top_dis    = max(breakdown, key=breakdown.get) if breakdown else "—"
    vet_refs   = stats.get("vet_referrals", 0)
    weekly     = get_weekly_case_count(entries)
    avg_risk   = _average_risk(entries)
    high_risk  = sum(1 for e in entries if e.get("severity") == "critical")

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_stat(str(weekly),   "Consultations This Week")
    with c2: render_stat(str(avg_risk), "Avg Farm Risk Score")
    with c3: render_stat(str(high_risk),"High Risk Consultations")
    with c4: render_stat(str(vet_refs), "Vet Referrals Total")

    if breakdown:
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        section_header("Disease Frequency")
        for disease, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            pct = int(count / total * 100) if total else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.45rem 0;border-bottom:1px solid var(--border);font-size:0.84rem;">'
                f'<span style="min-width:200px;color:var(--text-700);">{disease}</span>'
                f'<div style="flex:1;background:var(--border);border-radius:3px;height:6px;">'
                f'<div style="width:{pct}%;background:var(--green-500);height:100%;border-radius:3px;"></div></div>'
                f'<span style="min-width:35px;text-align:right;font-weight:600;color:var(--text-900);">{count}</span>'
                f'</div>', unsafe_allow_html=True)


def _entry_risk(e: dict) -> int:
    """Proxy risk score from a history entry."""
    sev = e.get("severity") or ""
    conf = e.get("triage_conf") or "none"
    vet  = e.get("vet_needed", 0)
    score = {"critical": 40, "moderate": 20, "low": 10}.get(sev, 0)
    score += {"high": 20, "medium": 12, "low": 5}.get(conf, 0)
    if vet: score += 15
    if sev == "critical": score += 10
    return min(score, 100)

def _average_risk(entries: list[dict]) -> int:
    if not entries: return 0
    scores = [_entry_risk(e) for e in entries]
    return int(sum(scores) / len(scores))