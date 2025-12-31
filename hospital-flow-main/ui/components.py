"""
Wiederverwendbare UI-Komponenten für HospitalFlow
"""
from utils import get_severity_color


def render_badge(text: str, severity: str = "low") -> str:
    """Rendert ein konsistentes Schweregrad-Badge (grün/gelb/rot)"""
    color = get_severity_color(severity)
    return f'<span class="badge" style="background: {color}; color: white;">{text}</span>'


def render_empty_state(icon: str, title: str, text: str) -> str:
    """Rendert einen konsistenten leeren Zustand"""
    return f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{text}</div>
    </div>
    """


def render_page_header(page_title: str, timestamp: str) -> str:
    """Rendert einen professionellen Seiten-Header"""
    return f"""
    <div class="page-header">
        <h1 class="page-title">{page_title}</h1>
        <p class="page-subtitle">Zuletzt aktualisiert: {timestamp}</p>
    </div>
    """

