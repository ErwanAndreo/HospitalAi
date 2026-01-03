"""
HospitalFlow Simulation-Implementierung

Erweiterte Simulation mit korrelierten Metriken, Tageszeiten-Mustern,
Wochentags-Mustern und Demo-Modus-Logik für spezielle Ereignisse.
"""
import threading
import time
import random
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from database import HospitalDB


class HospitalSimulation:
    """Simulation für HospitalFlow mit korrelierten Metriken und Ereignissen"""
    
    def __init__(self, db: HospitalDB, demo_mode: bool = False):
        """
        Initialisiert die Simulation.
        
        Args:
            db: HospitalDB-Instanz
            demo_mode: Ob Demo-Modus aktiviert ist (für spezielle Ereignisse)
        """
        self.db = db
        self.demo_mode = demo_mode
        self.lock = threading.RLock()  # Use reentrant lock for consistency with database.py
        self.running = False
        self.update_thread = None
        
        # Basis-Metriken (Startwerte)
        self.state = {
            'ed_load': 65.0,  # Notaufnahme-Auslastung (%)
            'waiting_count': 5,  # Wartende Patienten
            'beds_free': 45,  # Freie Betten
            'staff_load': 70.0,  # Personal-Auslastung (%)
            'rooms_free': 12,  # Freie Räume
            'or_load': 60.0,  # OP-Auslastung (%)
            'transport_queue': 3,  # Transport-Warteschlange
            'inventory_risk_count': 1  # Anzahl kritischer Inventar-Artikel
        }
        
        # Aktive Ereignisse
        self.active_events = []
        
        # Trends für natürliche Schwankungen
        self.trends = {
            'ed_load': 0.0,
            'waiting_count': 0.0,
            'beds_free': 0.0,
            'staff_load': 0.0,
            'rooms_free': 0.0,
            'or_load': 0.0,
            'transport_queue': 0.0
        }
        
        # Metrik-Historie (für Vorhersagen)
        self.metric_history = {
            'ed_load': [],
            'waiting_count': [],
            'beds_free': [],
            'staff_load': [],
            'rooms_free': [],
            'or_load': [],
            'transport_queue': []
        }
        
        # Letzte Update-Zeit
        self.last_update = datetime.now(timezone.utc)
        
        # Starte Update-Thread
        self.start()
    
    def set_demo_mode(self, demo_mode: bool):
        """Setzt Demo-Modus und beendet aktive Ereignisse wenn ausgeschaltet"""
        with self.lock:
            old_mode = self.demo_mode
            self.demo_mode = demo_mode
            
            # Wenn Demo-Modus ausgeschaltet wird, beende alle aktiven Ereignisse
            if old_mode and not demo_mode:
                self.active_events = []
    
    def start(self):
        """Startet die kontinuierliche Simulation"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def stop(self):
        """Stoppt die Simulation"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=2)
    
    def _update_loop(self):
        """Haupt-Update-Schleife (läuft alle 5 Sekunden)"""
        while self.running:
            try:
                self.update()
                time.sleep(5)  # Alle 5 Sekunden
            except Exception as e:
                print(f"Fehler in Simulation-Update: {e}")
                time.sleep(5)
    
    def update(self):
        """Aktualisiert die Simulation (wird alle 5 Sekunden aufgerufen)"""
        with self.lock:
            now = datetime.now(timezone.utc)
            
            # Berechne Tageszeit-Faktor (0-1)
            hour = now.hour
            if 8 <= hour <= 12:  # Morgen-Spitze
                time_factor = 1.2
            elif 14 <= hour <= 18:  # Nachmittags-Spitze
                time_factor = 1.15
            elif 22 <= hour or hour < 6:  # Nacht (niedrig)
                time_factor = 0.7
            else:  # Übergangszeiten
                time_factor = 0.9
            
            # Wochentags-Faktor
            weekday = now.weekday()  # 0=Montag, 6=Sonntag
            if weekday >= 5:  # Wochenende
                weekday_factor = 0.85
            else:  # Wochentag
                weekday_factor = 1.0
            
            # Basis-Update für normale Metriken
            self._update_normal_metrics(time_factor, weekday_factor)
            
            # Patientenfluss-Simulation (Normalbetrieb)
            self._simulate_patient_arrivals(time_factor, weekday_factor)
            
            # Patienten-Entlassungen (mit Zeitbeschränkungen)
            discharged_departments = []
            for _ in range(3):  # Mehrere Entlassungen pro Zyklus möglich
                dept = self._simulate_patient_discharges(hour)
                if dept:
                    discharged_departments.append(dept)
            
            # Transport-Generierung für Entlassungen
            if discharged_departments:
                self._generate_transports_for_discharges(discharged_departments)
            
            # Materialverbrauch bei Operationen
            self._simulate_operation_material_consumption(self.state.get('or_load', 60.0))
            
            # Demo-Modus: Spezielle Ereignisse
            if self.demo_mode:
                self._check_and_trigger_events()
            
            # Aktualisiere aktive Ereignisse
            self._update_active_events()
            
            # Speichere Metriken in Datenbank
            self._save_metrics_to_db()
            
            # Generiere Alerts basierend auf Schwellenwerten
            self._generate_alerts()
            
            # Prüfe und aktiviere geplante Transporte
            self._check_and_activate_planned_transports()
            
            # Aktualisiere Historie
            self._update_history()
            
            self.last_update = now
    
    def _update_normal_metrics(self, time_factor: float, weekday_factor: float):
        """Aktualisiert normale Metriken basierend auf Tageszeit/Wochentag"""
        base_factor = time_factor * weekday_factor
        
        # ED Load (Notaufnahme-Auslastung)
        base_ed_load = 60.0
        variation = random.uniform(-3, 3)
        self.state['ed_load'] = max(20, min(95, base_ed_load * base_factor + variation))
        
        # Waiting Count (korreliert mit ED Load)
        ed_factor = self.state['ed_load'] / 100
        base_waiting = 3
        self.state['waiting_count'] = max(0, int(base_waiting + (ed_factor * 15) + random.uniform(-2, 2)))
        
        # Beds Free (invers korreliert mit ED Load)
        base_beds = 50
        beds_factor = 1 - (ed_factor * 0.3)  # Wenn ED hoch, weniger freie Betten
        self.state['beds_free'] = max(5, int(base_beds * beds_factor * base_factor + random.uniform(-3, 3)))
        
        # Staff Load (korreliert mit ED Load)
        self.state['staff_load'] = max(40, min(90, self.state['ed_load'] * 0.9 + random.uniform(-5, 5)))
        
        # Rooms Free (korreliert mit Beds Free)
        base_rooms = 15
        rooms_factor = self.state['beds_free'] / 50
        self.state['rooms_free'] = max(2, int(base_rooms * rooms_factor + random.uniform(-2, 2)))
        
        # OR Load (OP-Auslastung, unabhängiger)
        base_or_load = 55.0
        self.state['or_load'] = max(30, min(85, base_or_load * base_factor + random.uniform(-5, 5)))
        
        # Transport Queue (verzögert korreliert mit ED Load)
        # Transporte kommen etwas später als ED Load
        base_transport = 2
        transport_factor = ed_factor * 0.7  # Leicht verzögert
        self.state['transport_queue'] = max(0, int(base_transport + (transport_factor * 8) + random.uniform(-1, 1)))
    
    def _check_and_trigger_events(self):
        """Prüft und triggert spezielle Ereignisse (nur im Demo-Modus)"""
        now = datetime.now(timezone.utc)
        
        # Prüfe ob bereits ein ähnliches Ereignis aktiv ist
        active_types = [e['type'] for e in self.active_events]
        
        # Surge Event (Auslastungsspitze)
        if 'surge' not in active_types and random.random() < 0.15:  # 15% Chance alle 5 Sek = ~30-60% alle 15-30 Min
            self._trigger_surge_event()
        
        # Equipment Failure (Geräteausfall)
        if 'equipment_failure' not in active_types and random.random() < 0.08:  # 8% Chance alle 5 Sek = ~20-40% alle 20-40 Min
            self._trigger_equipment_failure()
        
        # Staffing Shortage (Personalengpass)
        if 'staffing_shortage' not in active_types and random.random() < 0.10:  # 10% Chance alle 5 Sek = ~25-50% alle 25-45 Min
            self._trigger_staffing_shortage()
        
        # ManV Event (Massenanfall von Verletzten) - nur im Demo-Modus
        if 'manv' not in active_types and random.random() < 0.05:  # 5% Chance alle 5 Sek = ~15-30% alle 30-60 Min
            self._trigger_manv_event()
    
    def _trigger_surge_event(self):
        """Triggert ein Surge Event (Auslastungsspitze)"""
        duration = random.randint(20, 60)  # 20-60 Minuten
        intensity = random.uniform(1.3, 1.8)  # 30-80% Erhöhung
        
        event = {
            'type': 'surge',
            'start_time': datetime.now(timezone.utc),
            'duration_minutes': duration,
            'intensity': intensity,
            'affected_departments': ['ER', 'ICU', 'Surgery', 'Cardiology'],
            'description': f'Auslastungsspitze (Intensität: {intensity:.1f}x)'
        }
        
        self.active_events.append(event)
        
        # Speichere in DB (thread-safe)
        self.db.create_simulation_event(
            'surge',
            event['start_time'],
            duration,
            event['affected_departments'],
            event['description'],
            intensity=intensity
        )
    
    def _trigger_equipment_failure(self):
        """Triggert einen Geräteausfall"""
        duration = random.randint(30, 120)  # 30-120 Minuten
        departments = ['ER', 'ICU', 'Surgery', 'Cardiology', 'Orthopedics', 'Urology', 'Gastroenterology', 'Geriatrics', 'SpineCenter', 'ENT', 'Radiology']
        affected_dept = random.choice(departments)
        
        event = {
            'type': 'equipment_failure',
            'start_time': datetime.now(timezone.utc),
            'duration_minutes': duration,
            'affected_departments': [affected_dept],
            'description': f'Geräteausfall in {affected_dept}'
        }
        
        self.active_events.append(event)
        
        # Speichere in DB (thread-safe)
        self.db.create_simulation_event(
            'equipment_failure',
            event['start_time'],
            duration,
            event['affected_departments'],
            event['description']
        )
    
    def _trigger_staffing_shortage(self):
        """Triggert einen Personalengpass"""
        duration = random.randint(60, 180)  # 60-180 Minuten
        departments = ['ER', 'ICU', 'Surgery', 'Cardiology', 'Orthopedics', 'Urology', 'Gastroenterology', 'Geriatrics', 'SpineCenter', 'ENT']
        affected_dept = random.choice(departments)
        
        event = {
            'type': 'staffing_shortage',
            'start_time': datetime.now(timezone.utc),
            'duration_minutes': duration,
            'affected_departments': [affected_dept],
            'description': f'Personalengpass in {affected_dept}'
        }
        
        self.active_events.append(event)
        
        # Speichere in DB (thread-safe)
        self.db.create_simulation_event(
            'staffing_shortage',
            event['start_time'],
            duration,
            event['affected_departments'],
            event['description']
        )
    
    def _update_active_events(self):
        """Aktualisiert aktive Ereignisse und wendet deren Effekte an"""
        now = datetime.now(timezone.utc)
        events_to_remove = []
        
        for event in self.active_events:
            elapsed = (now - event['start_time']).total_seconds() / 60
            remaining = event['duration_minutes'] - elapsed
            
            if remaining <= 0:
                events_to_remove.append(event)
                continue
            
            # Wende Event-Effekte an
            if event['type'] == 'surge':
                # Erhöhe ED Load und korrelierte Metriken
                surge_factor = event.get('intensity', 1.5)
                self.state['ed_load'] = min(98, self.state['ed_load'] * surge_factor)
                self.state['waiting_count'] = int(self.state['waiting_count'] * surge_factor)
                self.state['staff_load'] = min(95, self.state['staff_load'] * 1.2)
            
            elif event['type'] == 'equipment_failure':
                # Reduziere Effizienz in betroffener Abteilung
                dept = event['affected_departments'][0] if event['affected_departments'] else 'ER'
                if dept == 'ER':
                    self.state['ed_load'] = min(95, self.state['ed_load'] * 1.15)
                elif dept == 'ICU':
                    self.state['beds_free'] = max(0, int(self.state['beds_free'] * 0.9))
            
            elif event['type'] == 'staffing_shortage':
                # Erhöhe Personal-Auslastung
                self.state['staff_load'] = min(95, self.state['staff_load'] * 1.25)
                self.state['ed_load'] = min(95, self.state['ed_load'] * 1.1)
            
            elif event['type'] == 'manv':
                # ManV: Sehr starker Anstieg in Notaufnahme
                manv_factor = event.get('intensity', 2.5)
                self.state['ed_load'] = min(98, self.state['ed_load'] * manv_factor)
                self.state['waiting_count'] = int(self.state['waiting_count'] * manv_factor)
                self.state['staff_load'] = min(95, self.state['staff_load'] * 1.4)
                self.state['beds_free'] = max(0, int(self.state['beds_free'] * 0.7))  # Viele Betten belegt
        
        # Entferne abgelaufene Ereignisse
        for event in events_to_remove:
            self.active_events.remove(event)
            
            # Update DB (thread-safe)
            self.db.update_simulation_event_end_time(
                event['type'],
                event['start_time'],
                now
            )
    
    def _save_metrics_to_db(self):
        """Speichert aktuelle Metriken in die Datenbank (Batch-Operation für Effizienz)"""
        # Speichere alle Metriken in einem Batch
        metrics_to_save = [
            ('ed_load', self.state['ed_load'], '%', 'ER'),
            ('waiting_count', self.state['waiting_count'], '', 'ER'),
            ('beds_free', self.state['beds_free'], '', None),
            ('staff_load', self.state['staff_load'], '%', None),
            ('rooms_free', self.state['rooms_free'], '', None),
            ('or_load', self.state['or_load'], '%', 'Surgery'),
            ('transport_queue', self.state['transport_queue'], '', None)
        ]
        
        # Verwende Batch-Operation für bessere Performance und weniger Lock-Contention
        self.db.save_metrics_batch(metrics_to_save)
    
    def _generate_alerts(self):
        """Generiert Alerts basierend auf aktuellen Metriken und Schwellenwerten (thread-safe)"""
        now = datetime.now(timezone.utc)
        
        # ED Load Alert
        ed_load = self.state.get('ed_load', 0)
        if ed_load > 85:
            self.db.create_alert_safe(now, 'high', 'Hohe Notaufnahme-Auslastung', 'ER', 'ed_load', ed_load)
        elif ed_load > 75:
            self.db.create_alert_safe(now, 'medium', 'Erhöhte Notaufnahme-Auslastung', 'ER', 'ed_load', ed_load)
        
        # Waiting Count Alert
        waiting_count = self.state.get('waiting_count', 0)
        if waiting_count > 15:
            self.db.create_alert_safe(now, 'high', f'{waiting_count} wartende Patienten', 'ER', 'waiting_count', waiting_count)
        elif waiting_count > 10:
            self.db.create_alert_safe(now, 'medium', f'{waiting_count} wartende Patienten', 'ER', 'waiting_count', waiting_count)
        
        # Beds Free Alert
        beds_free = self.state.get('beds_free', 0)
        if beds_free < 5:
            self.db.create_alert_safe(now, 'high', f'Nur noch {beds_free} freie Betten', 'ICU', 'beds_free', beds_free)
        elif beds_free < 10:
            self.db.create_alert_safe(now, 'medium', f'Nur noch {beds_free} freie Betten', 'ICU', 'beds_free', beds_free)
        
        # Transport Queue Alert
        transport_queue = self.state.get('transport_queue', 0)
        if transport_queue > 8:
            self.db.create_alert_safe(now, 'high', f'Erhöhte Transport-Warteschlange ({transport_queue})', 'Logistics', 'transport_queue', transport_queue)
        elif transport_queue > 5:
            self.db.create_alert_safe(now, 'medium', f'Erhöhte Transport-Warteschlange ({transport_queue})', 'Logistics', 'transport_queue', transport_queue)
    
    def _update_history(self):
        """Aktualisiert Metrik-Historie (für Vorhersagen)"""
        now = datetime.now(timezone.utc)
        
        for metric_name in self.metric_history.keys():
            if metric_name in self.state:
                self.metric_history[metric_name].append({
                    'timestamp': now,
                    'value': self.state[metric_name]
                })
                
                # Behalte nur letzte 1000 Einträge
                if len(self.metric_history[metric_name]) > 1000:
                    self.metric_history[metric_name] = self.metric_history[metric_name][-1000:]
    
    def get_current_metrics(self) -> Dict:
        """Gibt aktuelle Simulationsmetriken zurück"""
        with self.lock:
            return self.state.copy()
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Dict]:
        """Gibt historische Metrikdaten zurück"""
        with self.lock:
            if metric_name not in self.metric_history:
                return []
            
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            history = self.metric_history[metric_name]
            
            # Filtere nach Zeit
            filtered = [h for h in history if h['timestamp'] >= cutoff]
            
            # Wenn nicht genug Daten, hole aus DB
            if len(filtered) < minutes // 5:
                db_metrics = self.db.get_metrics_last_n_minutes(minutes)
                db_filtered = [m for m in db_metrics if m['metric_type'] == metric_name]
                
                # Kombiniere mit Memory-Historie
                for m in db_filtered:
                    try:
                        ts = datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00'))
                        if ts >= cutoff:
                            filtered.append({
                                'timestamp': ts,
                                'value': m['value']
                            })
                    except:
                        pass
                
                # Sortiere nach Timestamp
                filtered.sort(key=lambda x: x['timestamp'])
            
            return filtered[-minutes:] if len(filtered) > minutes else filtered
    
    def _save_patient_event(self, event_type: str, department: str, patient_category: str = None):
        """Speichert anonymisiertes Patientenevent in Datenbank (thread-safe)"""
        self.db.save_patient_event(event_type, department, patient_category)
    
    def _simulate_patient_arrivals(self, time_factor: float, weekday_factor: float):
        """Simuliert Patienten-Ankünfte basierend auf Tageszeit/Wochentag"""
        base_factor = time_factor * weekday_factor
        
        # Wahrscheinlichkeit für Patienten-Ankunft (pro 5-Sekunden-Zyklus)
        # Angepasst an realistische Raten: 0.1-0.3 pro Zyklus = 12-36 Patienten pro Stunde
        arrival_probability = 0.15 * base_factor
        
        if random.random() < arrival_probability:
            # Welche Abteilung bekommt den Patienten?
            departments = ['ER', 'ICU', 'Cardiology', 'Surgery', 'Orthopedics', 
                          'Urology', 'Gastroenterology', 'Geriatrics', 'SpineCenter', 'ENT']
            weights = [0.35, 0.15, 0.1, 0.1, 0.08, 0.05, 0.05, 0.04, 0.03, 0.05]  # ER hat höchste Wahrscheinlichkeit
            department = random.choices(departments, weights=weights)[0]
            
            patient_category = 'Notfall' if department == 'ER' else 'Planung'
            
            # Speichere Event
            self._save_patient_event('admission', department, patient_category)
            
            # Aktualisiere Metriken
            if department == 'ER':
                # Erhöhe ED Load leicht
                self.state['ed_load'] = min(95, self.state['ed_load'] + random.uniform(1, 3))
                self.state['waiting_count'] = max(0, int(self.state['waiting_count'] + random.uniform(0.5, 1.5)))
            
            # Reduziere freie Betten (wenn Patient stationär aufgenommen wird)
            if random.random() < 0.7:  # 70% werden stationär aufgenommen
                self.state['beds_free'] = max(0, int(self.state['beds_free'] - 1))
    
    def _simulate_patient_discharges(self, hour: int):
        """Simuliert Patienten-Entlassungen mit Zeitbeschränkungen"""
        # Zeitbeschränkung: Zwischen 20:00-06:00 Uhr unterschiedliche Wahrscheinlichkeiten
        if 20 <= hour or hour < 6:
            # Notaufnahme: reduzierte Wahrscheinlichkeit in der Nacht
            er_probability = 0.15  # 15% Entlassungswahrscheinlichkeit in der Nacht
            
            # Alle anderen Abteilungen: 10% Wahrscheinlichkeit
            other_departments = ['ICU', 'Cardiology', 'Surgery', 'Orthopedics',
                                'Urology', 'Gastroenterology', 'Geriatrics', 'SpineCenter', 'ENT']
            other_probability = 0.10  # 10% für andere Abteilungen
            
            # Prüfe beide unabhängig (können beide entlassen werden)
            department = None
            if random.random() < er_probability:
                department = 'ER'
            elif random.random() < other_probability:
                department = random.choice(other_departments)
            
            if department is None:
                return None
            
        elif 6 <= hour < 12:
            # Hauptzeit: 06:00-12:00 Uhr
            discharge_departments = ['ER', 'ICU', 'Cardiology', 'Surgery', 'Orthopedics',
                                     'Urology', 'Gastroenterology', 'Geriatrics', 'SpineCenter', 'ENT']
            discharge_probability = 0.35  # Erhöhte Rate tagsüber
            if random.random() < discharge_probability:
                department = random.choice(discharge_departments)
            else:
                return None
        else:  # 12-20 Uhr
            discharge_departments = ['ER', 'ICU', 'Cardiology', 'Surgery', 'Orthopedics',
                                     'Urology', 'Gastroenterology', 'Geriatrics', 'SpineCenter', 'ENT']
            discharge_probability = 0.25  # Erhöhte Rate tagsüber
            if random.random() < discharge_probability:
                department = random.choice(discharge_departments)
            else:
                return None
        
        # Speichere Event
        self._save_patient_event('discharge', department, 'Entlassung')
        
        # Erhöhe freie Betten
        self.state['beds_free'] = min(100, int(self.state['beds_free'] + 1))
        
        # Wenn Notaufnahme: Reduziere ED Load
        if department == 'ER':
            self.state['ed_load'] = max(20, self.state['ed_load'] - random.uniform(1, 2))
            self.state['waiting_count'] = max(0, int(self.state['waiting_count'] - 1))
        
        return department  # Rückgabe für Transport-Generierung
    
    def _generate_transports_for_discharges(self, discharged_departments: List[str]):
        """Generiert Transporte für 15-25% der Entlassungen"""
        if not discharged_departments:
            return
        
        # 15-25% der Entlassungen bekommen Transport
        transport_probability = random.uniform(0.15, 0.25)
        
        transport_destinations = [
            # Deutsche Städte
            'Berlin', 'München', 'Hamburg', 'Köln', 'Frankfurt', 'Stuttgart',
            'Düsseldorf', 'Dortmund', 'Essen', 'Leipzig', 'Bremen', 'Dresden',
            # Lokale Ziele
            'Apotheke', 'Physiotherapie', 'Massage', 'Reha-Zentrum', 'Ambulante Betreuung'
        ]
        
        for department in discharged_departments:
            if random.random() < transport_probability:
                destination = random.choice(transport_destinations)
                priority = random.choice(['medium', 'low'])  # Entlassungstransporte meist nicht kritisch
                
                try:
                    self.db.create_patient_transport(
                        from_location=department,
                        to_location=destination,
                        priority=priority,
                        estimated_time_minutes=random.randint(15, 60)
                    )
                    # Erhöhe Transport-Warteschlange
                    self.state['transport_queue'] = min(20, int(self.state['transport_queue'] + 1))
                except Exception as e:
                    # Fehler bei Transport-Erstellung ignorieren (z.B. DB-Lock)
                    pass
    
    def _simulate_operation_material_consumption(self, or_load: float):
        """Simuliert Materialverbrauch bei Operationen"""
        # Wenn OP-Auslastung hoch ist, generiere Operationen
        if or_load > 40:  # Mindest-Auslastung für OPs
            # Wahrscheinlichkeit für OP (pro Zyklus)
            op_probability = (or_load / 100) * 0.3  # Maximal 30% Chance bei 100% Auslastung
            
            if random.random() < op_probability:
                # OP-Abteilungen und Typen
                op_departments = {
                    'Surgery': ['Herz-OP', 'Bauch-OP', 'Gefäß-OP', 'Thorax-OP'],
                    'Cardiology': ['Herzkatheter', 'Angioplastie', 'Schrittmacher-Implantation'],
                    'Orthopedics': ['Knie-OP', 'Hüft-OP', 'Schulter-OP'],
                    'Urology': ['Prostata-OP', 'Nieren-OP', 'Blasen-OP'],
                    'Gastroenterology': ['Endoskopie', 'Koloskopie', 'Laparoskopie'],
                    'SpineCenter': ['Wirbelsäulen-OP', 'Bandscheiben-OP']
                }
                
                department = random.choice(list(op_departments.keys()))
                op_type = random.choice(op_departments[department])
                duration = random.randint(30, 240)  # 30-240 Minuten
                
                # Speichere Operation in Datenbank (thread-safe)
                now = datetime.now(timezone.utc)
                self.db.create_operation(
                    op_type,
                    department,
                    'completed',
                    duration,
                    now,
                    now - timedelta(minutes=duration)
                )
                
                # Material-Verbrauch basierend auf OP-Typ/Abteilung
                inventory_items = self.db.get_inventory_status()
                department_items = [item for item in inventory_items if item.get('department') == department]
                
                if department_items:
                    # Wähle 1-3 Material-Artikel zufällig aus
                    num_items = random.randint(1, min(3, len(department_items)))
                    selected_items = random.sample(department_items, num_items)
                    
                    for item in selected_items:
                        # Zufälliger Verbrauch: 1-5 Einheiten (ganzzahlig)
                        consumption_amount = random.randint(1, 5)
                        
                        # Aktualisiere Bestand (thread-safe)
                        self.db.update_inventory_consumption(
                            item['id'],
                            consumption_amount,
                            or_load / 100.0
                        )
    
    def _trigger_manv_event(self):
        """Triggert ein ManV Event (Massenanfall von Verletzten) - nur Demo-Modus"""
        duration = random.randint(30, 90)  # 30-90 Minuten
        intensity = random.uniform(2.0, 3.0)  # 2.0-3.0x stärker als normales Surge
        
        event = {
            'type': 'manv',
            'start_time': datetime.now(timezone.utc),
            'duration_minutes': duration,
            'intensity': intensity,
            'affected_departments': ['ER', 'ICU', 'Surgery'],
            'description': f'ManV - Massenanfall von Verletzten (Intensität: {intensity:.1f}x)'
        }
        
        self.active_events.append(event)
        
        # Speichere in DB (thread-safe)
        self.db.create_simulation_event(
            'manv',
            event['start_time'],
            duration,
            event['affected_departments'],
            event['description'],
            intensity=intensity
        )
    
    def apply_recommendation_effect(self, rec_type: str, effect_name: str, duration_minutes: int = 30):
        """Wendet Empfehlungseffekt an"""
        with self.lock:
            if effect_name == 'staffing_reassignment':
                # Reduziere ED Load und Waiting Count
                self.state['ed_load'] = max(20, self.state['ed_load'] - 8)
                self.state['waiting_count'] = max(0, int(self.state['waiting_count'] - 2))
                self.state['staff_load'] = min(95, self.state['staff_load'] + 5)
            
            elif effect_name == 'open_overflow_beds':
                # Erhöhe freie Betten
                self.state['beds_free'] += 3
                self.state['ed_load'] = max(20, self.state['ed_load'] - 5)
            
            elif effect_name == 'room_allocation':
                # Erhöhe freie Räume
                self.state['rooms_free'] += 2
    
    def calculate_planned_start_time(self, estimated_time_minutes: int = 15) -> datetime:
        """
        Berechnet eine realistische geplante Startzeit für einen Transport.
        
        Args:
            estimated_time_minutes: Geschätzte Fahrzeit in Minuten
        
        Returns:
            datetime: Geplante Startzeit (UTC)
        """
        now = datetime.now(timezone.utc)
        
        # Basis-Vorbereitungszeit: 5-10 Minuten
        preparation_time = random.randint(5, 10)
        
        # Wartezeit basierend auf Transport-Warteschlange
        # Jeder Transport in der Queue = ~10-15 Minuten zusätzliche Wartezeit
        transport_queue = self.state.get('transport_queue', 0)
        queue_wait_time = transport_queue * random.uniform(10, 15)
        
        # Priorität kann die Wartezeit beeinflussen (wird später über priority-Parameter erweitert)
        # Für jetzt: Standard-Wartezeit
        
        # Gesamte Wartezeit = Vorbereitung + Queue-Wartezeit
        total_wait_minutes = preparation_time + queue_wait_time
        
        # Mindest-Wartezeit: 5 Minuten (auch bei leerer Queue)
        total_wait_minutes = max(5, total_wait_minutes)
        
        # Berechne geplante Startzeit
        planned_start = now + timedelta(minutes=total_wait_minutes)
        
        return planned_start
    
    def _check_and_activate_planned_transports(self):
        """Prüft geplante Transporte und aktiviert sie, wenn die geplante Zeit erreicht ist"""
        now = datetime.now(timezone.utc)
        
        try:
            # Hole alle Transporte mit Status 'planned'
            all_transports = self.db.get_transport_requests()
            planned_transports = [t for t in all_transports if t.get('status') == 'planned']
            
            for transport in planned_transports:
                planned_start_time_str = transport.get('planned_start_time')
                if not planned_start_time_str:
                    continue
                
                try:
                    # Parse geplante Startzeit
                    if isinstance(planned_start_time_str, str):
                        planned_start_time = datetime.fromisoformat(planned_start_time_str.replace('Z', '+00:00'))
                    else:
                        planned_start_time = planned_start_time_str
                    
                    # Wenn geplante Zeit erreicht oder überschritten
                    if planned_start_time <= now:
                        transport_id = transport['id']
                        estimated_time = transport.get('estimated_time_minutes', 15)
                        
                        # Berechne erwartete Abschlusszeit
                        expected_completion = now + timedelta(minutes=estimated_time)
                        delay_minutes = 0
                        
                        # 15% Chance auf Verzögerung beim Aktivieren (Stau o.ä.)
                        if random.random() < 0.15:
                            # 20-50% der geplanten Dauer als Verzögerung
                            delay_percentage = random.uniform(0.2, 0.5)
                            delay_minutes = int(estimated_time * delay_percentage)
                            expected_completion = expected_completion + timedelta(minutes=delay_minutes)
                        
                        expected_completion_str = expected_completion.isoformat()
                        
                        # Setze Status auf 'in_progress' und setze start_time
                        update_kwargs = {
                            'status': 'in_progress',
                            'start_time': now.isoformat(),
                            'expected_completion_time': expected_completion_str
                        }
                        if delay_minutes > 0:
                            update_kwargs['delay_minutes'] = delay_minutes
                        
                        self.db.update_transport_status(transport_id, **update_kwargs)
                except Exception as e:
                    # Fehler bei einzelnen Transporten ignorieren
                    pass
        except Exception as e:
            # Fehler beim Abrufen der Transporte ignorieren
            pass

