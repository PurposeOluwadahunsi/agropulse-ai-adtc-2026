"""PDF report export using reportlab."""
from __future__ import annotations
import io
from datetime import datetime
from typing import Any

def generate_pdf_report(result: dict[str, Any]) -> bytes:
    """
    Generate a professional PDF consultation report.
    Returns PDF bytes ready for st.download_button.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError:
        raise RuntimeError("reportlab is not installed. Run: pip install reportlab")

    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    GREEN  = colors.HexColor("#1A3C2E")
    DGREEN = colors.HexColor("#2D6A4F")
    AMBER  = colors.HexColor("#D97706")
    RED    = colors.HexColor("#991B1B")
    LGREY  = colors.HexColor("#F8F6F1")
    BORDER = colors.HexColor("#E5E7EB")

    def h1(text):   return Paragraph(text, ParagraphStyle("h1", fontSize=20, textColor=GREEN, spaceAfter=4, fontName="Helvetica-Bold"))
    def h2(text):   return Paragraph(text, ParagraphStyle("h2", fontSize=11, textColor=DGREEN, spaceAfter=3, fontName="Helvetica-Bold", spaceBefore=10))
    def body(text): return Paragraph(str(text), ParagraphStyle("body", fontSize=9, textColor=colors.HexColor("#374151"), spaceAfter=3, leading=14))
    def small(text):return Paragraph(str(text), ParagraphStyle("small", fontSize=8, textColor=colors.HexColor("#6B7280"), spaceAfter=2))
    def hr():       return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=8, spaceBefore=4)

    sev      = (result.get("severity") or "unknown").upper()
    sev_col  = RED if sev == "CRITICAL" else AMBER if sev == "MODERATE" else DGREEN
    disease  = result.get("disease_name") or "No match"
    conf     = result.get("confidence", "none").capitalize()
    ts       = datetime.now().strftime("%Y-%m-%d %H:%M")
    symptoms = ", ".join(result.get("matched_symptoms") or []) or "None matched"
    sources  = ", ".join(result.get("rag_sources") or []) or "vetdb.json"

    # Header
    story += [h1("AgroPulse AI"), Spacer(1, 6), hr()]

    # Meta table
    meta = [["Report Date", ts], ["Consultation ID", f"Log #{result.get('log_id', '—')}"], ["Severity", sev], ["Confidence", conf]]
    t    = Table(meta, colWidths=[4*cm, 13*cm])
    t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 9), ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#6B7280")), ("TEXTCOLOR", (1,0), (1,-1), colors.HexColor("#111827")), ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("ROWBACKGROUNDS", (0,0), (-1,-1), [LGREY, colors.white]), ("BOX", (0,0), (-1,-1), 0.5, BORDER), ("GRID", (0,0), (-1,-1), 0.25, BORDER), ("TOPPADDING", (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4)]))
    story += [t, Spacer(1, 8)]

    # Possible disease
    story += [h2("Possible Disease"), body(f"{disease} — Severity: {sev}"), hr()]

    # Symptoms
    story += [h2("Reported Symptoms"), body(result.get("query", "—")), small(f"Matched symptoms: {symptoms}"), hr()]

    # AI Assessment
    ai_text = (result.get("ai_response") or "No AI response generated.").replace("\n", "<br/>")
    story  += [h2("AI Assessment"), body(ai_text[:2000]), hr()]

    # Farm Risk
    from ui.risk import compute_risk_score
    risk = compute_risk_score(result)
    reasons_text = " | ".join(risk["reasons"])
    story += [h2(f"Farm Risk Assessment {risk['score']}/100 ({risk['level']})"), body(reasons_text), hr()]

    # Immediate Actions
    if result.get("first_aid"):
        story += [h2("Immediate Actions"), body(result["first_aid"]), hr()]

    # Biosecurity
    biosec = result.get("biosecurity") or []
    if biosec:
        story += [h2("Biosecurity Measures")]
        for b in biosec:
            story.append(body(f"• {b}"))
        story.append(hr())

    # Vet recommendation
    wtc = result.get("when_to_call_vet") or ("Consult a veterinarian immediately." if result.get("vet_referral") else "Veterinary consultation is recommended.")
    story += [h2("Veterinary Recommendation"), body(wtc), hr()]

    # Sources
    story += [h2("Knowledge Sources"), body(sources), hr()]

    # Disclaimer
    story += [
        h2("Responsible AI Disclaimer"),
        body("AgroPulse AI is a decision-support tool only. This report does not constitute a confirmed veterinary diagnosis. "
             "All assessments describe possible conditions based on reported symptoms, rule-based triage, and retrieval-augmented generation "
             "from trusted veterinary references (FAO, OIE, NVRI, Merck). A licensed veterinarian must be consulted before "
             "administering any treatment."),
        Spacer(1, 8),
        small(f"Generated by AgroPulse AI"),
    ]

    doc.build(story)
    return buf.getvalue()





