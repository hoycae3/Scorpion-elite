"""Componentes UI reutilizables."""
from typing import List, Dict, Any, Optional


# ══════════════════════════════════════════════════════════
# SCORPION ELITE - COMPONENTES UI V2
# Dashboard tipo terminal con estilo moderno
# ══════════════════════════════════════════════════════════


def render_dashboard_header(username: str = "Usuario", saldo: str = "$0.00", show_settings: bool = True) -> str:
    """Renderiza el header principal del dashboard con usuario, saldo y configuración."""
    settings_btn = '<span style="color: #ffcc00; cursor: pointer; font-size: 1.2rem;">⚙️</span>' if show_settings else ''
    return f'''
    <div class="dash-header">
        <div class="dash-logo">
            <span class="dash-logo-icon">🦂</span>
            <span class="dash-logo-text">SCORPION ELITE</span>
        </div>
        <div class="dash-user-info">
            <span class="dash-user">👤 {username}</span>
            <span class="dash-saldo">💰 {saldo}</span>
            {settings_btn}
        </div>
    </div>
    '''


def render_nav_bar(active_tab: str = "hoy") -> str:
    """Renderiza la barra de navegación horizontal."""
    tabs = ["hoy", "manana", "futbol", "baloncesto", "tenis"]
    tabs_labels = ["📅 Hoy", "📅 Mañana", "⚽ Fútbol", "🏀 Baloncesto", "🎾 Tenis"]
    
    tabs_html = ""
    for tab, label in zip(tabs, tabs_labels):
        active_class = "nav-active" if tab == active_tab else ""
        tabs_html += f'<button class="nav-tab {active_class}" data-tab="{tab}">{label}</button>'
    
    return f'''
    <div class="dash-nav">
        {tabs_html}
    </div>
    '''


def render_dashboard_box(title: str, content: str, box_class: str = "dash-box") -> str:
    """Renderiza una caja genérica del dashboard."""
    return f'''
    <div class="{box_class}">
        <div class="dash-box-title">{title}</div>
        <div class="dash-box-content">{content}</div>
    </div>
    '''


def render_match_list(matches: List[Dict[str, Any]]) -> str:
    """Renderiza la lista de partidos del día."""
    if not matches:
        return '<div class="dash-empty">No hay partidos disponibles</div>'
    
    html = '<div class="match-list">'
    for match in matches:
        local = match.get("local", "Local")
        visitante = match.get("visitante", "Visita")
        hora = match.get("hora", "TBC")
        rango = match.get("rango", "")
        rango_color = "#39ff14" if rango == "A+" else ("#ffd700" if rango == "B" else "#888")
        
        html += f'''
        <div class="match-item">
            <span class="match-rango" style="color: {rango_color};">{rango}</span>
            <span class="match-teams">⚽ {local} vs {visitante}</span>
            <span class="match-time">{hora}</span>
        </div>
        '''
    html += '</div>'
    return html


def render_ai_analysis(data: Dict[str, Any]) -> str:
    """Renderiza el panel de análisis de IA."""
    prob_local = data.get("prob_local", 50)
    valor = data.get("valor", "NO")
    riesgo = data.get("riesgo", "Medio")
    confianza = data.get("confianza", 0)
    
    valor_color = "#39ff14" if valor == "SI" else "#ff6b6b"
    riesgo_color = {"Bajo": "#39ff14", "Medio": "#ffd700", "Alto": "#ff6b6b"}.get(riesgo, "#888")
    
    return f'''
    <div class="ai-analysis">
        <div class="ai-item">
            <span class="ai-label">Probabilidad Local:</span>
            <span class="ai-value">{prob_local}%</span>
        </div>
        <div class="ai-item">
            <span class="ai-label">Valor encontrado:</span>
            <span class="ai-value" style="color: {valor_color}; font-weight: bold;">{valor}</span>
        </div>
        <div class="ai-item">
            <span class="ai-label">Riesgo:</span>
            <span class="ai-value" style="color: {riesgo_color};">{riesgo}</span>
        </div>
        <div class="ai-item">
            <span class="ai-label">Confianza:</span>
            <span class="ai-value confianza">{confianza}%</span>
        </div>
    </div>
    '''


def render_markets(markets: List[str]) -> str:
    """Renderiza la lista de mercados disponibles."""
    if not markets:
        markets = ["Ganador", "Over/Under", "Ambos marcan", "Hándicap"]
    
    html = '<div class="markets-list">'
    for market in markets:
        html += f'<div class="market-item">✔ {market}</div>'
    html += '</div>'
    return html


def render_odds_comparator(odds: List[Dict[str, Any]]) -> str:
    """Renderiza el comparador de cuotas."""
    if not odds:
        # Ejemplo visual
        return '''
        <div class="odds-comparator">
            <div class="odds-row"><span class="odds-book">Bet365</span><span class="odds-val">1.82</span></div>
            <div class="odds-row"><span class="odds-book">Betano</span><span class="odds-val">1.88</span></div>
            <div class="odds-row best"><span class="odds-book">Pinnacle</span><span class="odds-val">1.90 ⭐</span></div>
            <div class="odds-row"><span class="odds-book">Stake</span><span class="odds-val">1.87</span></div>
        </div>
        '''
    
    html = '<div class="odds-comparator">'
    for odd in odds:
        book = odd.get("book", "Casa")
        val = odd.get("value", 0)
        is_best = odd.get("best", False)
        best_class = "best" if is_best else ""
        star = " ⭐" if is_best else ""
        html += f'<div class="odds-row {best_class}"><span class="odds-book">{book}</span><span class="odds-val">{val}{star}</span></div>'
    html += '</div>'
    return html


def render_statistics(stats: Dict[str, Any]) -> str:
    """Renderiza el panel de estadísticas."""
    items = [
        ("xG", stats.get("xg", "1.2 - 0.8")),
        ("Tiros", stats.get("tiros", "12 - 8")),
        ("Corners", stats.get("corners", "5 - 3")),
        ("Posesión", stats.get("posesion", "55% - 45%")),
    ]
    
    html = '<div class="stats-list">'
    for label, value in items:
        html += f'<div class="stat-item"><span class="stat-label">{label}</span><span class="stat-value">{value}</span></div>'
    html += '</div>'
    return html


def render_alerts(alerts: List[Dict[str, Any]]) -> str:
    """Renderiza el panel de alertas."""
    if not alerts:
        # Ejemplo visual
        return '''
        <div class="alerts-list">
            <div class="alert-item alert-warning">⚠️ Lesiones importantes</div>
            <div class="alert-item alert-info">📊 Cambio de cuota detectado</div>
            <div class="alert-item alert-success">💰 Dinero inteligente detectado</div>
            <div class="alert-item alert-fire">🔥 Pick con Value encontrado</div>
        </div>
        '''
    
    html = '<div class="alerts-list">'
    alert_colors = {
        "info": "alert-info",
        "warning": "alert-warning",
        "success": "alert-success",
        "fire": "alert-fire"
    }
    for alert in alerts:
        tipo = alert.get("tipo", "info")
        mensaje = alert.get("mensaje", "")
        color_class = alert_colors.get(tipo, "alert-info")
        html += f'<div class="alert-item {color_class}">{mensaje}</div>'
    html += '</div>'
    return html


# ══════════════════════════════════════════════════════════
# COMPONENTES LEGACY (mantener compatibilidad)
# ══════════════════════════════════════════════════════════


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
