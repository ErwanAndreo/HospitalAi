"""
Simulations-Engine für HospitalFlow
Stellt korrelierte Signale, Ereignisse und realistisches Verhalten bereit
"""
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import math


class HospitalSimulation:
    def __init__(self):
        self.state = {
            'ed_load': 65.0,  # 0-100%
            'waiting_count': 8,
            'beds_free': 45,
            'staff_load': 72.0,  # 0-100%
            'rooms_free': 12,
            'or_load': 58.0,  # 0-100%
            'transport_queue': 3,
            'inventory_risk_count': 2,
        }
        
        self.base_state = self.state.copy()
        self.trends = {
            'ed_load': 0.0,  # -1 to 1, trend direction
            'waiting_count': 0.0,
            'beds_free': 0.0,
            'staff_load': 0.0,
        }
        
        self.active_events = []  # List of active surge events
        self.recommendation_effects = {}  # Track active recommendation effects
        self.last_update = datetime.now(timezone.utc)
    
    def update(self, minutes_passed: int = 1):
        """Simulationsstatus basierend auf vergangener Zeit aktualisieren"""
        now = datetime.now(timezone.utc)
        
        # Remove expired events
        self.active_events = [
            e for e in self.active_events 
            if (now - e['start_time']).total_seconds() < e['duration_minutes'] * 60
        ]
        
        # Remove expired recommendation effects
        expired_effects = [
            k for k, v in self.recommendation_effects.items()
            if (now - v['start_time']).total_seconds() > v['duration_minutes'] * 60
        ]
        for k in expired_effects:
            del self.recommendation_effects[k]
        
        # Update trends based on current state
        self._update_trends()
        
        # Apply correlations
        self._apply_correlations()
        
        # Apply active events
        self._apply_events()
        
        # Apply recommendation effects
        self._apply_recommendation_effects()
        
        # Add natural variation
        self._add_natural_variation()
        
        # Ensure bounds
        self._enforce_bounds()
        
        self.last_update = now
    
    def _update_trends(self):
        """Trendrichtungen basierend auf aktuellem Zustand aktualisieren"""
        # ED load trend: tends to drift toward 70% if no intervention
        if self.state['ed_load'] < 70:
            self.trends['ed_load'] = min(0.3, self.trends['ed_load'] + 0.05)
        else:
            self.trends['ed_load'] = max(-0.3, self.trends['ed_load'] - 0.05)
        
        # Add some randomness to trends
        self.trends['ed_load'] += random.uniform(-0.1, 0.1)
        self.trends['ed_load'] = max(-1.0, min(1.0, self.trends['ed_load']))
    
    def _apply_correlations(self):
        """Korrigierte Signale anwenden"""
        # When ED load rises, waiting_count tends to rise
        if self.state['ed_load'] > 75:
            self.state['waiting_count'] += random.uniform(0.5, 1.5) * (self.state['ed_load'] - 75) / 25
        elif self.state['ed_load'] < 60:
            self.state['waiting_count'] -= random.uniform(0.2, 0.8)
        
        # Staff load rises with ED load (with some delay/smoothing)
        target_staff_load = 50 + (self.state['ed_load'] * 0.5)
        self.state['staff_load'] = self.state['staff_load'] * 0.8 + target_staff_load * 0.2
        
        # Transport queue rises with delay when ED load is high
        if self.state['ed_load'] > 70:
            self.state['transport_queue'] += random.uniform(0.1, 0.3)
        elif self.state['ed_load'] < 65:
            self.state['transport_queue'] = max(0, self.state['transport_queue'] - random.uniform(0.1, 0.2))
        
        # Beds free tends to drop when ED load is high
        if self.state['ed_load'] > 75:
            self.state['beds_free'] = max(0, self.state['beds_free'] - random.uniform(0.2, 0.5))
        elif self.state['ed_load'] < 60:
            self.state['beds_free'] += random.uniform(0.1, 0.3)
        
        # Rooms free correlates with beds free
        if self.state['beds_free'] < 10:
            self.state['rooms_free'] = max(0, self.state['rooms_free'] - random.uniform(0.1, 0.3))
    
    def _apply_events(self):
        """Aktive Auslastungsereignisse anwenden"""
        for event in self.active_events:
            intensity = event['intensity']
            elapsed = (datetime.now(timezone.utc) - event['start_time']).total_seconds() / 60
            
            # Event effect decreases over time
            decay = 1.0 - (elapsed / event['duration_minutes'])
            if decay > 0:
                # Surge increases ED load, waiting count, decreases beds free
                self.state['ed_load'] = min(100, self.state['ed_load'] + intensity * decay * 15)
                self.state['waiting_count'] += intensity * decay * 3
                self.state['beds_free'] = max(0, self.state['beds_free'] - intensity * decay * 2)
                self.state['staff_load'] = min(100, self.state['staff_load'] + intensity * decay * 10)
    
    def _apply_recommendation_effects(self):
        """Effekte aus akzeptierten Empfehlungen anwenden"""
        for effect_name, effect in self.recommendation_effects.items():
            elapsed = (datetime.now(timezone.utc) - effect['start_time']).total_seconds() / 60
            remaining = max(0, effect['duration_minutes'] - elapsed)
            
            if remaining > 0:
                # Decay effect over time
                strength = remaining / effect['duration_minutes']
                
                if effect_name == 'staffing_reassignment':
                    # Reduces ED load and waiting count
                    self.state['ed_load'] = max(0, self.state['ed_load'] - strength * 8)
                    self.state['waiting_count'] = max(0, self.state['waiting_count'] - strength * 2)
                    self.state['staff_load'] = max(0, self.state['staff_load'] - strength * 5)
                
                elif effect_name == 'open_overflow_beds':
                    # Increases beds free, reduces ED load
                    self.state['beds_free'] += strength * 3
                    self.state['ed_load'] = max(0, self.state['ed_load'] - strength * 5)
                
                elif effect_name == 'room_allocation':
                    # Increases rooms free
                    self.state['rooms_free'] += strength * 2
    
    def _add_natural_variation(self):
        """Natürliche zufällige Variation zu allen Metriken hinzufügen"""
        self.state['ed_load'] += random.uniform(-2, 2)
        self.state['waiting_count'] += random.uniform(-0.5, 0.5)
        self.state['beds_free'] += random.uniform(-0.3, 0.3)
        self.state['staff_load'] += random.uniform(-1, 1)
        self.state['rooms_free'] += random.uniform(-0.2, 0.2)
        self.state['or_load'] += random.uniform(-1.5, 1.5)
        self.state['transport_queue'] += random.uniform(-0.2, 0.2)
    
    def _enforce_bounds(self):
        """Sicherstellen, dass alle Metriken innerhalb gültiger Grenzen bleiben"""
        self.state['ed_load'] = max(0, min(100, self.state['ed_load']))
        self.state['waiting_count'] = max(0, int(self.state['waiting_count']))
        self.state['beds_free'] = max(0, int(self.state['beds_free']))
        self.state['staff_load'] = max(0, min(100, self.state['staff_load']))
        self.state['rooms_free'] = max(0, int(self.state['rooms_free']))
        self.state['or_load'] = max(0, min(100, self.state['or_load']))
        self.state['transport_queue'] = max(0, int(self.state['transport_queue']))
        self.state['inventory_risk_count'] = max(0, int(self.state['inventory_risk_count']))
    
    def trigger_surge_event(self, intensity: float = 1.0, duration_minutes: int = None):
        """Auslastungsereignis auslösen"""
        if duration_minutes is None:
            duration_minutes = random.randint(10, 20)
        
        event = {
            'start_time': datetime.now(timezone.utc),
            'duration_minutes': duration_minutes,
            'intensity': intensity,
            'type': 'surge'
        }
        self.active_events.append(event)
        return event
    
    def apply_discharge_event(self, count: int = 1):
        """Entlassungsereignisse simulieren (erhöht freie Betten)"""
        self.state['beds_free'] += count
        # Discharges reduce ED load slightly (patients leaving)
        self.state['ed_load'] = max(0, self.state['ed_load'] - count * 2)
        self._enforce_bounds()
    
    def apply_recommendation_effect(self, rec_type: str, effect_name: str, duration_minutes: int = 30):
        """Effekt aus akzeptierter Empfehlung anwenden"""
        self.recommendation_effects[effect_name] = {
            'start_time': datetime.now(timezone.utc),
            'duration_minutes': duration_minutes,
            'rec_type': rec_type
        }
    
    def get_current_metrics(self) -> Dict:
        """Aktuellen Simulationsstatus abrufen"""
        self.update()
        return self.state.copy()
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[Dict]:
        """Historische Werte für eine Metrik (simuliert) abrufen"""
        # For MVP, generate realistic historical data based on current state
        history = []
        now = datetime.now(timezone.utc)
        current_value = self.state.get(metric_name, 0)
        
        # Generate trend-based history
        for i in range(minutes, -1, -5):
            timestamp = now - timedelta(minutes=i)
            # Add some variation and trend
            variation = random.uniform(-5, 5) if metric_name in ['ed_load', 'staff_load', 'or_load'] else random.uniform(-2, 2)
            trend_factor = (minutes - i) / minutes * 0.1  # Slight trend
            value = current_value + variation - trend_factor * 5
            
            # Enforce bounds
            if metric_name in ['ed_load', 'staff_load', 'or_load']:
                value = max(0, min(100, value))
            else:
                value = max(0, value)
            
            history.append({
                'timestamp': timestamp,
                'value': value
            })
        
        return history
    
    def should_trigger_surge(self, demo_mode: bool = False) -> bool:
        """Bestimmen, ob ein Auslastungsereignis ausgelöst werden soll (Zufall)"""
        # 5% chance per update cycle, 20% in demo mode
        chance = 0.20 if demo_mode else 0.05
        return random.random() < chance
    
    def simulate_operations(self) -> List[Dict]:
        """
        Simuliere neue Operationen basierend auf OR Load.
        
        Returns:
            Liste von Dictionaries mit Operationen-Daten (operation_type, department, status, duration_minutes)
        """
        operations = []
        or_load = self.state.get('or_load', 58.0)
        
        # Operationen-Wahrscheinlichkeit basierend auf OR Load
        # Höhere OR Load → mehr Operationen
        # Bei 50% Load: ~1-2 Operationen alle 10 Minuten
        # Bei 100% Load: ~3-5 Operationen alle 10 Minuten
        base_ops_per_cycle = (or_load / 100.0) * 3.0  # 0-3 Operationen
        num_operations = max(0, int(base_ops_per_cycle + random.uniform(-0.5, 0.5)))
        
        # Operationstypen nach Abteilung
        operation_depts = {
            "Chirurgie": ["Appendektomie", "Cholezystektomie", "Darmresektion", "Laparotomie", "Hernien-OP"],
            "Orthopädie": ["Gelenkersatz", "Knochenbruch-OP", "Arthroskopie", "Sehnenreparatur", "Wirbelsäulen-OP"],
            "Urologie": ["Prostata-OP", "Nierenstein-OP", "Blasen-OP", "Zystoskopie", "Lithotripsie"],
            "HNO": ["Tonsillektomie", "Nasenscheidewand-OP", "Polypen-OP", "Ohren-OP", "Kehlkopf-OP"],
            "Kardiologie": ["Herzkatheter", "Stent-Implantation", "Schrittmacher-OP"],
            "Gastroenterologie": ["Magen-Darm-Spiegelung", "Polypenentfernung", "ERCP"],
        }
        
        # Abteilungs-Wahrscheinlichkeiten (Chirurgie und Orthopädie mehr als andere)
        dept_weights = {
            "Chirurgie": 0.35,
            "Orthopädie": 0.25,
            "Urologie": 0.15,
            "HNO": 0.10,
            "Kardiologie": 0.10,
            "Gastroenterologie": 0.05,
        }
        
        for _ in range(num_operations):
            # Wähle Abteilung basierend auf Gewichtungen
            dept = random.choices(
                list(dept_weights.keys()),
                weights=list(dept_weights.values())
            )[0]
            
            # Wähle Operationstyp aus Abteilung
            op_types = operation_depts.get(dept, ["Standard-OP"])
            operation_type = random.choice(op_types)
            
            # Status: neue Operationen sind "geplant"
            status = "geplant"
            
            # Dauer: 30-180 Minuten, abhängig von Operationstyp
            if "Katarakt" in operation_type or "Spiegelung" in operation_type:
                duration_minutes = random.randint(20, 60)
            elif "Appendektomie" in operation_type or "Hernien" in operation_type:
                duration_minutes = random.randint(45, 90)
            elif "Gelenkersatz" in operation_type or "Resektion" in operation_type:
                duration_minutes = random.randint(90, 180)
            else:
                duration_minutes = random.randint(30, 120)
            
            operations.append({
                'operation_type': operation_type,
                'department': dept,
                'status': status,
                'duration_minutes': duration_minutes,
                'planned_start_time': datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=random.randint(0, 60))
            })
        
        return operations
    
    def simulate_external_transports(self) -> List[Dict]:
        """
        Simuliere externe Transporte (zur Apotheke, zur Therapie oder ins Heimatland/Heimatstadt).
        
        Returns:
            Liste von Dictionaries mit Transport-Daten (from_location, to_location, priority, transport_type)
        """
        transports = []
        
        # Wahrscheinlichkeit: 35-45% Chance pro Zyklus, dass ein externer Transport erstellt wird
        # Erhöht von 15% auf 40% für mehr Transporte
        if random.random() < 0.40:
            # Gewichtete Auswahl: Apotheke, Therapie und Heimatstadt haben ähnliche Wahrscheinlichkeiten
            transport_type = random.choices(
                ['pharmacy', 'therapy', 'home'],
                weights=[0.35, 0.35, 0.30]  # 35% Apotheke, 35% Therapie, 30% Heimatstadt
            )[0]
            
            # Abteilungen, von denen Patienten entlassen werden können
            hospital_departments = [
                "Notaufnahme", "Intensivstation", "Chirurgie", "Orthopädie", 
                "Kardiologie", "Neurologie", "Innere Medizin", "Pädiatrie"
            ]
            from_location = random.choice(hospital_departments)
            
            if transport_type == 'pharmacy':
                # Transport zur Apotheke
                to_location = "Apotheke"
                priority = random.choice(['medium', 'low'])  # Meist nicht dringend
                estimated_time = random.randint(10, 25)  # 10-25 Minuten
            elif transport_type == 'therapy':
                # Transport zur Therapiestunde
                therapy_locations = [
                    "Physiotherapie", "Ergotherapie", "Logopädie", 
                    "Psychotherapie", "Rehabilitation"
                ]
                to_location = random.choice(therapy_locations)
                priority = random.choice(['medium', 'low'])  # Meist mittlere bis niedrige Priorität
                estimated_time = random.randint(15, 35)  # 15-35 Minuten
            else:  # home
                # Transport ins Heimatland/Heimatstadt (oder zum Krankenhaus dort)
                home_locations = [
                    "Berlin", "München", "Hamburg", "Köln", "Frankfurt", 
                    "Stuttgart", "Düsseldorf", "Dortmund", "Essen", "Leipzig",
                    "Wien", "Zürich", "Amsterdam", "Prag", "Warschau",
                    "Paris", "Brüssel", "Kopenhagen", "Stockholm", "Oslo"
                ]
                # Manchmal direkt zum Krankenhaus in der Heimatstadt
                if random.random() < 0.4:  # 40% Chance zum Krankenhaus
                    to_location = f"Krankenhaus {random.choice(home_locations)}"
                else:
                    to_location = random.choice(home_locations)
                priority = random.choice(['low', 'medium'])  # Meist niedrige Priorität
                estimated_time = random.randint(30, 120)  # 30-120 Minuten (längere Fahrt)
            
            transports.append({
                'from_location': from_location,
                'to_location': to_location,
                'priority': priority,
                'estimated_time_minutes': estimated_time,
                'transport_type': transport_type,
                'request_type': 'patient'
            })
        
        return transports


# Global simulation instance
_simulation_instance: Optional[HospitalSimulation] = None


def get_simulation() -> HospitalSimulation:
    """Globale Simulationsinstanz abrufen oder erstellen"""
    global _simulation_instance
    if _simulation_instance is None:
        _simulation_instance = HospitalSimulation()
    return _simulation_instance


def reset_simulation():
    """Simulation zurücksetzen (nützlich für Tests)"""
    global _simulation_instance
    _simulation_instance = None

