"""
Scorpion Elite V4 - Dashboard Analítico
Sistema de análisis deportivo con Web Scraping + APIs + 4 modelos matemáticos.
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
from scorpion.api.scraper import (
    obtener_partidos_hoy,
    obtener_partidos_liga,
    obtener_estadisticas_equipo,
    obtener_top_goleadores_liga,
    calcular_confianza_partido,
)
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
    """Obtiene partidos del día desde Web Scraping de Flashscore."""
    try:
        # Usar scraper de Flashscore
        partidos_scraped = obtener_partidos_hoy()
        
        # Convertir a formato del sistema
        partidos = []
        for p in partidos_scraped:
            class PartidoData:
                def __init__(self):
                    self.hora = p.hora
                    self.local = p.local
                    self.visitante = p.visitante
                    self.liga = p.liga
                    self.fecha = p.fecha
            partidos.append(PartidoData())
        
        if partidos:
            logger.info(f"Scraping: {len(partidos)} partidos obtenidos")
            return partidos
        
    except Exception as e:
        logger.warning(f"Error en scraping: {e}")
    
    # Fallback: intentar APIs tradicionales
    partidos = []
    for ln, lid in list(LIGAS.items())[:6]:
        try:
            fx = api.get_fixtures(lid, str(date.today()))
            for f in fx[:5]:
                partidos.append(api.parse_fixture(f))
        except Exception:
            pass
    
    return partidos


def get_goleadores_liga_scraper(liga_nombre: str):
    """Obtiene goleadores de una liga usando Web Scraping."""
    try:
        goleadores = obtener_top_goleadores_liga(liga_nombre)
        if goleadores:
            return [{"nombre": g.nombre, "goles": g.goles, "liga": liga_nombre} for g in goleadores]
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
    """Renderiza el dashboard principal con datos de Web Scraping."""
    col1, col2, col3 = st.columns([2, 1.2, 1.2])
    
    # Obtener datos con scraping
    picks_hoy = get_picks_del_dia()
    partidos = []
    analisis = []
    
    with st.spinner("🌐 Obteniendo partidos desde Flashscore..."):
        try:
            partidos = get_partidos_del_dia()
            
            # Analizar partidos con modelo matemático
            for p in partidos[:12]:
                try:
                    # Obtener forma reciente del equipo (scraping)
                    forma_local = obtener_estadisticas_equipo(p.local)
                    forma_visit = obtener_estadisticas_equipo(p.visitante)
                    
                    # Calcular confianza
                    confianza = calcular_confianza_partido(p.local, p.visitante, forma_local, forma_visit)
                    
                    # Crear resultado simplificado
                    class ResultadoSimple:
                        def __init__(self):
                            self.p1 = confianza["pct_local"]
                            self.p2 = confianza["pct_visit"]
                            self.pX = 100 - self.p1 - self.p2
                            self.confianza = confianza["confianza"]
                            self.over25 = confianza["over_25"]
                            self.resultado = confianza["resultado"]
                            # Rangos
                            if self.confianza >= 75:
                                self.rango = "A+"
                            elif self.confianza >= 65:
                                self.rango = "A"
                            elif self.confianza >= 55:
                                self.rango = "B"
                            else:
                                self.rango = "C"
                    
                    analisis.append({
                        "partido": p,
                        "resultado": ResultadoSimple(),
                        "forma_local": forma_local,
                        "forma_visit": forma_visit
                    })
                except Exception as e:
                    logger.warning(f"Error analizando {p.local}: {e}")
            
            if analisis:
                analisis.sort(key=lambda x: x["resultado"].confianza, reverse=True)
                
        except Exception as e:
            logger.warning(f"Error obteniendo partidos: {e}")
    
    # Selector de liga para goleadores
    liga_opciones = list(LIGAS.keys())[:6]
    liga_seleccionada = st.selectbox("🏆 Seleccionar Liga", liga_opciones, key="liga_selector")
    
    with st.spinner("📊 Cargando goleadores..."):
        goleadores = get_goleadores_liga_scraper(liga_seleccionada)
    
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
            st.info("📢 No hay picks publicados hoy. Publica picks desde el panel de administración.")
        
        # Partidos del día
        st.markdown("---")
        st.markdown(f'<p class="section-title">⚽ Partidos del Día ({len(partidos)} encontrados)</p>', unsafe_allow_html=True)
        
        if analisis:
            for a in analisis[:10]:
                p = a["partido"]
                r = a["resultado"]
                f = a["forma_local"]
                
                # Mostrar partido con análisis
                st.markdown(render_match_row(
                    local=f"{p.local} {f['forma']}",
                    visitante=p.visitante,
                    hora=p.hora,
                    liga=p.liga,
                    rango=r.rango,
                    over25=r.over25
                ), unsafe_allow_html=True)
        else:
            st.warning("⚠️ No se pudieron obtener partidos. Verificando conexión...")
    
    # Columna 2: Goleadores y Stats
    with col2:
        st.markdown(f'<p class="section-title">🏆 Top Goleadores - {liga_seleccionada.split()[0] if liga_seleccionada else "Liga"}</p>', unsafe_allow_html=True)
        
        if goleadores:
            for i, g in enumerate(goleadores[:10], 1):
                st.markdown(render_goleador(i, g["nombre"], g["goles"]), unsafe_allow_html=True)
        else:
            st.info("📊 Cargando goleadores...")
        
        # Stats
        st.markdown("---")
        st.markdown('<p class="section-title">📈 Stats del Sistema</p>', unsafe_allow_html=True)
        
        try:
            stats = db.get_estadisticas()
            st.markdown(render_metrica("Picks Publicados", str(stats.get("picks", 0))), unsafe_allow_html=True)
        except DatabaseError:
            st.markdown(render_metrica("Picks Publicados", "0"), unsafe_allow_html=True)
        
        st.markdown(render_metrica("Partidos Analizados", str(len(analisis))), unsafe_allow_html=True)
        st.markdown(render_metrica("Fuente", "Flashscore 🌐"), unsafe_allow_html=True)
    
    # Columna 3: Tendencias y Alertas
    with col3:
        st.markdown('<p class="section-title">📊 Predicciones y Tendencias</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-right-card">', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-bottom:5px;">🔥 Picks con Mayor Confianza</p>', unsafe_allow_html=True)
        
        if picks_hoy:
            for p in picks_hoy[:3]:
                conf_color = "#00ee66" if p.get("confianza", 0) >= 70 else "#ffd700"
                st.markdown(f'<div class="text-trend">• {p.get("mercado", "N/A")} @ {p.get("cuota", "N/A")} <span style="color: {conf_color};">[{p.get("confianza", 0)}%]</span></div>', unsafe_allow_html=True)
        elif analisis[:3]:
            for a in analisis[:3]:
                r = a["resultado"]
                prediccion = f"1" if r.resultado == "1" else ("X" if r.resultado == "X" else "2")
                st.markdown(f'<div class="text-trend">• {a["partido"].local[:15]} <span style="color:#00ee66;">{prediccion}</span> @ {r.confianza}%</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="text-trend">• Cargando predicciones...</div>', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-top:15px; margin-bottom:5px;">📈 Forma Reciente</p>', unsafe_allow_html=True)
        
        if analisis:
            for a in analisis[:4]:
                f = a["forma_local"]
                st.markdown(f'<div class="text-trend">• {a["partido"].local[:12]}: {f["forma"]} ({f["victorias"]}V-{f["empates"]}E-{f["derrotas"]}D)</div>', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-top:15px; margin-bottom:5px;">⚠️ Alertas</p>', unsafe_allow_html=True)
        st.markdown(render_alerta("🌐 Datos de Flashscore en tiempo real"), unsafe_allow_html=True)
        st.markdown(render_alerta("⚽ Análisis con modelos matemáticos"), unsafe_allow_html=True)
        
        if plan == "admin":
            st.markdown("---")
            st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px;">🔧 Panel Admin</p>', unsafe_allow_html=True)
            if st.button("📝 Publicar Pick", key="btn_admin"):
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
