"""farm/db.py — Shared DB utilities for Sprint 9 farm modules."""
from __future__ import annotations
from db.migrations import get_connection
from datetime import date, timedelta


def today() -> str:
    return date.today().isoformat()

def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()

# ── Livestock ─────────────────────────────────────────────────────

def ls_all() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM livestock ORDER BY created_at DESC;").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def ls_add(bird_type, breed, quantity, age_weeks, pen, date_added, supplier, notes):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO livestock (bird_type,breed,quantity,age_weeks,pen,date_added,supplier,notes) VALUES(?,?,?,?,?,?,?,?)",
                     (bird_type,breed,quantity,age_weeks,pen,date_added,supplier,notes))
    conn.close()

def ls_update(id, **kw):
    if not kw: return
    sets = ",".join(f"{k}=?" for k in kw)
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE livestock SET {sets},updated_at=datetime('now','localtime') WHERE id=?",
                     list(kw.values())+[id])
    conn.close()

def ls_delete(id):
    conn = get_connection()
    with conn: conn.execute("DELETE FROM livestock WHERE id=?", (id,))
    conn.close()

def ls_total_birds() -> int:
    conn = get_connection()
    r = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM livestock;").fetchone()[0]
    conn.close()
    return r

def ls_by_type() -> dict[str,int]:
    conn = get_connection()
    rows = conn.execute("SELECT bird_type, SUM(quantity) as total FROM livestock GROUP BY bird_type;").fetchall()
    conn.close()
    return {r["bird_type"]: r["total"] for r in rows}

# ── Mortality ─────────────────────────────────────────────────────

def mort_all(limit=50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM mortality ORDER BY date DESC, created_at DESC LIMIT ?;", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mort_add(date_v, bird_type, count, possible_cause, consultation_id, notes):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO mortality (date,bird_type,count,possible_cause,consultation_id,notes) VALUES(?,?,?,?,?,?)",
                     (date_v,bird_type,count,possible_cause,consultation_id,notes))
    conn.close()

def mort_delete(id):
    conn = get_connection()
    with conn: conn.execute("DELETE FROM mortality WHERE id=?", (id,))
    conn.close()

def mort_today() -> int:
    conn = get_connection()
    r = conn.execute("SELECT COALESCE(SUM(count),0) FROM mortality WHERE date=?;", (today(),)).fetchone()[0]
    conn.close(); return r

def mort_week() -> int:
    conn = get_connection()
    r = conn.execute("SELECT COALESCE(SUM(count),0) FROM mortality WHERE date>=?;", (days_ago(7),)).fetchone()[0]
    conn.close(); return r

def mort_month() -> int:
    conn = get_connection()
    r = conn.execute("SELECT COALESCE(SUM(count),0) FROM mortality WHERE date>=?;", (days_ago(30),)).fetchone()[0]
    conn.close(); return r

def mort_rate() -> float:
    total = ls_total_birds()
    month = mort_month()
    if total <= 0: return 0.0
    return round(month / total * 100, 2)

def mort_trend(days=14) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT date, SUM(count) as total FROM mortality WHERE date>=? GROUP BY date ORDER BY date;",
                        (days_ago(days),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Feed ──────────────────────────────────────────────────────────

def feed_all() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM feed_inventory ORDER BY feed_type, name;").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def feed_add(name, feed_type, quantity_kg, supplier, purchase_date, daily_usage_kg, notes):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO feed_inventory (name,feed_type,quantity_kg,supplier,purchase_date,daily_usage_kg,notes) VALUES(?,?,?,?,?,?,?)",
                     (name,feed_type,quantity_kg,supplier,purchase_date,daily_usage_kg,notes))
    conn.close()

def feed_update(id, **kw):
    if not kw: return
    sets = ",".join(f"{k}=?" for k in kw)
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE feed_inventory SET {sets},updated_at=datetime('now','localtime') WHERE id=?",
                     list(kw.values())+[id])
    conn.close()

def feed_delete(id):
    conn = get_connection()
    with conn: conn.execute("DELETE FROM feed_inventory WHERE id=?", (id,))
    conn.close()

def feed_low_stock(threshold_days=3) -> list[dict]:
    items = feed_all()
    low = []
    for item in items:
        if item["daily_usage_kg"] and item["daily_usage_kg"] > 0:
            days_left = item["quantity_kg"] / item["daily_usage_kg"]
            if days_left <= threshold_days:
                item["days_remaining"] = round(days_left, 1)
                low.append(item)
    return low

# ── Medication ────────────────────────────────────────────────────

def med_all() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM medication ORDER BY name;").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def med_add(name, quantity, unit, expiry_date, purpose, supplier, notes):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO medication (name,quantity,unit,expiry_date,purpose,supplier,notes) VALUES(?,?,?,?,?,?,?)",
                     (name,quantity,unit,expiry_date,purpose,supplier,notes))
    conn.close()

def med_update(id, **kw):
    if not kw: return
    sets = ",".join(f"{k}=?" for k in kw)
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE medication SET {sets},updated_at=datetime('now','localtime') WHERE id=?",
                     list(kw.values())+[id])
    conn.close()

def med_delete(id):
    conn = get_connection()
    with conn: conn.execute("DELETE FROM medication WHERE id=?", (id,))
    conn.close()

def med_alerts() -> dict:
    """Return expired, expiring_soon (<=7 days), low_stock (<=10 units)."""
    from datetime import datetime
    meds = med_all()
    today_str = today()
    soon_str  = (date.today() + timedelta(days=7)).isoformat()
    expired, expiring, low = [], [], []
    for m in meds:
        exp = m.get("expiry_date") or ""
        if exp and exp < today_str: expired.append(m)
        elif exp and exp <= soon_str: expiring.append(m)
        if m["quantity"] <= 10: low.append(m)
    return {"expired": expired, "expiring_soon": expiring, "low_stock": low}

# ── Vaccination ───────────────────────────────────────────────────

def vacc_all() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM vaccination ORDER BY scheduled_date DESC;").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def vacc_add(vaccine, bird_group, scheduled_date, notes):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO vaccination (vaccine,bird_group,scheduled_date,notes) VALUES(?,?,?,?)",
                     (vaccine,bird_group,scheduled_date,notes))
    conn.close()

def vacc_complete(id, completed_date):
    conn = get_connection()
    with conn:
        conn.execute("UPDATE vaccination SET status='completed', completed_date=? WHERE id=?",
                     (completed_date, id))
    conn.close()

def vacc_delete(id):
    conn = get_connection()
    with conn: conn.execute("DELETE FROM vaccination WHERE id=?", (id,))
    conn.close()

def vacc_upcoming(days=14) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM vaccination WHERE status='pending' AND scheduled_date BETWEEN ? AND ? ORDER BY scheduled_date;",
                        (today(), (date.today()+timedelta(days=days)).isoformat())).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def vacc_overdue() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM vaccination WHERE status='pending' AND scheduled_date < ? ORDER BY scheduled_date;",
                        (today(),)).fetchall()
    conn.close()
    # Mark as missed in DB
    for r in rows:
        with get_connection() as conn2:
            conn2.execute("UPDATE vaccination SET status='missed' WHERE id=?", (r["id"],))
    return [dict(r) for r in rows]

# ── Egg production ────────────────────────────────────────────────

def egg_all(limit=30) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM egg_production ORDER BY date DESC LIMIT ?;", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def egg_add(date_v, egg_count, broken, sold, notes):
    conn = get_connection()
    with conn:
        conn.execute("INSERT INTO egg_production (date,egg_count,broken,sold,notes) VALUES(?,?,?,?,?)",
                     (date_v,egg_count,broken,sold,notes))
    conn.close()

def egg_delete(id):
    conn = get_connection()
    with conn: conn.execute("DELETE FROM egg_production WHERE id=?", (id,))
    conn.close()

def egg_today() -> int:
    conn = get_connection()
    r = conn.execute("SELECT COALESCE(SUM(egg_count),0) FROM egg_production WHERE date=?;", (today(),)).fetchone()[0]
    conn.close(); return r

def egg_weekly_avg() -> int:
    conn = get_connection()
    r = conn.execute("SELECT COALESCE(AVG(egg_count),0) FROM egg_production WHERE date>=?;", (days_ago(7),)).fetchone()[0]
    conn.close(); return int(r)