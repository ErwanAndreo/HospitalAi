"""
Seitenmodul für Transport
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
    """Rendert die Transport-Seite"""
    st.markdown("### Transportanfragen")
    
    transport = db.get_transport_requests()
    
    if transport:
        status_filter = st.selectbox("Nach Status filtern", ["Alle", "Ausstehend", "In Bearbeitung", "Abgeschlossen"], key="transport_status")

        status_filter_map = {
            "Alle": None,
            "Ausstehend": ["pending", "ausstehend"],
            "In Bearbeitung": ["in_progress", "in_bearbeitung"],
            "Abgeschlossen": ["completed", "abgeschlossen"]
        }
        filtered_transport = transport
        if status_filter != "Alle":
            filtered_transport = [t for t in transport if t['status'] in status_filter_map[status_filter]]

        # Zusammenfassende Kennzahlen
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ausstehend", len([t for t in transport if t['status'] in ['pending', 'ausstehend']]))
        with col2:
            st.metric("In Bearbeitung", len([t for t in transport if t['status'] in ['in_progress', 'in_bearbeitung']]))
        with col3:
            st.metric("Abgeschlossen", len([t for t in transport if t['status'] in ['completed', 'abgeschlossen']]))
        with col4:
            avg_time = sum([t['estimated_time_minutes'] or 0 for t in transport]) / len(transport) if transport else 0
            st.metric("Ø geschätzte Zeit", format_duration_minutes(int(avg_time)))

        st.markdown("---")
        
        # Transport table
        for trans in filtered_transport:
            priority_color = get_priority_color(trans['priority'])
            status_color = get_status_color(trans['status'])
            
            # Translate priority, status, and request_type to German
            priority_map = {'high': 'HOCH', 'medium': 'MITTEL', 'low': 'NIEDRIG', 'hoch': 'HOCH', 'mittel': 'MITTEL', 'niedrig': 'NIEDRIG'}
            status_map = {
                'pending': 'AUSSTEHEND',
                'in_progress': 'IN BEARBEITUNG',
                'completed': 'ABGESCHLOSSEN',
                'ausstehend': 'AUSSTEHEND',
                'in_bearbeitung': 'IN BEARBEITUNG',
                'abgeschlossen': 'ABGESCHLOSSEN'
            }
            request_type_map = {
                'patient': 'Patient',
                'equipment': 'Gerät',
                'specimen': 'Probe',
                'Patient': 'Patient',
                'Gerät': 'Gerät',
                'Probe': 'Probe'
            }
            priority_display = priority_map.get(trans['priority'].lower(), trans['priority'].upper())
            status_display = status_map.get(trans['status'].lower().replace(' ', '_'), trans['status'].replace('_', ' ').upper())
            request_type_display = request_type_map.get(trans['request_type'], trans['request_type'].title())
            
            st.html(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="badge" style="background: {priority_color}; color: white;">{priority_display}</span>
                        <span class="badge" style="background: {status_color}; color: white; margin-left: 0.5rem;">{status_display}</span>
                        <strong style="margin-left: 0.5rem;">{request_type_display}</strong>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">
                            {trans['from_location']} → {trans['to_location']}
                            {f"• Geschätzt: {format_duration_minutes(trans['estimated_time_minutes'])}" if trans['estimated_time_minutes'] else ""}
                            {f"• Tatsächlich: {format_duration_minutes(trans['actual_time_minutes'])}" if trans['actual_time_minutes'] else ""}
                            • {format_time_ago(trans['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """)
    else:
        st.markdown(render_empty_state("🚑", "Keine Transportanfragen", "Zurzeit keine aktiven Transportanfragen"), unsafe_allow_html=True)
