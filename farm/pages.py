"""
farm/pages.py — Sprint 9 farm management UI pages.
All farm module render functions live here.
Imports farm/db.py for data. No business logic in UI.
"""
from __future__ import annotations
import streamlit as st
from datetime import date
from ui.components import section_header, render_stat

import farm.db as db

BIRD_TYPES  = ["Broilers","Layers","Cockerels","Growers","Chicks","Custom"]
FEED_TYPES  = ["Starter Feed","Grower Feed","Finisher Feed","Layer Mash","Custom"]


# ── Shared helpers ────────────────────────────────────────────────

def _card(body: str, cls: str = "info") -> None:
    st.markdown(f'<div class="assessment-card {cls}">{body}</div>', unsafe_allow_html=True)

def _label(text: str) -> None:
    st.markdown(f'<div class="ac-label">{text}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# LIVESTOCK
# ════════════════════════════════════════════════════════════════

def render_livestock_page() -> None:
    section_header("Livestock Management")

    # Summary cards
    total   = db.ls_total_birds()
    by_type = db.ls_by_type()
    c1,c2,c3 = st.columns(3)
    with c1: render_stat(str(total), "Total Birds")
    with c2: render_stat(str(len(by_type)), "Bird Categories")
    with c3: render_stat(str(len(db.ls_all())), "Flock Groups")

    # Distribution
    if by_type:
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        section_header("Bird Distribution")
        for btype, qty in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            pct = int(qty / total * 100) if total else 0
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.4rem 0;border-bottom:1px solid var(--border);font-size:0.84rem;">'
                f'<span style="min-width:120px;color:var(--text-700);">{btype}</span>'
                f'<div style="flex:1;background:var(--border);border-radius:3px;height:6px;">'
                f'<div style="width:{pct}%;background:var(--green-500);height:100%;border-radius:3px;"></div></div>'
                f'<span style="min-width:60px;text-align:right;font-weight:600;color:var(--text-900);">{qty:,} birds</span>'
                f'</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)

    # Add form
    with st.expander("+ Add Flock Group", expanded=False):
        with st.form("add_livestock"):
            c1,c2 = st.columns(2)
            with c1:
                btype  = st.selectbox("Bird Type", BIRD_TYPES)
                breed  = st.text_input("Breed (optional)")
                qty    = st.number_input("Quantity", min_value=1, value=100)
                age    = st.number_input("Age (weeks)", min_value=0, value=1)
            with c2:
                pen    = st.text_input("Pen/House")
                added  = st.date_input("Date Added", value=date.today())
                supp   = st.text_input("Supplier (optional)")
                notes  = st.text_area("Notes", height=70)
            if st.form_submit_button("Add Flock", use_container_width=True):
                db.ls_add(btype,breed,qty,age,pen,str(added),supp,notes)
                st.success(f"Added {qty} {btype}."); st.rerun()

    # Table
    flocks = db.ls_all()
    if not flocks:
        st.markdown('<div class="empty-state"><div class="es-title">No flocks recorded</div><div class="es-body">Add your first flock group above.</div></div>', unsafe_allow_html=True)
        return

    section_header("Flock Groups")
    search = st.text_input("Search by type or pen", "")
    if search:
        flocks = [f for f in flocks if search.lower() in f["bird_type"].lower() or search.lower() in (f["pen"] or "").lower()]

    header = '<div class="hist-wrap"><div class="hist-row" style="grid-template-columns:1fr 1fr 80px 70px 80px 80px;">'\
             '<span>Type</span><span>Breed</span><span>Qty</span><span>Age(wk)</span><span>Pen</span><span>Action</span></div>'
    rows = ""
    for f in flocks:
        rows += (f'<div class="hist-row" style="grid-template-columns:1fr 1fr 80px 70px 80px 80px;">'
                 f'<span>{f["bird_type"]}</span><span>{f["breed"] or "—"}</span>'
                 f'<span>{f["quantity"]:,}</span><span>{f["age_weeks"] or "—"}</span>'
                 f'<span>{f["pen"] or "—"}</span>'
                 f'<span style="color:var(--red-700);cursor:pointer;" onclick="">ID:{f["id"]}</span></div>')
    st.markdown(header+rows+"</div>", unsafe_allow_html=True)

    with st.expander("Delete a flock group"):
        ids = [f["id"] for f in flocks]
        del_id = st.selectbox("Select ID to delete", ids)
        if st.button("Delete", key="del_ls"):
            db.ls_delete(del_id); st.success("Deleted."); st.rerun()


# ════════════════════════════════════════════════════════════════
# MORTALITY
# ════════════════════════════════════════════════════════════════

def render_mortality_page() -> None:
    section_header("Mortality Tracker")

    today_m = db.mort_today(); week_m = db.mort_week(); month_m = db.mort_month(); rate = db.mort_rate()
    c1,c2,c3,c4 = st.columns(4)
    with c1: render_stat(str(today_m), "Today's Deaths")
    with c2: render_stat(str(week_m),  "This Week")
    with c3: render_stat(str(month_m), "This Month")
    with c4: render_stat(f"{rate}%",   "Monthly Rate")

    if today_m >= 10:
        st.markdown('<div class="emergency-alert"><div class="ea-title">Elevated Mortality Alert</div><div class="ea-body">Today\'s mortality is elevated. Run a consultation to identify a possible cause.</div></div>', unsafe_allow_html=True)

    with st.expander("+ Log Mortality", expanded=False):
        with st.form("add_mort"):
            c1,c2 = st.columns(2)
            with c1:
                m_date  = st.date_input("Date", value=date.today())
                m_type  = st.selectbox("Bird Type", BIRD_TYPES)
                m_count = st.number_input("Number of Deaths", min_value=1, value=1)
            with c2:
                m_cause = st.text_input("Possible Cause")
                m_notes = st.text_area("Notes", height=70)
            if st.form_submit_button("Log Mortality", use_container_width=True):
                db.mort_add(str(m_date),m_type,m_count,m_cause,None,m_notes)
                st.success("Logged."); st.rerun()

    records = db.mort_all()
    if not records:
        st.markdown('<div class="empty-state"><div class="es-title">No mortality records</div></div>', unsafe_allow_html=True)
        return

    section_header("Recent Records")
    header = '<div class="hist-wrap"><div class="hist-row" style="grid-template-columns:110px 1fr 60px 1fr 60px;">'\
             '<span>Date</span><span>Bird Type</span><span>Count</span><span>Cause</span><span>Action</span></div>'
    rows = ""
    for r in records[:20]:
        rows += (f'<div class="hist-row" style="grid-template-columns:110px 1fr 60px 1fr 60px;">'
                 f'<span>{r["date"]}</span><span>{r["bird_type"]}</span><span>{r["count"]}</span>'
                 f'<span>{r["possible_cause"] or "—"}</span><span>ID:{r["id"]}</span></div>')
    st.markdown(header+rows+"</div>", unsafe_allow_html=True)

    with st.expander("Delete a record"):
        ids = [r["id"] for r in records]
        del_id = st.selectbox("Select ID", ids, key="del_mort_id")
        if st.button("Delete", key="del_mort"):
            db.mort_delete(del_id); st.success("Deleted."); st.rerun()


# ════════════════════════════════════════════════════════════════
# FEED
# ════════════════════════════════════════════════════════════════

def render_feed_page() -> None:
    section_header("Feed Inventory")

    low_stock = db.feed_low_stock()
    if low_stock:
        items_str = ", ".join(f["name"] for f in low_stock)
        st.markdown(f'<div class="vet-alert"><strong>Low Stock Alert:</strong> {items_str} — restock soon.</div>', unsafe_allow_html=True)

    with st.expander("+ Add Feed Stock", expanded=False):
        with st.form("add_feed"):
            c1,c2 = st.columns(2)
            with c1:
                f_name  = st.text_input("Feed Name")
                f_type  = st.selectbox("Feed Type", FEED_TYPES)
                f_qty   = st.number_input("Quantity (kg)", min_value=0.0, value=50.0)
                f_daily = st.number_input("Daily Usage (kg)", min_value=0.0, value=5.0)
            with c2:
                f_supp  = st.text_input("Supplier")
                f_pdate = st.date_input("Purchase Date", value=date.today())
                f_notes = st.text_area("Notes", height=70)
            if st.form_submit_button("Add Feed", use_container_width=True):
                if f_name:
                    db.feed_add(f_name,f_type,f_qty,f_supp,str(f_pdate),f_daily,f_notes)
                    st.success("Feed added."); st.rerun()

    feeds = db.feed_all()
    if not feeds:
        st.markdown('<div class="empty-state"><div class="es-title">No feed records</div></div>', unsafe_allow_html=True)
        return

    section_header("Current Stock")
    for f in feeds:
        days_left = round(f["quantity_kg"] / f["daily_usage_kg"], 1) if f.get("daily_usage_kg") and f["daily_usage_kg"] > 0 else None
        cls = "critical" if (days_left and days_left <= 3) else "moderate" if (days_left and days_left <= 7) else "low"
        days_str = f"{days_left} days remaining" if days_left is not None else "Usage not set"
        st.markdown(
            f'<div class="assessment-card {cls}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div><div class="ac-value" style="font-size:0.95rem;">{f["name"]}</div>'
            f'<div style="font-size:0.78rem;color:var(--text-500);">{f["feed_type"]} | {f["quantity_kg"]} kg in stock</div></div>'
            f'<div style="text-align:right;font-size:0.82rem;font-weight:600;">{days_str}</div>'
            f'</div></div>', unsafe_allow_html=True)

    with st.expander("Adjust Stock / Delete"):
        ids = [f["id"] for f in feeds]
        sel_id = st.selectbox("Select feed", ids, format_func=lambda x: next((f["name"] for f in feeds if f["id"]==x),""))
        new_qty = st.number_input("New quantity (kg)", min_value=0.0, value=0.0)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("Update Quantity", use_container_width=True):
                db.feed_update(sel_id, quantity_kg=new_qty); st.success("Updated."); st.rerun()
        with c2:
            if st.button("Delete Record", use_container_width=True):
                db.feed_delete(sel_id); st.success("Deleted."); st.rerun()


# ════════════════════════════════════════════════════════════════
# MEDICATION
# ════════════════════════════════════════════════════════════════

def render_medication_page() -> None:
    section_header("Medication Inventory")

    alerts = db.med_alerts()
    if alerts["expired"]:
        st.markdown(f'<div class="emergency-alert"><div class="ea-title">Expired Medicines</div><div class="ea-body">{", ".join(m["name"] for m in alerts["expired"])} — remove from use immediately.</div></div>', unsafe_allow_html=True)
    if alerts["expiring_soon"]:
        st.markdown(f'<div class="vet-alert"><strong>Expiring Soon:</strong> {", ".join(m["name"] for m in alerts["expiring_soon"])}</div>', unsafe_allow_html=True)

    with st.expander("+ Add Medication", expanded=False):
        with st.form("add_med"):
            c1,c2 = st.columns(2)
            with c1:
                m_name   = st.text_input("Medicine Name")
                m_qty    = st.number_input("Quantity", min_value=0.0, value=1.0)
                m_unit   = st.selectbox("Unit", ["ml","g","kg","tablets","vials","sachets"])
                m_expiry = st.date_input("Expiry Date", value=date.today())
            with c2:
                m_purp  = st.text_input("Purpose")
                m_supp  = st.text_input("Supplier")
                m_notes = st.text_area("Notes", height=70)
            if st.form_submit_button("Add Medicine", use_container_width=True):
                if m_name:
                    db.med_add(m_name,m_qty,m_unit,str(m_expiry),m_purp,m_supp,m_notes)
                    st.success("Added."); st.rerun()

    meds = db.med_all()
    if not meds:
        st.markdown('<div class="empty-state"><div class="es-title">No medicines recorded</div></div>', unsafe_allow_html=True)
        return

    section_header("Medicine Stock")
    today_str = date.today().isoformat()
    for m in meds:
        exp = m.get("expiry_date") or ""
        if exp < today_str:   cls, badge = "critical", "EXPIRED"
        elif exp <= (date.today().replace(day=date.today().day)).isoformat(): cls, badge = "moderate", "EXPIRING SOON"
        else: cls, badge = "low", "OK"
        st.markdown(
            f'<div class="assessment-card {cls}">'
            f'<div style="display:flex;justify-content:space-between;">'
            f'<div><div class="ac-value" style="font-size:0.95rem;">{m["name"]}</div>'
            f'<div style="font-size:0.78rem;color:var(--text-500);">{m["purpose"] or "General"} | {m["quantity"]} {m["unit"]} | Exp: {exp or "—"}</div></div>'
            f'<span class="sev-badge {"sev-critical" if cls=="critical" else "sev-moderate" if cls=="moderate" else "sev-low"}">{badge}</span>'
            f'</div></div>', unsafe_allow_html=True)

    with st.expander("Delete"):
        ids = [m["id"] for m in meds]
        del_id = st.selectbox("Select", ids, format_func=lambda x: next((m["name"] for m in meds if m["id"]==x),""), key="del_med_sel")
        if st.button("Delete", key="del_med"):
            db.med_delete(del_id); st.success("Deleted."); st.rerun()


# ════════════════════════════════════════════════════════════════
# VACCINATION
# ════════════════════════════════════════════════════════════════

def render_vaccination_page() -> None:
    section_header("Vaccination Manager")

    overdue  = db.vacc_overdue()
    upcoming = db.vacc_upcoming()

    if overdue:
        st.markdown(f'<div class="emergency-alert"><div class="ea-title">Overdue Vaccinations</div><div class="ea-body">{len(overdue)} vaccination(s) overdue: {", ".join(v["vaccine"] for v in overdue)}</div></div>', unsafe_allow_html=True)
    if upcoming:
        st.markdown(f'<div class="vet-alert"><strong>Upcoming:</strong> {len(upcoming)} vaccination(s) due in the next 14 days.</div>', unsafe_allow_html=True)

    with st.expander("+ Schedule Vaccination", expanded=False):
        with st.form("add_vacc"):
            c1,c2 = st.columns(2)
            with c1:
                v_vac   = st.text_input("Vaccine Name")
                v_group = st.text_input("Bird Group / Pen")
            with c2:
                v_date  = st.date_input("Scheduled Date", value=date.today())
                v_notes = st.text_area("Notes", height=70)
            if st.form_submit_button("Schedule", use_container_width=True):
                if v_vac:
                    db.vacc_add(v_vac,v_group,str(v_date),v_notes)
                    st.success("Scheduled."); st.rerun()

    all_v = db.vacc_all()
    if not all_v:
        st.markdown('<div class="empty-state"><div class="es-title">No vaccinations scheduled</div></div>', unsafe_allow_html=True)
        return

    section_header("All Vaccinations")
    status_cls = {"pending":"sev-moderate","completed":"sev-low","missed":"sev-critical"}
    header = '<div class="hist-wrap"><div class="hist-row" style="grid-template-columns:1fr 1fr 110px 90px 80px;">'\
             '<span>Vaccine</span><span>Group</span><span>Scheduled</span><span>Status</span><span>Action</span></div>'
    rows = ""
    for v in all_v:
        cls   = status_cls.get(v["status"],"sev-unknown")
        rows += (f'<div class="hist-row" style="grid-template-columns:1fr 1fr 110px 90px 80px;">'
                 f'<span>{v["vaccine"]}</span><span>{v["bird_group"] or "—"}</span>'
                 f'<span>{v["scheduled_date"]}</span>'
                 f'<span><span class="sev-badge {cls}">{v["status"].upper()}</span></span>'
                 f'<span>ID:{v["id"]}</span></div>')
    st.markdown(header+rows+"</div>", unsafe_allow_html=True)

    with st.expander("Mark Complete / Delete"):
        pending = [v for v in all_v if v["status"]=="pending"]
        if pending:
            v_ids   = [v["id"] for v in pending]
            sel_vid = st.selectbox("Select pending", v_ids, format_func=lambda x: next((v["vaccine"] for v in pending if v["id"]==x),""))
            comp_date = st.date_input("Completion Date", value=date.today())
            if st.button("Mark Complete", use_container_width=True):
                db.vacc_complete(sel_vid, str(comp_date)); st.success("Marked complete."); st.rerun()

        all_ids = [v["id"] for v in all_v]
        del_vid = st.selectbox("Delete ID", all_ids, key="del_v_sel")
        if st.button("Delete", key="del_vacc"):
            db.vacc_delete(del_vid); st.success("Deleted."); st.rerun()


# ════════════════════════════════════════════════════════════════
# EGG PRODUCTION
# ════════════════════════════════════════════════════════════════

def render_egg_page() -> None:
    section_header("Egg Production")

    today_e = db.egg_today(); weekly_avg = db.egg_weekly_avg()
    c1,c2 = st.columns(2)
    with c1: render_stat(str(today_e),    "Today's Production")
    with c2: render_stat(str(weekly_avg), "Weekly Average")

    with st.expander("+ Log Production", expanded=False):
        with st.form("add_egg"):
            c1,c2 = st.columns(2)
            with c1:
                e_date  = st.date_input("Date", value=date.today())
                e_count = st.number_input("Total Eggs", min_value=0, value=0)
            with c2:
                e_broke = st.number_input("Broken", min_value=0, value=0)
                e_sold  = st.number_input("Sold", min_value=0, value=0)
            e_notes = st.text_area("Notes", height=60)
            if st.form_submit_button("Log", use_container_width=True):
                db.egg_add(str(e_date),e_count,e_broke,e_sold,e_notes)
                st.success("Logged."); st.rerun()

    records = db.egg_all()
    if not records:
        st.markdown('<div class="empty-state"><div class="es-title">No production records</div></div>', unsafe_allow_html=True)
        return

    section_header("Production Records")
    header = '<div class="hist-wrap"><div class="hist-row" style="grid-template-columns:110px 80px 70px 70px 1fr;">'\
             '<span>Date</span><span>Total</span><span>Broken</span><span>Sold</span><span>Notes</span></div>'
    rows = ""
    for r in records:
        rows += (f'<div class="hist-row" style="grid-template-columns:110px 80px 70px 70px 1fr;">'
                 f'<span>{r["date"]}</span><span>{r["egg_count"]}</span>'
                 f'<span>{r["broken"]}</span><span>{r["sold"]}</span>'
                 f'<span>{r["notes"] or "—"}</span></div>')
    st.markdown(header+rows+"</div>", unsafe_allow_html=True)

    with st.expander("Delete"):
        ids = [r["id"] for r in records]
        del_id = st.selectbox("Select ID", ids, key="del_egg_sel")
        if st.button("Delete", key="del_egg"):
            db.egg_delete(del_id); st.success("Deleted."); st.rerun()