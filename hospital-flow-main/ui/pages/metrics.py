"""
Seitenmodul für Live-Metriken - Umfassende Datenübersicht
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import pandas as pd
import io
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from ui.components import render_badge, render_empty_state


# Deutsche Übersetzungen
DEPT_MAP = {
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
    'Other': 'Andere',
    'N/A': 'N/A',
}

METRIC_TYPE_MAP = {
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
}

SEVERITY_MAP = {
    'high': 'hoch',
    'medium': 'mittel',
    'low': 'niedrig',
    'hoch': 'hoch',
    'mittel': 'mittel',
    'niedrig': 'niedrig',
}

STATUS_MAP = {
    'pending': 'ausstehend',
    'in_progress': 'in Bearbeitung',
    'completed': 'abgeschlossen',
    'accepted': 'akzeptiert',
    'rejected': 'abgelehnt',
    'resolved': 'gelöst',
    'acknowledged': 'bestätigt',
}


def get_time_range_minutes(time_range: str) -> int:
    """Konvertiere Zeitraum-String zu Minuten"""
    time_ranges = {
        '1h': 60,
        '6h': 360,
        '24h': 1440,
        '7d': 10080,
        '30d': 43200,
        'all': None,
    }
    return time_ranges.get(time_range, 10080)  # Default: 7 Tage


def filter_dataframe(df: pd.DataFrame, search_text: str = "", departments: list = None, 
                     min_value: float = None, max_value: float = None) -> pd.DataFrame:
    """Filtere DataFrame basierend auf verschiedenen Kriterien"""
    if df.empty:
        return df
    
    filtered = df.copy()
    
    # Textsuche
    if search_text:
        text_cols = filtered.select_dtypes(include=['object']).columns
        mask = pd.Series([False] * len(filtered))
        for col in text_cols:
            mask |= filtered[col].astype(str).str.contains(search_text, case=False, na=False)
        filtered = filtered[mask]
    
    # Abteilung
    if departments and 'department' in filtered.columns:
        filtered = filtered[filtered['department'].isin(departments)]
    
    # Wertebereich
    numeric_cols = filtered.select_dtypes(include=['number']).columns
    if min_value is not None and len(numeric_cols) > 0:
        # Filtere auf erste numerische Spalte
        filtered = filtered[filtered[numeric_cols[0]] >= min_value]
    if max_value is not None and len(numeric_cols) > 0:
        filtered = filtered[filtered[numeric_cols[0]] <= max_value]
    
    return filtered


def export_to_csv(df: pd.DataFrame, filename_prefix: str = "export") -> bytes:
    """Exportiere DataFrame zu CSV"""
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8')
    return output.getvalue().encode('utf-8')


def render_metrics_section(df: pd.DataFrame, time_range_minutes: int, search_text: str, 
                           selected_departments: list, min_value: float, max_value: float):
    """Rendert Metriken-Sektion"""
    st.markdown("### Metriken")
    
    if df.empty:
        st.info("Keine Metriken verfügbar")
        return
    
    # Filter anwenden
    filtered_df = filter_dataframe(df, search_text, selected_departments, min_value, max_value)
    
    if filtered_df.empty:
        st.warning("Keine Metriken entsprechen den Filtern")
        return
    
    # Übersichtskarten
    metric_types = filtered_df['metric_type'].unique()
    cols = st.columns(min(4, len(metric_types)))
    
    for idx, metric_type in enumerate(metric_types[:4]):
        col_idx = idx % 4
        with cols[col_idx]:
            latest = filtered_df[filtered_df['metric_type'] == metric_type].iloc[-1]
            label = METRIC_TYPE_MAP.get(metric_type, metric_type.replace('_', ' ').title())
            
            if metric_type in ['patient_count', 'waiting_count']:
                value_str = f"{int(round(latest['value']))}"
            elif metric_type in ['occupancy', 'ed_load', 'or_load', 'staff_load']:
                value_str = f"{latest['value']:.1f}%"
            elif metric_type == 'wait_time':
                value_str = f"{latest['value']:.1f} Min."
            elif metric_type == 'throughput':
                value_str = f"{latest['value']:.1f}/h"
            else:
                unit = latest.get('unit', '')
                value_str = f"{latest['value']:.1f} {unit}" if unit else f"{latest['value']:.1f}"
            
            st.metric(label, value_str)
    
    st.markdown("---")
    
    # Tabelle
    st.markdown("#### Metriken-Tabelle")
    display_df = filtered_df.copy()
    display_df['Zeitstempel'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['Typ'] = display_df['metric_type'].map(lambda x: METRIC_TYPE_MAP.get(x, x))
    display_df['Wert'] = display_df['value'].round(2)
    display_df['Einheit'] = display_df.get('unit', '')
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    
    table_cols = ['Zeitstempel', 'Typ', 'Wert', 'Einheit', 'Abteilung']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['timestamp', 'metric_type', 'value', 'unit', 'department']], "metrics")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )
    
    st.markdown("---")
    
    # Diagramm
    st.markdown("#### Metrik-Trends")
    metric_type_labels = [METRIC_TYPE_MAP.get(mt, mt.replace('_', ' ').title()) for mt in metric_types]
    selected_label = st.selectbox("Metrik-Typ auswählen", metric_type_labels, key="metric_chart_select")
    selected_metric = [k for k, v in METRIC_TYPE_MAP.items() if v == selected_label][0] if selected_label in metric_type_labels else metric_types[0]
    
    metric_data = filtered_df[filtered_df['metric_type'] == selected_metric].sort_values('timestamp')
    if not metric_data.empty:
        metric_data = metric_data.copy()
        if 'department' in metric_data.columns:
            metric_data['Abteilung'] = metric_data['department'].map(lambda d: DEPT_MAP.get(d, d) if pd.notna(d) else '')
            color_col = 'Abteilung'
        else:
            color_col = None
        
        fig = px.line(
            metric_data,
            x='timestamp',
            y='value',
            color=color_col if color_col and metric_data[color_col].nunique() > 1 else None,
            title=f"{METRIC_TYPE_MAP.get(selected_metric, selected_metric)} Verlauf",
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


def render_alerts_section(df: pd.DataFrame, search_text: str, selected_departments: list, 
                         selected_severities: list):
    """Rendert Alerts-Sektion"""
    st.markdown("### Warnungen/Alerts")
    
    if df.empty:
        st.info("Keine Warnungen verfügbar")
        return
    
    # Filter nach Schweregrad
    if selected_severities and 'severity' in df.columns:
        df = df[df['severity'].isin(selected_severities)]
    
    # Weitere Filter
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Warnungen entsprechen den Filtern")
        return
    
    # Kritische Alerts als Karten
    critical_alerts = filtered_df[filtered_df['severity'].isin(['high', 'hoch', 'critical', 'kritisch'])]
    if not critical_alerts.empty:
        st.markdown("#### Kritische Warnungen")
        for _, alert in critical_alerts.head(5).iterrows():
            severity_color = get_severity_color(alert['severity'])
            severity_de = SEVERITY_MAP.get(alert['severity'], alert['severity'])
            badge_html = render_badge(severity_de.upper(), alert['severity'])
            dept = DEPT_MAP.get(alert.get('department', 'N/A'), alert.get('department', 'N/A'))
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; 
                        border-left: 4px solid {severity_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                {badge_html}
                <strong style="margin-left: 0.5rem; color: #1f2937;">{alert['message']}</strong>
                <div style="color: #6b7280; font-size: 0.875rem; margin-top: 0.5rem;">
                    {dept} • {format_time_ago(alert['timestamp'])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabelle
    st.markdown("#### Alerts-Tabelle")
    display_df = filtered_df.copy()
    display_df['Zeitstempel'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['Typ'] = display_df.get('alert_type', '')
    display_df['Schweregrad'] = display_df['severity'].map(lambda x: SEVERITY_MAP.get(x, x))
    display_df['Nachricht'] = display_df['message']
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    display_df['Status'] = display_df.get('resolved', 0).map(lambda x: 'Gelöst' if x else 'Aktiv')
    
    table_cols = ['Zeitstempel', 'Typ', 'Schweregrad', 'Nachricht', 'Abteilung', 'Status']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['timestamp', 'alert_type', 'severity', 'message', 'department', 'resolved']], "alerts")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


def render_predictions_section(df: pd.DataFrame, search_text: str, selected_departments: list):
    """Rendert Vorhersagen-Sektion"""
    st.markdown("### Vorhersagen")
    
    if df.empty:
        st.info("Keine Vorhersagen verfügbar")
        return
    
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Vorhersagen entsprechen den Filtern")
        return
    
    # Tabelle
    st.markdown("#### Vorhersagen-Tabelle")
    display_df = filtered_df.copy()
    display_df['Zeitstempel'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['Typ'] = display_df.get('prediction_type', '').map(lambda x: METRIC_TYPE_MAP.get(x, x))
    display_df['Vorhergesagter Wert'] = display_df['predicted_value'].round(2)
    display_df['Konfidenz'] = (display_df.get('confidence', 0) * 100).round(1).astype(str) + '%'
    display_df['Zeithorizont'] = display_df.get('time_horizon_minutes', 0).astype(str) + ' Min.'
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    
    table_cols = ['Zeitstempel', 'Typ', 'Vorhergesagter Wert', 'Konfidenz', 'Zeithorizont', 'Abteilung']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Visualisierung
    if not filtered_df.empty:
        st.markdown("#### Vorhersagen nach Zeithorizont")
        fig = px.bar(
            filtered_df,
            x='time_horizon_minutes',
            y='predicted_value',
            color='prediction_type',
            title="Vorhergesagte Werte nach Zeithorizont",
            labels={'time_horizon_minutes': 'Zeithorizont (Minuten)', 'predicted_value': 'Vorhergesagter Wert'}
        )
        fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['timestamp', 'prediction_type', 'predicted_value', 'confidence', 'time_horizon_minutes', 'department']], "predictions")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


def render_recommendations_section(df: pd.DataFrame, search_text: str, selected_departments: list, 
                                  selected_statuses: list):
    """Rendert Empfehlungen-Sektion"""
    st.markdown("### Empfehlungen")
    
    if df.empty:
        st.info("Keine Empfehlungen verfügbar")
        return
    
    # Filter nach Status
    if selected_statuses and 'status' in df.columns:
        df = df[df['status'].isin(selected_statuses)]
    
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Empfehlungen entsprechen den Filtern")
        return
    
    # Hohe Priorität als Karten
    high_priority = filtered_df[filtered_df['priority'].isin(['high', 'hoch'])]
    if not high_priority.empty:
        st.markdown("#### Hohe Priorität")
        for _, rec in high_priority.head(3).iterrows():
            priority_color = get_priority_color(rec['priority'])
            priority_de = SEVERITY_MAP.get(rec['priority'], rec['priority'])
            badge_html = render_badge(priority_de.upper(), rec['priority'])
            dept = DEPT_MAP.get(rec.get('department', 'N/A'), rec.get('department', 'N/A'))
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; 
                        border-left: 4px solid {priority_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                {badge_html}
                <strong style="margin-left: 0.5rem; color: #1f2937;">{rec.get('title', 'N/A')}</strong>
                <p style="color: #4b5563; margin-top: 0.5rem; margin-bottom: 0;">{rec.get('description', '')[:200]}...</p>
                <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.5rem;">
                    {dept} • {format_time_ago(rec['timestamp'])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabelle
    st.markdown("#### Empfehlungen-Tabelle")
    display_df = filtered_df.copy()
    display_df['Zeitstempel'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['Titel'] = display_df.get('title', '')
    display_df['Priorität'] = display_df['priority'].map(lambda x: SEVERITY_MAP.get(x, x))
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    display_df['Status'] = display_df.get('status', '').map(lambda x: STATUS_MAP.get(x, x) if pd.notna(x) else '')
    
    table_cols = ['Zeitstempel', 'Titel', 'Priorität', 'Abteilung', 'Status']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['timestamp', 'title', 'priority', 'department', 'status']], "recommendations")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


def render_transport_section(df: pd.DataFrame, search_text: str, selected_departments: list, 
                            selected_statuses: list):
    """Rendert Transport-Sektion"""
    st.markdown("### Transport")
    
    if df.empty:
        st.info("Keine Transportanfragen verfügbar")
        return
    
    # Filter nach Status
    if selected_statuses and 'status' in df.columns:
        df = df[df['status'].isin(selected_statuses)]
    
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Transportanfragen entsprechen den Filtern")
        return
    
    # Tabelle
    st.markdown("#### Transport-Tabelle")
    display_df = filtered_df.copy()
    display_df['Zeitstempel'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['Typ'] = display_df.get('request_type', '')
    display_df['Von'] = display_df.get('from_location', '')
    display_df['Nach'] = display_df.get('to_location', '')
    display_df['Priorität'] = display_df['priority'].map(lambda x: SEVERITY_MAP.get(x, x))
    display_df['Status'] = display_df.get('status', '').map(lambda x: STATUS_MAP.get(x, x) if pd.notna(x) else '')
    display_df['Geschätzte Zeit'] = display_df.get('estimated_time_minutes', 0).astype(str) + ' Min.'
    
    table_cols = ['Zeitstempel', 'Typ', 'Von', 'Nach', 'Priorität', 'Status', 'Geschätzte Zeit']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['timestamp', 'request_type', 'from_location', 'to_location', 'priority', 'status', 'estimated_time_minutes']], "transport")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"transport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


def render_inventory_section(df: pd.DataFrame, search_text: str, selected_departments: list):
    """Rendert Inventar-Sektion"""
    st.markdown("### Inventar")
    
    if df.empty:
        st.info("Keine Inventardaten verfügbar")
        return
    
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Inventardaten entsprechen den Filtern")
        return
    
    # Hervorhebung kritischer Bestände
    critical_items = filtered_df[filtered_df['current_stock'] < filtered_df['min_threshold']]
    if not critical_items.empty:
        st.markdown("#### ⚠️ Kritische Bestände")
        for _, item in critical_items.iterrows():
            st.warning(f"**{item['item_name']}** ({item.get('department', 'N/A')}): {item['current_stock']} {item.get('unit', '')} (Mindest: {item['min_threshold']})")
    
    st.markdown("---")
    
    # Tabelle
    st.markdown("#### Inventar-Tabelle")
    display_df = filtered_df.copy()
    display_df['Artikel'] = display_df.get('item_name', '')
    display_df['Kategorie'] = display_df.get('category', '')
    display_df['Aktueller Bestand'] = display_df['current_stock']
    display_df['Mindestschwelle'] = display_df['min_threshold']
    display_df['Max. Kapazität'] = display_df.get('max_capacity', 0)
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    display_df['Einheit'] = display_df.get('unit', '')
    
    table_cols = ['Artikel', 'Kategorie', 'Aktueller Bestand', 'Mindestschwelle', 'Max. Kapazität', 'Abteilung', 'Einheit']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['item_name', 'category', 'current_stock', 'min_threshold', 'max_capacity', 'department', 'unit']], "inventory")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


def render_devices_section(df: pd.DataFrame, search_text: str, selected_departments: list):
    """Rendert Geräte-Sektion"""
    st.markdown("### Geräte")
    
    if df.empty:
        st.info("Keine Gerätedaten verfügbar")
        return
    
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Gerätedaten entsprechen den Filtern")
        return
    
    # Tabelle
    st.markdown("#### Geräte-Tabelle")
    display_df = filtered_df.copy()
    display_df['Gerät'] = display_df.get('device_type', '')
    display_df['Geräte-ID'] = display_df.get('device_id', '')
    display_df['Dringlichkeit'] = display_df.get('urgency_level', '').map(lambda x: SEVERITY_MAP.get(x, x) if pd.notna(x) else '')
    display_df['Nächste Wartung'] = pd.to_datetime(display_df.get('next_maintenance_due', ''), errors='coerce').dt.strftime('%Y-%m-%d')
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    
    table_cols = ['Gerät', 'Geräte-ID', 'Dringlichkeit', 'Nächste Wartung', 'Abteilung']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        csv_data = export_to_csv(filtered_df[['device_type', 'device_id', 'urgency_level', 'next_maintenance_due', 'department']], "devices")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


def render_capacity_section(df: pd.DataFrame, search_text: str, selected_departments: list):
    """Rendert Kapazität-Sektion"""
    st.markdown("### Kapazität")
    
    if df.empty:
        st.info("Keine Kapazitätsdaten verfügbar")
        return
    
    filtered_df = filter_dataframe(df, search_text, selected_departments)
    
    if filtered_df.empty:
        st.warning("Keine Kapazitätsdaten entsprechen den Filtern")
        return
    
    # Visualisierung
    if not filtered_df.empty and 'utilization_rate' in filtered_df.columns:
        st.markdown("#### Auslastung nach Abteilung")
        fig = px.bar(
            filtered_df,
            x='department',
            y='utilization_rate',
            title="Kapazitätsauslastung",
            labels={'department': 'Abteilung', 'utilization_rate': 'Auslastung (%)'},
            color='utilization_rate',
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Tabelle
    st.markdown("#### Kapazitäts-Tabelle")
    display_df = filtered_df.copy()
    display_df['Abteilung'] = display_df.get('department', '').map(lambda x: DEPT_MAP.get(x, x) if pd.notna(x) else '')
    display_df['Belegte Betten'] = display_df.get('occupied_beds', 0)
    display_df['Freie Betten'] = display_df.get('available_beds', 0)
    display_df['Gesamt'] = display_df.get('total_beds', 0)
    display_df['Auslastung %'] = (display_df.get('utilization_rate', 0) * 100).round(1) if 'utilization_rate' in display_df.columns else 0
    
    table_cols = ['Abteilung', 'Belegte Betten', 'Freie Betten', 'Gesamt', 'Auslastung %']
    st.dataframe(display_df[table_cols], use_container_width=True, hide_index=True)
    
    # Export
    col1, col2 = st.columns([1, 4])
    with col1:
        export_cols = ['department', 'occupied_beds', 'available_beds', 'total_beds', 'utilization_rate']
        available_cols = [col for col in export_cols if col in filtered_df.columns]
        csv_data = export_to_csv(filtered_df[available_cols], "capacity")
        st.download_button(
            "📥 CSV Export",
            csv_data,
            f"capacity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv"
        )


@st.cache_data(ttl=300)  # Cache für 5 Minuten
def get_all_data(_db, _sim, time_range_minutes: int):
    """Hole alle Daten mit Caching"""
    data = {}
    
    try:
        # Metriken
        if time_range_minutes:
            data['metrics'] = _db.get_metrics_last_n_minutes(time_range_minutes)
        else:
            data['metrics'] = _db.get_recent_metrics(1000)
    except Exception as e:
        data['metrics'] = []
    
    try:
        # Alerts
        hours = (time_range_minutes // 60) if time_range_minutes else 168  # Default: 7 Tage
        data['alerts'] = _db.get_alerts_by_time_range(hours)
    except Exception as e:
        data['alerts'] = []
    
    try:
        # Vorhersagen
        data['predictions'] = _db.get_predictions(60)  # Nächste 60 Minuten
    except Exception as e:
        data['predictions'] = []
    
    try:
        # Empfehlungen
        data['recommendations'] = _db.get_pending_recommendations()
    except Exception as e:
        data['recommendations'] = []
    
    try:
        # Transport
        data['transport'] = _db.get_transport_requests()
    except Exception as e:
        data['transport'] = []
    
    try:
        # Inventar
        data['inventory'] = _db.get_inventory_status()
    except Exception as e:
        data['inventory'] = []
    
    try:
        # Geräte
        data['devices'] = _db.get_device_maintenance_urgencies()
    except Exception as e:
        data['devices'] = []
    
    try:
        # Kapazität
        sim_metrics = _sim.get_current_metrics() if _sim else {}
        if sim_metrics and isinstance(sim_metrics, dict) and len(sim_metrics) > 0:
            data['capacity'] = _db.get_capacity_from_simulation(sim_metrics)
        else:
            data['capacity'] = _db.get_capacity_overview()
    except Exception as e:
        try:
            data['capacity'] = _db.get_capacity_overview()
        except:
            data['capacity'] = []
    
    return data


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Live-Metriken-Seite mit umfassender Datenübersicht"""
    st.markdown("### Live-Metriken - Umfassende Datenübersicht")
    
    # Auto-Refresh Toggle
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-Refresh (5 Min.)", value=False, key="auto_refresh_metrics")
    with col2:
        if st.button("🔄 Jetzt aktualisieren"):
            st.cache_data.clear()
            st.rerun()
    
    # Filter-Bereich
    with st.expander("🔍 Filter", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            time_range = st.selectbox(
                "Zeitraum",
                ['1h', '6h', '24h', '7d', '30d', 'all'],
                index=3,  # Default: 7d
                key="time_range_filter"
            )
            time_range_minutes = get_time_range_minutes(time_range)
        
        with col2:
            # Alle verfügbaren Abteilungen sammeln
            all_departments = set()
            # Aus Metriken
            metrics_sample = db.get_recent_metrics(100)
            if metrics_sample:
                depts = [m.get('department') for m in metrics_sample if m.get('department')]
                all_departments.update(depts)
            # Aus Kapazität
            capacity_sample = db.get_capacity_overview()
            if capacity_sample:
                depts = [c.get('department') for c in capacity_sample if c.get('department')]
                all_departments.update(depts)
            
            department_list = sorted([d for d in all_departments if d])
            selected_departments = st.multiselect(
                "Abteilung",
                department_list,
                key="department_filter"
            )
        
        with col3:
            search_text = st.text_input("🔍 Textsuche", key="search_filter", placeholder="Suche in allen Feldern...")
        
        # Zusätzliche Filter
        col4, col5 = st.columns(2)
        with col4:
            min_value = st.number_input("Min. Wert", value=None, key="min_value_filter", placeholder="Optional")
        with col5:
            max_value = st.number_input("Max. Wert", value=None, key="max_value_filter", placeholder="Optional")
    
    # Daten abrufen
    try:
        all_data = get_all_data(db, sim, time_range_minutes)
    except Exception as e:
        st.error(f"Fehler beim Laden der Daten: {str(e)}")
        return
    
    # Konvertiere zu DataFrames
    dataframes = {}
    for key, value in all_data.items():
        try:
            if value:
                dataframes[key] = pd.DataFrame(value)
            else:
                dataframes[key] = pd.DataFrame()
        except Exception as e:
            dataframes[key] = pd.DataFrame()
    
    # Zusätzliche Filter für spezifische Tabs (vor den Tabs definieren)
    alerts_df = dataframes.get('alerts', pd.DataFrame())
    recommendations_df = dataframes.get('recommendations', pd.DataFrame())
    transport_df = dataframes.get('transport', pd.DataFrame())
    
    # Zusätzliche Filter in einem Expander
    with st.expander("🔧 Erweiterte Filter", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        selected_severities = None
        with col1:
            if not alerts_df.empty and 'severity' in alerts_df.columns:
                severity_options = alerts_df['severity'].unique().tolist()
                selected_severities = st.multiselect(
                    "Schweregrad (Alerts)",
                    severity_options,
                    key="severity_filter_alerts"
                )
        
        selected_rec_statuses = None
        with col2:
            if not recommendations_df.empty and 'status' in recommendations_df.columns:
                rec_status_options = recommendations_df['status'].unique().tolist()
                selected_rec_statuses = st.multiselect(
                    "Status (Empfehlungen)",
                    rec_status_options,
                    key="status_filter_recommendations"
                )
        
        selected_transport_statuses = None
        with col3:
            if not transport_df.empty and 'status' in transport_df.columns:
                transport_status_options = transport_df['status'].unique().tolist()
                selected_transport_statuses = st.multiselect(
                    "Status (Transport)",
                    transport_status_options,
                    key="status_filter_transport"
                )
    
    # Tabs für verschiedene Datentypen
    tabs = st.tabs([
        "📊 Metriken",
        "⚠️ Alerts",
        "🔮 Vorhersagen",
        "💡 Empfehlungen",
        "🚑 Transport",
        "📦 Inventar",
        "🔧 Geräte",
        "🏥 Kapazität"
    ])
    
    # Rendere Sektionen
    with tabs[0]:
        render_metrics_section(
            dataframes.get('metrics', pd.DataFrame()),
            time_range_minutes,
            search_text,
            selected_departments,
            min_value,
            max_value
        )
    
    with tabs[1]:
        render_alerts_section(
            alerts_df,
            search_text,
            selected_departments,
            selected_severities
        )
    
    with tabs[2]:
        render_predictions_section(
            dataframes.get('predictions', pd.DataFrame()),
            search_text,
            selected_departments
        )
    
    with tabs[3]:
        render_recommendations_section(
            recommendations_df,
            search_text,
            selected_departments,
            selected_rec_statuses
        )
    
    with tabs[4]:
        render_transport_section(
            transport_df,
            search_text,
            selected_departments,
            selected_transport_statuses
        )
    
    with tabs[5]:
        render_inventory_section(
            dataframes.get('inventory', pd.DataFrame()),
            search_text,
            selected_departments
        )
    
    with tabs[6]:
        render_devices_section(
            dataframes.get('devices', pd.DataFrame()),
            search_text,
            selected_departments
        )
    
    with tabs[7]:
        render_capacity_section(
            dataframes.get('capacity', pd.DataFrame()),
            search_text,
            selected_departments
        )
    
    # Auto-Refresh Info
    if auto_refresh:
        st.info("ℹ️ Auto-Refresh ist aktiv. Daten werden alle 5 Minuten automatisch aktualisiert (Cache-TTL).")
