"""farm/insights.py — Plain-language farm insights from stored data only.
No AI model used. Pure rule-based summarisation of existing records.
"""
from __future__ import annotations
from dataclasses import dataclass
import farm.db as db
from farm.performance import compute_performance
from core.biosecurity import compute_biosecurity_score
from farm.recommendations import _mortality_trend, egg_intelligence


@dataclass
class DailySummary:
    lines: list[str]
    overall_status: str  # 'stable' | 'attention' | 'critical'


def get_daily_summary(history: list[dict]) -> DailySummary:
    lines: list[str] = []
    status = "stable"

    perf = compute_performance(history)
    if perf.status == "Excellent" or perf.status == "Good":
        lines.append(f"Farm is {perf.status.lower()} overall (performance {perf.score}/100).")
    else:
        lines.append(f"Farm performance needs attention ({perf.score}/100 — {perf.status}).")
        status = "attention" if status == "stable" else status

    # Feed
    low_feed = db.feed_low_stock(threshold_days=7)
    all_feed = db.feed_all()
    if not all_feed:
        lines.append("No feed records available yet.")
    elif low_feed:
        days = min(f["quantity_kg"]/f["daily_usage_kg"] for f in low_feed if f.get("daily_usage_kg"))
        lines.append(f"Feed will last approximately {int(days)} more day(s) — reorder soon.")
        status = "attention" if status == "stable" else status
    else:
        lines.append("Feed stock is adequate.")

    # Vaccination
    overdue = db.vacc_overdue()
    if overdue:
        n = len(overdue)
        lines.append(f"{n} vaccination{'s are' if n>1 else ' is'} overdue.")
        status = "critical"
    else:
        upcoming = db.vacc_upcoming()
        if upcoming:
            lines.append(f"{len(upcoming)} vaccination(s) due within 14 days.")
        else:
            lines.append("Vaccinations are up to date.")

    # Mortality
    today_m = db.mort_today(); rate = db.mort_rate()
    if today_m >= 10 or rate >= 5:
        lines.append(f"Mortality is high today ({today_m} deaths, {rate}% monthly rate).")
        status = "critical"
    elif today_m > 0:
        lines.append(f"Mortality is low ({today_m} today, {rate}% monthly rate).")
    else:
        lines.append("No mortality recorded today.")

    # Egg production
    ei = egg_intelligence()
    if ei["today"] > 0 or ei["week_avg"] > 0:
        lines.append(f"Egg production is {ei['trend'].lower()} ({ei['today']} today vs {ei['week_avg']} weekly average).")

    # Biosecurity
    bio = compute_biosecurity_score(history)
    lines.append(f"Biosecurity score is {bio.score}/100 ({bio.status}).")
    if bio.score < 60:
        status = "critical"

    return DailySummary(lines=lines, overall_status=status)


def get_ai_insight(history: list[dict]) -> str:
    """One-paragraph plain-language insight — no AI model, rule-based synthesis."""
    perf = compute_performance(history)
    bio  = compute_biosecurity_score(history)
    overdue = db.vacc_overdue()
    low_feed = db.feed_low_stock(threshold_days=5)
    today_m = db.mort_today()

    parts = []
    if perf.score >= 80:
        parts.append("the farm is currently stable")
    elif perf.score >= 50:
        parts.append("the farm shows some areas needing attention")
    else:
        parts.append("the farm requires immediate attention in several areas")

    issues = []
    if low_feed: issues.append("feed needs to be replenished soon")
    if overdue:  issues.append(f"{len(overdue)} vaccination{'s remain' if len(overdue)>1 else ' remains'} overdue")
    if today_m >= 5: issues.append("mortality is elevated today")
    if bio.score < 70: issues.append("biosecurity practices could be strengthened")

    if issues:
        parts.append(", ".join(issues))

    if not issues:
        return f"Based on current records, {parts[0]}, with no urgent issues detected. Continue current management practices."

    return f"Based on current records, {parts[0]}, but {parts[1]}."


def get_whats_changed(history: list[dict], previous_snapshot: dict | None) -> list[str]:
    """Compare current state against a previous snapshot stored in session state."""
    if not previous_snapshot:
        return ["This is your first visit this session — no comparison available yet."]

    changes = []
    today_m = db.mort_today()
    if today_m != previous_snapshot.get("mortality_today", today_m):
        diff = today_m - previous_snapshot.get("mortality_today", today_m)
        changes.append(f"Mortality {'increased' if diff>0 else 'decreased'} by {abs(diff)} since last visit.")

    today_e = db.egg_today()
    prev_e = previous_snapshot.get("eggs_today", today_e)
    if today_e != prev_e:
        changes.append(f"Egg production {'improved' if today_e>prev_e else 'declined'} since last visit.")

    bio = compute_biosecurity_score(history)
    prev_bio = previous_snapshot.get("biosecurity_score", bio.score)
    if bio.score != prev_bio:
        changes.append(f"Biosecurity score changed from {prev_bio} to {bio.score}.")

    low_feed = len(db.feed_low_stock())
    prev_feed = previous_snapshot.get("low_feed_count", low_feed)
    if low_feed != prev_feed:
        changes.append(f"Feed stock status changed ({'more' if low_feed>prev_feed else 'fewer'} items low).")

    total = len(history)
    prev_total = previous_snapshot.get("consultation_count", total)
    if total > prev_total:
        changes.append(f"{total - prev_total} new consultation(s) recorded since last visit.")

    if not changes:
        changes.append("No significant changes since last visit.")
    return changes


def build_snapshot(history: list[dict]) -> dict:
    """Build a snapshot dict to compare against on next visit."""
    bio = compute_biosecurity_score(history)
    return {
        "mortality_today":    db.mort_today(),
        "eggs_today":         db.egg_today(),
        "biosecurity_score":  bio.score,
        "low_feed_count":     len(db.feed_low_stock()),
        "consultation_count": len(history),
    }