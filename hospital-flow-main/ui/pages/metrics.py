"""
Seitenmodul für Live-Metriken
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
    """Rendert die Live-Metriken-Seite"""
    st.markdown("### Live-Metriken")
    
    metrics = db.get_recent_metrics(20)
    if metrics:
        df = pd.DataFrame(metrics)
        # German translation for metric types
        metric_type_map = {
            'patient_count': 'Patientenzahl',
            'wait_time': 'Wartezeit',
            'occupancy': 'Auslastung',
            'throughput': 'Durchsatz',
            'waiting_count': 'Wartende Patienten',
            'ed_load': 'Notaufnahme-Auslastung',
            'or_load': 'OP-Auslastung',
            'staff_load': 'Personal-Auslastung',
            'transport_queue': 'Transport-Warteschlange',
            'rooms_free': 'Freie Räume',
            'beds_free': 'Freie Betten',
            # Bei Bedarf weitere hinzufügen
        }
        # Gruppieren nach Metrik-Typ
        metric_types = df['metric_type'].unique()
        cols = st.columns(3)
        # Unit translation
        unit_map = {
            'minutes': 'Minuten',
            'hours': 'Stunden',
            'patients': 'Patienten',
            'beds': 'Betten',
            'rooms': 'Räume'
        }
        for idx, metric_type in enumerate(metric_types[:6]):
            col_idx = idx % 3
            with cols[col_idx]:
                latest = df[df['metric_type'] == metric_type].iloc[0]
                label = metric_type_map.get(metric_type, metric_type.replace('_', ' ').title())
                # Fix units and formatting for specific metrics
                if metric_type in ['patient_count', 'waiting_count']:
                    unit = ''
                    value_str = f"{int(round(latest['value']))}"
                elif metric_type in ['occupancy', 'ed_load', 'or_load', 'staff_load']:
                    unit = '%'
                    value_str = f"{latest['value']:.1f} {unit}"
                elif metric_type == 'wait_time':
                    # Always show wait_time in minutes
                    unit = 'Minuten'
                    value_str = f"{latest['value']:.1f} {unit}"
                elif metric_type == 'throughput':
                    # Always show throughput as per hour
                    unit = 'pro Stunde'
                    value_str = f"{latest['value']:.1f} {unit}"
                else:
                    unit = latest.get('unit', '')
                    unit_de = unit_map.get(unit, unit)
                    value_str = f"{latest['value']:.1f} {unit_de}" if unit_de else f"{latest['value']:.1f}"
                st.metric(
                    label,
                    value_str,
                    delta=None
                )
        # Time series chart
        st.markdown("---")
        st.markdown("### Metrik-Trends")
        # Deutsche Beschriftungen in Selectbox verwenden
        metric_type_labels = [metric_type_map.get(mt, mt.replace('_', ' ').title()) for mt in metric_types]
        metric_type_label_map = dict(zip(metric_type_labels, metric_types))
        selected_label = st.selectbox("Metrik-Typ auswählen", metric_type_labels, key="metric_select")
        selected_metric = metric_type_label_map[selected_label]
        metric_data = df[df['metric_type'] == selected_metric].sort_values('timestamp')
        # German translation for department names
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
        if not metric_data.empty:
            label = metric_type_map.get(selected_metric, selected_metric.replace('_', ' ').title())
            # Abteilungsnamen für Plotting ins Deutsche mappen und als 'Abteilung' in Legende anzeigen
            metric_data = metric_data.copy()
            if 'department' in metric_data.columns:
                metric_data['Abteilung'] = metric_data['department'].map(lambda d: dept_map.get(d, d))
                color_col = 'Abteilung'
            else:
                color_col = 'department'
            fig = px.line(
                metric_data,
                x='timestamp',
                y='value',
                color=color_col,
                title=f"{label} Verlauf",
                markers=True
            )
            fig.update_layout(
                height=400,
                xaxis_title="Zeit",
                yaxis_title="Wert",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Metriken verfügbar")
