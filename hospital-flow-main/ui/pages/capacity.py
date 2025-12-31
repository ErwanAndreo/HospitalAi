"""
Seitenmodul für Kapazitätsübersicht
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
    """Rendert die Kapazitätsübersicht-Seite"""
    st.markdown("### Kapazitätsübersicht")
    
    # Simulierte Metriken abrufen für konsistente Daten
    sim_metrics = sim.get_current_metrics()
    # Kapazitätsdaten aus Simulation berechnen (konsistent mit Dashboard)
    capacity = db.get_capacity_from_simulation(sim_metrics)
    
    if capacity:
        df_cap = pd.DataFrame(capacity)
        
        # Gesamte Kennzahlen
        gesamt_betten = df_cap['total_beds'].sum()
        belegte_betten = df_cap['occupied_beds'].sum()
        verfügbare_betten = df_cap['available_beds'].sum()
        gesamt_auslastung = belegte_betten / gesamt_betten if gesamt_betten > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Gesamtbetten", gesamt_betten)
        with col2:
            st.metric("Belegt", belegte_betten)
        with col3:
            st.metric("Verfügbar", verfügbare_betten)
        with col4:
            kapazitäts_status = calculate_capacity_status(gesamt_auslastung)
            st.metric("Gesamtauslastung", f"{kapazitäts_status['percentage']}%")

        st.markdown("---")
        
        # Department capacity cards
        # Mapping for department names (English to German)
        department_map = {
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
        for cap in capacity:
            cap_status = calculate_capacity_status(cap['utilization_rate'])
            dept_color = get_department_color(cap['department'])
            # Deutschen Abteilungsnamen verwenden, falls verfügbar
            german_dept = department_map.get(cap['department'], cap['department'])
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {cap_status['color']};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: {dept_color};">{german_dept}</h4>
                    <span class="badge" style="background: {cap_status['color']}; color: white;">{cap_status['status'].upper()}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Gesamt</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">{cap['total_beds']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Belegt</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #DC2626;">{cap['occupied_beds']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #6b7280; text-transform: uppercase;">Verfügbar</div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #10B981;">{cap['available_beds']}</div>
                    </div>
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.875rem; color: #6b7280;">Auslastung</span>
                        <span style="font-weight: 600; color: {cap_status['color']};">{cap_status['percentage']}%</span>
                    </div>
                    <div style="background: #e5e7eb; height: 12px; border-radius: 6px; overflow: hidden;">
                        <div style="background: {cap_status['color']}; height: 100%; width: {cap_status['percentage']}%;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
       # Capacity charts
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            # Mapping for department names (English to German)
            department_map = {
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
            # Deutsche Abteilungsspalte für Plotting hinzufügen
            df_cap['Abteilung'] = df_cap['department'].map(department_map).fillna(df_cap['department'])
            color_map = {department_map.get(dept, dept): get_department_color(dept) for dept in df_cap['department']}
            fig = px.bar(
                df_cap,
                x='Abteilung',
                y='utilization_rate',
                title="Auslastung nach Abteilung",
                color='Abteilung',
                color_discrete_map=color_map,
                labels={'utilization_rate': 'Auslastung (%)', 'Abteilung': 'Abteilung'}
            )
            fig.update_layout(
                height=400,
                yaxis=dict(
                    tickformat='.0%',
                    title='Auslastung (%)'
                ),
                xaxis=dict(title='Abteilung'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure(data=[
                go.Bar(name='Belegt', x=df_cap['Abteilung'], y=df_cap['occupied_beds'], marker_color='#DC2626'),
                go.Bar(name='Verfügbar', x=df_cap['Abteilung'], y=df_cap['available_beds'], marker_color='#10B981')
            ])
            fig.update_layout(
                title="Bettenverfügbarkeit nach Abteilung",
                height=400,
                barmode='stack',
                xaxis_title="Abteilung",
                yaxis_title="Betten",
                legend_title_text="Status",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("📋", "Keine Kapazitätsdaten verfügbar", "Kapazitätsdaten werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)
