# Offene Probleme - Fix-Liste

## Status: Alle kritischen Probleme behoben ✅

Nach der Funktionalitätsprüfung wurden alle kritischen Bugs identifiziert und behoben.

---

## ✅ Bereits behoben

### 1. Inventar-Empfehlungen: `order_quantity` konnte negativ werden

**Status**: ✅ **BEHOBEN**

**Problem**:

- `order_quantity` konnte negativ oder 0 werden, wenn `suggested_qty <= current_stock`
- Negatives `order_quantity` wurde an die DB-Methode übergeben

**Fix implementiert**:

- ✅ `ui/pages/inventory.py`: Validierung mit `max(0, ...)` hinzugefügt
- ✅ Button wird nur angezeigt, wenn `order_quantity > 0`
- ✅ `db.py`: Zusätzliche Validierung in `create_inventory_order()` mit `ValueError` bei `quantity <= 0`

---

## ⚠️ Fehlende Funktionalität (Optional)

### 2. Transport-Anfragen: Keine UI zum manuellen Erstellen

**Status**: ⚠️ **FEHLENDE FUNKTIONALITÄT** (nicht kritisch, könnte beabsichtigt sein)

**Beschreibung**:

- Die Transport-Seite zeigt nur vorhandene Transport-Anfragen an
- Es gibt keine Buttons oder Formulare zum manuellen Erstellen neuer Transport-Anfragen
- Transporte werden aktuell nur automatisch erstellt durch:
  1. Inventar-Bestellungen (automatisch via `create_inventory_order()`)
  2. Externe Transport-Simulation (automatisch in `app.py`)

**Bewertung**:

- Dies könnte beabsichtigt sein (nur automatische Erstellung)
- Für vollständige Funktionalität würde ein Formular zum Erstellen fehlen

**Empfehlung** (falls gewünscht):

- Formular in `ui/pages/transport.py` hinzufügen mit Feldern:
  - `from_location` (String/Selectbox)
  - `to_location` (String/Selectbox)
  - `priority` (Selectbox: hoch, mittel, niedrig)
  - `request_type` (Selectbox: patient, equipment, specimen)
- `db.create_patient_transport()` existiert bereits und kann verwendet werden
- Für Equipment/Specimen könnte `db.create_inventory_order()` erweitert werden oder neue Methode erstellt werden

**Dateien die geändert werden müssten**:

- `ui/pages/transport.py`: Formular hinzufügen
- Optional: `db.py`: Neue Methode für Equipment/Specimen-Transporte (falls `create_patient_transport()` nur für Patienten verwendet werden soll)

---

## ✅ Funktioniert korrekt

### 3. Betrieb-Empfehlungen: Annehmen/Ablehnen

**Status**: ✅ **Funktioniert korrekt**

- Alle Funktionen getestet und bestätigt
- Keine Probleme gefunden

---

## Zusammenfassung

**Kritische Bugs**: 0 (alle behoben) ✅

**Fehlende Features**: 1 (optional, möglicherweise beabsichtigt)

- Manuelle Erstellung von Transport-Anfragen

**Empfehlung**:

- Wenn manuelle Transport-Erstellung gewünscht ist → Feature implementieren
- Wenn nur automatische Erstellung gewünscht ist → Keine Aktion nötig

---

_Zuletzt aktualisiert: 2024-12-19_
