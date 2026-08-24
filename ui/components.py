"""
ui/components.py  (Sprint 6 — redesigned)

All reusable HTML components for AgroPulse AI.
Every component uses design tokens from styles.py.
app.py calls these — no raw HTML elsewhere.
"""

from __future__ import annotations
from typing import Any
import streamlit as st


# ── Hero ──────────────────────────────────────────────────────────

def render_hero() -> None:
    st.markdown("""
    <div class="ap-hero">
        <div class="ap-hero-left">
            <p class="tagline">Offline Poultry Intelligence System</p>
            <h1>AgroPulse AI</h1>
            <p class="description">
                AI-powered poultry disease decision support for African farmers.
                Runs fully offline using trusted veterinary knowledge from FAO, OIE, and NVRI.
            </p>
        </div>
        <div class="ap-hero-badges">
            <span class="badge-pill">Offline AI</span>
            <span class="badge-pill">Local LLM</span>
            <span class="badge-pill blue">RAG Enabled</span>
            <span class="badge-pill blue">Evidence-Based</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str) -> None:
    st.markdown(
        f'<div class="section-header">{title}</div>',
        unsafe_allow_html=True,
    )


# ── Dashboard Cards ───────────────────────────────────────────────

def dash_card(
    icon: str,
    label: str,
    value: str,
    desc: str = "",
    value_class: str = "",
) -> None:
    desc_html = f'<div class="card-desc">{desc}</div>' if desc else ""
    st.markdown(f"""
    <div class="dash-card">
        <span class="card-icon">{icon}</span>
        <div class="card-label">{label}</div>
        <div class="card-value {value_class}">{value}</div>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)


# ── Severity ──────────────────────────────────────────────────────

def sev_badge(severity: str) -> str:
    s   = (severity or "unknown").lower()
    cls = {"critical": "sev-critical", "moderate": "sev-moderate",
           "low": "sev-low"}.get(s, "sev-unknown")
    return f'<span class="sev-badge {cls}">{s.upper()}</span>'


# ── Confidence Bar ────────────────────────────────────────────────

def render_confidence(confidence: str, score: float, max_score: float = 15.0) -> None:
    pct     = min(100, int((score / max_score) * 100))
    label   = confidence.capitalize() if confidence != "none" else "Not assessed"
    fill_cls = {"high": "high", "medium": "moderate", "low": "low"}.get(confidence, "low")
    st.markdown(f"""
    <div class="conf-container">
        <div class="conf-row">
            <span class="conf-label">{label} confidence</span>
            <span class="conf-pct">{pct}%</span>
        </div>
        <div class="conf-track">
            <div class="conf-fill {fill_cls}" style="width:{pct}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Assessment Cards ──────────────────────────────────────────────

def assessment_card(
    label: str,
    value: str = "",
    body: str = "",
    card_class: str = "info",
) -> None:
    value_html = f'<div class="ac-value">{value}</div>' if value else ""
    body_html  = f'<div class="ac-body">{body}</div>'   if body  else ""
    st.markdown(f"""
    <div class="assessment-card {card_class}">
        <div class="ac-label">{label}</div>
        {value_html}{body_html}
    </div>
    """, unsafe_allow_html=True)


# ── Symptom Tags ──────────────────────────────────────────────────

def render_symptoms(symptoms: list[str]) -> None:
    if not symptoms:
        st.markdown("""
        <div class="assessment-card info">
            <div class="ac-label">Matched Symptoms</div>
            <div class="ac-body" style="color:var(--text-500);font-style:italic;">
                No specific symptoms matched. Provide more detail for better results.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    tags = "".join(
        f'<span class="symptom-tag">&#10003; {s}</span>' for s in symptoms
    )
    st.markdown(f"""
    <div class="assessment-card info">
        <div class="ac-label">Matched Symptoms</div>
        <div style="margin-top:0.4rem;line-height:2;">{tags}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Emergency Alert ───────────────────────────────────────────────

def render_emergency_alert(disease_name: str) -> None:
    st.markdown(f"""
    <div class="emergency-alert">
        <div class="ea-title">Critical Condition Identified</div>
        <div class="ea-body">
            <strong>{disease_name}</strong> is classified as a critical condition.<br>
            Immediate action is required to prevent flock loss and disease spread.<br><br>
            1. Isolate all affected birds from the healthy flock now.<br>
            2. Restrict all movement in and out of the farm.<br>
            3. Do not handle dead birds without protective equipment.<br>
            4. Contact a licensed veterinarian immediately.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Vet Alert ─────────────────────────────────────────────────────

def render_vet_alert(when_to_call: str = "") -> None:
    detail = f"<br><br>{when_to_call}" if when_to_call else ""
    st.markdown(f"""
    <div class="vet-alert">
        <strong>Veterinary Referral Required</strong><br>
        This condition warrants professional veterinary assessment.
        Do not administer treatment without veterinary confirmation.{detail}
    </div>
    """, unsafe_allow_html=True)


# ── Action Plan ───────────────────────────────────────────────────

def render_action_plan(actions: list[str]) -> None:
    if not actions:
        return
    items = "".join(
        f'<div class="action-item">'
        f'<span class="action-num">{i+1}</span>'
        f'<span>{a}</span></div>'
        for i, a in enumerate(actions)
    )
    st.markdown(f"""
    <div class="action-plan">
        <div class="ac-label" style="margin-bottom:0.6rem;">Today\'s Recommended Actions</div>
        {items}
    </div>
    """, unsafe_allow_html=True)


# ── Evidence Panel ────────────────────────────────────────────────

def render_evidence_sources(sources: list[str]) -> None:
    if not sources:
        return

    source_meta = {
        "FAO":   ("FAO Animal Health Manual",    "UN Food & Agriculture Org",    100),
        "OIE":   ("OIE Terrestrial Manual",      "World Organisation for AH",    97),
        "NVRI":  ("NVRI Nigeria Guidelines",     "Nat. Vet. Research Institute",  95),
        "Merck": ("Merck Veterinary Manual",     "Merck & Co. (11th Ed.)",       93),
    }

    cards = ""
    seen  = set()
    for src in sources:
        for key, (title, authority, conf) in source_meta.items():
            if key in src and key not in seen:
                seen.add(key)
                cards += f'<div class="source-card"><span class="src-icon">📄</span><div><div class="src-title">{title}</div><div class="src-meta">{authority}</div></div><div class="src-conf">{conf}% authority</div></div>'
        if not any(k in src for k in source_meta) and src not in seen:
            seen.add(src)
            short = src.split(",")[0].strip()[:45]
            cards += f'<div class="source-card"><span class="src-icon">📄</span><div><div class="src-title">{short}</div><div class="src-meta">Veterinary Reference</div></div><div class="src-conf">Verified</div></div>'

    if cards:
        st.markdown(
            f'<div class="evidence-card"><div class="ev-label">Retrieved Knowledge Sources</div>{cards}</div>',
            unsafe_allow_html=True,
        )

def render_reasoning(explanation: str) -> None:
    if not explanation:
        return
    st.markdown(f"""
    <div class="evidence-card">
        <div class="ev-label">Reasoning</div>
        <div class="reasoning-box">{explanation}</div>
    </div>
    """, unsafe_allow_html=True)


def render_history_table(entries: list[dict[str, Any]]) -> None:
    if not entries:
        st.markdown(
            '<div style="padding:1rem;color:var(--text-500);font-size:0.82rem;text-align:center;">No consultations recorded yet.</div>',
            unsafe_allow_html=True,
        )
        return

    header = '<div class="hist-wrap"><div class="hist-row"><span>Date &amp; Time</span><span>Disease</span><span>Severity</span><span>Confidence</span><span>Time</span></div>'
    
    body = ""
    for e in entries:
        disease  = e.get("disease_hit") or "No match"
        severity = (e.get("severity") or "").lower()
        conf     = e.get("triage_conf") or "—"
        ts       = e.get("timestamp") or "—"
        ms       = e.get("response_ms")
        time_s   = f"{ms/1000:.0f}s" if ms else "—"
        
        css = {"critical": "sev-critical", "moderate": "sev-moderate", "low": "sev-low"}.get(severity, "sev-unknown")
        badge = f'<span class="sev-badge {css}">{severity.upper()}</span>' if severity else "—"
        
        body += f'<div class="hist-row"><span>{ts}</span><span>{disease}</span><span>{badge}</span><span>{conf}</span><span>{time_s}</span></div>'

    st.markdown(header + body + "</div>", unsafe_allow_html=True)
# ── Stats ─────────────────────────────────────────────────────────

def render_stat(value: str, label: str) -> None:
    st.markdown(f"""
    <div class="stat-block">
        <div class="stat-val">{value}</div>
        <div class="stat-lbl">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Empty Assessment ──────────────────────────────────────────────

def render_empty_assessment() -> None:
    st.markdown("""
    <div class="empty-state">
        <span class="es-icon">🔬</span>
        <div class="es-title">No Assessment Yet</div>
        <div class="es-body">
            Describe your observations in the consultation panel<br>
            and click <strong>Analyze Case</strong> to begin.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── AI Response ───────────────────────────────────────────────────

def render_ai_response(text: str) -> None:
    if not text:
        return
    formatted = text.replace("\n", "<br>")
    st.markdown(f"""
    <div class="ai-response">
        <div class="ai-label">AI Detailed Advisory</div>
        {formatted}
    </div>
    """, unsafe_allow_html=True)


# ── Timing Footer ─────────────────────────────────────────────────

def render_timing(triage_ms: int, rag_ms: int, llm_ms: int,
                  total_ms: int, log_id: int) -> None:
    st.markdown(
        f'<div class="timing-footer">'
        f'Triage: {triage_ms}ms &nbsp;|&nbsp; '
        f'RAG: {rag_ms}ms &nbsp;|&nbsp; '
        f'LLM: {llm_ms/1000:.1f}s &nbsp;|&nbsp; '
        f'Total: {total_ms/1000:.1f}s &nbsp;|&nbsp; '
        f'Log ID: {log_id}'
        f'</div>',
        unsafe_allow_html=True,
    )