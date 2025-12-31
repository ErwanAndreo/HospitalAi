"""
Hilfsfunktionen für HospitalFlow
Vorhersagen, Berechnungen und Formatierungshelfer
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random


def calculate_prediction_confidence(base_value: float, time_horizon: int) -> float:
    """Berechne Prognose-Vertrauen basierend auf dem Zeithorizont"""
    # Kürzere Horizonte = höheres Vertrauen
    confidence = max(0.6, 1.0 - (time_horizon / 60) * 0.3)
    return round(confidence, 2)


def format_time_ago(timestamp: str) -> str:
    """Formatiere Zeitstempel als relative Zeit"""
    if isinstance(timestamp, str):
        try:
            # Versuche zuerst ISO-Format
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            try:
                # Versuche SQLite-Datumsformat mit Mikrosekunden
                # SQLite CURRENT_TIMESTAMP gibt UTC zurück, also als UTC behandeln
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            except:
                try:
                    # Versuche SQLite-Datumsformat ohne Mikrosekunden
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except:
                    # Fallback auf "kürzlich", wenn das Parsen fehlschlägt
                    return "kürzlich"
    else:
        dt = timestamp
    
    # SQLite CURRENT_TIMESTAMP und datetime.now(timezone.utc) geben UTC zurück
    # Vergleiche UTC-Zeit mit UTC-Zeit für korrekte Zeitdifferenz
    from datetime import timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # Remove timezone info for comparison with naive dt
    diff = now - dt
    
    if diff.total_seconds() < 60:
        return "gerade eben"
    elif diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"vor {mins} Min."
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"vor {hours} Std."
    else:
        days = int(diff.total_seconds() / 86400)
        return f"vor {days} Tg."


def get_severity_color(severity: str) -> str:
    """Farbe für Schweregrad-Badge ermitteln"""
    farben = {
        "hoch": "#DC2626",      # rot-600
        "mittel": "#F59E0B",    # bernstein-500
        "niedrig": "#10B981",   # smaragd-500
        "kritisch": "#991B1B",  # rot-800
        # Für Kompatibilität mit englischen Keys:
        "high": "#DC2626",
        "medium": "#F59E0B",
        "low": "#10B981",
        "critical": "#991B1B",
    }
    return farben.get(severity.lower(), "#6B7280")


def get_priority_color(priority: str) -> str:
    """Farbe für Prioritäts-Badge ermitteln"""
    return get_severity_color(priority)


def get_risk_color(risk_level: str) -> str:
    """Farbe für Risikostufen-Badge ermitteln (unterstützt Deutsch und Englisch)"""
    return get_severity_color(risk_level)


def get_status_color(status: str) -> str:
    """Farbe für Status-Badge ermitteln"""
    farben = {
        # Deutsch
        "ausstehend": "#F59E0B",      # bernstein-500
        "in_bearbeitung": "#3B82F6",  # blau-500
        "abgeschlossen": "#10B981",   # smaragd-500
        "akzeptiert": "#10B981",      # smaragd-500
        "abgelehnt": "#EF4444",       # rot-500
        "betriebsbereit": "#10B981",  # smaragd-500
        "wartung": "#F59E0B",         # bernstein-500
        "kritisch": "#DC2626",        # rot-600
        # Englisch (Kompatibilität)
        "pending": "#F59E0B",
        "in_progress": "#3B82F6",
        "completed": "#10B981",
        "accepted": "#10B981",
        "rejected": "#EF4444",
        "operational": "#10B981",
        "maintenance": "#F59E0B",
        "critical": "#DC2626",
    }
    return farben.get(status.lower(), "#6B7280")


def calculate_inventory_status(current: int, min_threshold: int, max_capacity: int) -> Dict:
    """Berechne Lagerstatus und Prozentsatz"""
    prozent = (current / max_capacity) * 100 if max_capacity > 0 else 0
    ist_niedrig = current < min_threshold
    ist_kritisch = current < (min_threshold * 0.5)
    # Status sowohl auf Deutsch als auch Englisch für Kompatibilität
    if ist_kritisch:
        status = "kritisch"
        status_en = "critical"
    elif ist_niedrig:
        status = "niedrig"
        status_en = "low"
    else:
        status = "normal"
        status_en = "normal"
    return {
        "percentage": round(prozent, 1),
        "is_low": ist_niedrig,
        "is_critical": ist_kritisch,
        "status": status,
        "status_en": status_en
    }


def calculate_capacity_status(utilization: float) -> Dict:
    """Berechne Kapazitätsstatus"""
    if utilization >= 0.9:
        status = "kritisch"
        status_en = "critical"
        color = "#DC2626"
    elif utilization >= 0.75:
        status = "hoch"
        status_en = "high"
        color = "#F59E0B"
    elif utilization >= 0.5:
        status = "moderat"
        status_en = "moderate"
        color = "#3B82F6"
    else:
        status = "niedrig"
        status_en = "low"
        color = "#10B981"
    return {
        "status": status,
        "status_en": status_en,
        "color": color,
        "percentage": round(utilization * 100, 1)
    }


def generate_short_term_prediction(current_value: float, trend: str = "stable") -> Dict:
    """Erzeuge 5-15 Minuten Prognosen"""
    # Einfache Prognoselogik
    if trend == "increasing":
        multiplikator = 1.1
    elif trend == "decreasing":
        multiplikator = 0.9
    else:
        multiplikator = 1.0
    
    prognosen = []
    for minuten in [5, 10, 15]:
        prognosewert = current_value * (multiplikator ** (minuten / 10))
        vertrauen = calculate_prediction_confidence(prognosewert, minuten)
        prognosen.append({
            "minuten": minuten,
            "wert": round(prognosewert, 1),
            "vertrauen": vertrauen
        })
    
    return prognosen


def format_duration_minutes(minutes: int) -> str:
    """Formatiere Dauer in Minuten als lesbare Zeichenkette"""
    if minutes < 60:
        return f"{minutes} Min."
    else:
        stunden = minutes // 60
        minuten = minutes % 60
        if minuten == 0:
            return f"{stunden} Std."
        return f"{stunden} Std. {minuten} Min."


def get_department_color(department: str) -> str:
    """Gibt eine konsistente Farbe für die Abteilung zurück"""
    farben = {
        "ER": "#EF4444",              # Notaufnahme
        "ICU": "#DC2626",             # Intensivstation
        "Surgery": "#3B82F6",         # Chirurgie
        "Cardiology": "#8B5CF6",      # Kardiologie
        "General Ward": "#10B981",    # Allgemeinstation
        # Deutsche Abteilungsnamen für Kompatibilität
        "Notaufnahme": "#EF4444",
        "Intensivstation": "#DC2626",
        "Chirurgie": "#3B82F6",
        "Kardiologie": "#8B5CF6",
        "Allgemeinstation": "#10B981",
    }
    return farben.get(department, "#6B7280")


def get_max_usage_hours(device_type: str) -> int:
    """Gibt die maximale Betriebsstunden für einen Gerätetyp zurück"""
    max_hours_mapping = {
        'Beatmungsgerät': 4200,
        'Monitor': 6000,
        'OP-Monitor': 6000,
        'Defibrillator': 3000,
        'CT-Gerät': 5000,
        'MRT-Gerät': 5500,
        'Röntgengerät': 4000,
        'EKG-Gerät': 3000,
        'Ultraschallgerät': 3500,
    }
    return max_hours_mapping.get(device_type, 4000)  # Default: 4000 Stunden


def calculate_device_urgency(days_until_maintenance: int, usage_hours: int, max_usage_hours: int) -> str:
    """
    Berechne die Wartungsdringlichkeit eines Geräts basierend auf:
    - Tagen bis zur nächsten Wartung
    - Betriebsstunden im Verhältnis zur maximalen Betriebszeit
    
    Args:
        days_until_maintenance: Tage bis zur nächsten fälligen Wartung (kann negativ sein)
        usage_hours: Aktuelle Betriebsstunden
        max_usage_hours: Maximale Betriebsstunden für diesen Gerätetyp
    
    Returns:
        'hoch', 'mittel' oder 'niedrig'
    """
    # Berechne Dringlichkeit basierend auf Tagen bis Wartung
    days_urgency = "niedrig"
    if days_until_maintenance < 0 or days_until_maintenance < 7:
        days_urgency = "hoch"
    elif days_until_maintenance < 30:
        days_urgency = "mittel"
    
    # Berechne Dringlichkeit basierend auf Betriebsstunden
    if max_usage_hours > 0:
        hours_percentage = (usage_hours / max_usage_hours) * 100
        hours_urgency = "niedrig"
        if hours_percentage >= 95:  # >= 95% = hoch
            hours_urgency = "hoch"
        elif hours_percentage >= 85:  # >= 85% = mittel
            hours_urgency = "mittel"
    else:
        hours_urgency = "niedrig"
    
    # Nimm höchste Dringlichkeit (OR-Logik)
    if days_urgency == "hoch" or hours_urgency == "hoch":
        return "hoch"
    elif days_urgency == "mittel" or hours_urgency == "mittel":
        return "mittel"
    return "niedrig"


def get_system_status() -> tuple[str, str]:
    """Gibt den aktuellen Systemstatus zurück (Status, Farbe)"""
    # In einer echten App würde hier der Systemzustand geprüft
    # Für das MVP: immer "betriebsbereit"
    return "betriebsbereit", "#10B981"


def calculate_metric_severity(value: float, thresholds: dict) -> tuple[str, str]:
    """
    Berechne Schweregrad basierend auf Wert und Schwellenwerten
    Rückgabe: (schweregrad, hinweis_text)
    thresholds: {'critical': max, 'watch': max, 'stable': max}
    """
    if value >= thresholds.get('critical', 90):
        return 'hoch', 'Kritisch'
    elif value >= thresholds.get('watch', 70):
        return 'mittel', 'Beobachten'
    else:
        return 'niedrig', 'Stabil'


def get_metric_severity_for_load(load_percent: float) -> tuple[str, str]:
    """Gibt den Schweregrad für Auslastungsmetriken (0-100%) zurück"""
    if load_percent >= 90:
        return 'hoch', 'Kritisch'
    elif load_percent >= 75:
        return 'mittel', 'Beobachten'
    else:
        return 'niedrig', 'Stabil'


def get_metric_severity_for_count(count: int, thresholds: dict) -> tuple[str, str]:
    """Ermittle Schweregrad für zählbasierte Metriken"""
    if count >= thresholds.get('critical', 20):
        return 'high', 'Kritisch'
    elif count >= thresholds.get('watch', 10):
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def get_metric_severity_for_free(free: int, total: int) -> tuple[str, str]:
    """Ermittle Schweregrad für freie/verfügbare Metriken (niedriger ist schlechter)"""
    if total == 0:
        return 'high', 'Kritisch'
    free_percent = (free / total) * 100
    if free_percent <= 5:
        return 'high', 'Kritisch'
    elif free_percent <= 15:
        return 'medium', 'Beobachten'
    else:
        return 'low', 'Stabil'


def calculate_explanation_score(trend_strength: float, data_points: int, confidence: float) -> str:
    """
    Erkläre den Erklärungsscore (niedrig/mittel/hoch) basierend auf Trendstärke
    trend_strength: 0-1 (wie stark ist der Trend)
    data_points: Anzahl der verwendeten Datenpunkte
    confidence: 0-1 (Prognose-Vertrauen)
    """
    # Faktoren kombinieren
    score = (trend_strength * 0.4) + (min(data_points / 20, 1.0) * 0.3) + (confidence * 0.3)
    
    if score >= 0.7:
        return "hoch"
    elif score >= 0.4:
        return "mittel"
    else:
        return "niedrig"


def get_explanation_score_color(score: str) -> str:
    """Farbe für Erklärungsscore-Badge ermitteln"""
    farben = {
        "hoch": "#10B981",    # smaragd-500
        "mittel": "#F59E0B",  # bernstein-500
        "niedrig": "#6B7280", # grau-500
        # Für Kompatibilität mit englischen Keys:
        "high": "#10B981",
        "medium": "#F59E0B",
        "low": "#6B7280",
    }
    return farben.get(score.lower(), "#6B7280")


def calculate_patient_arrival_prediction(
    ed_load: float,
    time_horizon_minutes: int,
    trend: float = 0.0,
    has_active_surge: bool = False,
    historical_arrivals: List[Dict] = None
) -> tuple[float, float]:
    """
    Berechne Vorhersage für Patientenzugang basierend auf aktuellen Daten.
    
    Args:
        ed_load: Aktuelle Notaufnahme-Auslastung (0-100%)
        time_horizon_minutes: Zeithorizont für Vorhersage (5, 10, oder 15)
        trend: Trend-Richtung (-1 bis 1, von Simulation)
        has_active_surge: Ob ein aktives Surge-Event läuft
        historical_arrivals: Historische Patientenzugänge (optional)
    
    Returns:
        tuple: (predicted_count, confidence)
    """
    # Basis: ED-Load skaliert auf Patientenzugang
    # Höherer Load → mehr erwartete Ankünfte
    # 0% Load → ~0-1 Patienten/15min, 100% Load → ~8-12 Patienten/15min
    base_rate = (ed_load / 100.0) * 10.0  # 0-10 Patienten bei 100% Load
    
    # Skaliere auf Zeithorizont (proportional)
    time_factor = time_horizon_minutes / 15.0
    base_prediction = base_rate * time_factor
    
    # Trend-Anpassung: Trend beeinflusst Vorhersage
    trend_adjustment = trend * 2.0  # Trend kann ±2 Patienten beeinflussen
    base_prediction += trend_adjustment
    
    # Surge-Event: +30-50% bei aktiven Surges
    if has_active_surge:
        surge_multiplier = random.uniform(1.3, 1.5)
        base_prediction *= surge_multiplier
    
    # Tageszeit-Muster: Mehr Ankünfte am Nachmittag (14-18 Uhr)
    current_hour = datetime.now().hour
    if 14 <= current_hour <= 18:
        time_multiplier = random.uniform(1.1, 1.3)
    elif 8 <= current_hour <= 12:
        time_multiplier = random.uniform(0.9, 1.1)
    elif 0 <= current_hour <= 6:
        time_multiplier = random.uniform(0.6, 0.8)
    else:
        time_multiplier = random.uniform(0.8, 1.0)
    base_prediction *= time_multiplier
    
    # Historische Daten berücksichtigen (falls verfügbar)
    if historical_arrivals:
        # Berechne Durchschnitt der letzten Stunde
        recent_arrivals = [a for a in historical_arrivals if a.get('value', 0) > 0]
        if recent_arrivals:
            avg_recent = sum(a['value'] for a in recent_arrivals) / len(recent_arrivals)
            # Kombiniere Basis-Vorhersage mit historischem Durchschnitt (gewichteter Durchschnitt)
            base_prediction = (base_prediction * 0.6) + (avg_recent * 0.4)
    
    # Runde auf ganze Zahl und stelle sicher, dass es nicht negativ ist
    predicted_count = max(0, round(base_prediction))
    
    # Confidence basierend auf Zeithorizont und Datenqualität
    base_confidence = calculate_prediction_confidence(base_prediction, time_horizon_minutes)
    # Höheres Vertrauen wenn historische Daten verfügbar sind
    if historical_arrivals and len(historical_arrivals) >= 5:
        confidence = min(0.95, base_confidence + 0.05)
    else:
        confidence = base_confidence
    
    return predicted_count, confidence


def calculate_bed_demand_prediction(
    current_utilization: float,
    expected_patient_arrivals: int,
    time_horizon_minutes: int,
    total_beds: int,
    ready_for_discharge: int = 0,
    trend: float = 0.0
) -> tuple[float, float]:
    """
    Berechne Vorhersage für Bettenbedarf (Auslastung in Prozent).
    
    Args:
        current_utilization: Aktuelle Bettenauslastung (0-1.0 oder 0-100%)
        expected_patient_arrivals: Erwartete Anzahl neuer Patienten
        time_horizon_minutes: Zeithorizont für Vorhersage (5, 10, oder 15)
        total_beds: Gesamtanzahl Betten in der Abteilung
        ready_for_discharge: Anzahl Patienten, die entlassen werden können
        trend: Trend-Richtung (-1 bis 1)
    
    Returns:
        tuple: (predicted_utilization_percent, confidence)
    """
    # Normalisiere current_utilization auf 0-1.0
    if current_utilization > 1.0:
        current_utilization = current_utilization / 100.0
    
    # Berechne erwartete Änderung basierend auf Patientenzugang
    # Jeder neue Patient benötigt ein Bett
    beds_needed = expected_patient_arrivals
    
    # Entlassungen reduzieren Bedarf
    beds_freed = ready_for_discharge
    
    # Netto-Änderung der belegten Betten
    net_bed_change = beds_needed - beds_freed
    
    # Aktuelle belegte Betten
    current_occupied = current_utilization * total_beds
    
    # Erwartete belegte Betten
    predicted_occupied = max(0, min(total_beds, current_occupied + net_bed_change))
    
    # Trend-Anpassung: Trend beeinflusst Auslastung
    trend_adjustment = trend * 0.05  # Trend kann ±5% Auslastung beeinflussen
    predicted_utilization = (predicted_occupied / total_beds) + trend_adjustment
    
    # Stelle sicher, dass Auslastung zwischen 0 und 1.0 bleibt
    predicted_utilization = max(0.0, min(1.0, predicted_utilization))
    
    # Konvertiere zu Prozent
    predicted_utilization_percent = predicted_utilization * 100.0
    
    # Confidence basierend auf Zeithorizont
    # Kürzere Horizonte = höheres Vertrauen
    # Mehr Entlassungsdaten = höheres Vertrauen
    base_confidence = calculate_prediction_confidence(predicted_utilization_percent, time_horizon_minutes)
    
    if ready_for_discharge > 0:
        # Höheres Vertrauen wenn Entlassungsdaten verfügbar sind
        confidence = min(0.95, base_confidence + 0.05)
    else:
        confidence = base_confidence
    
    return round(predicted_utilization_percent, 1), confidence


def calculate_daily_consumption_from_activity(
    item: Dict,
    ed_load: float,
    beds_occupied: int = 0,
    capacity_data: List[Dict] = None,
    operations_count: int = 0,
    operations_consumption: Dict[str, float] = None
) -> float:
    """
    Berechne täglichen Verbrauch basierend auf Krankenhausaktivität.
    
    Args:
        item: Inventar-Artikel-Dict mit item_name, department, min_threshold, etc.
        ed_load: Aktuelle ED-Load (0-100%)
        beds_occupied: Anzahl belegter Betten (optional, wird aus capacity_data berechnet wenn nicht gegeben)
        capacity_data: Liste von Kapazitätsdaten pro Abteilung
        operations_count: Anzahl abgeschlossener Operationen in der Abteilung (pro Tag/Tagesschnitt)
        operations_consumption: Dict mit item_name -> consumption_amount von Operationen (optional)
    
    Returns:
        Täglicher Verbrauch als float
    """
    # Basis-Verbrauchsrate basierend auf Artikel-Typ und Mindestbestand
    item_name = item.get('item_name', '').lower()
    department = item.get('department', '')
    min_threshold = item.get('min_threshold', 10)
    
    # Artikel-spezifische Basis-Verbrauchsrate (pro Tag)
    base_consumption = 1.0
    
    # Bestimme Basis-Verbrauch basierend auf Artikel-Typ
    if 'sauerstoff' in item_name or 'oxygen' in item_name:
        base_consumption = min_threshold * 0.15  # 15% des Mindestbestands pro Tag
    elif 'infusion' in item_name:
        base_consumption = min_threshold * 0.20  # 20% pro Tag
    elif 'maske' in item_name or 'mask' in item_name:
        base_consumption = min_threshold * 0.10  # 10% pro Tag
    elif 'filter' in item_name:
        base_consumption = min_threshold * 0.12  # 12% pro Tag
    else:
        # Standard: 10% des Mindestbestands pro Tag
        base_consumption = min_threshold * 0.10
    
    # ED Load Multiplikator (0.5-1.5x)
    # Höhere ED Load → mehr Verbrauch
    ed_multiplier = 0.5 + (ed_load / 100.0) * 1.0  # 0.5 bei 0% Load, 1.5 bei 100% Load
    
    # Bettenauslastung Multiplikator (0.7-1.3x)
    # Berechne Bettenauslastung wenn nicht gegeben
    if beds_occupied == 0 and capacity_data:
        # Finde Abteilung in capacity_data
        dept_capacity = next((c for c in capacity_data if c.get('department') == department), None)
        if dept_capacity:
            total_beds = dept_capacity.get('total_beds', 0)
            occupied = dept_capacity.get('occupied_beds', 0)
            if total_beds > 0:
                beds_utilization = (occupied / total_beds) * 100
                beds_multiplier = 0.7 + (beds_utilization / 100.0) * 0.6  # 0.7-1.3x
            else:
                beds_multiplier = 1.0
        else:
            beds_multiplier = 1.0
    elif beds_occupied > 0:
        # Wenn beds_occupied gegeben, schätze Multiplikator basierend auf typischer Kapazität
        # Annahme: 50 belegte Betten = 100% Auslastung für Multiplikator-Berechnung
        beds_utilization = min(100, (beds_occupied / 50.0) * 100)
        beds_multiplier = 0.7 + (beds_utilization / 100.0) * 0.6
    else:
        beds_multiplier = 1.0
    
    # Abteilungs-spezifische Faktoren
    dept_multiplier = 1.0
    if department:
        dept_lower = department.lower()
        if 'intensiv' in dept_lower or 'icu' in dept_lower:
            dept_multiplier = 1.5  # Intensivstation: 1.5x
        elif 'chirurgie' in dept_lower or 'surgery' in dept_lower:
            dept_multiplier = 1.2  # Chirurgie: 1.2x
        elif 'kardiologie' in dept_lower or 'cardiology' in dept_lower:
            dept_multiplier = 1.1  # Kardiologie: 1.1x
        elif 'notaufnahme' in dept_lower or 'er' in dept_lower:
            dept_multiplier = 1.3  # Notaufnahme: 1.3x
    
    # Operations-basierter Verbrauch
    operations_consumption_amount = 0.0
    item_name = item.get('item_name', '')
    if operations_consumption and item_name in operations_consumption:
        # Direkter Verbrauch aus Operationen (bereits berechnet)
        operations_consumption_amount = operations_consumption[item_name] * operations_count
    elif operations_count > 0:
        # Schätze Operations-Verbrauch basierend auf Artikel-Typ
        if 'maske' in item_name.lower() or 'mask' in item_name.lower():
            operations_consumption_amount = operations_count * random.uniform(2.0, 5.0)
        elif 'handschuh' in item_name.lower():
            operations_consumption_amount = operations_count * random.uniform(8.0, 15.0)
        elif 'verband' in item_name.lower() or 'kompresse' in item_name.lower():
            operations_consumption_amount = operations_count * random.uniform(3.0, 8.0)
        elif 'kittel' in item_name.lower():
            operations_consumption_amount = operations_count * random.uniform(1.0, 2.0)
        elif 'naht' in item_name.lower():
            operations_consumption_amount = operations_count * random.uniform(1.0, 3.0)
        elif 'tuch' in item_name.lower():
            operations_consumption_amount = operations_count * random.uniform(3.0, 8.0)
    
    # Kombinierte Berechnung: Basis-Verbrauch + Operations-Verbrauch
    base_daily_consumption = base_consumption * ed_multiplier * beds_multiplier * dept_multiplier
    daily_consumption = base_daily_consumption + operations_consumption_amount
    
    # Stelle sicher, dass Verbrauch mindestens 1.0 ist
    return max(1.0, round(daily_consumption, 2))


def calculate_operation_consumption(
    operation_type: str,
    department: str,
    duration_minutes: int = 60
) -> Dict[str, float]:
    """
    Berechne Materialverbrauch pro Operation basierend auf Operationstyp und Dauer.
    
    Args:
        operation_type: Typ der Operation (z.B. "Appendektomie", "Gelenkersatz")
        department: Abteilung
        duration_minutes: Dauer der Operation in Minuten
    
    Returns:
        Dict mit item_name -> consumption_amount
    """
    consumption = {}
    
    # Basis-Materialien für jede Operation
    base_materials = {
        'OP-Masken': 2.0,  # 2-5 Masken pro OP
        'OP-Handschuhe': 8.0,  # 8-15 Paare pro OP
        'OP-Tücher': 3.0,  # 3-8 Tücher
        'Desinfektionsmittel': 0.5,  # Liter
    }
    
    # Kleine Operationen (unter 60 Min)
    if duration_minutes < 60:
        for material, base_amount in base_materials.items():
            consumption[material] = base_amount * random.uniform(0.7, 1.0)
        consumption['Wundverbände'] = random.uniform(2.0, 4.0)
        consumption['Sterile Kompressen'] = random.uniform(2.0, 5.0)
    # Mittlere Operationen (60-120 Min)
    elif duration_minutes < 120:
        for material, base_amount in base_materials.items():
            consumption[material] = base_amount * random.uniform(1.0, 1.5)
        consumption['Wundverbände'] = random.uniform(4.0, 8.0)
        consumption['Sterile Kompressen'] = random.uniform(5.0, 10.0)
        consumption['Nahtmaterial'] = random.uniform(1.0, 2.0)
    # Große Operationen (über 120 Min)
    else:
        for material, base_amount in base_materials.items():
            consumption[material] = base_amount * random.uniform(1.5, 2.5)
        consumption['Wundverbände'] = random.uniform(8.0, 15.0)
        consumption['Sterile Kompressen'] = random.uniform(10.0, 20.0)
        consumption['Nahtmaterial'] = random.uniform(2.0, 4.0)
    
    # Abteilungs-spezifische Materialien
    dept_lower = department.lower()
    if 'chirurgie' in dept_lower:
        consumption['OP-Kittel'] = random.uniform(1.0, 2.0)
        if 'darm' in operation_type.lower() or 'resektion' in operation_type.lower():
            consumption['Drainagen'] = random.uniform(1.0, 3.0)
    elif 'orthopädie' in dept_lower:
        if 'gelenk' in operation_type.lower() or 'bruch' in operation_type.lower():
            consumption['Gipsbinden'] = random.uniform(2.0, 5.0)
            consumption['Schienen'] = random.uniform(0.0, 1.0)
    elif 'urologie' in dept_lower:
        consumption['Katheter'] = random.uniform(1.0, 2.0)
    elif 'kardiologie' in dept_lower:
        consumption['Katheter'] = random.uniform(1.0, 3.0)
    elif 'intensiv' in dept_lower:
        consumption['Beatmungsfilter'] = random.uniform(0.5, 1.0)
        consumption['Katheter'] = random.uniform(1.0, 2.0)
    
    return consumption


def calculate_days_until_stockout(
    current_stock: int,
    daily_consumption_rate: float
) -> Optional[float]:
    """
    Berechne präzise Tage bis Engpass basierend auf aktuellem Bestand und Verbrauchsrate.
    
    Args:
        current_stock: Aktueller Bestand
        daily_consumption_rate: Tägliche Verbrauchsrate
    
    Returns:
        Tage bis Engpass (float) oder None wenn kein Engpass erwartet
    """
    if daily_consumption_rate <= 0:
        return None
    
    days_until_stockout = current_stock / daily_consumption_rate
    
    # Runde auf 1 Dezimalstelle
    return round(days_until_stockout, 1)


def calculate_reorder_suggestion(
    item: Dict,
    daily_consumption_rate: float,
    days_until_stockout: Optional[float],
    safety_buffer_days: int = 2,
    delivery_time_days: int = 1
) -> Dict:
    """
    Berechne Nachfüllvorschlag mit Menge und Bestelltermin.
    
    Args:
        item: Inventar-Artikel-Dict
        daily_consumption_rate: Tägliche Verbrauchsrate
        days_until_stockout: Tage bis Engpass (None wenn kein Engpass)
        safety_buffer_days: Sicherheitspuffer in Tagen (Standard: 2)
        delivery_time_days: Lieferzeit in Tagen (Standard: 1)
    
    Returns:
        Dict mit 'suggested_qty', 'order_by_date', 'order_by_days', 'priority', 'reasoning'
    """
    current_stock = item.get('current_stock', 0)
    min_threshold = item.get('min_threshold', 0)
    max_capacity = item.get('max_capacity', 0)
    
    # Bestimme Priorität
    if days_until_stockout is None:
        priority = "niedrig"
        suggested_qty = 0
        order_by_days = None
        reasoning = "Kein Engpass erwartet"
    elif days_until_stockout <= safety_buffer_days + delivery_time_days:
        priority = "hoch"
        # Kritisch: Bestelle sofort, genug für mindestens 2x Mindestbestand
        suggested_qty = max(min_threshold * 2, int(daily_consumption_rate * (safety_buffer_days + delivery_time_days + 7)))
        order_by_days = 0  # Sofort bestellen
        reasoning = f"Kritisch: Engpass in {days_until_stockout:.1f} Tagen erwartet"
    elif days_until_stockout <= (safety_buffer_days + delivery_time_days) * 2:
        priority = "mittel"
        # Bestelle innerhalb der nächsten Tage
        suggested_qty = max(min_threshold * 1.5, int(daily_consumption_rate * (safety_buffer_days + delivery_time_days + 14)))
        order_by_days = max(0, int(days_until_stockout - safety_buffer_days - delivery_time_days))
        reasoning = f"Engpass in {days_until_stockout:.1f} Tagen erwartet"
    else:
        priority = "niedrig"
        # Planmäßige Bestellung
        suggested_qty = max(min_threshold, int(daily_consumption_rate * 14))  # 2 Wochen Vorrat
        order_by_days = max(0, int(days_until_stockout - safety_buffer_days - delivery_time_days))
        reasoning = f"Planmäßige Bestellung empfohlen"
    
    # Stelle sicher, dass nicht über max_capacity hinausgegangen wird
    if max_capacity > 0:
        suggested_qty = min(suggested_qty, max_capacity)
    
    # Berechne Bestelltermin (Datum)
    from datetime import datetime, timedelta
    if order_by_days is not None:
        order_by_date = (datetime.now() + timedelta(days=order_by_days)).date()
        order_by_date_str = order_by_date.strftime('%Y-%m-%d')
    else:
        order_by_date_str = None
    
    return {
        'suggested_qty': int(suggested_qty),
        'order_by_date': order_by_date_str,
        'order_by_days': order_by_days,
        'priority': priority,
        'reasoning': reasoning,
        'daily_consumption_rate': daily_consumption_rate,
        'days_until_stockout': days_until_stockout
    }

