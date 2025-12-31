"""
Seitenmodul für Empfehlungen
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import random
import html
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from ui.components import render_badge, render_empty_state


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Empfehlungen-Seite"""
    st.markdown("### Ausstehende Empfehlungen")
    st.markdown("Überprüfen und Annehmen/Ablehnen von KI-generierten Empfehlungen")
    st.markdown("")  # Abstand
    
    recommendations = db.get_pending_recommendations()
    
    if recommendations:
        for rec in recommendations:
            priority_color = get_priority_color(rec['priority'])
            badge_html = render_badge(rec['priority'].upper(), rec['priority'])
            
            # Erklärungsscore abrufen
            explanation_score = rec.get('explanation_score', 'medium')
            score_color = get_explanation_score_color(explanation_score)
            score_badge = render_badge(f"Vertrauen: {explanation_score.upper()}", explanation_score if explanation_score != 'low' else 'medium')
            
            # Use new template format if available, otherwise fall back to old format
            has_new_format = rec.get('action') and rec.get('reason')
            
            if has_new_format:
                # Textwerte abrufen (keine HTML-Escape nötig, da von Anwendung generiert)
                title = str(rec.get('title', 'N/A'))
                action = str(rec.get('action', 'N/A'))
                reason = str(rec.get('reason', 'N/A'))
                expected_impact = str(rec.get('expected_impact', 'N/A'))
                safety_note = str(rec.get('safety_note', 'N/A'))
                department = str(rec.get('department', 'N/A'))
                rec_type = str(rec.get('rec_type', 'N/A'))
                
                # Deutsche Übersetzungen
                dept_map = {
                    'ER': 'Notaufnahme',
                    'ED': 'Notaufnahme',
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
                    'Ward': 'Station',
                    'Other': 'Andere',
                    'N/A': 'N/A',
                }
                rec_type_map = {
                    'capacity': 'Kapazität',
                    'staffing': 'Personal',
                    'inventory': 'Inventar',
                    'general': 'Allgemein',
                }
                department_de = dept_map.get(department, department)
                rec_type_de = rec_type_map.get(rec_type, rec_type.replace('_', ' ').title())
                
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="margin-bottom: 1rem;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{title}</h4>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem;">
                            {badge_html}
                        </div>
                    </div>
                    <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; margin-bottom: 0.75rem;">
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Maßnahme:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{action}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Begründung:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{reason}</p>
                        </div>
                        <div style="margin-bottom: 0.75rem;">
                            <strong style="color: #1f2937; font-size: 0.875rem;">Erwartete Auswirkung:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{expected_impact}</p>
                        </div>
                        <div>
                            <strong style="color: #1f2937; font-size: 0.875rem;">Sicherheits-Hinweis:</strong>
                            <p style="margin: 0.25rem 0 0 0; color: #4b5563; line-height: 1.6;">{safety_note}</p>
                        </div>
                    </div>
                    <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.75rem;">
                        {department_de} • {rec_type_de} • {format_time_ago(rec['timestamp'])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fallback to old format
                # Textwerte abrufen (keine HTML-Escape nötig, da von Anwendung generiert)
                title = str(rec.get('title', 'N/A'))
                description = str(rec.get('description', 'N/A'))
                department = str(rec.get('department', 'N/A'))
                rec_type = str(rec.get('rec_type', 'N/A'))
                
                # Deutsche Übersetzungen
                dept_map = {
                    'ER': 'Notaufnahme',
                    'ED': 'Notaufnahme',
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
                    'Ward': 'Station',
                    'Other': 'Andere',
                    'N/A': 'N/A',
                }
                rec_type_map = {
                    'capacity': 'Kapazität',
                    'staffing': 'Personal',
                    'inventory': 'Inventar',
                    'general': 'Allgemein',
                }
                department_de = dept_map.get(department, department)
                rec_type_de = rec_type_map.get(rec_type, rec_type.replace('_', ' ').title())
                
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 1rem;">
                        {badge_html}
                        <div style="flex: 1;">
                            <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{title}</h4>
                            <p style="color: #6b7280; margin: 0; line-height: 1.6;">{description}</p>
                            <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem;">
                                {department_de} • {rec_type_de} • {format_time_ago(rec['timestamp'])}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                action = st.text_input("Maßnahme / Begründung", key=f"action_{rec['id']}", placeholder="Bitte ergreifende Maßnahme oder Ablehnungsgrund eingeben")
            with col2:
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                if st.button("✅ Annehmen", key=f"accept_{rec['id']}", use_container_width=True):
                    if action:
                        db.accept_recommendation(rec['id'], action)
                        # Apply simulation effect based on recommendation type
                        rec_type = rec.get('rec_type', '')
                        if 'staffing' in rec_type.lower() or 'reassign' in rec.get('action', '').lower():
                            sim.apply_recommendation_effect(rec_type, 'staffing_reassignment', duration_minutes=30)
                        elif 'capacity' in rec_type.lower() or 'overflow' in rec.get('action', '').lower() or 'bed' in rec.get('action', '').lower():
                            sim.apply_recommendation_effect(rec_type, 'open_overflow_beds', duration_minutes=45)
                        elif 'room' in rec_type.lower() or 'room' in rec.get('action', '').lower():
                            sim.apply_recommendation_effect(rec_type, 'room_allocation', duration_minutes=30)
                        st.success("✅ Empfehlung angenommen")
                        st.rerun()
                    else:
                        st.warning("⚠️ Bitte Maßnahme eingeben")
            with col3:
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                if st.button("❌ Ablehnen", key=f"reject_{rec['id']}", use_container_width=True):
                    if action:
                        db.reject_recommendation(rec['id'], action)
                        st.info("❌ Empfehlung abgelehnt")
                        st.rerun()
                    else:
                        st.warning("⚠️ Bitte Ablehnungsgrund eingeben")
            
            st.markdown("---")
    else:
        st.markdown(render_empty_state("✅", "Keine ausstehenden Empfehlungen", "Alle Empfehlungen wurden überprüft"), unsafe_allow_html=True)
