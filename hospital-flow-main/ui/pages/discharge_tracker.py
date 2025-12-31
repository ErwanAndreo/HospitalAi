"""
Seitenmodul für Entlassung
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
    """Rendert die Entlassung-Seite"""
    # Erwartete Entlassungen simulieren
    from datetime import timezone
    jetzt = datetime.now(timezone.utc)

    # Erwartete Entlassungen für die nächsten 12 Stunden (stündliche Intervalle) generieren
    stündliche_entlassungen = []
    for stunde in range(12):
        stundenzeit = jetzt + timedelta(hours=stunde)
        # Entlassungszahlen simulieren (morgens/nachmittags höher, nachts niedriger)
        if 8 <= stunde < 12:  # Morgenpeak
            anzahl = random.randint(3, 8)
        elif 12 <= stunde < 18:  # Nachmittagspeak
            anzahl = random.randint(2, 6)
        elif 18 <= stunde < 22:  # Abend
            anzahl = random.randint(1, 4)
        else:  # Nacht
            anzahl = random.randint(0, 2)

        stündliche_entlassungen.append({
            'stunde': stundenzeit,
            'stunden_label': stundenzeit.strftime('%H:00'),
            'anzahl': anzahl
        })

    # Erwartete Entlassungen in den nächsten 4 Stunden berechnen
    nächste_4h_entlassungen = sum([d['anzahl'] for d in stündliche_entlassungen[:4]])

    # Große Kennzahl für die nächsten 4 Stunden
    st.markdown("### Erwartete Entlassungen")
    st.markdown("")  # Abstand

    spalte1, spalte2, spalte3 = st.columns([2, 1, 1])
    with spalte1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <div style="color: white; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; opacity: 0.9;">
                Erwartete Entlassungen in den nächsten 4 Stunden
            </div>
            <div style="color: white; font-size: 4rem; font-weight: 700; line-height: 1;">
                {nächste_4h_entlassungen}
            </div>
            <div style="color: white; font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">
                Aggregierte Anzahl
            </div>
        </div>
        """, unsafe_allow_html=True)

    with spalte2:
        nächste_8h_entlassungen = sum([d['anzahl'] for d in stündliche_entlassungen[:8]])
        st.metric("Nächste 8 Stunden", nächste_8h_entlassungen, delta=None)

    with spalte3:
        nächste_12h_entlassungen = sum([d['anzahl'] for d in stündliche_entlassungen])
        st.metric("Nächste 12 Stunden", nächste_12h_entlassungen, delta=None)

    st.markdown("---")

    # Zeitstrahl für die nächsten 12 Stunden
    st.markdown("### Entlassungs-Zeitstrahl (Nächste 12 Stunden)")
    st.markdown("")  # Abstand

    df_zeitstrahl = pd.DataFrame(stündliche_entlassungen)

    fig_zeitstrahl = px.bar(
        df_zeitstrahl,
        x='stunden_label',
        y='anzahl',
        title="",
        labels={'stunden_label': 'Zeit', 'anzahl': 'Erwartete Entlassungen'},
        color='anzahl',
        color_continuous_scale='Blues'
    )
    fig_zeitstrahl.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title="",
        yaxis_title="Erwartete Entlassungen",
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#e5e7eb', showline=False)
    )
    fig_zeitstrahl.update_traces(marker_line_width=0)
    st.plotly_chart(fig_zeitstrahl, use_container_width=True)

    st.markdown("---")

    # Empfehlungen
    st.markdown("### Empfehlungen")
    st.markdown("")  # Abstand

    # Empfehlungen basierend auf Entlassungsmustern simulieren
    empfehlungen = []

    # Prüfe auf Fälle, die eine frühere Entlassungsplanung benötigen
    hohe_entlassungsstunden = [d for d in stündliche_entlassungen[:6] if d['anzahl'] >= 5]
    if hohe_entlassungsstunden:
        gesamt_hoch = sum([d['anzahl'] for d in hohe_entlassungsstunden])
        empfehlungen.append({
            "type": "early_planning",
            "message": f"Frühzeitige Entlassungsplanung für {gesamt_hoch} Fälle (gesamt) starten",
            "details": f"Hohes Entlassungsaufkommen in den nächsten 6 Stunden erwartet. Frühzeitige Planung kann Verzögerungen um 20-30% reduzieren.",
            "priority": "mittel"
        })

    # Prüfe auf potenzielle Engpässe
    spitzenstunde = max(stündliche_entlassungen[:8], key=lambda x: x['anzahl'])
    if spitzenstunde['anzahl'] >= 6:
        empfehlungen.append({
            "type": "resource_allocation",
            "message": f"Zusätzliche Ressourcen für {spitzenstunde['stunden_label']} bereitstellen (erwartet {spitzenstunde['anzahl']} Entlassungen)",
            "details": f"Spitzenzeit für Entlassungen erkannt. Zusätzliche Mitarbeitende oder Transportkapazität einplanen.",
            "priority": "hoch"
        })

    # Prüfe auf niedrige Entlassungsphasen (Aufholpotenzial)
    niedrige_entlassungsstunden = [d for d in stündliche_entlassungen if d['anzahl'] <= 1]
    if len(niedrige_entlassungsstunden) >= 3:
        empfehlungen.append({
            "type": "catch_up",
            "message": f"Niedrigphasen für Aufholarbeiten nutzen (mind. 3 Stunden mit ≤1 erwarteter Entlassung)",
            "details": "Mehrere Niedrigphasen erkannt. Gute Gelegenheit, ausstehende Entlassungen zu bearbeiten.",
            "priority": "niedrig"
        })

    if empfehlungen:
        for emp in empfehlungen:
            priority_color = get_priority_color(emp['priority'])
            badge_html = render_badge(emp['priority'].upper(), emp['priority'])

            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {priority_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: start; gap: 0.75rem; margin-bottom: 0.75rem;">
                    {badge_html}
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{emp['message']}</h4>
                        <p style="color: #6b7280; margin: 0; line-height: 1.6;">{emp['details']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(render_empty_state("💡", "Keine Empfehlungen zum aktuellen Zeitpunkt", "Alle Systeme arbeiten im normalen Bereich"), unsafe_allow_html=True)

    # Weitere aggregierte Statistiken
    st.markdown("---")
    st.markdown("### Statistiken")
    st.markdown("")  # Abstand

    spalte1, spalte2, spalte3, spalte4 = st.columns(4)

    with spalte1:
        spitzenstunde = max(stündliche_entlassungen, key=lambda x: x['anzahl'])
        st.metric("Spitzenstunde", spitzenstunde['stunden_label'], delta=f"{spitzenstunde['anzahl']} Entlassungen")

    with spalte2:
        durchschnitt_pro_stunde = sum([d['anzahl'] for d in stündliche_entlassungen]) / len(stündliche_entlassungen)
        st.metric("Durchschnitt pro Stunde", f"{durchschnitt_pro_stunde:.1f}", delta=None)

    with spalte3:
        gesamt_12h = sum([d['anzahl'] for d in stündliche_entlassungen])
        st.metric("Gesamt (12h)", gesamt_12h, delta=None)

    with spalte4:
        niedrige_stunden = len([d for d in stündliche_entlassungen if d['anzahl'] <= 1])
        st.metric("Stunden mit niedriger Aktivität", niedrige_stunden, delta=None)
