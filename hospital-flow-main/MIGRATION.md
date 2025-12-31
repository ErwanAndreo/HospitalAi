# Migrationsanleitung - Modulare Struktur

## Status

✅ **Abgeschlossen:**
- `ui/styling.py` - CSS-Styling extrahiert
- `ui/components.py` - Wiederverwendbare Komponenten
- `db.py` - Vollständig auf Deutsch übersetzt
- `simulation.py` - Bereits auf Deutsch
- `utils.py` - Vollständig auf Deutsch übersetzt

⏳ **In Arbeit:**
- Aufteilung von `app.py` in Seitenmodule

## Aktuelle Situation

Die aktuelle `app.py` funktioniert weiterhin. Sie kann schrittweise in Module aufgeteilt werden.

## Migrationsstrategie

### Option 1: Schrittweise Migration (Empfohlen)

1. **Behalte die aktuelle `app.py`** als funktionierende Version
2. **Erstelle neue Seitenmodule** in `ui/pages/`
3. **Migriere eine Seite nach der anderen** von `app.py` in das entsprechende Modul
4. **Aktualisiere `app.py`** um die neuen Module zu verwenden

### Option 2: Vollständige Neuorganisation

1. Erstelle alle Seitenmodule auf einmal
2. Erstelle eine neue `app.py` die alle Module verwendet
3. Teste gründlich

## Beispiel: Dashboard-Modul

Ein Beispiel für die Struktur eines Seitenmoduls:

```python
# ui/pages/dashboard.py
"""
Dashboard-Seite für HospitalFlow
"""
import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
from ui.components import render_badge, render_empty_state
from utils import (
    get_severity_color, get_priority_color,
    get_metric_severity_for_load, get_metric_severity_for_count, 
    get_metric_severity_for_free, format_time_ago
)

def render(db, sim, get_cached_alerts, get_cached_recommendations, get_cached_capacity):
    """Rendert die Dashboard-Seite"""
    # Alle Dashboard-Logik hier...
    pass
```

## Nächste Schritte

1. Wähle eine Seite aus (z.B. Dashboard)
2. Kopiere den entsprechenden Code-Block aus `app.py`
3. Erstelle `ui/pages/dashboard.py` mit der `render()` Funktion
4. Importiere das Modul in `app.py` und ersetze den entsprechenden Block
5. Teste die Seite
6. Wiederhole für die nächste Seite

## Vorteile der Migration

- **Bessere Wartbarkeit**: Jede Seite ist isoliert
- **Einfacheres Testen**: Module können einzeln getestet werden
- **Wiederverwendbarkeit**: Komponenten können überall verwendet werden
- **Klarere Organisation**: Logische Trennung von Code

## Hinweis

Die aktuelle `app.py` funktioniert weiterhin. Die Migration kann schrittweise erfolgen, ohne die Funktionalität zu beeinträchtigen.

