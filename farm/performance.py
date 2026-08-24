"""farm/performance.py — Farm Performance Score (0-100) from existing data."""
from __future__ import annotations
from dataclasses import dataclass, field
import farm.db as db
from core.biosecurity import compute_biosecurity_score


@dataclass
class PerformanceReport:
    score: int
    status: str
    status_css: str
    reasons: list[str]
    recommendations: list[str]


def compute_performance(history: list[dict]) -> PerformanceReport:
    score = 100
    reasons: list[str] = []
    recs: list[str] = []

    # Mortality (max -25)
    rate = db.mort_rate()
    if rate >= 5:
        score -= 25; reasons.append(f"High mortality rate: {rate}%"); recs.append("Investigate cause of mortality urgently.")
    elif rate >= 2:
        score -= 12; reasons.append(f"Moderate mortality rate: {rate}%"); recs.append("Monitor mortality daily.")
    else:
        reasons.append("Low mortality rate — good flock health.")

    # Biosecurity (max -20)
    bio = compute_biosecurity_score(history)
    if bio.score < 60:
        score -= 20; reasons.append(f"Low biosecurity score: {bio.score}/100"); recs.append("Review biosecurity protocols immediately.")
    elif bio.score < 80:
        score -= 8; reasons.append(f"Moderate biosecurity score: {bio.score}/100")
    else:
        reasons.append(f"Good biosecurity score: {bio.score}/100.")

    # Feed (max -20)
    low = db.feed_low_stock()
    all_feed = db.feed_all()
    if not all_feed:
        score -= 10; reasons.append("No feed records found."); recs.append("Add feed inventory records.")
    elif low:
        score -= 20; reasons.append(f"{len(low)} feed item(s) critically low."); recs.append("Restock feed within 48 hours.")
    else:
        reasons.append("Feed stock adequate.")

    # Vaccination (max -20)
    overdue = db.vacc_overdue()
    if overdue:
        score -= 20; reasons.append(f"{len(overdue)} vaccination(s) overdue."); recs.append("Complete overdue vaccinations immediately.")
    else:
        upcoming = db.vacc_upcoming()
        if upcoming:
            score -= 5; reasons.append(f"{len(upcoming)} vaccination(s) due soon.")
            recs.append("Schedule upcoming vaccinations.")
        else:
            reasons.append("Vaccination schedule up to date.")

    # Egg production (max -15)
    today_e = db.egg_today(); weekly_avg = db.egg_weekly_avg()
    if weekly_avg > 0 and today_e < weekly_avg * 0.7:
        score -= 15; reasons.append("Egg production significantly below weekly average.")
        recs.append("Review feed quality and flock health.")
    elif today_e > 0:
        reasons.append("Egg production stable.")

    score = max(0, min(100, score))

    if score >= 85:   status, css = "Excellent", "sev-low"
    elif score >= 70: status, css = "Good",      "sev-low"
    elif score >= 50: status, css = "Fair",       "sev-moderate"
    else:             status, css = "Needs Attention", "sev-critical"

    if not recs:
        recs.append("Continue current management practices.")

    return PerformanceReport(score=score, status=status, status_css=css,
                             reasons=reasons, recommendations=recs)