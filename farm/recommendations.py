from __future__ import annotations
from dataclasses import dataclass
import farm.db as db


@dataclass
class Recommendation:
    title: str
    body: str
    action: str
    priority: str  # 'critical' | 'moderate' | 'low'


def get_recommendations(history: list[dict]) -> list[Recommendation]:
    recs: list[Recommendation] = []

    # Feed
    low_feed = db.feed_low_stock(threshold_days=3)
    if low_feed:
        names = ", ".join(f["name"] for f in low_feed)
        recs.append(Recommendation(
            title="Low Feed Stock",
            body=f"{names} estimated to last 3 days or less.",
            action="Purchase additional feed within 48 hours.",
            priority="critical",
        ))
    else:
        warn_feed = db.feed_low_stock(threshold_days=7)
        if warn_feed:
            names = ", ".join(f["name"] for f in warn_feed)
            recs.append(Recommendation(
                title="Feed Stock Warning",
                body=f"{names} estimated to last less than 7 days.",
                action="Plan feed purchase within the next 3-5 days.",
                priority="moderate",
            ))

    # Mortality
    today_m = db.mort_today(); week_m = db.mort_week()
    if today_m >= 10:
        recs.append(Recommendation(
            title="High Mortality Today",
            body=f"{today_m} deaths recorded today.",
            action="Inspect housing conditions and run an AI consultation immediately.",
            priority="critical",
        ))
    trend = _mortality_trend()
    if trend == "increasing":
        recs.append(Recommendation(
            title="Increasing Mortality Trend",
            body=f"Mortality has increased over the past 2 weeks ({week_m} this week).",
            action="Inspect ventilation, water quality, and isolate sick birds.",
            priority="moderate",
        ))

    # Vaccination
    overdue = db.vacc_overdue()
    if overdue:
        names = ", ".join(v["vaccine"] for v in overdue)
        recs.append(Recommendation(
            title="Overdue Vaccinations",
            body=f"{names} vaccination(s) are overdue.",
            action="Complete vaccination immediately.",
            priority="critical",
        ))

    # Egg production
    today_e = db.egg_today(); weekly_avg = db.egg_weekly_avg()
    if weekly_avg > 0 and today_e < weekly_avg * 0.7:
        recs.append(Recommendation(
            title="Egg Production Drop",
            body=f"Today's production ({today_e}) is significantly below the weekly average ({weekly_avg}).",
            action="Review feed quality, lighting schedule, and flock health.",
            priority="moderate",
        ))

    # Medication
    alerts = db.med_alerts()
    if alerts["expired"]:
        names = ", ".join(m["name"] for m in alerts["expired"])
        recs.append(Recommendation(
            title="Expired Medicines",
            body=f"{names} have expired.",
            action="Remove expired medicines from use and restock.",
            priority="critical",
        ))

    # Disease history
    critical_count = sum(1 for e in history if e.get("severity") == "critical")
    if critical_count >= 3:
        recs.append(Recommendation(
            title="Repeated Critical Disease Consultations",
            body=f"{critical_count} critical disease consultations recorded.",
            action="Schedule a full farm biosecurity review with a veterinarian.",
            priority="moderate",
        ))

    # Sort by priority
    order = {"critical": 0, "moderate": 1, "low": 2}
    recs.sort(key=lambda r: order.get(r.priority, 2))
    return recs


def _mortality_trend() -> str:
    """Simple trend: compare last 7 days vs prior 7 days."""
    from datetime import date, timedelta
    from db.migrations import get_connection
    conn = get_connection()
    today = date.today()
    w1_start = (today - timedelta(days=7)).isoformat()
    w2_start = (today - timedelta(days=14)).isoformat()
    w1 = conn.execute("SELECT COALESCE(SUM(count),0) FROM mortality WHERE date>=?", (w1_start,)).fetchone()[0]
    w2 = conn.execute("SELECT COALESCE(SUM(count),0) FROM mortality WHERE date>=? AND date<?", (w2_start, w1_start)).fetchone()[0]
    conn.close()
    if w2 == 0: return "stable"
    change = (w1 - w2) / w2
    if change > 0.15:   return "increasing"
    elif change < -0.15: return "decreasing"
    return "stable"


def feed_planner() -> dict:
    """Smart feed planner — depletion and reorder dates."""
    from datetime import date, timedelta
    feeds = db.feed_all()
    results = []
    for f in feeds:
        if not f.get("daily_usage_kg") or f["daily_usage_kg"] <= 0:
            continue
        days_left   = f["quantity_kg"] / f["daily_usage_kg"]
        deplete_date = date.today() + timedelta(days=int(days_left))
        reorder_date = date.today() + timedelta(days=max(0, int(days_left) - 2))
        # Suggest 14 days of stock
        suggested_qty = f["daily_usage_kg"] * 14
        results.append({
            "name":           f["name"],
            "feed_type":      f["feed_type"],
            "quantity_kg":    f["quantity_kg"],
            "daily_usage_kg": f["daily_usage_kg"],
            "days_remaining": round(days_left, 1),
            "depletion_date": deplete_date.strftime("%d %b %Y"),
            "reorder_date":   reorder_date.strftime("%d %b %Y"),
            "suggested_kg":   round(suggested_qty, 1),
        })
    return {"items": results}


def mortality_intelligence() -> dict:
    """Mortality trend analysis."""
    trend = _mortality_trend()
    week_m = db.mort_week()
    today_m = db.mort_today()

    if trend == "increasing":
        forecast = f"{int(week_m * 1.2)}–{int(week_m * 1.4)} birds"
        rec = "Inspect ventilation, water quality and isolate sick birds."
    elif trend == "decreasing":
        forecast = f"{max(0, int(week_m * 0.7))}–{int(week_m * 0.9)} birds"
        rec = "Continue current management — mortality is improving."
    else:
        forecast = f"{int(week_m * 0.9)}–{int(week_m * 1.1)} birds"
        rec = "Mortality is stable. Maintain biosecurity protocols."

    return {
        "trend":    trend.capitalize(),
        "today":    today_m,
        "week":     week_m,
        "forecast": forecast,
        "recommendation": rec,
    }


def egg_intelligence() -> dict:
    """Egg production comparison."""
    from db.migrations import get_connection
    from datetime import date, timedelta
    conn = get_connection()
    today_str  = date.today().isoformat()
    week_ago   = (date.today() - timedelta(days=7)).isoformat()
    month_ago  = (date.today() - timedelta(days=30)).isoformat()

    today_e = db.egg_today()
    week_avg = conn.execute("SELECT COALESCE(AVG(egg_count),0) FROM egg_production WHERE date>=?", (week_ago,)).fetchone()[0]
    month_avg = conn.execute("SELECT COALESCE(AVG(egg_count),0) FROM egg_production WHERE date>=?", (month_ago,)).fetchone()[0]
    conn.close()

    week_avg  = round(week_avg, 1)
    month_avg = round(month_avg, 1)

    def pct(a, b): return round((a - b) / b * 100, 1) if b > 0 else 0

    w_diff = pct(today_e, week_avg)
    m_diff = pct(today_e, month_avg)

    if w_diff >= 5:   trend, rec = "Above Average", "Maintain current feeding schedule."
    elif w_diff <= -10: trend, rec = "Below Average", "Review feed quality, lighting, and flock health."
    else:             trend, rec = "Stable",        "Egg production is consistent."

    return {
        "today": today_e, "week_avg": week_avg, "month_avg": month_avg,
        "week_diff": w_diff, "month_diff": m_diff,
        "trend": trend, "recommendation": rec,
    }