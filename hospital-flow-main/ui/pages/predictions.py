"""
Seitenmodul für Vorhersagen
"""
import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from ui.components import render_badge, render_empty_state


def format_prediction_value(pred_type: str, value: float) -> tuple[str, str]:
    if pred_type == 'patient_arrival':
        return f"{int(value)}", "neue Patienten erwartet"
    elif pred_type == 'bed_demand':
        return f"{value:.1f}%", "Bettenauslastung"
    else:
        return f"{value:.1f}", ""


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Vorhersagen-Seite"""
    st.markdown("### 5-15 Minuten Vorhersagen")
    
    predictions = db.get_predictions(15)
    predictions = [p for p in predictions if p['prediction_type'] in ['patient_arrival', 'bed_demand']]
    
    if predictions:
        df = pd.DataFrame(predictions)
        pred_type_map = {
            'patient_arrival': 'Patientenzugang',
            'bed_demand': 'Bettenbedarf',
        }
        dept_map = {
            'Kardiologie': 'Kardiologie',
            'Gastroenterologie': 'Gastroenterologie',
            'Akutgeriatrie': 'Akutgeriatrie',
            'Chirurgie': 'Chirurgie',
            'Intensivstation': 'Intensivstation',
            'Orthopädie': 'Orthopädie',
            'Urologie': 'Urologie',
            'Wirbelsäule': 'Wirbelsäule',
            'HNO': 'HNO',
            'Notaufnahme': 'Notaufnahme',
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
            'Other': 'Andere',
            'N/A': 'N/A'
        }
        
        capacity_data = get_cached_capacity() if get_cached_capacity else db.get_capacity_overview()
        capacity_by_dept = {c['department']: c for c in capacity_data}
        
        st.markdown("#### Bevorstehende Vorhersagen")
        for pred in predictions[:20]:
            confidence_color = "#10B981" if pred['confidence'] > 0.8 else "#F59E0B" if pred['confidence'] > 0.7 else "#EF4444"
            pred_type_key = pred['prediction_type']
            pred_type = pred_type_map.get(pred_type_key, pred_type_key.replace('_', ' ').title())
            dept = pred.get('department', 'N/A')
            dept_de = dept_map.get(dept, dept)
            minutes = pred['time_horizon_minutes']
            if minutes == 1:
                time_str = f'in {minutes} Minute'
            else:
                time_str = f'in {minutes} Minuten'
            
            formatted_value, value_description = format_prediction_value(pred_type_key, pred['predicted_value'])
            
            html_before = f"""<div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<div style="flex: 1;">
<strong>{pred_type}</strong>
<div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem;">{dept_de} • {time_str}</div>
</div>
<div style="text-align: right; margin-left: 1rem;">
<div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">{formatted_value}</div>
<div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">{value_description}</div>
<div style="font-size: 0.75rem; color: {confidence_color}; margin-top: 0.25rem;">{pred['confidence']*100:.0f}% Vertrauen</div>
</div>
</div>
</div>"""
            
            st.markdown(html_before, unsafe_allow_html=True)
        
        st.markdown("### Prognose-Vertrauen nach Zeithorizont")
        
        df = pd.DataFrame(predictions)
        if len(df) > 0:
            pred_type_map = {
                'patient_arrival': 'Patientenzugang',
                'bed_demand': 'Bettenbedarf',
            }
            df_plot = df.copy()
            df_plot['Vorhersagetyp'] = df_plot['prediction_type'].map(lambda x: pred_type_map.get(x, x.replace('_', ' ').title()))
            fig = px.scatter(
                df_plot,
                x='time_horizon_minutes',
                y='confidence',
                size='predicted_value',
                color='Vorhersagetyp',
                hover_data=['department'],
                title=""
            )
            fig.update_layout(
                height=400,
                xaxis_title="Zeithorizont (Minuten)",
                yaxis_title="Vertrauen",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(render_empty_state("🔮", "Keine Vorhersagen verfügbar", "Vorhersagen werden hier angezeigt, sobald sie verfügbar sind"), unsafe_allow_html=True)
