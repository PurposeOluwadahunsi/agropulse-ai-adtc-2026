"""core/outbreak.py — Outbreak pattern detection from consultation history."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

CLUSTER_WINDOW_DAYS = 7
CLUSTER_MIN_CASES   = 2

@dataclass
class OutbreakAlert:
    disease: str
    case_count: int
    severity: str
    similarity: str
    latest_timestamp: str
    recommendations: list[str] = field(default_factory=list)
    alert_level: str = "warning"

@dataclass
class OutbreakReport:
    alerts: list[OutbreakAlert]
    high_risk_count: int
    total_analysed: int
    window_days: int
    generated_at: str

def _parse_ts(ts: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try: return datetime.strptime(ts, fmt)
        except: pass
    return datetime.min

def detect_outbreaks(entries: list[dict[str, Any]], window_days: int = CLUSTER_WINDOW_DAYS, min_cases: int = CLUSTER_MIN_CASES) -> OutbreakReport:
    cutoff  = datetime.now() - timedelta(days=window_days)
    recent  = [e for e in entries if e.get("disease_hit") and e.get("timestamp") and _parse_ts(e["timestamp"]) >= cutoff]
    buckets: dict[str, list] = defaultdict(list)
    for e in recent:
        buckets[e["disease_hit"]].append(e)

    alerts = []
    high_risk = sum(1 for e in recent if (e.get("severity") or "") == "critical")

    for disease, cases in buckets.items():
        if len(cases) < min_cases:
            continue
        crit_pct   = sum(1 for c in cases if c.get("severity") == "critical") / len(cases)
        similarity = "High" if crit_pct >= 0.6 else "Moderate"
        sev        = "critical" if crit_pct >= 0.5 else "moderate"
        tss        = [_parse_ts(c["timestamp"]) for c in cases if c.get("timestamp")]
        latest     = max(tss).strftime("%Y-%m-%d %H:%M") if tss else "—"
        recs       = ["Isolate all birds showing symptoms", "Restrict movement of birds and equipment", "Strengthen biosecurity protocols", "Contact a licensed veterinarian"]
        alerts.append(OutbreakAlert(disease=disease, case_count=len(cases), severity=sev, similarity=similarity, latest_timestamp=latest, recommendations=recs, alert_level="critical" if crit_pct >= 0.6 else "warning"))

    alerts.sort(key=lambda a: a.case_count, reverse=True)
    return OutbreakReport(alerts=alerts, high_risk_count=high_risk, total_analysed=len(recent), window_days=window_days, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"))

def get_weekly_case_count(entries: list[dict[str, Any]]) -> int:
    cutoff = datetime.now() - timedelta(days=7)
    return sum(1 for e in entries if e.get("disease_hit") and e.get("timestamp") and _parse_ts(e["timestamp"]) >= cutoff)