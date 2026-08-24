"""farm/context.py — Builds AI context from farm management data."""
from __future__ import annotations
import farm.db as db


def get_farm_context() -> str:
    """Return a plain-text summary of farm data to inject into LLM prompt."""
    lines = []

    total = db.ls_total_birds()
    if total > 0:
        by_type = db.ls_by_type()
        lines.append(f"FARM DATA: {total} total birds ({', '.join(f'{v} {k}' for k,v in by_type.items())}).")

    today_m = db.mort_today(); week_m = db.mort_week()
    if week_m > 0:
        lines.append(f"MORTALITY: {today_m} deaths today, {week_m} this week (rate {db.mort_rate()}%).")
        if today_m >= 10:
            lines.append("WARNING: Elevated mortality today — factor this into your assessment.")

    low_feed = db.feed_low_stock()
    if low_feed:
        lines.append(f"FEED ALERT: Low stock — {', '.join(f['name'] for f in low_feed)}.")

    overdue = db.vacc_overdue()
    if overdue:
        lines.append(f"VACCINATION OVERDUE: {', '.join(v['vaccine'] for v in overdue)} — remind the farmer.")

    today_e = db.egg_today(); weekly_avg = db.egg_weekly_avg()
    if today_e > 0 and weekly_avg > 0 and today_e < weekly_avg * 0.7:
        lines.append(f"EGG PRODUCTION DROP: Today {today_e} vs weekly avg {weekly_avg} — possible disease impact.")

    med_alerts = db.med_alerts()
    if med_alerts["expired"]:
        lines.append(f"EXPIRED MEDICINES: {', '.join(m['name'] for m in med_alerts['expired'])}.")

    if not lines:
        return ""

    return "\nFARM MANAGEMENT CONTEXT (use only if relevant — do not invent data):\n" + "\n".join(lines) + "\n"