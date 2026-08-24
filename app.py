from __future__ import annotations
import os, sys, time
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import streamlit as st
st.set_page_config(page_title="AgroPulse AI", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

from ui.styles     import apply_styles, apply_sidebar_button_fix
from ui.navigation import render_sidebar, get_active_page, set_active_page
from ui.components import (
    render_hero, section_header, dash_card, sev_badge,
    render_symptoms, render_emergency_alert, render_vet_alert,
    render_action_plan, render_evidence_sources, render_reasoning,
    render_ai_response, render_timing, render_confidence,
    render_history_table, render_stat, render_empty_assessment, assessment_card,
)
from ui.pages import (
    render_knowledge_base_page, render_history_page,
    render_statistics_page, render_about_page, render_analytics_page,
)
from ui.risk      import render_risk_panel
from ui.demo      import render_demo_page
from ui.analytics import _average_risk
from ui.charts    import chart_disease_frequency, chart_consultation_trend
from ui.state import (
    init_state, get_session_id, set_session_id,
    get_last_result, set_last_result,
    get_history, set_history, get_stats, set_stats,
    get_logbook, set_logbook, is_startup_done, mark_startup_done,
)
from ui.pipeline  import run_startup, get_farm_status
from core.logbook import Logbook, LogEntry
from core.triage  import triage
from core.rag     import retrieve
from core.llm     import generate
from core.biosecurity import compute_biosecurity_score
from core.outbreak    import get_weekly_case_count, detect_outbreaks
from farm.pages import (
    render_livestock_page, render_mortality_page, render_feed_page,
    render_medication_page, render_vaccination_page, render_egg_page,
)
from farm.context import get_farm_context
from farm.smart import (
    render_daily_summary, render_performance_panel, render_smart_operations,
    render_feed_planner, render_mortality_intelligence,
    render_smart_recommendations, render_vaccination_calendar,
)
from farm.performance import compute_performance
from farm.insights import get_daily_summary, get_ai_insight
from farm.sample_data import load_sample_data, has_sample_data
import farm.db as fdb

SAMPLE_QUERIES = {
    "Respiratory":  "My chickens are gasping for air, some have twisted necks and I see green droppings. About 10 birds died this morning.",
    "Digestive":    "The chicks have watery whitish diarrhoea and they huddle together picking at their vents.",
    "Bloody stool": "I found blood in the droppings of my 3-week-old chicks and their combs are very pale.",
    "Sudden death": "Several adult birds died suddenly this morning. Their combs are blue and wattles are swollen.",
    "Egg quality":  "Egg production has dropped suddenly. Many eggs have no shells or very pale shells. The birds look healthy otherwise.",
}

@st.cache_resource
def _get_logbook() -> Logbook:
    return Logbook()

apply_styles()
apply_sidebar_button_fix()
init_state()

def do_startup() -> None:
    with st.spinner("Starting AgroPulse AI..."):
        lb = _get_logbook(); set_logbook(lb)
        ok, session_id, error = run_startup(lb)
        if not ok:
            st.error(f"Startup failed: {error}"); st.stop()
        set_session_id(session_id)
        set_history(lb.get_recent(50))
        set_stats(lb.get_stats())
        mark_startup_done()

if not is_startup_done():
    do_startup()

def refresh() -> None:
    lb = get_logbook()
    if lb:
        set_history(lb.get_recent(50))
        set_stats(lb.get_stats())

def run_pipeline_with_progress(query: str, show_tts: bool = False) -> None:
    lb=get_logbook(); session_id=get_session_id(); status=st.empty()
    def show(msg):
        status.markdown(
            f'<div style="background:#fff;border:1px solid #E5E7EB;border-left:4px solid #4A7C59;'
            f'border-radius:8px;padding:0.9rem 1.1rem;font-size:0.875rem;color:#374151;'
            f'display:flex;align-items:center;gap:0.6rem;">'
            f'<span style="color:#4A7C59;">&#9679;</span>{msg}</div>', unsafe_allow_html=True)

    show("&#10122; Checking symptoms..."); t0=time.perf_counter()
    triage_result=triage(query); triage_ms=int((time.perf_counter()-t0)*1000); time.sleep(0.1)
    show("&#10123; Searching knowledge base..."); t0=time.perf_counter()
    rag_chunks=retrieve(query,k=2); rag_ms=int((time.perf_counter()-t0)*1000); time.sleep(0.1)
    show("&#10124; Calculating farm risk..."); time.sleep(0.2)
    show("&#10125; Generating AI assessment &mdash; please wait...")
    farm_ctx=get_farm_context(); t0=time.perf_counter(); tokens=[]
    for token in generate(query,stream=True): tokens.append(token)
    ai_response="".join(tokens)
    if farm_ctx and any(kw in farm_ctx for kw in ["WARNING","ALERT","DROP","OVERDUE"]):
        ai_response=f"[Farm data noted: {farm_ctx.strip()}]\n\n"+ai_response
    llm_ms=int((time.perf_counter()-t0)*1000)
    show("&#10126; Preparing recommendations..."); time.sleep(0.15)
    show("&#10127; Saving to logbook...")
    entry=LogEntry(
        session_id=session_id,user_input=query,ai_response=ai_response,
        triage_matched=triage_result.matched,disease_hit=triage_result.disease_name,
        disease_id=triage_result.disease_id,severity=triage_result.severity,
        triage_score=triage_result.score,triage_conf=triage_result.confidence,
        matched_symptoms=triage_result.matched_symptoms,vet_needed=triage_result.vet_referral,
        rag_sources=list({c["source"] for c in rag_chunks}),
        response_ms=triage_ms+rag_ms+llm_ms,
    )
    log_id=lb.write_entry(entry); time.sleep(0.1)
    show("&#10003; Complete."); time.sleep(0.35); status.empty()
    result={
        "success":True,"error":"","query":query,
        "triage_matched":triage_result.matched,"disease_name":triage_result.disease_name,
        "disease_id":triage_result.disease_id,"severity":triage_result.severity,
        "confidence":triage_result.confidence,"triage_score":triage_result.score,
        "matched_symptoms":triage_result.matched_symptoms,"vet_referral":triage_result.vet_referral,
        "first_aid":triage_result.first_aid,"treatment":triage_result.treatment,
        "prevention":triage_result.prevention,
        "biosecurity":getattr(triage_result,"biosecurity",[]),
        "when_to_call_vet":getattr(triage_result,"when_to_call_vet",""),
        "ai_response":ai_response,"rag_sources":list({c["source"] for c in rag_chunks}),
        "response_ms":triage_ms+rag_ms+llm_ms,"triage_ms":triage_ms,
        "rag_ms":rag_ms,"llm_ms":llm_ms,"log_id":log_id,
    }
    if show_tts and ai_response:
        try:
            from voice.tts import speak; speak(ai_response,block=False)
        except Exception: pass
    set_last_result(result); refresh(); st.rerun()

def render_assessment(result: dict) -> None:
    severity=result.get("severity") or ""
    if severity=="critical" and result.get("disease_name"):
        render_emergency_alert(result["disease_name"])
    if result["triage_matched"] and result["disease_name"]:
        badge=sev_badge(severity)
        st.markdown(f'<div class="assessment-card {severity}"><div class="ac-label">Possible Disease</div><div class="ac-value">{result["disease_name"]}</div><div style="margin-top:0.4rem;">{badge}</div></div>',unsafe_allow_html=True)
    else:
        assessment_card("Possible Disease",body="No specific disease matched. Provide more specific symptoms.",card_class="info")
    st.markdown('<div class="assessment-card info"><div class="ac-label">Confidence Assessment</div>',unsafe_allow_html=True)
    render_confidence(result["confidence"],result["triage_score"])
    st.markdown("</div>",unsafe_allow_html=True)
    if result["vet_referral"]: render_vet_alert(result.get("when_to_call_vet",""))
    render_symptoms(result["matched_symptoms"])
    if result.get("first_aid"):
        steps=[s.strip() for s in result["first_aid"].split(".") if s.strip()]
        render_action_plan(steps[:5])
    section_header("Farm Risk Intelligence"); render_risk_panel(result)
    section_header("AI Detailed Advisory"); render_ai_response(result["ai_response"])
    section_header("Evidence Used")
    render_symptoms(result["matched_symptoms"])
    render_evidence_sources(result["rag_sources"])
    render_reasoning(result.get("explanation") or
        f"Assessment based on {len(result.get('matched_symptoms',[]))} matched symptom(s) for {result.get('disease_name','a known condition')}.")
    section_header("Export Report")
    if st.button("Download PDF Report",use_container_width=True,key="pdf_btn"):
        try:
            from ui.reports import generate_pdf_report
            pdf=generate_pdf_report(result)
            slug=(result.get("disease_name") or "report").replace(" ","_").lower()
            st.download_button("Click to save PDF",pdf,f"agropulse_{slug}.pdf","application/pdf",key="pdf_dl")
        except RuntimeError as e: st.error(str(e))
    render_timing(result.get("triage_ms",0),result.get("rag_ms",0),result.get("llm_ms",0),result.get("response_ms",0),result.get("log_id",0))

render_sidebar()
page=get_active_page()

# ════════ HOME ════════════════════════════════════════════════════
if page=="home":
    render_hero()
    history=get_history(); stats=get_stats() or {}
    farm_status,farm_css=get_farm_status(history)
    total=stats.get("total_queries",0)
    bio_rep=compute_biosecurity_score(history)
    avg_r=_average_risk(history)
    breakdown=stats.get("disease_breakdown",{})
    top_dis=max(breakdown,key=breakdown.get) if breakdown else "—"
    perf=compute_performance(history)
    total_birds=fdb.ls_total_birds()
    today_mort=fdb.mort_today()
    today_eggs=fdb.egg_today()
    low_feed=len(fdb.feed_low_stock())
    overdue_v=len(fdb.vacc_overdue())

    # 1. Daily Summary
    render_daily_summary(history)

    # First-time judge experience — sample data prompt
    if not has_sample_data():
        st.markdown(
            '<div class="assessment-card info" style="border-left-color:var(--blue-700);">'
            '<div class="ac-label" style="color:var(--blue-700);">First Time Here?</div>'
            '<div class="ac-body">Load sample farm data to instantly see AgroPulse AI\'s full capabilities — '
            'livestock, mortality, feed, vaccinations, and egg production records.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Load Sample Farm Data", use_container_width=True, key="load_sample"):
            with st.spinner("Loading sample farm data..."):
                n = load_sample_data()
            st.success(f"Loaded {n} sample records. Explore Smart Operations, Livestock, and Analytics.")
            st.rerun()

    # 2. Daily Assistant Summary (plain language)
    from farm.smart import render_daily_assistant_summary, render_ai_insight_panel, render_whats_changed
    render_daily_assistant_summary(history)

    # 3. AI Insight
    render_ai_insight_panel(history)

    # 4. What Changed Since Last Visit
    render_whats_changed(history)

    # 5. Smart Recommendations
    render_smart_recommendations(history)

    # 6. Smart Operations cards
    render_smart_operations(history)

    # 7. Performance
    render_performance_panel(history)

    # 5. Alerts
    section_header("Active Alerts")
    alerts=[]
    if today_mort>=10: alerts.append(("critical","High Mortality",f"{today_mort} deaths today."))
    if low_feed>0: alerts.append(("moderate","Low Feed Stock",f"{low_feed} item(s) running low."))
    if overdue_v>0: alerts.append(("moderate","Overdue Vaccinations",f"{overdue_v} overdue."))
    if bio_rep.score<60: alerts.append(("critical","Critical Biosecurity",f"Score {bio_rep.score}/100."))
    ob=detect_outbreaks(history)
    for a in ob.alerts[:2]:
        alerts.append(("moderate" if a.alert_level=="warning" else "critical",
                        f"Possible {a.disease} Cluster",f"{a.case_count} cases in {a.window_days} days."))
    if not alerts:
        st.markdown('<div class="assessment-card low"><div class="ac-body" style="color:var(--green-700);font-weight:600;">No active alerts. All systems normal.</div></div>',unsafe_allow_html=True)
    else:
        for cls,title,body in alerts:
            st.markdown(f'<div class="assessment-card {cls}"><div class="ac-label">{title}</div><div class="ac-body">{body}</div></div>',unsafe_allow_html=True)

    # 6. Analytics preview
    if history and breakdown:
        section_header("Analytics Preview")
        pc1,pc2=st.columns(2)
        with pc1:
            st.markdown('<div class="ac-label">Disease Frequency</div>',unsafe_allow_html=True)
            chart_disease_frequency(breakdown)
        with pc2:
            st.markdown('<div class="ac-label">Consultation Trend</div>',unsafe_allow_html=True)
            chart_consultation_trend(history)

    # 7. Quick Actions
    section_header("Quick Actions")
    qa1,qa2,qa3,qa4,qa5=st.columns(5)
    with qa1:
        if st.button("+ New Consultation",use_container_width=True): set_active_page("consultation"); st.rerun()
    with qa2:
        if st.button("★ Smart Operations",use_container_width=True): set_active_page("smart"); st.rerun()
    with qa3:
        if st.button("▼ Add Mortality",use_container_width=True): set_active_page("mortality"); st.rerun()
    with qa4:
        if st.button("▶ Demo Mode",use_container_width=True): set_active_page("demo"); st.rerun()
    with qa5:
        if st.button("◈ Analytics",use_container_width=True): set_active_page("analytics"); st.rerun()

    if history:
        section_header("Recent Consultations")
        render_history_table(history[:5])

# ════════ SMART OPERATIONS ════════════════════════════════════════
elif page=="smart":
    render_hero()
    section_header("Smart Farm Operations Platform")
    history=get_history()
    render_daily_summary(history)
    st.markdown("<div style='margin-top:1rem;'></div>",unsafe_allow_html=True)
    render_smart_recommendations(history)
    st.markdown("<div style='margin-top:1rem;'></div>",unsafe_allow_html=True)
    render_smart_operations(history)
    st.markdown("<div style='margin-top:1rem;'></div>",unsafe_allow_html=True)
    render_performance_panel(history)
    st.markdown("<div style='margin-top:1rem;'></div>",unsafe_allow_html=True)
    t1,t2,t3=st.tabs(["Feed Planner","Mortality Intelligence","Vaccination Calendar"])
    with t1: render_feed_planner()
    with t2: render_mortality_intelligence()
    with t3: render_vaccination_calendar()

# ════════ CONSULTATION ════════════════════════════════════════════
elif page=="consultation":
    render_hero()
    left_col,right_col=st.columns([1,1.4],gap="large")
    with left_col:
        section_header("Describe Symptoms")
        prefill=st.session_state.pop("prefill_query","")
        sample_choice=st.selectbox("Load a sample",["— Select —"]+list(SAMPLE_QUERIES.keys()),index=0,label_visibility="collapsed")
        if sample_choice!="— Select —": prefill=SAMPLE_QUERIES[sample_choice]
        observation=st.text_area("Describe what you observed",value=prefill,
            placeholder="Describe symptoms in detail. Include bird count, age, and duration.",height=200)
        tts_enabled=st.toggle("Enable Voice Response",value=st.session_state.get("tts_enabled",False))
        st.session_state["tts_enabled"]=tts_enabled
        if st.button("Analyze Case",use_container_width=True):
            if not observation or not observation.strip(): st.warning("Please describe your observations.")
            else: run_pipeline_with_progress(observation.strip(),show_tts=tts_enabled)
        st.markdown("<p style='font-size:0.75rem;color:var(--text-300);margin-top:0.4rem;'>Include specific symptoms, bird count, age, and duration.</p>",unsafe_allow_html=True)
        section_header("Consultation History"); render_history_table(get_history()[:8])
    with right_col:
        section_header("Assessment")
        result=get_last_result()
        if result is None: render_empty_assessment()
        else: render_assessment(result)

# ════════ VOICE ═══════════════════════════════════════════════════
elif page=="voice":
    render_hero(); section_header("Voice Input")
    st.markdown('<div class="about-section"><h3>Speak Your Observations</h3><p>Record offline using Whisper. English provides best accuracy.</p></div>',unsafe_allow_html=True)
    col1,col2=st.columns([1,1],gap="large")
    with col1:
        language=st.selectbox("Language",["English","Hausa","Yoruba","Igbo"])
        lang_code={"English":"en","Hausa":"ha","Yoruba":"yo","Igbo":"ig"}[language]
        duration=st.slider("Duration (s)",5,20,8)
        tts_voice=st.toggle("Read response aloud",False)
        if st.button("◎ Record Voice Input",use_container_width=True):
            vs=st.empty()
            try:
                from voice.stt import record_and_transcribe
                vs.markdown('<div style="background:#EFF6FF;border-left:4px solid #1D4ED8;border-radius:8px;padding:0.9rem;color:#1D4ED8;">◎ Listening...</div>',unsafe_allow_html=True)
                text,error=record_and_transcribe(duration_seconds=duration,language=lang_code)
                if error: vs.error(error)
                elif not text: vs.warning("No speech detected.")
                else:
                    vs.markdown(f'<div style="background:#EEF7EF;border-left:4px solid #4A7C59;border-radius:8px;padding:0.9rem;color:#2D6A4F;">&#10003; {text}</div>',unsafe_allow_html=True)
                    time.sleep(1); vs.empty()
                    st.session_state["prefill_query"]=text; st.session_state["tts_enabled"]=tts_voice
                    set_active_page("consultation"); st.rerun()
            except Exception: vs.error("Voice input unavailable. Please type instead.")
    with col2:
        st.markdown('<div class="about-section"><h3>Steps</h3><ol style="font-size:0.875rem;line-height:1.8;padding-left:1.1rem;"><li>Select language</li><li>Set duration</li><li>Click Record</li><li>Speak clearly</li><li>Review transcript</li></ol></div>',unsafe_allow_html=True)

# ════════ DEMO ════════════════════════════════════════════════════
elif page=="demo":
    render_hero()
    def on_demo(q):
        st.session_state["prefill_query"]=q; set_active_page("consultation"); st.rerun()
    render_demo_page(on_select_case=on_demo)

# ════════ OTHER PAGES ═════════════════════════════════════════════
elif page=="analytics":   render_hero(); render_analytics_page()
elif page=="livestock":   render_livestock_page()
elif page=="mortality":   render_mortality_page()
elif page=="feed":        render_feed_page()
elif page=="medication":  render_medication_page()
elif page=="vaccination": render_vaccination_page()
elif page=="eggs":        render_egg_page()
elif page=="history":     render_history_page()
elif page=="knowledge":   render_knowledge_base_page()
elif page=="statistics":  render_statistics_page()
elif page=="about":       render_about_page()