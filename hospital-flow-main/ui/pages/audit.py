"""
Seitenmodul für Prüfprotokoll
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import random
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from ui.components import render_badge, render_empty_state


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Prüfprotokoll-Seite"""
    st.markdown("### Prüfprotokoll")
    st.markdown("Alle Systemaktionen und Änderungen verfolgen")
    
    audit_log = db.get_audit_log(100)
    
    if audit_log:
        # Filteroptionen
        col1, col2 = st.columns(2)
        with col1:
            action_filter = st.selectbox(
                "Nach Aktion filtern",
                ["Alle"] + list(set([a['action_type'] for a in audit_log])),
                key="audit_action"
            )
        with col2:
            limit = st.slider("Anzahl der Einträge", 10, 100, 50, key="audit_limit")
        
        filtered_log = audit_log[:limit]
        if action_filter != "Alle":
            filtered_log = [a for a in filtered_log if a['action_type'] == action_filter]
        
        # Audit-Log-Tabelle
        st.markdown("---")
        for entry in filtered_log:
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #667eea;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span style="font-weight: 600; color: #1f2937;">{entry['action_type'].replace('_', ' ').title()}</span>
                            {f"<span style='color: #6b7280; font-size: 0.875rem;'>({entry['entity_type']} #{entry['entity_id']})</span>" if entry['entity_id'] else ""}
                        </div>
                        {f"<div style='color: #6b7280; font-size: 0.875rem;'>{entry['details']}</div>" if entry['details'] else ""}
                        <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem;">
                            {entry.get('user_role', 'system').title()} • {format_time_ago(entry['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("📝", "Keine Prüfprotokoll-Einträge", "Prüfprotokoll-Einträge werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)
