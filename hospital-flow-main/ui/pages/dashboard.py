"""
Seitenmodul für Dashboard
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
    """Rendert die Dashboard-Seite"""
    # Daten abrufen (gecacht, um Flackern zu vermeiden)
    alerts = get_cached_alerts()
    recommendations = get_cached_recommendations()
    transport = db.get_transport_requests()
    inventory = db.get_inventory_status()
    devices = db.get_device_maintenance_urgencies()
    predictions = db.get_predictions(15)
    
    # Simulierte Metriken abrufen (korreliert)
    sim_metrics = sim.get_current_metrics()
    
    # Kapazitätsdaten aus Simulation berechnen (konsistent mit Simulationsdaten)
    capacity = db.get_capacity_from_simulation(sim_metrics)
    
    # Dashboard-Metriken mit Simulation berechnen
    # ED Load (from simulation)
    ed_load = sim_metrics['ed_load']
    ed_severity, ed_hint = get_metric_severity_for_load(ed_load)
    
    # Waiting count (from simulation - correlated with ED load)
    waiting_count = int(sim_metrics['waiting_count'])
    waiting_severity, waiting_hint = get_metric_severity_for_count(waiting_count, {'critical': 20, 'watch': 10})
    
    # Beds free (from simulation - konsistent mit Kapazitätsdaten)
    beds_free = int(sim_metrics['beds_free'])
    total_beds = sum([c['total_beds'] for c in capacity]) if capacity else 100
    beds_severity, beds_hint = get_metric_severity_for_free(beds_free, total_beds)
    
    # Staff load (from simulation - correlated with ED load)
    staff_load = sim_metrics['staff_load']
    staff_severity, staff_hint = get_metric_severity_for_load(staff_load)
    
    # Rooms free (from simulation - correlated with beds free)
    rooms_free = int(sim_metrics['rooms_free'])
    total_rooms = db.get_total_rooms()
    rooms_severity, rooms_hint = get_metric_severity_for_free(rooms_free, total_rooms)
    
    # OR load (from simulation)
    or_load = sim_metrics['or_load']
    or_severity, or_hint = get_metric_severity_for_load(or_load)
    
    # Transport queue (from simulation - delayed correlation with ED load)
    transport_queue = int(sim_metrics['transport_queue'])
    transport_severity, transport_hint = get_metric_severity_for_count(transport_queue, {'critical': 8, 'watch': 5})
    
    # Inventar-/Gerätedringlichkeit (Anzahl dringender Artikel)
    low_inventory = len([i for i in inventory if i['current_stock'] < i['min_threshold']])
    high_urgency_devices = len([d for d in devices if d['urgency_level'] in ['high', 'hoch']])
    urgency_count = low_inventory + high_urgency_devices
    urgency_severity, urgency_hint = get_metric_severity_for_count(urgency_count, {'critical': 5, 'watch': 3})
    
    # Auf aktive Auslastungsereignisse prüfen
    active_surges = [e for e in sim.active_events if e['type'] == 'surge']
    if active_surges:
        surge = active_surges[0]
        from datetime import timezone
        elapsed = (datetime.now(timezone.utc) - surge['start_time']).total_seconds() / 60
        remaining = max(0, surge['duration_minutes'] - elapsed)
        st.warning(f"⚠️ **Aktives Auslastungsereignis**: Noch {remaining:.0f} Minuten verbleibend (Intensität: {surge['intensity']:.1f})")
        st.markdown("")  # Spacing
    
    # Live Status Section
    st.markdown("### Live Status")
    st.markdown("")  # Abstand
    
    # 8 Metric Cards in 4x2 grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        severity_color = get_severity_color(ed_severity)
        badge_html = render_badge(ed_hint, ed_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Notaufnahme-Auslastung</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{ed_load:.0f}%</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        severity_color = get_severity_color(waiting_severity)
        badge_html = render_badge(waiting_hint, waiting_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Wartende Patienten</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{waiting_count}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        severity_color = get_severity_color(beds_severity)
        badge_html = render_badge(beds_hint, beds_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Freie Betten</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{beds_free}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = get_severity_color(staff_severity)
        badge_html = render_badge(staff_hint, staff_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Personal-Auslastung</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{staff_load:.0f}%</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Zweite Zeile der Metrik-Karten
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        severity_color = get_severity_color(rooms_severity)
        badge_html = render_badge(rooms_hint, rooms_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Freie Räume</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{rooms_free}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        severity_color = get_severity_color(or_severity)
        badge_html = render_badge(or_hint, or_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">OP-Auslastung</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{or_load:.0f}%</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        severity_color = get_severity_color(transport_severity)
        badge_html = render_badge(transport_hint, transport_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Transport-Warteschlange</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{transport_queue}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        severity_color = get_severity_color(urgency_severity)
        badge_html = render_badge(urgency_hint, urgency_severity)
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: {severity_color};">
            <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 0.75rem;">Bestands-/Gerätedringlichkeit</div>
            <div style="font-size: 2.5rem; font-weight: 700; color: #111827; margin: 0.75rem 0; letter-spacing: -0.02em;">{urgency_count}</div>
            <div style="margin-top: 1rem;">
                {badge_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Diagramme und Ausblick-Panel
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Diagramm-Abschnitt
        st.markdown("### Trends (Letzte 60 Minuten)")
        st.markdown("")  # Spacing
        
        # Historische Daten aus Simulation abrufen
        waiting_history = sim.get_metric_history('waiting_count', 60)
        ed_history = sim.get_metric_history('ed_load', 60)
        
        # In DataFrames konvertieren
        df_waiting = pd.DataFrame(waiting_history)
        df_waiting['timestamp'] = pd.to_datetime(df_waiting['timestamp'])
        
        df_ed = pd.DataFrame(ed_history)
        df_ed['timestamp'] = pd.to_datetime(df_ed['timestamp'])
        
        # Warteschlangen-Diagramm
        fig_waiting = px.line(
            df_waiting,
            x='timestamp',
            y='value',
            title="Wartende Anzahl",
            labels={'value': 'Anzahl', 'timestamp': ''}
        )
        fig_waiting.update_layout(
            height=250,
            margin=dict(l=40, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showline=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False, title=''),
            showlegend=False,
            font=dict(size=11)
        )
        fig_waiting.update_traces(line_color='#667eea', line_width=2.5, marker=dict(size=4))
        st.plotly_chart(fig_waiting, use_container_width=True)
        
        st.markdown("")  # Spacing
        
        # Notaufnahme-Auslastungs-Diagramm
        fig_ed = px.line(
            df_ed,
            x='timestamp',
            y='value',
            title="Notaufnahme-Auslastung",
            labels={'value': 'Auslastung %', 'timestamp': ''}
        )
        fig_ed.update_layout(
            height=250,
            margin=dict(l=40, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showline=False),
            yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False, range=[0, 100], title=''),
            showlegend=False,
            font=dict(size=11)
        )
        fig_ed.update_traces(line_color='#DC2626', line_width=2.5, marker=dict(size=4))
        st.plotly_chart(fig_ed, use_container_width=True)
    
    with col2:
        # Ausblick-Panel für nächste 15 Minuten
        st.markdown("### Ausblick: Nächste 15 Minuten")
        st.markdown("")  # Spacing
        
        # Top 3 vorhergesagte Engpässe abrufen
        bottleneck_predictions = []
        for pred in predictions:
            if pred['time_horizon_minutes'] <= 15:
                bottleneck_predictions.append(pred)
        
        # Nach vorhergesagtem Wert sortieren (absteigend) und Top 3 nehmen
        bottleneck_predictions.sort(key=lambda x: x['predicted_value'], reverse=True)
        top_bottlenecks = bottleneck_predictions[:3]
        
        # German translation for prediction types
        pred_type_map = {
            'patient_arrival': 'Patientenzugang',
            'bed_demand': 'Bettenbedarf',
            'resource_needed': 'Ressourcenbedarf',
            'waiting_count': 'Wartende Patienten',
            'ed_load': 'Notaufnahme-Auslastung',
            'or_load': 'OP-Auslastung',
            'staff_load': 'Personal-Auslastung',
            'transport_queue': 'Transport-Warteschlange',
            'rooms_free': 'Freie Räume',
            'beds_free': 'Freie Betten',
            # Bei Bedarf weitere hinzufügen
        }
        if top_bottlenecks:
            for i, bottleneck in enumerate(top_bottlenecks, 1):
                pred_type_key = bottleneck['prediction_type']
                pred_type = pred_type_map.get(pred_type_key, pred_type_key.replace('_', ' ').title())
                pred_value = bottleneck['predicted_value']
                pred_minutes = bottleneck['time_horizon_minutes']
                dept = bottleneck.get('department', 'N/A')
                # German translation for department names (add more as needed)
                dept_map = {
                    'ER': 'Notaufnahme',
                    'ICU': 'Intensivstation',
                    'Surgery': 'Chirurgie',
                    'General Ward': 'Allgemeinstation',
                    'Cardiology': 'Kardiologie',
                    'Neurology': 'Neurologie',
                    'Pediatrics': 'Pädiatrie',
                    'Oncology': 'Onkologie',
                    'Orthopedics': 'Orthopädie',
                    'Maternity': 'Geburtshilfe',
                    'Radiology': 'Radiologie',
                    'Other': 'Andere'
                }
                dept_de = dept_map.get(dept, dept)
                # German time string
                if pred_minutes == 1:
                    time_str = f'in {pred_minutes} Minute'
                else:
                    time_str = f'in {pred_minutes} Minuten'
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 3px solid #667eea; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="font-size: 0.875rem; font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">
                        {i}. {pred_type}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #667eea; margin: 0.25rem 0;">
                        {pred_value:.0f}
                    </div>
                    <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.5rem;">
                        {dept_de} • {time_str}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(render_empty_state("📊", "Keine vorhergesagten Engpässe", "System arbeitet im normalen Bereich"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Kürzliche Warnungen
    st.markdown("### Kürzliche Warnungen")
    st.markdown("")  # Abstand
    if alerts:
        severity_de_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
        for alert in alerts[:5]:
            severity_color = get_severity_color(alert['severity'])
            severity_de = severity_de_map.get(alert['severity'], alert['severity'])
            badge_html = render_badge(severity_de.upper(), alert['severity'])
            st.markdown(f"""
            <div class="info-card" style="border-left: 4px solid {severity_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                            {badge_html}
                            <strong style="color: #111827; font-size: 0.9375rem; font-weight: 600;">{alert['message']}</strong>
                        </div>
                        <div style="color: #6b7280; font-size: 0.8125rem; font-weight: 500;">
                            {alert.get('department', 'N/A')} • {format_time_ago(alert['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Keine aktiven Warnungen")
    
    # Ausstehende Empfehlungen
    st.markdown("### Ausstehende Empfehlungen")
    st.markdown("")  # Abstand
    if recommendations:
        priority_de_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig'}
        for rec in recommendations[:3]:
            priority_color = get_priority_color(rec['priority'])
            priority_de = priority_de_map.get(rec['priority'], rec['priority'])
            badge_html = render_badge(priority_de.upper(), rec['priority'])
            st.markdown(f"""
            <div class="info-card" style="border-left: 4px solid {priority_color};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                            {badge_html}
                            <strong style="color: #111827; font-size: 1rem; font-weight: 600;">{rec['title']}</strong>
                        </div>
                        <p style="color: #4b5563; margin-top: 0.5rem; margin-bottom: 0; line-height: 1.7; font-size: 0.9375rem;">{rec['description']}</p>
                        <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 1rem; font-weight: 500;">
                            {rec.get('department', 'N/A')} • {format_time_ago(rec['timestamp'])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("✅", "Keine ausstehenden Empfehlungen", "Alle Empfehlungen wurden überprüft"), unsafe_allow_html=True)
