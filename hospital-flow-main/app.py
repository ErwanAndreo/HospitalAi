"""
HospitalFlow - Krankenhaus-Betriebsdashboard
Moderne Streamlit-Anwendung für Krankenhauspersonal mit Live-Metriken, Vorhersagen und Empfehlungen
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
import pandas as pd
import random
import time
from zoneinfo import ZoneInfo
from db import HospitalDB
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color
)
from simulation import get_simulation
from ui.styling import apply_custom_styles
from ui.components import render_badge, render_empty_state

# ===== TIMEZONE CONFIGURATION =====
# Set your local timezone here (e.g., 'Europe/Berlin', 'Europe/Vienna', 'America/New_York', 'Asia/Tokyo')
# For Central European Time (CET/CEST), use 'Europe/Berlin' or 'Europe/Zurich'
LOCAL_TIMEZONE = 'Europe/Berlin'  # Change this to your timezone

def get_local_time():
    """Get current time in configured local timezone"""
    return datetime.now(timezone.utc).astimezone(ZoneInfo(LOCAL_TIMEZONE))
# ===================================

# Seitenkonfiguration
st.set_page_config(
    page_title="HospitalFlow",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Leistung: Deaktiviere Neustart bei Widget-Interaktion, um Flackern zu vermeiden
if 'rerun_disabled' not in st.session_state:
    st.session_state.rerun_disabled = False

# Styling anwenden
apply_custom_styles()

# Datenbank initialisieren (für Leistung gecacht)
@st.cache_resource
def init_db():
    # #region agent log
    import json
    import os
    log_path = '/Users/erwan/Programmieren/ItManagementV3/hospital-flow-main/.cursor/debug.log'
    try:
        cwd = os.getcwd()
        log_dir = os.path.dirname(log_path)
        log_dir_exists = os.path.exists(log_dir) if log_dir else False
        log_file_exists = os.path.exists(log_path)
        log_dir_writable = os.access(log_dir, os.W_OK) if log_dir_exists else False
        log_parent_exists = os.path.exists(os.path.dirname(log_dir)) if log_dir else False
        # Try to write diagnostic info to a safe location first
        safe_log = os.path.join(cwd, '.cursor', 'debug.log') if os.path.exists(os.path.join(cwd, '.cursor')) else None
        if safe_log and os.path.exists(os.path.dirname(safe_log)):
            with open(safe_log, 'a') as f:
                f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'run1', 'hypothesisId': 'A,B,C,D', 'location': 'app.py:52', 'message': 'Environment check before init_db', 'data': {'cwd': cwd, 'log_path': log_path, 'log_dir': log_dir, 'log_dir_exists': log_dir_exists, 'log_file_exists': log_file_exists, 'log_dir_writable': log_dir_writable, 'log_parent_exists': log_parent_exists, 'safe_log': safe_log}, 'timestamp': int(__import__('time').time() * 1000)}) + '\n')
    except Exception as diag_e:
        pass  # Ignore diagnostic errors
    # #endregion
    # #region agent log
    try:
        db_obj = HospitalDB()
        db_type = str(type(db_obj))
        has_method = hasattr(db_obj, 'get_device_maintenance_urgencies')
        # Try safe log path first, fallback to original
        safe_log = os.path.join(os.getcwd(), '.cursor', 'debug.log')
        log_to_use = safe_log if os.path.exists(os.path.dirname(safe_log)) else log_path
        log_dir_to_create = os.path.dirname(log_to_use)
        if not os.path.exists(log_dir_to_create):
            os.makedirs(log_dir_to_create, exist_ok=True)
        with open(log_to_use, 'a') as f:
            f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'run1', 'hypothesisId': 'A,B,C', 'location': 'app.py:67', 'message': 'HospitalDB initialized', 'data': {'db_type': db_type, 'has_method': has_method, 'log_used': log_to_use}, 'timestamp': int(__import__('time').time() * 1000)}) + '\n')
    except Exception as e:
        # Try to log error to safe location
        try:
            safe_log = os.path.join(os.getcwd(), '.cursor', 'debug.log')
            log_dir_to_create = os.path.dirname(safe_log)
            if not os.path.exists(log_dir_to_create):
                os.makedirs(log_dir_to_create, exist_ok=True)
            with open(safe_log, 'a') as f:
                f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'run1', 'hypothesisId': 'A,B,C,E', 'location': 'app.py:75', 'message': 'HospitalDB init error', 'data': {'error': str(e), 'error_type': type(e).__name__, 'log_attempted': log_path}, 'timestamp': int(__import__('time').time() * 1000)}) + '\n')
        except:
            pass
        db_obj = HospitalDB()
    # #endregion
    return db_obj

db = init_db()
# #region agent log
import json
import os
log_path = '/Users/erwan/Programmieren/ItManagementV3/hospital-flow-main/.cursor/debug.log'
try:
    # Use safe log path that works in both host and container
    safe_log = os.path.join(os.getcwd(), '.cursor', 'debug.log')
    log_dir_to_create = os.path.dirname(safe_log)
    if not os.path.exists(log_dir_to_create):
        os.makedirs(log_dir_to_create, exist_ok=True)
    with open(safe_log, 'a') as f:
        f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'run1', 'hypothesisId': 'A,B,C', 'location': 'app.py:95', 'message': 'db variable assigned', 'data': {'db_type': str(type(db)), 'has_method': hasattr(db, 'get_device_maintenance_urgencies'), 'log_used': safe_log, 'cwd': os.getcwd()}, 'timestamp': int(__import__('time').time() * 1000)}) + '\n')
except Exception as e:
    # Try original path as fallback
    try:
        log_dir_to_create = os.path.dirname(log_path)
        if not os.path.exists(log_dir_to_create):
            os.makedirs(log_dir_to_create, exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'run1', 'hypothesisId': 'A,B,C,E', 'location': 'app.py:103', 'message': 'db assignment log error', 'data': {'error': str(e), 'error_type': type(e).__name__}, 'timestamp': int(__import__('time').time() * 1000)}) + '\n')
    except:
        pass
# #endregion

# Navigation mit Icons
PAGES = {
    "📊 Dashboard": "dashboard",
    "📈 Live-Metriken": "metrics",
    "🔮 Vorhersagen": "predictions",
    "⚙️ Betrieb": "operations",
    "📋 Kapazitätsübersicht": "capacity",
    "📅 Dienstplan": "dienstplan",

    "🚑 Transport": "transport",
    "📦 Inventar": "inventory",
    "🔧 Gerätewartung": "devices",
    "🏥 Entlassungsplanung": "discharge"
}

# Systemstatus abrufen
system_status, status_color = get_system_status()


# HospitalFlow title in sidebar (top left)
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
    <span style="font-size: 2rem;">🏥</span>
    <span style="font-size: 1.5rem; font-weight: 700; color: #4f46e5; letter-spacing: -0.025em;">HospitalFlow</span>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation with professional styling
st.sidebar.markdown("""
<div style="padding: 0.5rem 0 1.5rem 0; border-bottom: 1px solid #e5e7eb; margin-bottom: 1rem;">
    <h3 style="color: #667eea; margin: 0; font-size: 1.125rem; font-weight: 600; letter-spacing: -0.01em;">Navigation</h3>
</div>
""", unsafe_allow_html=True)

# Seitenauswahl mit Icons
page_key = st.sidebar.radio(
    "Seite auswählen",
    list(PAGES.keys()),
    label_visibility="collapsed",
    key="nav_radio"
)

# Seitennamen ohne Icon extrahieren
page = page_key.split(" ", 1)[1] if " " in page_key else page_key

# Severity Legend (compact and professional) - unter der Seitenauswahl
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="legend" style="margin-bottom: 1rem;">
    <div style="font-size: 0.7rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; font-weight: 600;">Schweregrad</div>
    <div class="legend-item">
        <span class="badge" style="background: #DC2626; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Hoch</span>
    </div>
    <div class="legend-item">
        <span class="badge" style="background: #F59E0B; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Mittel</span>
    </div>
    <div class="legend-item">
        <span class="badge" style="background: #10B981; color: white; width: 10px; height: 10px; padding: 0; border-radius: 50%; display: inline-block;"></span>
        <span style="font-size: 0.75rem;">Niedrig</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Demo Mode und Auto-Refresh Variablen definieren (für spätere Verwendung)
# Diese werden später unten in der Sidebar angezeigt
demo_mode = st.session_state.get('demo_mode', False)
auto_refresh = st.session_state.get('auto_refresh', True)
refresh_interval_key = st.session_state.get('refresh_interval', '30 Sekunden')
interval_map = {"10 Sekunden": 10, "30 Sekunden": 30, "60 Sekunden": 60}
refresh_seconds = interval_map.get(refresh_interval_key, 30)

# Professioneller Seiten-Header
page_timestamp = get_local_time().strftime('%H:%M:%S')
st.markdown(f"""
<div class="page-header">
    <h1 class="page-title">{page}</h1>
    <p class="page-subtitle">Zuletzt aktualisiert: {page_timestamp}</p>
</div>
""", unsafe_allow_html=True)

# Simulation initialisieren (pro Sitzung gecacht)
if 'simulation' not in st.session_state:
    st.session_state.simulation = get_simulation()

sim = st.session_state.simulation

# Simulationsstatus aktualisieren (nur wenn genug Zeit vergangen ist, um Flackern zu vermeiden)
if 'last_sim_update' not in st.session_state:
    st.session_state.last_sim_update = datetime.now(timezone.utc)

time_since_update = (datetime.now(timezone.utc) - st.session_state.last_sim_update).total_seconds()
if time_since_update > 2:  # Maximal alle 2 Sekunden aktualisieren
    sim.update()
    st.session_state.last_sim_update = datetime.now(timezone.utc)

# Auf Auslastungsereignisse prüfen (zufällige Chance, aber nicht zu häufig)
if 'last_surge_check' not in st.session_state:
    st.session_state.last_surge_check = datetime.now(timezone.utc)

time_since_last_check = (datetime.now(timezone.utc) - st.session_state.last_surge_check).total_seconds()
# Im Demo-Modus häufiger prüfen (alle 1 Minute statt 5 Minuten)
check_interval = 60 if demo_mode else 300
if time_since_last_check > check_interval:
    if sim.should_trigger_surge(demo_mode=demo_mode):
        sim.trigger_surge_event(intensity=random.uniform(0.7, 1.0))
    st.session_state.last_surge_check = datetime.now(timezone.utc)

# Vorhersagen aktualisieren (regelmäßig, z.B. alle 2-3 Minuten)
if 'last_prediction_update' not in st.session_state:
    st.session_state.last_prediction_update = datetime.now(timezone.utc)

time_since_prediction_update = (datetime.now(timezone.utc) - st.session_state.last_prediction_update).total_seconds()
# Aktualisiere Vorhersagen alle 2-3 Minuten (180 Sekunden)
prediction_update_interval = 180
if time_since_prediction_update > prediction_update_interval:
    try:
        # Hole aktuellen Simulationszustand
        sim_metrics = sim.get_current_metrics()
        sim_trends = sim.trends
        sim_active_events = sim.active_events
        
        # Aktualisiere Vorhersagen
        db.update_predictions(sim_metrics, sim_trends, sim_active_events)
        st.session_state.last_prediction_update = datetime.now(timezone.utc)
    except Exception as e:
        # Fehler beim Update ignorieren (nicht kritisch)
        pass

# Warnungen generieren (regelmäßig, z.B. alle 30-60 Sekunden)
if 'last_alert_generation' not in st.session_state:
    st.session_state.last_alert_generation = datetime.now(timezone.utc)

time_since_alert_generation = (datetime.now(timezone.utc) - st.session_state.last_alert_generation).total_seconds()
# Generiere Warnungen alle 30-60 Sekunden
alert_generation_interval = 45
if time_since_alert_generation > alert_generation_interval:
    try:
        # Hole aktuellen Simulationszustand
        sim_metrics = sim.get_current_metrics()
        sim_trends = sim.trends
        
        # Generiere Warnungen basierend auf aktuellen Daten
        db.generate_alerts(sim_metrics, sim_trends)
        st.session_state.last_alert_generation = datetime.now(timezone.utc)
    except Exception as e:
        # Fehler beim Update ignorieren (nicht kritisch)
        pass

# Operationen-Simulation (regelmäßig, z.B. alle 5-10 Minuten)
if 'last_operations_simulation' not in st.session_state:
    st.session_state.last_operations_simulation = datetime.now(timezone.utc)

time_since_ops_sim = (datetime.now(timezone.utc) - st.session_state.last_operations_simulation).total_seconds()
# Simuliere Operationen alle 5-10 Minuten (300 Sekunden)
operations_simulation_interval = 300
if time_since_ops_sim > operations_simulation_interval:
    try:
        from utils import calculate_operation_consumption
        
        # Generiere neue Operationen
        new_operations = sim.simulate_operations()
        
        # Speichere neue Operationen in Datenbank
        for op in new_operations:
            db.record_operation(
                operation_type=op['operation_type'],
                department=op['department'],
                status=op['status'],
                duration_minutes=op['duration_minutes'],
                planned_start_time=op['planned_start_time']
            )
        
        # Aktualisiere Status bestehender Operationen (geplant → laufend → abgeschlossen)
        # Hole Operationen mit Status "geplant" oder "laufend"
        planned_ops = db.get_recent_operations(hours=24, status='geplant')
        running_ops = db.get_recent_operations(hours=24, status='laufend')
        
        # Prüfe geplante Operationen: Starte sie, wenn geplante Startzeit erreicht
        for op in planned_ops:
            if op.get('planned_start_time'):
                planned_start = op['planned_start_time']
                if isinstance(planned_start, str):
                    try:
                        planned_start = datetime.fromisoformat(planned_start.replace('Z', '+00:00'))
                    except:
                        planned_start = datetime.strptime(planned_start, '%Y-%m-%d %H:%M:%S.%f')
                elif not isinstance(planned_start, datetime):
                    continue
                # Entferne timezone info für Vergleich
                if planned_start.tzinfo:
                    planned_start = planned_start.replace(tzinfo=None)
                now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                if planned_start <= now_naive:
                    # Starte Operation
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE operations 
                        SET status = 'laufend', start_time = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (op['id'],))
                    conn.commit()
                    conn.close()
        
        # Prüfe laufende Operationen: Schließe sie ab, wenn Dauer erreicht
        for op in running_ops:
            if op.get('start_time') and op.get('duration_minutes'):
                start_time = op['start_time']
                if isinstance(start_time, str):
                    try:
                        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    except:
                        try:
                            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')
                        except:
                            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                elif not isinstance(start_time, datetime):
                    continue
                # Entferne timezone info für Vergleich
                if start_time.tzinfo:
                    start_time = start_time.replace(tzinfo=None)
                duration_minutes = op['duration_minutes']
                end_time = start_time + timedelta(minutes=duration_minutes)
                now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
                if end_time <= now_naive:
                    # Schließe Operation ab und berechne Materialverbrauch
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE operations 
                        SET status = 'abgeschlossen', end_time = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (op['id'],))
                    conn.commit()
                    conn.close()
                    
                    # Berechne Materialverbrauch für diese Operation
                    consumption_map = calculate_operation_consumption(
                        operation_type=op['operation_type'],
                        department=op['department'],
                        duration_minutes=duration_minutes
                    )
                    
                    # Aktualisiere Inventar-Bestand
                    db.update_inventory_from_operation(
                        operation_type=op['operation_type'],
                        department=op['department'],
                        consumption_map=consumption_map
                    )
        
        st.session_state.last_operations_simulation = datetime.now(timezone.utc)
    except Exception as e:
        # Fehler beim Update ignorieren (nicht kritisch)
        pass

# Entlassungen durchführen (regelmäßig, z.B. alle 3-5 Minuten)
if 'last_discharge_processing' not in st.session_state:
    st.session_state.last_discharge_processing = datetime.now(timezone.utc)

time_since_discharge_processing = (datetime.now(timezone.utc) - st.session_state.last_discharge_processing).total_seconds()
# Verarbeite Entlassungen alle 3-5 Minuten (240 Sekunden)
discharge_processing_interval = 240
if time_since_discharge_processing > discharge_processing_interval:
    try:
        # Hole Entlassungsplanungsdaten aus der Datenbank
        discharge_data = db.get_discharge_planning()
        
        if discharge_data:
            # Aggregiere alle entlassungsbereiten Patienten über alle Abteilungen
            total_ready_for_discharge = sum([
                dept.get('ready_for_discharge_count', 0) 
                for dept in discharge_data
            ])
            
            # Führe Entlassungen durch (nicht alle auf einmal, sondern mit gewisser Wahrscheinlichkeit/Teilmenge)
            # Realistisch: Nicht alle entlassungsbereiten Patienten werden sofort entlassen
            # Verwendet eine gewisse Rate (z.B. 30-70% der entlassungsbereiten Patienten pro Zyklus)
            if total_ready_for_discharge > 0:
                # Berechne Anzahl zu entlassender Patienten
                # Basis: 40-60% der entlassungsbereiten Patienten, aber mindestens 1 wenn > 0
                discharge_rate = random.uniform(0.4, 0.6)
                patients_to_discharge = max(1, int(total_ready_for_discharge * discharge_rate))
                
                # Führe Entlassungen in der Simulation durch
                sim.apply_discharge_event(count=patients_to_discharge)
        
        st.session_state.last_discharge_processing = datetime.now(timezone.utc)
    except Exception as e:
        # Fehler beim Update ignorieren (nicht kritisch)
        pass

# Inventar-Verbrauch aufzeichnen (regelmäßig, z.B. alle 5-10 Minuten)
if 'last_consumption_update' not in st.session_state:
    st.session_state.last_consumption_update = datetime.now(timezone.utc)

time_since_consumption_update = (datetime.now(timezone.utc) - st.session_state.last_consumption_update).total_seconds()
# Aktualisiere Verbrauch alle 5-10 Minuten (300 Sekunden)
consumption_update_interval = 300
if time_since_consumption_update > consumption_update_interval:
    try:
        from utils import calculate_daily_consumption_from_activity
        
        # Hole aktuellen Simulationszustand
        sim_metrics = sim.get_current_metrics()
        capacity_data = db.get_capacity_overview()
        
        # Berechne belegte Betten
        beds_occupied = sum([c.get('occupied_beds', 0) for c in capacity_data])
        
        # Hole Operationen-Verbrauch pro Abteilung (letzte 24 Stunden, für Tagesdurchschnitt)
        operations_consumption_by_dept = db.get_operations_consumption(hours=24)
        
        # Hole alle Inventar-Artikel
        inventory = db.get_inventory_status()
        
        # Für jeden Artikel: Berechne und speichere Verbrauch
        for item in inventory:
            department = item.get('department', '')
            
            # Anzahl Operationen in dieser Abteilung (für Verbrauchsberechnung)
            operations_count = operations_consumption_by_dept.get(department, 0)
            # Umrechnung: Anzahl Operationen in 24h → durchschnittlicher Tagesverbrauch
            # (wir speichern alle 5-10 Minuten, daher teilen wir durch Anzahl Intervalle pro Tag)
            daily_operations_count = operations_count / (24 * 60 / consumption_update_interval)
            
            # Berechne Verbrauch basierend auf Aktivität (inkl. Operationen)
            daily_consumption = calculate_daily_consumption_from_activity(
                item=item,
                ed_load=sim_metrics.get('ed_load', 65.0),
                beds_occupied=beds_occupied,
                capacity_data=capacity_data,
                operations_count=daily_operations_count
            )
            
            # Berechne Aktivitätsfaktor (kombiniert ED Load und Bettenauslastung)
            ed_factor = 0.5 + (sim_metrics.get('ed_load', 65.0) / 100.0) * 1.0
            beds_utilization = (beds_occupied / max(1, sum([c.get('total_beds', 0) for c in capacity_data]))) * 100
            beds_factor = 0.7 + (beds_utilization / 100.0) * 0.6
            activity_factor = (ed_factor + beds_factor) / 2.0
            
            # Speichere Verbrauchseintrag (täglicher Verbrauch)
            # Da wir alle 5-10 Minuten aufzeichnen, speichern wir den geschätzten täglichen Verbrauch
            db.record_inventory_consumption(
                item_id=item['id'],
                item_name=item['item_name'],
                consumption_amount=daily_consumption,
                department=item.get('department'),
                ed_load=sim_metrics.get('ed_load', 65.0),
                beds_occupied=beds_occupied,
                activity_factor=activity_factor
            )
        
        st.session_state.last_consumption_update = datetime.now(timezone.utc)
    except Exception as e:
        # Fehler beim Update ignorieren (nicht kritisch)
        pass

# Datenabruf cachen, um Flackern zu vermeiden
@st.cache_data(ttl=2)  # Cache für 2 Sekunden für schnellere Updates
def get_cached_alerts():
    return db.get_active_alerts()

@st.cache_data(ttl=2)
def get_cached_recommendations():
    return db.get_pending_recommendations()

@st.cache_data(ttl=2)
def get_cached_capacity():
    return db.get_capacity_overview()

# Seitenmodule importieren
from ui.pages import dashboard, operations, metrics, predictions, transport, inventory, devices, discharge_planning, capacity, dienstplan

# Seiteninhalt - Routing zu Seitenmodulen
if page == "Dashboard":
    dashboard.render(db, sim, get_cached_alerts, get_cached_recommendations, get_cached_capacity)
elif page == "Betrieb":
    operations.render(db, sim, get_cached_alerts, get_cached_recommendations, get_cached_capacity)
elif page == "Live-Metriken":
    metrics.render(db, sim)
elif page == "Vorhersagen":
    predictions.render(db, sim)
elif page == "Transport":
    transport.render(db, sim)
elif page == "Inventar":
    inventory.render(db, sim)
elif page == "Gerätewartung":
    devices.render(db, sim)
elif page == "Entlassungsplanung":
    discharge_planning.render(db, sim)
elif page == "Kapazitätsübersicht":
    capacity.render(db, sim)
elif page == "Dienstplan":
    dienstplan.render(db, sim)

# Sidebar-Footer
st.sidebar.markdown("---")
st.sidebar.markdown("")  # Spacing

# Demo Mode toggle (in sidebar - above refresh button)
demo_mode_new = st.sidebar.toggle("🎬 Demo-Modus", value=demo_mode, help="Erhöht die Ereignisfrequenz für Demonstrationszwecke", key="demo_mode_toggle")
st.session_state['demo_mode'] = demo_mode_new
demo_mode = demo_mode_new
if demo_mode:
    st.sidebar.info("Demo-Modus: Ereignisse treten häufiger auf")

# Auto-Refresh toggle (in sidebar - above refresh button)
auto_refresh_new = st.sidebar.toggle("🔄 Auto-Refresh", value=auto_refresh, help="Aktualisiert die Seite automatisch alle 30 Sekunden", key="auto_refresh_toggle")
st.session_state['auto_refresh'] = auto_refresh_new
auto_refresh = auto_refresh_new

refresh_interval_options = ["10 Sekunden", "30 Sekunden", "60 Sekunden"]
refresh_interval_index = refresh_interval_options.index(refresh_interval_key) if refresh_interval_key in refresh_interval_options else 1
refresh_interval = st.sidebar.selectbox("Aktualisierungsintervall", refresh_interval_options, index=refresh_interval_index, key="refresh_interval_selectbox", disabled=not auto_refresh)
st.session_state['refresh_interval'] = refresh_interval
refresh_seconds = interval_map[refresh_interval]
if auto_refresh:
    st.sidebar.info(f"Auto-Refresh: Alle {refresh_seconds} Sekunden")

st.sidebar.markdown("")  # Spacing

if st.sidebar.button("🔄 Daten aktualisieren", use_container_width=True):
    st.rerun()

st.sidebar.markdown("")  # Spacing
st.sidebar.markdown("""
<div style="font-size: 0.75rem; color: #9ca3af; padding: 0.5rem 0; line-height: 1.6;">
    <p style="margin: 0.25rem 0;"><strong>HospitalFlow MVP v1.0</strong></p>
    <p style="margin: 0.25rem 0;">Nur aggregierte Daten</p>
    <p style="margin: 0.25rem 0;">Keine personenbezogenen Daten</p>
</div>
""", unsafe_allow_html=True)

# Professioneller Footer mit Datenschutz & Ethik
footer_timestamp = get_local_time().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(f"""
<div class="footer">
    <div class="footer-content">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2.5rem; margin-bottom: 2rem;">
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Datenschutz</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    Alle angezeigten Daten sind aggregiert und anonymisiert. Es werden keine personenbezogenen Gesundheitsdaten (PHI) oder Patientenkennungen gespeichert oder angezeigt. Die Daten dienen ausschließlich operativen Einblicken.
                </p>
            </div>
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Ethik</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    KI-Empfehlungen sind lediglich Vorschläge. Alle Entscheidungen verbleiben beim Menschen. Das Personal behält die volle Kontrolle über Entscheidungen zur Patientenversorgung. Das System unterstützt, ersetzt aber niemals das klinische Urteilsvermögen.
                </p>
            </div>
            <div>
                <h4 style="color: #111827; font-size: 0.9375rem; font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.01em;">Datennutzung</h4>
                <p style="color: #4b5563; font-size: 0.8125rem; line-height: 1.7; margin: 0;">
                    Kennzahlen, Prognosen und Empfehlungen basieren auf Mustern operativer Daten. Alle Aktionen werden im Prüfprotokoll für Transparenz und Nachvollziehbarkeit protokolliert.
                </p>
            </div>
        </div>
        <div style="text-align: center; padding-top: 1.5rem; border-top: 1px solid #e5e7eb;">
            <p style="color: #9ca3af; font-size: 0.75rem; margin: 0; font-weight: 500;">
                HospitalFlow MVP v1.0 • Entwickelt für den Krankenhausbetrieb • Letzte Aktualisierung: {footer_timestamp}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-Refresh implementieren
if auto_refresh:
    # Prüfe ob genug Zeit vergangen ist seit dem letzten Refresh
    if 'last_auto_refresh' not in st.session_state:
        st.session_state.last_auto_refresh = time.time()
    
    elapsed = time.time() - st.session_state.last_auto_refresh
    if elapsed >= refresh_seconds:
        st.session_state.last_auto_refresh = time.time()
        st.rerun()

