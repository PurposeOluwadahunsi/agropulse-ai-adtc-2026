"""farm/sample_data.py — One-click sample farm data for demo readiness.
Populates realistic records so judges see a fully working platform instantly.
Only runs when explicitly triggered — never automatic.
"""
from __future__ import annotations
from datetime import date, timedelta
import farm.db as db


def load_sample_data() -> int:
    """
    Insert a realistic sample farm dataset.
    Returns number of records created. Safe to call once —
    does not check for duplicates, intended for empty/demo databases.
    """
    count = 0
    today = date.today()

    # Livestock
    db.ls_add("Broilers", "Ross 308", 850, 5, "Pen A", str(today - timedelta(days=20)), "Agro Supplies Ltd", "Main broiler batch"); count += 1
    db.ls_add("Layers", "ISA Brown", 320, 24, "Pen B", str(today - timedelta(days=120)), "Sunrise Hatchery", "Primary laying flock"); count += 1
    db.ls_add("Chicks", "Ross 308", 200, 1, "Brooder", str(today - timedelta(days=3)), "Agro Supplies Ltd", "New batch"); count += 1

    # Feed
    db.feed_add("Starter Feed", "Starter Feed", 180, "Grand Cereals", str(today - timedelta(days=5)), 22, "For chicks"); count += 1
    db.feed_add("Grower Feed", "Grower Feed", 95, "Grand Cereals", str(today - timedelta(days=8)), 18, "For broilers"); count += 1
    db.feed_add("Layer Mash", "Layer Mash", 40, "Vital Feeds", str(today - timedelta(days=10)), 16, "For layers — running low"); count += 1

    # Mortality — last 14 days, mostly low
    for i in range(14, 0, -1):
        d = today - timedelta(days=i)
        deaths = 1 if i % 4 == 0 else 0
        if deaths:
            db.mort_add(str(d), "Broilers", deaths, "Natural" if i > 3 else "Suspected respiratory", None, ""); count += 1

    # Vaccination
    db.vacc_add("Newcastle (La Sota)", "Broilers Pen A", str(today - timedelta(days=10)), "Given via drinking water"); count += 1
    db.vacc_add("Gumboro (IBD)", "Chicks", str(today + timedelta(days=3)), "Scheduled for brooder batch"); count += 1
    db.vacc_add("Newcastle Booster", "Layers Pen B", str(today - timedelta(days=2)), "Overdue — needs completion"); count += 1

    # Egg production — last 14 days
    base = 260
    for i in range(14, 0, -1):
        d = today - timedelta(days=i)
        variance = (i % 5) - 2
        eggs = max(0, base + variance * 4)
        db.egg_add(str(d), eggs, max(0, variance), int(eggs * 0.8), ""); count += 1

    # Medication
    db.med_add("Amprolium", 3, "L", str(today + timedelta(days=60)), "Coccidiosis treatment", "VetPharm Nigeria", ""); count += 1
    db.med_add("Multivitamin", 1, "kg", str(today - timedelta(days=5)), "General health", "VetPharm Nigeria", "Expired — remove from use"); count += 1

    return count


def has_sample_data() -> bool:
    """Check if the farm database already has any records."""
    return bool(db.ls_all() or db.mort_all() or db.feed_all())