"""
Seitenmodul für Gerätewartung
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
    """Rendert die Gerätewartung-Seite"""
    st.markdown("### Gerätewartungs-Dringlichkeitsanalyse")
    
    devices = db.get_device_maintenance_urgencies()
    
    if devices:
        # Dringlichkeitszusammenfassung
        high_urgency = len([d for d in devices if d['urgency_level'] in ['high', 'hoch']])
        medium_urgency = len([d for d in devices if d['urgency_level'] in ['medium', 'mittel']])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Geräte mit hoher Dringlichkeit", high_urgency, delta=None)
        with col2:
            st.metric("Geräte mit mittlerer Dringlichkeit", medium_urgency, delta=None)
        with col3:
            st.metric("Gesamtanzahl Geräte", len(devices))

        st.markdown("---")
        
        # Gerätetabelle anzeigen
        st.markdown("#### Gerätewartungsstatus")
        st.markdown("")  # Abstand
        
        # Mapping für Gerätetypen ins Deutsche
        device_type_map = {
            'Imaging': 'Bildgebung',
            'Life Support': 'Lebensunterstützung',
            'Emergency': 'Notfall',
            'Monitoring': 'Überwachung',
            'Therapy': 'Therapie',
            'Surgical': 'Chirurgisch',
            'Diagnostic': 'Diagnostik',
            'Other': 'Andere',
        }
        # Mapping für Dringlichkeitsstufen ins Deutsche
        urgency_level_map = {'high': 'hoch', 'medium': 'mittel', 'low': 'niedrig', 'hoch': 'hoch', 'mittel': 'mittel', 'niedrig': 'niedrig'}
        urgency_label_map = {'hoch': 'HOCHE DRINGLICHKEIT', 'mittel': 'MITTLERE DRINGLICHKEIT', 'niedrig': 'GERINGE DRINGLICHKEIT'}
        
        # Importiere Dringlichkeitsberechnung und max hours
        from utils import get_max_usage_hours
        
        # Mapping für Abteilungsnamen ins Deutsche
        department_map = {
            'Radiology': 'Radiologie',
            'ER': 'Notaufnahme',
            'ICU': 'Intensivstation',
            'Cardiology': 'Kardiologie',
            'Surgery': 'Chirurgie',
            'General Ward': 'Allgemeinstation',
            'Neurology': 'Neurologie',
            'Pediatrics': 'Pädiatrie',
            'Oncology': 'Onkologie',
            'Orthopedics': 'Orthopädie',
            'Maternity': 'Geburtshilfe',
            'Other': 'Andere',
        }
        
        for device in devices:
            # Berechne days_until_due aus next_maintenance_due
            days_until_due = None
            if device.get('next_maintenance_due'):
                try:
                    if isinstance(device['next_maintenance_due'], str):
                        next_due = datetime.strptime(device['next_maintenance_due'], '%Y-%m-%d')
                    else:
                        next_due = device['next_maintenance_due']
                    days_until_due = (next_due - datetime.now()).days
                except:
                    days_until_due = None
            
            # Berechne Tage seit letzter Wartung
            days_since_last = None
            last_maintenance_str = None
            if device.get('last_maintenance'):
                try:
                    if isinstance(device['last_maintenance'], str):
                        last_maintenance_date = datetime.strptime(device['last_maintenance'], '%Y-%m-%d')
                    else:
                        last_maintenance_date = device['last_maintenance']
                    days_since_last = (datetime.now() - last_maintenance_date).days
                    last_maintenance_str = last_maintenance_date.strftime('%d.%m.%Y')
                except:
                    pass
            
            # Betriebszeit seit letzter Wartung
            usage_hours = device.get('usage_hours', 0)
            max_usage_hours = get_max_usage_hours(device.get('device_type', ''))
            usage_hours_display = f"{usage_hours:,} h"
            if max_usage_hours > 0:
                usage_hours_display += f" / {max_usage_hours:,} h"
            
            # Berechne empfohlenes Wartungsfenster basierend auf days_until_due
            if days_until_due is not None:
                if days_until_due < 0:
                    recommended_window = 'Überfällig'
                elif days_until_due <= 3:
                    recommended_window = 'Innerhalb von 3 Tagen'
                elif days_until_due <= 7:
                    recommended_window = 'Innerhalb von 1 Woche'
                elif days_until_due <= 14:
                    recommended_window = 'Innerhalb von 2 Wochen'
                elif days_until_due <= 28:
                    recommended_window = 'Innerhalb von 4 Wochen'
                else:
                    recommended_window = 'Bald'
            else:
                recommended_window = 'Nicht verfügbar'
            
            urgency_level_de = urgency_level_map.get(device.get('urgency_level', ''), device.get('urgency_level', ''))
            urgency_color = get_severity_color(urgency_level_de)
            urgency_badge = render_badge(urgency_label_map.get(urgency_level_de, urgency_level_de.upper()), urgency_level_de)
            device_type_de = device_type_map.get(device.get('device_type', ''), device.get('device_type', ''))
            department_de = department_map.get(device.get('department', ''), device.get('department', ''))
            
            days_display = f"{days_until_due} Tage" if days_until_due is not None else "N/V"
            last_maintenance_display = f"{last_maintenance_str} (vor {days_since_last} Tagen)" if last_maintenance_str and days_since_last is not None else (last_maintenance_str if last_maintenance_str else "N/V")
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {urgency_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="display: grid; grid-template-columns: 1.5fr 1fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{device.get('device_type', 'N/V')}</div>
                        <div style="font-size: 0.75rem; color: #6b7280;">{device.get('device_id', 'N/V')} • {department_de}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Gerätetyp</div>
                        <div style="font-weight: 600; color: #1f2937;">{device_type_de}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Letzte Wartung</div>
                        <div style="font-weight: 600; color: #1f2937; font-size: 0.875rem;">{last_maintenance_display}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Betriebszeit</div>
                        <div style="font-weight: 600; color: #1f2937; font-size: 0.875rem;">{usage_hours_display}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Tage bis fällig</div>
                        <div style="font-weight: 600; color: {urgency_color};">{days_display}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Empfohlenes Wartungsfenster</div>
                        <div style="font-weight: 600; color: #667eea; font-size: 0.875rem;">{recommended_window}</div>
                    </div>
                    <div>
                        {urgency_badge}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Dringlichkeitsverteilung chart
        st.markdown("---")
        st.markdown("### Dringlichkeitsverteilung")
        df_dev = pd.DataFrame(devices)
        urgency_counts = df_dev['urgency_level'].value_counts()
        
        # Map German urgency levels to display names for pie chart
        urgency_label_map_chart = {'high': 'Hoch', 'medium': 'Mittel', 'low': 'Niedrig', 'hoch': 'Hoch', 'mittel': 'Mittel', 'niedrig': 'Niedrig'}
        urgency_display_names = [urgency_label_map_chart.get(name, name) for name in urgency_counts.index]
        
        fig = px.pie(
            values=urgency_counts.values,
            names=urgency_display_names,
            color=urgency_counts.index,
            color_discrete_map={
                'high': '#DC2626',
                'medium': '#F59E0B',
                'low': '#10B981',
                'hoch': '#DC2626',
                'mittel': '#F59E0B',
                'niedrig': '#10B981'
            }
        )
        fig.update_layout(
            height=300,
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🔧", "Keine Gerätedaten verfügbar", "Gerätewartungsdaten werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)
