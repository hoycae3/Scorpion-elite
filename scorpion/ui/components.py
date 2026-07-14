"""Componentes UI reutilizables."""
from typing import List, Dict, Any, Optional


def render_header(titulo: str = "SCORPION ELITE", subtitulo: str = "Dashboard Analítico") -> str:
    """Renderiza el header principal."""
    return f'''
    <div class="header-container">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 35px; margin-right: 15px;">🦂</span>
            <h1 class="header-title">{titulo} <span class="header-subtitle">{subtitulo}</span></h1>
        </div>
    </div>
    '''


def render_pick_card(
    numero: int,
    liga: str,
    local: str,
    visitante: str,
    mercado: str,
    cuota: Optional[float] = None,
    confianza: Optional[float] = None,
    rango: str = "B"
) -> str:
    """Renderiza una tarjeta de pick."""
    emoji = "🟢" if rango == "A+" else "🟡"
    return f'''
    <div class="pick-card">
        <div class="pick-header">PICK {numero} | {liga[:20]}</div>
        <div class="pick-body">{local} vs {visitante}</div>
        <div class="pick-header">Selección: {mercado}</div>
        <div class="pick-footer">
            <span>Cuota: {cuota if cuota else 'N/A'}</span>
            <strong>{confianza if confianza else 0}%</strong>
        </div>
    </div>
    '''


def render_match_row(
    local: str,
    visitante: str,
    hora: str = "TBC",
    liga: str = "",
    rango: Optional[str] = None,
    over25: Optional[float] = None
) -> str:
    """Renderiza una fila de partido."""
    rango_color = "#00ee66" if rango == "A+" else ("#ffd700" if rango == "B" else "#888")
    rango_texto = rango if rango else ""
    over_text = f" | O2.5: {over25}%" if over25 else ""
    return f'''
    <div class="match-row">
        <span style="color: {rango_color}; font-weight: bold;">{rango_texto}</span>
        ⚽ {local} vs {visitante}
        <span style="float:right; color: #d4af37;">{hora}{over_text}</span>
    </div>
    '''


def render_goleador(posicion: int, nombre: str, goles: int) -> str:
    """Renderiza una fila de goleador."""
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    emoji = emojis[min(posicion - 1, 4)] if posicion <= 5 else f"{posicion}."
    return f'''
    <div class="goleador-row">
        <span class="goleador-num">{emoji}</span>
        <span class="goleador-nom">{nombre}</span>
        <span class="goleador-gol">{goles} ⚽</span>
    </div>
    '''


def render_alerta(mensaje: str, tipo: str = "info") -> str:
    """Renderiza una alerta."""
    iconos = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
    icono = iconos.get(tipo, "ℹ️")
    return f'<div class="text-alert">{icono} {mensaje}</div>'


def render_metrica(label: str, valor: str, color: str = "#d4af37") -> str:
    """Renderiza una métrica."""
    return f'''
    <div style="padding: 10px; background: #131926; border-radius: 8px; margin-bottom: 10px;">
        <div style="color: #8a94a6; font-size: 12px;">{label}</div>
        <div style="color: {color}; font-size: 24px; font-weight: bold;">{valor}</div>
    </div>
    '''
