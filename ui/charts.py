from __future__ import annotations
from typing import Any
import streamlit as st

def _no_data(msg: str = "No data available yet.") -> None:
    st.markdown(
        f'<div class="empty-state" style="padding:1.5rem;"><div class="es-title">No Data</div>'
        f'<div class="es-body">{msg}</div></div>', unsafe_allow_html=True)

def chart_disease_frequency(breakdown: dict[str, int]) -> None:
    if not breakdown:
        _no_data("Run consultations to see disease frequency."); return
    try:
        import plotly.graph_objects as go
        diseases = list(breakdown.keys()); counts = list(breakdown.values())
        fig = go.Figure(go.Bar(x=counts, y=diseases, orientation='h',
            marker_color='#2D6A4F', text=counts, textposition='outside'))
        fig.update_layout(margin=dict(l=0,r=20,t=10,b=0), height=max(200, len(diseases)*40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=12)))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        for d,c in sorted(breakdown.items(), key=lambda x:x[1], reverse=True):
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid var(--border);font-size:0.84rem;"><span>{d}</span><strong>{c}</strong></div>', unsafe_allow_html=True)

def chart_consultation_trend(entries: list[dict[str, Any]]) -> None:
    if not entries:
        _no_data("No consultation history to display."); return
    try:
        import plotly.graph_objects as go
        from collections import Counter
        dates = [e["timestamp"][:10] for e in entries if e.get("timestamp")]
        counts = Counter(dates)
        sorted_dates = sorted(counts.keys())
        fig = go.Figure(go.Scatter(x=sorted_dates, y=[counts[d] for d in sorted_dates],
            mode='lines+markers', line=dict(color='#2D6A4F', width=2),
            marker=dict(size=6, color='#4A7C59'), fill='tozeroy',
            fillcolor='rgba(74,124,89,0.1)'))
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=220,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#E5E7EB'))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        _no_data("Install plotly: pip install plotly")

def chart_severity_pie(entries: list[dict[str, Any]]) -> None:
    if not entries:
        _no_data("No data for severity distribution."); return
    try:
        import plotly.graph_objects as go
        from collections import Counter
        sevs = [e.get("severity") or "unknown" for e in entries if e.get("disease_hit")]
        if not sevs: _no_data("No matched diseases yet."); return
        counts = Counter(sevs)
        colours = {"critical":"#DC2626","moderate":"#D97706","low":"#2D6A4F","unknown":"#9CA3AF"}
        labels = list(counts.keys()); values = list(counts.values())
        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.4,
            marker_colors=[colours.get(l,"#9CA3AF") for l in labels],
            textinfo='label+percent'))
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=240,
            paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        _no_data("Install plotly: pip install plotly")

def chart_risk_trend(entries: list[dict[str, Any]]) -> None:
    """Plot farm risk scores over time using proxy scoring from history entries."""
    if not entries:
        _no_data("No risk data available yet."); return
    try:
        import plotly.graph_objects as go
        from ui.analytics import _entry_risk
        dated = [(e["timestamp"][:10], _entry_risk(e)) for e in entries if e.get("timestamp")]
        if not dated: _no_data(); return
        dated.sort(key=lambda x: x[0])
        dates = [d[0] for d in dated]; scores = [d[1] for d in dated]
        fig = go.Figure(go.Scatter(x=dates, y=scores, mode='lines+markers',
            line=dict(color='#D97706', width=2), marker=dict(size=6, color='#D97706')))
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=220,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0,105], showgrid=True, gridcolor='#E5E7EB'),
            xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        _no_data("Install plotly: pip install plotly")

def chart_consultation_scatter(entries: list[dict[str, Any]]) -> None:
    if not entries:
        _no_data("No consultations to display."); return
    try:
        import plotly.express as px
        import pandas as pd
        rows = [{"Date": e["timestamp"][:10], "Disease": e.get("disease_hit") or "No match",
                 "Severity": e.get("severity") or "unknown"}
                for e in entries if e.get("timestamp")]
        if not rows: _no_data(); return
        df = pd.DataFrame(rows)
        col_map = {"critical":"#DC2626","moderate":"#D97706","low":"#2D6A4F","unknown":"#9CA3AF"}
        fig = px.scatter(df, x="Date", y="Disease", color="Severity",
                         color_discrete_map=col_map, height=300)
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        _no_data("Install plotly and pandas: pip install plotly pandas")