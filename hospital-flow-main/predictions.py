"""
HospitalFlow Vorhersage-Algorithmen

Algorithmen-basierte Vorhersagen, die KI-Verhalten simulieren.
Verwendet statistische Methoden und simulierte ML-Ansätze.
"""
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from database import HospitalDB


class PredictionEngine:
    """Engine für Vorhersagen mit algorithmen-basierten Methoden"""
    
    def __init__(self, db: HospitalDB):
        """
        Initialisiert die Vorhersage-Engine.
        
        Args:
            db: HospitalDB-Instanz
        """
        self.db = db
    
    def predict_patient_arrival(self, time_horizon_minutes: int, department: str = 'ER') -> Dict:
        """
        Vorhersage für Patientenzugang.
        
        Args:
            time_horizon_minutes: Zeithorizont in Minuten (5, 10, 15)
            department: Abteilung
            
        Returns:
            Dict mit predicted_value, confidence, etc.
        """
        # Hole historische Daten
        history = self.db.get_metrics_last_n_minutes(60)
        patient_history = [m for m in history if m['metric_type'] == 'waiting_count']
        
        # Basis-Vorhersage mit Moving Average
        if len(patient_history) >= 3:
            recent_values = [m['value'] for m in patient_history[-12:]]  # Letzte 12 Einträge (1 Stunde)
            moving_avg = np.mean(recent_values)
            
            # Trend-Berechnung
            if len(recent_values) >= 2:
                trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
            else:
                trend = 0
            
            # Tageszeit-Faktor
            now = datetime.now(timezone.utc)
            hour = now.hour
            if 8 <= hour <= 12:
                time_factor = 1.3
            elif 14 <= hour <= 18:
                time_factor = 1.2
            elif 22 <= hour or hour < 6:
                time_factor = 0.6
            else:
                time_factor = 0.9
            
            # Wochentags-Faktor
            weekday = now.weekday()
            weekday_factor = 0.85 if weekday >= 5 else 1.0
            
            # Vorhergesagter Wert
            base_prediction = moving_avg + (trend * (time_horizon_minutes / 5))
            predicted_value = base_prediction * time_factor * weekday_factor
            
            # Konfidenz basierend auf Datenqualität
            confidence = min(0.95, 0.6 + (len(patient_history) / 20) * 0.35)
            
            # Anpassung für Zeithorizont (länger = weniger Konfidenz)
            confidence *= (1 - (time_horizon_minutes / 60) * 0.2)
        else:
            # Fallback ohne Historie
            predicted_value = 5.0
            confidence = 0.5
        
        return {
            'prediction_type': 'patient_arrival',
            'predicted_value': max(0, int(predicted_value)),
            'confidence': max(0.3, confidence),
            'time_horizon_minutes': time_horizon_minutes,
            'department': department,
            'model_version': 'v1.0-statistical'
        }
    
    def predict_bed_demand(self, time_horizon_minutes: int, department: str = 'ICU') -> Dict:
        """
        Vorhersage für Bettenbedarf.
        
        Args:
            time_horizon_minutes: Zeithorizont in Minuten (15, 30, 60)
            department: Abteilung
            
        Returns:
            Dict mit predicted_value (als %), confidence, etc.
        """
        # Hole Kapazitätsdaten
        capacity = self.db.get_capacity_overview()
        dept_capacity = next((c for c in capacity if c['department'] == department), None)
        
        if not dept_capacity:
            return {
                'prediction_type': 'bed_demand',
                'predicted_value': 75.0,
                'confidence': 0.5,
                'time_horizon_minutes': time_horizon_minutes,
                'department': department,
                'model_version': 'v1.0-statistical'
            }
        
        current_utilization = dept_capacity.get('utilization_percent', 75.0)
        
        # Hole historische Metriken
        history = self.db.get_metrics_last_n_minutes(120)  # 2 Stunden
        bed_history = [m for m in history if m['metric_type'] == 'beds_free']
        
        # Berechne Trend
        if len(bed_history) >= 3:
            recent_beds = [m['value'] for m in bed_history[-24:]]  # Letzte 24 Einträge
            bed_trend = (recent_beds[-1] - recent_beds[0]) / len(recent_beds) if len(recent_beds) > 1 else 0
            
            # Konvertiere zu Auslastung
            total_beds = dept_capacity.get('total_beds', 20)
            current_free = recent_beds[-1] if recent_beds else total_beds * 0.25
            current_occupied = total_beds - current_free
            
            # Vorhersage: Wie viele Betten werden in X Minuten belegt sein?
            # Annahme: Aktueller Trend setzt sich fort
            minutes_factor = time_horizon_minutes / 60  # Stunden
            predicted_occupied = current_occupied + (bed_trend * minutes_factor * -1)  # Negativ weil weniger frei = mehr belegt
            predicted_utilization = (predicted_occupied / total_beds) * 100 if total_beds > 0 else current_utilization
            
            # Begrenze auf realistische Werte
            predicted_utilization = max(10, min(98, predicted_utilization))
            
            # Konfidenz
            confidence = min(0.9, 0.5 + (len(bed_history) / 30) * 0.4)
            confidence *= (1 - (time_horizon_minutes / 120) * 0.15)  # Länger = weniger Konfidenz
        else:
            # Fallback
            predicted_utilization = current_utilization
            confidence = 0.5
        
        return {
            'prediction_type': 'bed_demand',
            'predicted_value': predicted_utilization,
            'confidence': max(0.3, confidence),
            'time_horizon_minutes': time_horizon_minutes,
            'department': department,
            'model_version': 'v1.0-statistical'
        }
    
    def generate_predictions(self, time_horizons: List[int] = [5, 10, 15]) -> List[Dict]:
        """
        Generiert genau 12 Vorhersagen über alle Abteilungen hinweg.
        
        Verteilung:
        - 6 Patientenzugang-Vorhersagen: 2 Abteilungen × 3 Zeithorizonte (5, 10, 15 Min)
        - 6 Bettenbedarf-Vorhersagen: 2 Abteilungen × 3 Zeithorizonte (5, 10, 15 Min)
        
        Args:
            time_horizons: Liste von Zeithorizonten in Minuten (Standard: [5, 10, 15])
            
        Returns:
            Liste von genau 12 Vorhersage-Dicts
        """
        predictions = []
        
        # Hole alle verfügbaren Abteilungen aus der Datenbank
        capacity_data = self.db.get_capacity_overview()
        all_departments = [c['department'] for c in capacity_data if c.get('department')]
        
        # Falls keine Abteilungen gefunden, verwende Standard-Abteilungen
        if not all_departments:
            all_departments = ['ER', 'ICU', 'Surgery', 'Cardiology', 'General Ward', 
                              'Orthopedics', 'Urology', 'Gastroenterology', 'Geriatrics']
        
        # Wähle Abteilungen für Patientenzugang-Vorhersagen
        # ER ist primär, dann wähle eine weitere relevante Abteilung
        patient_arrival_depts = []
        if 'ER' in all_departments:
            patient_arrival_depts.append('ER')
        
        # Wähle eine weitere relevante Abteilung für Patientenzugang
        priority_for_arrival = ['ICU', 'Surgery', 'Cardiology', 'General Ward']
        for dept in priority_for_arrival:
            if dept in all_departments and dept not in patient_arrival_depts and len(patient_arrival_depts) < 2:
                patient_arrival_depts.append(dept)
        
        # Falls noch nicht genug, füge weitere Abteilungen hinzu
        remaining_for_arrival = [d for d in all_departments if d not in patient_arrival_depts]
        while len(patient_arrival_depts) < 2 and remaining_for_arrival:
            patient_arrival_depts.append(remaining_for_arrival.pop(0))
        
        # Fallback falls immer noch nicht genug
        if len(patient_arrival_depts) < 2:
            if 'ER' not in patient_arrival_depts:
                patient_arrival_depts.insert(0, 'ER')
            if len(patient_arrival_depts) < 2:
                patient_arrival_depts.append('ER')
        
        # Wähle Abteilungen für Bettenbedarf-Vorhersagen
        # Priorisiere ICU und ER, dann andere Abteilungen
        bed_demand_depts = []
        priority_depts = ['ICU', 'ER', 'Surgery', 'Cardiology', 'General Ward']
        for dept in priority_depts:
            if dept in all_departments and len(bed_demand_depts) < 2:
                bed_demand_depts.append(dept)
        
        # Falls noch nicht genug, füge weitere Abteilungen hinzu
        remaining_depts = [d for d in all_departments if d not in bed_demand_depts]
        while len(bed_demand_depts) < 2 and remaining_depts:
            bed_demand_depts.append(remaining_depts.pop(0))
        
        # Fallback falls immer noch nicht genug
        if len(bed_demand_depts) < 2:
            if 'ICU' not in bed_demand_depts:
                bed_demand_depts.insert(0, 'ICU')
            if len(bed_demand_depts) < 2:
                bed_demand_depts.append('ER')
        
        # Generiere 6 Patientenzugang-Vorhersagen (2 Abteilungen × 3 Zeithorizonte)
        for dept in patient_arrival_depts[:2]:  # Sicherstellen, dass nur 2 verwendet werden
            for horizon in time_horizons:
                if horizon <= 15:  # Nur für kurze Zeithorizonte
                    pred = self.predict_patient_arrival(horizon, dept)
                    predictions.append(pred)
        
        # Generiere 6 Bettenbedarf-Vorhersagen (2 Abteilungen × 3 Zeithorizonte)
        for dept in bed_demand_depts[:2]:  # Sicherstellen, dass nur 2 verwendet werden
            for horizon in time_horizons:
                if horizon <= 15:  # Verwende die gleichen Zeithorizonte
                    pred = self.predict_bed_demand(horizon, dept)
                    predictions.append(pred)
        
        # Sicherstellen, dass genau 12 Vorhersagen generiert wurden
        # Falls weniger, füge fehlende hinzu
        while len(predictions) < 12:
            # Füge fehlende Patientenzugang-Vorhersagen hinzu
            if len([p for p in predictions if p['prediction_type'] == 'patient_arrival']) < 6:
                dept = patient_arrival_depts[0]
                horizon = time_horizons[len([p for p in predictions if p['prediction_type'] == 'patient_arrival']) % len(time_horizons)]
                pred = self.predict_patient_arrival(horizon, dept)
                predictions.append(pred)
            # Füge fehlende Bettenbedarf-Vorhersagen hinzu
            elif len([p for p in predictions if p['prediction_type'] == 'bed_demand']) < 6:
                dept = bed_demand_depts[0]
                horizon = time_horizons[len([p for p in predictions if p['prediction_type'] == 'bed_demand']) % len(time_horizons)]
                pred = self.predict_bed_demand(horizon, dept)
                predictions.append(pred)
            else:
                break
        
        # Falls mehr als 12, begrenze auf 12 (bevorzuge die ersten)
        if len(predictions) > 12:
            predictions = predictions[:12]
        
        # Speichere in DB
        self._save_predictions(predictions)
        
        return predictions
    
    def _save_predictions(self, predictions: List[Dict]):
        """Speichert Vorhersagen in die Datenbank (thread-safe)"""
        self.db.save_predictions_batch(predictions)

