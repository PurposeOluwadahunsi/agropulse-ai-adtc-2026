"""
ui/demo.py  (Sprint 7 — new)

Demo Mode for AgroPulse AI.
Provides professionally written cases that judges can select and run
without typing. Each case triggers the full AI pipeline.
"""

from __future__ import annotations
import streamlit as st
from ui.navigation import set_active_page


DEMO_CASES = [
    {
        "id":       "newcastle",
        "title":    "Newcastle Disease",
        "subtitle": "Critical | Respiratory + Nervous Signs",
        "severity": "critical",
        "query": (
            "My chickens are gasping for air and some have twisted necks. "
            "A few are circling and cannot stand. I see green watery droppings. "
            "About 15 birds died this morning out of a flock of 200. "
            "The birds are 8 weeks old."
        ),
        "hint": "Classic presentation of Newcastle Disease with nervous signs.",
    },
    {
        "id":       "gumboro",
        "title":    "Gumboro Disease",
        "subtitle": "Critical | Digestive + Vent Picking",
        "severity": "critical",
        "query": (
            "My 3-week-old chicks have watery whitish diarrhoea. "
            "They huddle together and keep picking at their own vents. "
            "The vent feathers are soiled. They are trembling and reluctant to move. "
            "Mortality started 2 days ago and is increasing."
        ),
        "hint": "Vent-picking and white diarrhoea are distinguishing features of Gumboro.",
    },
    {
        "id":       "coccidiosis",
        "title":    "Coccidiosis",
        "subtitle": "Moderate | Bloody Droppings",
        "severity": "moderate",
        "query": (
            "I found blood in the droppings of my 4-week-old broiler chicks. "
            "The droppings are reddish-brown. Their combs are very pale. "
            "They are drooping their wings and huddling near the heat source. "
            "They have stopped eating."
        ),
        "hint": "Bloody droppings with pale comb strongly suggest cecal coccidiosis.",
    },
    {
        "id":       "cholera",
        "title":    "Fowl Cholera",
        "subtitle": "Critical | Sudden Death with Blue Comb",
        "severity": "critical",
        "query": (
            "Several adult laying hens died suddenly this morning. "
            "Their combs and wattles turned blue before death. "
            "The wattles are swollen. There is mucous discharge from the mouth. "
            "The remaining birds are breathing with difficulty."
        ),
        "hint": "Cyanosis and swollen wattles distinguish Fowl Cholera from Newcastle.",
    },
    {
        "id":       "crd",
        "title":    "Chronic Respiratory Disease",
        "subtitle": "Moderate | Slow-Spreading Respiratory Signs",
        "severity": "moderate",
        "query": (
            "My birds have been coughing and sneezing for the past two weeks. "
            "The cough is spreading slowly through the flock. "
            "Some birds have foamy discharge from their eyes. "
            "Feed conversion has reduced and the birds are not growing well."
        ),
        "hint": "Slow spread and foamy eye discharge point to Mycoplasma (CRD).",
    },
    {
        "id":       "eds",
        "title":    "Egg Drop Syndrome",
        "subtitle": "Low | Egg Quality Loss in Healthy Flock",
        "severity": "low",
        "query": (
            "Egg production dropped by 30% in the last week. "
            "Many eggs have no shells at all or very pale shells. "
            "Some eggs have watery whites. "
            "The birds appear healthy, are eating normally, and there is no mortality."
        ),
        "hint": "Healthy birds with shell-less eggs suggest Egg Drop Syndrome (EDS-76).",
    },
]


def render_demo_page(on_select_case) -> None:
    """
    Render the Demo Mode page.

    Args:
        on_select_case: Callback that receives the selected query string.
                        Called when the user clicks Run Demo for a case.
    """
    from ui.components import section_header, sev_badge

    section_header("Demo Mode")

    st.markdown(
        '<div class="about-section" style="margin-bottom:1rem;">'
        '<h3>Experience AgroPulse AI</h3>'
        '<p>Select a pre-written case below to see AgroPulse AI analyse a real-world '
        'poultry health scenario. No typing required — click <strong>Run This Case</strong> '
        'and the full AI pipeline will run automatically.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(2)

    for i, case in enumerate(DEMO_CASES):
        col = cols[i % 2]
        with col:
            badge    = sev_badge(case["severity"])
            severity = case["severity"]
            card_cls = severity

            st.markdown(
                f'<div class="assessment-card {card_cls}" style="min-height:140px;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:flex-start;margin-bottom:0.4rem;">'
                f'<div class="ac-value" style="font-size:0.95rem;">{case["title"]}</div>'
                f'{badge}'
                f'</div>'
                f'<div class="ac-body" style="font-size:0.78rem;color:var(--text-500);'
                f'margin-bottom:0.5rem;">{case["subtitle"]}</div>'
                f'<div class="ac-body" style="font-size:0.82rem;'
                f'font-style:italic;color:var(--text-700);">'
                f'&#8220;{case["hint"]}&#8221;</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if st.button(
                f"Run: {case['title']}",
                key=f"demo_{case['id']}",
                use_container_width=True,
            ):
                on_select_case(case["query"])