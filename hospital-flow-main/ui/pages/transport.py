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
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            status_filter = st.selectbox("Nach Status filtern", ["Alle", "Ausstehend", "In Bearbeitung", "Abgeschlossen"], key="transport_status")
        with col_filter2:
            type_filter = st.selectbox("Nach Typ filtern", ["Alle", "Inventar", "Patient"], key="transport_type")
        
        status_filter_map = {
            "Alle": None,
            "Ausstehend": ["pending", "ausstehend"],
            "In Bearbeitung": ["in_progress", "in_bearbeitung"],
            "Abgeschlossen": ["completed", "abgeschlossen"]
        }
        filtered_transport = transport
        if status_filter != "Alle":
            filtered_transport = [t for t in filtered_transport if t['status'] in status_filter_map[status_filter]]
        if type_filter != "Alle":
            if type_filter == "Inventar":
                filtered_transport = [t for t in filtered_transport if t.get('related_entity_type') == 'inventory_order']
            elif type_filter == "Patient":
                filtered_transport = [t for t in filtered_transport if t.get('related_entity_type') == 'patient_transfer' or t.get('request_type') == 'patient']

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
        
        # Zeige alle Transportanfragen
        if filtered_transport:
            st.markdown("### Alle Transportanfragen")
            for trans in filtered_transport:
                _render_transport_card(trans, db)
            st.markdown("---")
        
        # Gruppiere Transporte nach Status
        running_transports = [t for t in filtered_transport if t['status'] in ['in_progress', 'in_bearbeitung']]
        planned_transports = [t for t in filtered_transport if t['status'] in ['pending', 'ausstehend']]
        completed_transports = [t for t in filtered_transport if t['status'] in ['completed', 'abgeschlossen']]
        
        # Zeige zuerst laufende Transporte
        if running_transports:
            st.markdown("### 🚑 Laufende Transporte")
            for trans in running_transports:
                _render_transport_card(trans, db)
            st.markdown("---")
        
        # Dann geplante Transporte
        if planned_transports:
            st.markdown("### 📋 Geplante Transporte")
            for trans in planned_transports:
                _render_transport_card(trans, db)
            st.markdown("---")
        
        # Dann abgeschlossene Transporte
        if completed_transports:
            st.markdown("### ✅ Abgeschlossene Transporte")
            for trans in completed_transports:
                _render_transport_card(trans, db)
        
        # Fallback: Wenn keine Transporte in den gefilterten Ergebnissen sind
        if not running_transports and not planned_transports and not completed_transports:
            st.info("Keine Transporte entsprechen den ausgewählten Filtern.")
    
    else:
        st.markdown(render_empty_state("🚑", "Keine Transportanfragen", "Zurzeit keine aktiven Transportanfragen"), unsafe_allow_html=True)


def _render_transport_card(trans, db):
    """Rendert eine einzelne Transportkarte"""
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
    
    # Hole Details basierend auf related_entity_type
    details_info = ""
    related_type = trans.get('related_entity_type')
    if related_type == 'inventory_order':
        # Hole Bestellungs-Details
        order_id = trans.get('related_entity_id')
        if order_id:
            # Try to get inventory order - use method if available, otherwise query directly
            order = None
            try:
                if hasattr(db, 'get_inventory_orders'):
                    orders = db.get_inventory_orders()
                    order = next((o for o in orders if o['id'] == order_id), None)
                else:
                    # Fallback: query directly from database
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT quantity, item_name FROM inventory_orders WHERE id = ?
                    """, (order_id,))
                    result = cursor.fetchone()
                    conn.close()
                    if result:
                        order = {'quantity': result[0], 'item_name': result[1]}
            except Exception:
                pass
            if order:
                details_info = f" • <strong>{order['quantity']}x {order['item_name']}</strong>"
    elif related_type == 'patient_transfer':
        details_info = " • <strong>Patiententransfer</strong>"
    
    # Geplante Startzeit für geplante Transporte
    planned_time_info = ""
    if trans['status'] in ['pending', 'ausstehend']:
        planned_start = trans.get('planned_start_time')
        if planned_start:
            try:
                if isinstance(planned_start, str):
                    planned_time = datetime.fromisoformat(planned_start.replace('Z', '+00:00'))
                else:
                    planned_time = planned_start
                
                # Formatiere Datum und Uhrzeit
                if planned_time.tzinfo:
                    planned_time = planned_time.replace(tzinfo=None)
                formatted_date = planned_time.strftime('%d.%m.%Y')
                formatted_time = planned_time.strftime('%H:%M')
                planned_time_info = f" • Geplant: <span style='color: {status_color}; font-weight: 600;'>{formatted_date} um {formatted_time} Uhr</span>"
            except:
                pass
    
    # Erwartete Abschlusszeit für in_progress Transporte
    completion_info = ""
    if trans['status'] in ['in_progress', 'in_bearbeitung']:
        expected_completion = trans.get('expected_completion_time')
        if expected_completion:
            try:
                if isinstance(expected_completion, str):
                    completion_time = datetime.fromisoformat(expected_completion.replace('Z', '+00:00'))
                else:
                    completion_time = expected_completion
                
                now = datetime.now(completion_time.tzinfo) if completion_time.tzinfo else datetime.now()
                remaining = (completion_time - now).total_seconds() / 60
                if remaining > 0:
                    completion_info = f" • Erwartete Ankunft in: <span style='color: {status_color}; font-weight: 600;'>{format_duration_minutes(int(remaining))}</span>"
                else:
                    completion_info = " • Erwartete Ankunft: <span style='color: #DC2626; font-weight: 600;'>Jetzt</span>"
            except:
                pass
    
    # Verzögerung/Stau anzeigen
    delay_info = ""
    delay_minutes = trans.get('delay_minutes')
    if delay_minutes and delay_minutes > 0:
        delay_info = f" • <span style='color: #DC2626;'>⚠️ Verzögerung: +{format_duration_minutes(delay_minutes)} (Stau)</span>"
    
    st.html(f"""
    <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 1;">
                <div>
                    <span class="badge" style="background: {priority_color}; color: white;">{priority_display}</span>
                    <span class="badge" style="background: {status_color}; color: white; margin-left: 0.5rem;">{status_display}</span>
                    <strong style="margin-left: 0.5rem;">{request_type_display}</strong>
                    {details_info}
                </div>
                <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">
                    {trans['from_location']} → {trans['to_location']}
                    {f"• Geschätzt: {format_duration_minutes(trans['estimated_time_minutes'])}" if trans['estimated_time_minutes'] else ""}
                    {f"• Tatsächlich: {format_duration_minutes(trans['actual_time_minutes'])}" if trans['actual_time_minutes'] else ""}
                    {planned_time_info}
                    {completion_info}
                    {delay_info}
                    • {format_time_ago(trans['timestamp'])}
                </div>
            </div>
        </div>
    </div>
    """)
