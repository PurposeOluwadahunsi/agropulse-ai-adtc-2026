"""core/biosecurity.py — Biosecurity score from consultation history."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

@dataclass
class BiosecurityReport:
    score: int
    status: str
    status_css: str
    reasons: list[str]
    recommendations: list[str]

def compute_biosecurity_score(entries: list[dict[str, Any]]) -> BiosecurityReport:
    if not entries:
        return BiosecurityReport(score=100, status="No Data", status_css="sev-unknown", reasons=["No consultation history available."], recommendations=["Run your first consultation to begin tracking biosecurity."])

    total        = len(entries)
    critical     = sum(1 for e in entries if e.get("severity") == "critical")
    vet_refs     = sum(1 for e in entries if e.get("vet_needed"))
    no_match     = sum(1 for e in entries if not e.get("disease_hit"))
    cutoff       = datetime.now() - timedelta(days=30)
    recent_crit  = sum(1 for e in entries if e.get("severity") == "critical" and e.get("timestamp") and _parse_ts(e["timestamp"]) >= cutoff)

    diseases = [e["disease_hit"] for e in entries if e.get("disease_hit")]
    repeats  = sum(1 for d in set(diseases) if diseases.count(d) >= 2)

    # Score starts at 100, deductions applied
    score = 100
    reasons = []
    recs    = []

    if critical > 0:
        ded = min(30, critical * 8)
        score -= ded
        reasons.append(f"{critical} critical severity consultation(s) recorded")
        recs.append("Review vaccination schedule with a veterinarian")

    if vet_refs > 0:
        ded = min(20, vet_refs * 5)
        score -= ded
        reasons.append(f"{vet_refs} veterinary referral(s) issued")
        recs.append("Ensure all recommended veterinary visits were completed")

    if repeats > 0:
        ded = min(20, repeats * 7)
        score -= ded
        reasons.append(f"Repeated diseases detected ({repeats} condition(s) seen more than once)")
        recs.append("Identify and eliminate disease entry points on the farm")

    if recent_crit > 0:
        ded = min(15, recent_crit * 5)
        score -= ded
        reasons.append(f"{recent_crit} critical case(s) in the last 30 days")
        recs.append("Increase disinfection frequency and review litter management")

    score = max(0, score)
    recs += ["Separate newly introduced birds for 2 weeks before mixing", "Maintain clean water and feed storage at all times"]

    if score >= 80:   status, css = "Good",             "sev-low"
    elif score >= 60: status, css = "Needs Improvement", "sev-moderate"
    elif score >= 40: status, css = "At Risk",           "sev-critical"
    else:             status, css = "Critical Risk",     "sev-critical"

    if not reasons:
        reasons = ["No critical events detected in consultation history"]

    return BiosecurityReport(score=score, status=status, status_css=css, reasons=reasons, recommendations=recs)

def _parse_ts(ts: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try: return datetime.strptime(ts, fmt)
        except: pass
    return datetime.min