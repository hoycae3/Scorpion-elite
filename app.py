"""
Scorpion Elite V4 - Dashboard Analítico
Sistema de análisis deportivo con 4 modelos matemáticos + datos reales.
"""
import streamlit as st
import os
import logging
from datetime import date

# Configurar logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Importar módulos refactorizados
from scorpion.config import config, LIGAS
from scorpion.db.database import get_db, DatabaseError
from scorpion.models.math import MotorAnalisis
from scorpion.api.football import FootballAPI
from scorpion.ui.components import (
    render_header,
    render_pick_card,
    render_match_row,
    render_goleador,
    render_metrica,
    render_alerta,
)

# Configuración de página
st.set_page_config(
    layout="wide",
    page_title="Scorpion Elite - Dashboard Analítico",
    page_icon="🦂"
)

# Cargar CSS externo
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Inicializar componentes globales
db = get_db()
motor = MotorAnalisis()
api = FootballAPI()


def init_session():
    """Inicializa variables de sesión."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "plan" not in st.session_state:
        st.session_state.plan = None


def render_login_form() -> bool:
    """Renderiza formulario de login."""
    with st.form("login_form"):
        st.markdown("<p style='color:#dfba6b; margin:0; font-weight:bold;'>Acceso</p>", unsafe_allow_html=True)
        user_input = st.text_input("Usuario", placeholder="Tu cédula o 'admin'", label_visibility="collapsed")
        password_input = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed")
        submit_btn = st.form_submit_button("Entrar →")
        
        if submit_btn:
            if user_input == "admin" and password_input == config.ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.user = "admin"
                st.session_state.plan = "admin"
                st.success("✅ Acceso concedido como Administrador")
                return True
            elif user_input:
                try:
                    ok, plan, dr = db.verificar_acceso(user_input)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.user = user_input
                        st.session_state.plan = plan
                        st.success(f"✅ Bienvenido - Plan {plan.upper()}")
                        return True
                    else:
                        st.error(f"❌ Acceso denegado: {dr}")
                except DatabaseError as e:
                    st.error(f"Error de base de datos: {e}")
    return False


def get_picks_del_dia():
    """Obtiene picks publicados para hoy."""
    try:
        return db.get_picks(str(date.today()), plan="admin")
    except DatabaseError:
        return []


def get_partidos_del_dia():
    """Obtiene partidos del día desde APIs con datos de fallback."""
    partidos = []
    for ln, lid in list(LIGAS.items())[:6]:
        try:
            fx = api.get_fixtures(lid, str(date.today()))
            for f in fx[:5]:
                partidos.append(api.parse_fixture(f))
        except Exception as e:
            logger.warning(f"Error obteniendo fixtures de {ln}: {e}")
    
    # Si no hay partidos de hoy, obtener de la semana
    if not partidos:
        try:
            from datetime import timedelta
            for ln, lid in list(LIGAS.items())[:4]:
                fx = api.get_fixtures(lid, desde=str(date.today()), hasta=str(date.today() + timedelta(days=7)))
                for f in fx[:3]:
                    partidos.append(api.parse_fixture(f))
        except Exception:
            pass
    
    return partidos


def get_goleadores_liga(liga_id: int, liga_nombre: str):
    """Obtiene goleadores de una liga desde API."""
    try:
        # Obtener fixtures para tener equipos
        fx = api.get_fixtures(liga_id, str(date.today()))
        if not fx:
            from datetime import timedelta
            fx = api.get_fixtures(liga_id, desde=str(date.today()), hasta=str(date.today() + timedelta(days=7)))
        
        goleadores = []
        equipos_vistos = set()
        
        for f in fx[:15]:  # Revisar hasta 15 partidos
            home_id = f["teams"]["home"]["id"]
            away_id = f["teams"]["away"]["id"]
            
            for tid, tname in [(home_id, f["teams"]["home"]["name"]), (away_id, f["teams"]["away"]["name"])]:
                if tid in equipos_vistos:
                    continue
                equipos_vistos.add(tid)
                
                try:
                    gm, gc = api.get_stats_equipo(tid, liga_id)
                    if gm is not None:
                        # Estimar goles en temporada (aprox 20 partidos)
                        goleadores.append({
                            "nombre": tname,
                            "goles": round(gm * 18),  # Aproximado
                            "liga": liga_nombre
                        })
                except Exception:
                    pass
                
                if len(equipos_vistos) >= 12:
                    break
        
        # Ordenar por goles
        goleadores.sort(key=lambda x: x["goles"], reverse=True)
        return goleadores[:10]
    except Exception as e:
        logger.warning(f"Error obteniendo goleadores: {e}")
        return []


def main():
    """Función principal."""
    init_session()
    
    # Header con logo y login en la misma línea
    col_header_left, col_header_right = st.columns([4, 1])
    
    with col_header_left:
        st.markdown(render_header(), unsafe_allow_html=True)
    
    with col_header_right:
        if st.session_state.get("logged_in"):
            st.markdown(f"""
            <div style="text-align: right; padding: 10px; background: #131926; border-radius: 8px; margin-top: 20px;">
                <div style="color: #d4af37; font-weight: bold;">👤 {st.session_state.get('user', 'Admin')}</div>
                <div style="color: #888; font-size: 12px;">Plan: {st.session_state.get('plan', 'gratis').upper()}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Cerrar sesión", key="logout_btn"):
                st.session_state.clear()
                st.rerun()
        else:
            st.markdown("<p style='color:#dfba6b; margin: 20px 0 5px; font-weight:bold; text-align: right;'>Acceso</p>", unsafe_allow_html=True)
            with st.form("login_form_main", clear_on_submit=True):
                user_input = st.text_input("Usuario", placeholder="Tu cédula o 'admin'", label_visibility="collapsed", key="user_main")
                password_input = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed", key="pass_main")
                submit_btn = st.form_submit_button("Entrar →")
                
                if submit_btn:
                    if user_input == "admin" and password_input == config.ADMIN_PASSWORD:
                        st.session_state.logged_in = True
                        st.session_state.user = "admin"
                        st.session_state.plan = "admin"
                        st.success("✅ Acceso concedido como Administrador")
                        st.rerun()
                    elif user_input:
                        try:
                            ok, plan, dr = db.verificar_acceso(user_input)
                            if ok:
                                st.session_state.logged_in = True
                                st.session_state.user = user_input
                                st.session_state.plan = plan
                                st.success(f"✅ Bienvenido - Plan {plan.upper()}")
                                st.rerun()
                            else:
                                st.error(f"❌ Acceso denegado: {dr}")
                        except DatabaseError as e:
                            st.error(f"Error de base de datos: {e}")
    
    # Dashboard siempre visible (sin pantalla de bienvenida)
    user = st.session_state.get("user", "invitado")
    plan = st.session_state.get("plan", "gratis")
    render_dashboard(user, plan)


def render_dashboard(user: str, plan: str):
    """Renderiza el dashboard principal."""
    col1, col2, col3 = st.columns([2, 1.2, 1.2])
    
    # Obtener datos
    picks_hoy = get_picks_del_dia()
    
    with st.spinner("Cargando partidos..."):
        partidos = get_partidos_del_dia()
    
    # Columna 1: Picks y Partidos
    with col1:
        st.markdown('<p class="section-title">🔥 Picks Recomendados del Día</p>', unsafe_allow_html=True)
        
        if picks_hoy:
            sub_c1, sub_c2, sub_c3 = st.columns(3)
            for i, (pick, col) in enumerate(zip(picks_hoy[:3], [sub_c1, sub_c2, sub_c3]), 1):
                with col:
                    st.markdown(render_pick_card(
                        numero=i,
                        liga=pick.get("liga", ""),
                        local=pick.get("local", ""),
                        visitante=pick.get("visitante", ""),
                        mercado=pick.get("mercado", ""),
                        cuota=pick.get("cuota"),
                        confianza=pick.get("confianza"),
                        rango=pick.get("rango", "B")
                    ), unsafe_allow_html=True)
        else:
            # Picks de ejemplo cuando no hay publicados
            st.markdown(render_pick_card(
                numero=1, liga="Premier League",
                local="Manchester City", visitante="Liverpool",
                mercado="Over 2.5 Goles", cuota=1.75, confianza=72, rango="A+"
            ), unsafe_allow_html=True)
            st.markdown(render_pick_card(
                numero=2, liga="La Liga",
                local="Real Madrid", visitante="Barcelona",
                mercado="BTTS - Ambos Marcan", cuota=1.65, confianza=68, rango="B"
            ), unsafe_allow_html=True)
            st.markdown(render_pick_card(
                numero=3, liga="Champions League",
                local="Bayern Munich", visitante=" PSG",
                mercado="Victoria Local (1)", cuota=1.80, confianza=65, rango="B"
            ), unsafe_allow_html=True)
        
        # Mejores partidos
        st.markdown("---")
        st.markdown('<p class="section-title">⚽ Mejores Partidos del Día</p>', unsafe_allow_html=True)
        
        if partidos:
            # Analizar partidos
            analisis = []
            for p in partidos[:10]:
                try:
                    stats_local = api.obtener_stats_completo(p.local, p.liga)
                    stats_visit = api.obtener_stats_completo(p.visitante, p.liga)
                    resultado = motor.analizar(
                        gm_local=stats_local.gm,
                        gc_local=stats_local.gc,
                        gm_visitante=stats_visit.gm,
                        gc_visitante=stats_visit.gc,
                        elo_local=stats_local.elo,
                        elo_visitante=stats_visit.elo,
                        liga=p.liga,
                        usar_datos_reales=stats_local.ok or stats_visit.ok
                    )
                    analisis.append({
                        "partido": p,
                        "resultado": resultado
                    })
                except Exception as e:
                    logger.warning(f"Error analizando {p.local} vs {p.visitante}: {e}")
            
            # Ordenar por confianza
            if analisis:
                analisis.sort(key=lambda x: x["resultado"].confianza, reverse=True)
                
                for a in analisis[:6]:
                    p = a["partido"]
                    r = a["resultado"]
                    st.markdown(render_match_row(
                        local=p.local,
                        visitante=p.visitante,
                        hora=p.hora,
                        liga=p.liga,
                        rango=r.rango,
                        over25=r.over25
                    ), unsafe_allow_html=True)
        else:
            # Partidos de ejemplo
            st.markdown(render_match_row("Manchester City", "Liverpool", "21:00", "Premier League", "A+", 72), unsafe_allow_html=True)
            st.markdown(render_match_row("Real Madrid", "Barcelona", "21:00", "La Liga", "B", 68), unsafe_allow_html=True)
            st.markdown(render_match_row("Bayern Munich", "PSG", "21:00", "Champions League", "B", 65), unsafe_allow_html=True)
            st.markdown(render_match_row("Juventus", "Inter Milan", "20:45", "Serie A", "B", 62), unsafe_allow_html=True)
            st.markdown(render_match_row("Atletico Madrid", "Sevilla", "21:00", "La Liga", "C", 55), unsafe_allow_html=True)
    
    # Columna 2: Goleadores y Stats
    with col2:
        st.markdown('<p class="section-title">🏆 Top Goleadores</p>', unsafe_allow_html=True)
        
        liga_opciones = list(LIGAS.keys())[:6]
        liga_sel = st.selectbox("Liga", liga_opciones)
        liga_id = LIGAS.get(liga_sel, 39)
        
        with st.spinner("Cargando goleadores..."):
            goleadores = get_goleadores_liga(liga_id, liga_sel)
        
        if goleadores:
            for i, g in enumerate(goleadores[:8], 1):
                st.markdown(render_goleador(i, g["nombre"], g["goles"]), unsafe_allow_html=True)
        else:
            # Goleadores de ejemplo
            goleadores_ejemplo = [
                ("Erling Haaland", 33), ("Mohamed Salah", 28), ("Kylian Mbappé", 26),
                ("Harry Kane", 24), ("Robert Lewandowski", 22), ("Lautaro Martínez", 21),
                ("Vinicius Jr", 19), ("Bukayo Saka", 18)
            ]
            for i, (nombre, goles) in enumerate(goleadores_ejemplo, 1):
                st.markdown(render_goleador(i, nombre, goles), unsafe_allow_html=True)
        
        # Stats
        st.markdown("---")
        st.markdown('<p class="section-title">📈 Stats del Día</p>', unsafe_allow_html=True)
        
        try:
            stats = db.get_estadisticas()
            st.markdown(render_metrica("Picks Publicados", str(stats.get("picks", 0))), unsafe_allow_html=True)
            st.markdown(render_metrica("Partidos Analizados", str(len(partidos) if partidos else 0)), unsafe_allow_html=True)
            st.markdown(render_metrica("Goleadores", str(len(goleadores) if goleadores else 8)), unsafe_allow_html=True)
        except DatabaseError:
            st.markdown(render_metrica("Picks Publicados", "0"), unsafe_allow_html=True)
            st.markdown(render_metrica("Partidos Analizados", "5+"), unsafe_allow_html=True)
    
    # Columna 3: Tendencias y Alertas
    with col3:
        st.markdown('<p class="section-title">📊 Mercados y Tendencias</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-right-card">', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-bottom:5px;">🔥 Picks con Mayor Confianza</p>', unsafe_allow_html=True)
        
        if picks_hoy:
            for p in picks_hoy[:3]:
                conf_color = "#00ee66" if p.get("confianza", 0) >= 70 else "#ffd700"
                st.markdown(f'<div class="text-trend">• {p.get("mercado", "N/A")} @ {p.get("cuota", "N/A")} <span style="color: {conf_color};">[{p.get("confianza", 0)}%]</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="text-trend">• Over 2.5 @ 1.75 [72%]</div>', unsafe_allow_html=True)
            st.markdown('<div class="text-trend">• BTTS @ 1.65 [68%]</div>', unsafe_allow_html=True)
            st.markdown('<div class="text-trend">• Victoria 1 @ 1.80 [65%]</div>', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-top:15px; margin-bottom:5px;">📈 Tendencias de Equipos</p>', unsafe_allow_html=True)
        
        if analisis:
            for a in analisis[:3]:
                r = a["resultado"]
                if r.p1 > r.p2:
                    st.markdown(f'<div class="text-trend">📈 {a["partido"].local}: {r.p1}% victoria</div>', unsafe_allow_html=True)
                elif r.p2 > r.p1:
                    st.markdown(f'<div class="text-trend">📉 {a["partido"].local}: {r.p2}% visita</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="text-trend">⚖️ {a["partido"].local}: Empate</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="text-trend">📈 Man City: 80% últimos 10</div>', unsafe_allow_html=True)
            st.markdown('<div class="text-trend">📈 Real Madrid: 75% últimos 10</div>', unsafe_allow_html=True)
            st.markdown('<div class="text-trend">📉 Barcelona: 60% últimos 10</div>', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-top:15px; margin-bottom:5px;">⚠️ Alertas de Última Hora</p>', unsafe_allow_html=True)
        st.markdown(render_alerta("Datos actualizados desde múltiples APIs deportivas"), unsafe_allow_html=True)
        st.markdown(render_alerta("Los análisis son solo informativos"), unsafe_allow_html=True)
        
        if plan == "admin":
            st.markdown("---")
            st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px;">🔧 Panel Admin</p>', unsafe_allow_html=True)
            st.info("Usa el panel de administración para publicar picks.")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_welcome():
    """Renderiza pantalla de bienvenida."""
    st.markdown("""
    <div style="text-align: center; padding: 50px; background: #131926; border-radius: 15px; margin-top: 50px;">
        <h2 style="color: #d4af37;">🦂 Bienvenido a Scorpion Elite</h2>
        <p style="color: #8a94a6; font-size: 16px;">
            Sistema de análisis deportivo con 4 modelos matemáticos + datos reales de internet
        </p>
        <p style="color: #00ee66; font-size: 14px;">
            Inicia sesión para acceder al dashboard completo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Info de planes
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    planes = [
        ("🆓 Gratis", "5 análisis/día", "Sin datos reales"),
        ("📅 Día", "Análisis completo", "1 liga"),
        ("📆 Semana", "Multi-liga", "+ Escalera"),
        ("👑 Mes", "Ilimitado", "+ Combinadas")
    ]
    for col, (plan, desc1, desc2) in zip([c1, c2, c3, c4], planes):
        with col:
            st.markdown(f"""
            <div style="background: #131926; border: 1px solid #3a3f50; border-radius: 8px; padding: 15px; text-align: center;">
                <h3 style="color: #d4af37; margin: 0;">{plan}</h3>
                <p style="color: #fff; font-size: 14px; margin: 5px 0;">{desc1}</p>
                <p style="color: #8a94a6; font-size: 12px;">{desc2}</p>
            </div>
            """, unsafe_allow_html=True)


# Footer
st.markdown("""
<div class="footer">
    🦂 Scorpion Elite V4 Pro 2025 · Sistema de análisis estadístico deportivo<br>
    Solo uso informativo · Las apuestas implican riesgo real de pérdida
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
