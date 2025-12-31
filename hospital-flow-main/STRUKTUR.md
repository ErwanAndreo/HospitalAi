# HospitalFlow - Projektstruktur

## Neue modulare Struktur

Das Projekt wurde in eine modulare Struktur umorganisiert, bei der alle Kommentare, Docstrings und UI-Texte auf Deutsch sind.

### Verzeichnisstruktur

```
hospital-flow/
├── app.py                 # Hauptanwendung mit Routing
├── db.py                  # Datenbankoperationen (deutsch)
├── simulation.py          # Simulations-Engine (deutsch)
├── utils.py               # Hilfsfunktionen (deutsch)
├── ui/                    # UI-Module
│   ├── __init__.py
│   ├── styling.py         # CSS und Styling
│   ├── components.py      # Wiederverwendbare UI-Komponenten
│   └── pages/             # Seitenmodule
│       ├── __init__.py
│       ├── dashboard.py
│       ├── metrics.py
│       ├── predictions.py
│       ├── operations.py
│       ├── alerts.py
│       ├── recommendations.py
│       ├── transport.py
│       ├── inventory.py
│       ├── devices.py
│       ├── discharge.py
│       ├── discharge_tracker.py
│       ├── capacity.py
│       ├── audit.py
│       └── assets.py
├── requirements.txt
├── README.md
└── hospitalflow.db
```

### Module

#### `ui/styling.py`
Enthält alle CSS-Styles für die Anwendung. Wird einmal beim Start geladen.

#### `ui/components.py`
Wiederverwendbare UI-Komponenten:
- `render_badge()` - Schweregrad-Badges
- `render_empty_state()` - Leere Zustände
- `render_page_header()` - Seiten-Header

#### `ui/pages/`
Jede Seite hat ihr eigenes Modul:
- Jedes Modul exportiert eine `render()` Funktion
- Nimmt `db`, `sim`, und andere benötigte Parameter entgegen
- Rendert die komplette Seite

#### `app.py`
Hauptanwendung:
- Initialisiert Datenbank und Simulation
- Lädt Styling und Komponenten
- Routet zu den entsprechenden Seitenmodulen
- Verwaltet Sidebar-Navigation

### Verwendung

1. **Styling anwenden**: `ui.styling.apply_custom_styles()`
2. **Komponenten verwenden**: `from ui.components import render_badge, render_empty_state`
3. **Seiten rendern**: `from ui.pages.dashboard import render; render(db, sim, ...)`

### Vorteile der modularen Struktur

- **Bessere Wartbarkeit**: Jede Seite ist isoliert
- **Einfacheres Testen**: Module können einzeln getestet werden
- **Wiederverwendbarkeit**: Komponenten können überall verwendet werden
- **Klarere Organisation**: Logische Trennung von Styling, Komponenten und Seiten
- **Deutsche Sprache**: Alle Kommentare, Docstrings und UI-Texte sind auf Deutsch

