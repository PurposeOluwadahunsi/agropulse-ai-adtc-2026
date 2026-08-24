"""
ui/risk.py  (Sprint 7 — new)

Farm Risk Intelligence.

Computes a transparent Farm Risk Score from existing pipeline outputs.
No new AI — only summarises what the triage engine and LLM already produced.

Score formula (max 100):
    Severity          critical=40  moderate=20  low=10
    Confidence        high=20      medium=12     low=5
    Matched symptoms  min(symptoms * 5, 15)
    Vet referral      +15 if required
    Contagious flag   +10 if disease is known contagious (from severity critical)
"""

from __future__ import annotations
from typing import Any
import streamlit as st


# ── Score calculation ─────────────────────────────────────────────

def compute_risk_score(result: dict[str, Any]) -> dict[str, Any]:
    """
    Compute a Farm Risk Score from an existing pipeline result dict.

    Args:
        result: The result dict produced by the analysis pipeline.

    Returns:
        Dict with keys:
            score         int (0-100)
            level         str ('LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL')
            level_css     str (CSS class name)
            reasons       list[str]
            impact        dict[str, str]
    """
    score   = 0
    reasons = []

    severity   = (result.get("severity") or "").lower()
    confidence = (result.get("confidence") or "none").lower()
    symptoms   = result.get("matched_symptoms") or []
    vet        = result.get("vet_referral", False)
    disease    = result.get("disease_name") or ""
    matched    = result.get("triage_matched", False)

    if not matched:
        return {
            "score":     0,
            "level":     "UNDETERMINED",
            "level_css": "sev-unknown",
            "reasons":   ["No disease pattern matched. Provide more specific symptoms for a risk assessment."],
            "impact":    _impact_table("none", False, 0),
        }

    # Severity component (max 40)
    sev_scores = {"critical": 40, "moderate": 20, "low": 10}
    sev_val    = sev_scores.get(severity, 0)
    score     += sev_val
    if severity == "critical":
        reasons.append(f"{disease} is classified as a critical severity condition")
    elif severity == "moderate":
        reasons.append(f"{disease} is classified as a moderate severity condition")

    # Confidence component (max 20)
    conf_scores = {"high": 20, "medium": 12, "low": 5}
    conf_val    = conf_scores.get(confidence, 0)
    score      += conf_val
    if conf_val >= 12:
        reasons.append(f"Multiple symptom matches confirmed with {confidence} confidence")
    elif conf_val > 0:
        reasons.append(f"Partial symptom match with {confidence} confidence")

    # Symptom count component (max 15)
    sym_val = min(len(symptoms) * 5, 15)
    score  += sym_val
    if len(symptoms) >= 3:
        reasons.append(f"{len(symptoms)} specific symptoms matched to this condition")
    elif len(symptoms) > 0:
        reasons.append(f"{len(symptoms)} symptom(s) matched")

    # Vet referral component (+15)
    if vet:
        score  += 15
        reasons.append("Veterinary intervention is recommended for this condition")

    # Contagious bonus for critical diseases (+10)
    # Critical diseases in vetdb are all contagious
    if severity == "critical":
        score  += 10
        reasons.append(f"{disease} is highly contagious — flock-wide spread is possible")

    score = min(score, 100)

    # Risk level
    if score >= 75:
        level     = "CRITICAL RISK"
        level_css = "sev-critical"
    elif score >= 50:
        level     = "HIGH RISK"
        level_css = "sev-critical"
    elif score >= 25:
        level     = "MODERATE RISK"
        level_css = "sev-moderate"
    else:
        level     = "LOW RISK"
        level_css = "sev-low"

    return {
        "score":     score,
        "level":     level,
        "level_css": level_css,
        "reasons":   reasons,
        "impact":    _impact_table(severity, vet, len(symptoms)),
    }


def _impact_table(
    severity: str,
    vet_required: bool,
    symptom_count: int,
) -> dict[str, str]:
    """
    Generate Farm Impact indicators from existing data.
    Labels only — no invented predictions.
    """
    sev = severity.lower()

    spread = {
        "critical": "Critical",
        "moderate": "High",
        "low":      "Moderate",
    }.get(sev, "Low")

    production = {
        "critical": "Severe",
        "moderate": "Moderate",
        "low":      "Low",
    }.get(sev, "Minimal")

    mortality = {
        "critical": "High",
        "moderate": "Moderate",
        "low":      "Low",
    }.get(sev, "Low")

    biosecurity = "Immediate" if sev == "critical" else ("Recommended" if sev == "moderate" else "Standard")
    vet_urgency = "Urgent" if vet_required else ("Advisable" if sev in ("critical", "moderate") else "Optional")

    return {
        "Disease Spread Risk":   spread,
        "Production Impact":     production,
        "Mortality Risk":        mortality,
        "Biosecurity Priority":  biosecurity,
        "Veterinary Urgency":    vet_urgency,
    }


# ── Display ───────────────────────────────────────────────────────

_IMPACT_COLOURS = {
    "Critical":    ("var(--red-bg)",    "var(--red-700)"),
    "Severe":      ("var(--red-bg)",    "var(--red-700)"),
    "Urgent":      ("var(--red-bg)",    "var(--red-700)"),
    "High":        ("var(--amber-bg)",  "var(--amber)"),
    "Immediate":   ("var(--red-bg)",    "var(--red-700)"),
    "Moderate":    ("var(--amber-bg)",  "var(--amber)"),
    "Recommended": ("var(--amber-bg)",  "var(--amber)"),
    "Advisable":   ("var(--amber-bg)",  "var(--amber)"),
    "Low":         ("var(--green-50)",  "var(--green-700)"),
    "Minimal":     ("var(--green-50)",  "var(--green-700)"),
    "Standard":    ("var(--green-50)",  "var(--green-700)"),
    "Optional":    ("var(--green-50)",  "var(--green-700)"),
}


def render_risk_panel(result: dict[str, Any]) -> None:
    """
    Render the Farm Risk Assessment and Estimated Farm Impact panels.

    Args:
        result: Pipeline result dict from app.py.
    """
    risk = compute_risk_score(result)

    # ── Risk Score Card ───────────────────────────────────────────
    score_colour = {
        "CRITICAL RISK": "var(--red-700)",
        "HIGH RISK":     "var(--red-500)",
        "MODERATE RISK": "var(--amber)",
        "LOW RISK":      "var(--green-700)",
        "UNDETERMINED":  "var(--text-500)",
    }.get(risk["level"], "var(--text-500)")

    reasons_html = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:0.5rem;'
        f'padding:0.3rem 0;font-size:0.82rem;color:var(--text-700);">'
        f'<span style="color:{score_colour};margin-top:0.15rem;">&#8226;</span>'
        f'<span>{r}</span></div>'
        for r in risk["reasons"]
    )

    st.markdown(
        f'<div class="assessment-card {("critical" if risk["score"] >= 50 else "moderate" if risk["score"] >= 25 else "low")}">'
        f'<div class="ac-label">Farm Risk Assessment</div>'
        f'<div style="display:flex;align-items:baseline;gap:0.75rem;margin:0.4rem 0;">'
        f'<div style="font-size:2rem;font-weight:800;color:{score_colour};line-height:1;">'
        f'{risk["score"]}<span style="font-size:1rem;font-weight:400;color:var(--text-500);">/100</span>'
        f'</div>'
        f'<span class="sev-badge {"sev-critical" if risk["score"] >= 50 else "sev-moderate" if risk["score"] >= 25 else "sev-low"}">'
        f'{risk["level"]}</span>'
        f'</div>'
        f'<div style="margin-top:0.5rem;">{reasons_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Farm Impact Table ─────────────────────────────────────────
    impact      = risk["impact"]
    impact_rows = ""
    for label, value in impact.items():
        bg, fg = _IMPACT_COLOURS.get(value, ("var(--bg)", "var(--text-700)"))
        impact_rows += (
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;padding:0.45rem 0;'
            f'border-bottom:1px solid var(--border);font-size:0.84rem;">'
            f'<span style="color:var(--text-700);">{label}</span>'
            f'<span style="background:{bg};color:{fg};padding:0.15rem 0.55rem;'
            f'border-radius:4px;font-size:0.72rem;font-weight:700;">{value}</span>'
            f'</div>'
        )

    st.markdown(
        f'<div class="assessment-card info" style="margin-top:0.75rem;">'
        f'<div class="ac-label">Estimated Farm Impact</div>'
        f'<div style="margin-top:0.4rem;">{impact_rows}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )