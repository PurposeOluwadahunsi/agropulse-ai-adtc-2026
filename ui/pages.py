"""ui/pages.py (Sprint 10 — updated analytics with charts, empty states, filters)"""
from __future__ import annotations
from typing import Any
import streamlit as st
from ui.components import section_header, render_history_table, render_stat, render_empty_assessment, sev_badge
from ui.state import get_history, get_stats, get_last_result
from ui.analytics import render_outbreak_panel, render_biosecurity_panel, render_health_timeline, render_trend_analytics, _average_risk
from ui.charts import chart_disease_frequency, chart_consultation_trend, chart_severity_pie, chart_risk_trend, chart_consultation_scatter
from core.outbreak import get_weekly_case_count
from core.biosecurity import compute_biosecurity_score

DISEASES = [
    ("ND001","Newcastle Disease","critical","Twisted neck, gasping, green diarrhoea, sudden death"),
    ("IBD001","Gumboro Disease","critical","Watery white diarrhoea, vent-picking, huddling"),
    ("COC001","Coccidiosis","moderate","Bloody droppings, pale comb, poor weight gain"),
    ("FT001","Fowl Typhoid","critical","Sulphur-yellow diarrhoea, pale shrunken comb"),
    ("MD001","Marek's Disease","critical","Progressive leg paralysis, grey iris, skin tumours"),
    ("FC001","Fowl Cholera","critical","Blue comb, swollen wattles, sudden death"),
    ("IB001","Infectious Bronchitis","moderate","Misshapen eggs, tracheal rales, coughing"),
    ("AI001","Avian Influenza","critical","Massive sudden death, haemorrhage on legs"),
    ("IC001","Infectious Coryza","moderate","Foul nasal discharge, swollen face"),
    ("CRD001","Chronic Respiratory Dis.","moderate","Foamy eye, slow spread, chronic cough"),
    ("ASP001","Aspergillosis","moderate","Chick gasping, extended neck, brooder pneumonia"),
    ("EDS001","Egg Drop Syndrome","low","Shell-less eggs, pale shells, healthy birds"),
]

def _empty(title: str, body: str) -> None:
    st.markdown(f'<div class="empty-state"><div class="es-title">{title}</div><div class="es-body">{body}</div></div>', unsafe_allow_html=True)

def render_knowledge_base_page() -> None:
    section_header("Knowledge Base")
    st.markdown('<div class="about-section"><h3>Disease Reference Library</h3><p>12 curated poultry diseases from FAO, OIE, NVRI Nigeria, and Merck Veterinary Manual.</p></div>', unsafe_allow_html=True)
    for _, name, severity, symptoms in DISEASES:
        badge = sev_badge(severity)
        st.markdown(f'<div class="assessment-card {severity}" style="margin-bottom:0.5rem;"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;"><div class="ac-value" style="font-size:0.95rem;">{name}</div>{badge}</div><div class="ac-body" style="font-size:0.8rem;color:var(--text-500);">Key symptoms: {symptoms}</div></div>', unsafe_allow_html=True)

def render_history_page() -> None:
    section_header("Consultation History")
    history = get_history()
    if not history:
        _empty("No Consultation History", "Start your first AI consultation to begin building farm insights."); return

    stats = get_stats() or {}
    c1,c2,c3 = st.columns(3)
    with c1: render_stat(str(stats.get("total_queries",0)), "Total Consultations")
    with c2: render_stat(str(stats.get("triage_hits",0)), "Triage Matches")
    with c3: render_stat(str(stats.get("vet_referrals",0)), "Vet Referrals")

    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    with st.expander("Filter & Search", expanded=False):
        fc1,fc2,fc3 = st.columns(3)
        with fc1: search = st.text_input("Search disease","")
        with fc2: sev_filter = st.selectbox("Severity",["All","critical","moderate","low"])
        with fc3: sort_by = st.selectbox("Sort by",["Date (newest)","Date (oldest)","Severity"])

    filtered = history
    if search: filtered = [e for e in filtered if search.lower() in (e.get("disease_hit") or "").lower()]
    if sev_filter != "All": filtered = [e for e in filtered if e.get("severity")==sev_filter]
    if sort_by == "Date (oldest)": filtered = list(reversed(filtered))
    elif sort_by == "Severity":
        order={"critical":0,"moderate":1,"low":2}
        filtered = sorted(filtered, key=lambda e: order.get(e.get("severity") or "",3))

    if filtered: render_history_table(filtered[:20])
    else: _empty("No Results", "No consultations match your filter.")

def render_statistics_page() -> None:
    section_header("Statistics")
    history = get_history(); stats = get_stats() or {}
    if not history:
        _empty("No Statistics Yet", "Run your first consultation to generate statistics."); return

    total_q=stats.get("total_queries",0); breakdown=stats.get("disease_breakdown",{})
    top_dis=max(breakdown,key=breakdown.get) if breakdown else "—"
    hits=stats.get("triage_hits",0); rate=f"{int(hits/total_q*100)}%" if total_q else "—"
    vet_refs=stats.get("vet_referrals",0)

    c1,c2,c3,c4=st.columns(4)
    with c1: render_stat(str(total_q),"Total Consultations")
    with c2: render_stat(top_dis,"Most Frequent Disease")
    with c3: render_stat(rate,"Triage Match Rate")
    with c4: render_stat(str(vet_refs),"Vet Referrals Issued")

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    t1,t2 = st.tabs(["Disease Charts","Trend Charts"])
    with t1:
        c1,c2=st.columns(2)
        with c1:
            section_header("Disease Frequency")
            chart_disease_frequency(breakdown)
        with c2:
            section_header("Severity Distribution")
            chart_severity_pie(history)
    with t2:
        section_header("Consultation Trend Over Time")
        chart_consultation_trend(history)
        section_header("Farm Risk Trend")
        chart_risk_trend(history)
        section_header("Consultation Timeline")
        chart_consultation_scatter(history)

def render_analytics_page() -> None:
    history = get_history(); stats = get_stats() or {}
    if not history:
        section_header("Farm Intelligence")
        _empty("No Farm Data Yet","Run your first consultation to begin generating farm intelligence insights."); return
    render_outbreak_panel(history)
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    render_trend_analytics(history, stats)
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    render_biosecurity_panel(history)
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    render_health_timeline(history)

def render_about_page() -> None:
    section_header("About AgroPulse AI")
    st.markdown("""
    <div class="about-section"><h3>Project Overview</h3><p>AgroPulse AI is an offline AI-powered poultry disease decision support system built for African poultry farmers, agricultural extension officers, and veterinary field workers. Developed for the Africa Deep Tech Challenge 2026.</p></div>
    <div class="about-section"><h3>Mission</h3><p>To give every Nigerian poultry farmer access to expert-level disease advisory at the point of need — in the field, offline, and in plain language.</p></div>
    <div class="about-section"><h3>AI Architecture</h3><p>Three-layer pipeline: <strong>Triage Engine</strong> (rule-based weighted symptom matching), <strong>RAG Retrieval</strong> (ChromaDB + sentence-transformers), <strong>Local LLM</strong> (Phi-3 Mini via Ollama).</p></div>
    <div class="about-section"><h3>Technology Stack</h3><p><span class="tech-badge">Python 3.11</span><span class="tech-badge">Streamlit</span><span class="tech-badge">Ollama</span><span class="tech-badge">Phi-3 Mini</span><span class="tech-badge">ChromaDB</span><span class="tech-badge">sentence-transformers</span><span class="tech-badge">SQLite</span><span class="tech-badge">Whisper</span><span class="tech-badge">reportlab</span><span class="tech-badge">Plotly</span></p></div>
    <div class="about-section"><h3>Knowledge Sources</h3><ul><li>FAO Animal Health Manuals</li><li>OIE Terrestrial Animal Health Code</li><li>NVRI Nigeria guidelines</li><li>Merck Veterinary Manual 11th Edition</li></ul></div>
    <div class="about-section"><h3>Responsible AI</h3><div class="rai-box">AgroPulse AI is a <strong>decision-support tool</strong>, not a diagnostic replacement. All assessments describe possible conditions. A licensed veterinarian must always be consulted before administering treatment.</div></div>
    <div class="about-section"><h3>Limitations</h3><ul><li>Response time 100–160s on CPU (Phi-3 Mini requires ~3.5GB RAM)</li><li>Vague queries return no match by design</li><li>Knowledge base covers 12 diseases</li><li>Does not replace laboratory testing</li></ul></div>
    """, unsafe_allow_html=True)