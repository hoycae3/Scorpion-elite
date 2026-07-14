"""
Scorpion Elite V4 - Dashboard Analítico
Sistema de análisis deportivo con 4 modelos matemáticos + datos reales.
"""
import streamlit as st
import os
from datetime import date

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
    """Obtiene partidos del día desde APIs."""
    partidos = []
    for ln, lid in list(LIGAS.items())[:6]:
        try:
            fx = api.get_fixtures(lid, str(date.today()))
            for f in fx[:5]:
                partidos.append(api.parse_fixture(f))
        except Exception:
            pass
    return partidos


def main():
    """Función principal."""
    init_session()
    
    # Header
    st.markdown(render_header(), unsafe_allow_html=True)
    
    # Login
    col_space, col_login = st.columns([3, 1])
    with col_login:
        if render_login_form():
            st.rerun()
    
    # Contenido principal
    if st.session_state.get("logged_in"):
        user = st.session_state.get("user")
        plan = st.session_state.get("plan")
        
        # Botón logout
        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.rerun()
        
        # Dashboard
        render_dashboard(user, plan)
    else:
        render_welcome()


def render_dashboard(user: str, plan: str):
    """Renderiza el dashboard principal."""
    col1, col2, col3 = st.columns([2, 1.2, 1.2])
    
    # Columna 1: Picks y Partidos
    with col1:
        st.markdown('<p class="section-title">🔥 Picks Recomendados del Día</p>', unsafe_allow_html=True)
        
        picks_hoy = get_picks_del_dia()
        
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
            st.info("📢 No hay picks publicados hoy.")
        
        # Mejores partidos
        st.markdown("---")
        st.markdown('<p class="section-title">⚽ Mejores Partidos del Día</p>', unsafe_allow_html=True)
        
        with st.spinner("Cargando partidos..."):
            partidos = get_partidos_del_dia()
        
        if partidos:
            # Analizar partidos
            analisis = []
            for p in partidos[:8]:
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
                        "resultado": resultado,
                        "stats_local": stats_local,
                        "stats_visit": stats_visit
                    })
                except Exception:
                    pass
            
            # Ordenar por confianza
            analisis.sort(key=lambda x: x["resultado"].confianza, reverse=True)
            
            for a in analisis[:5]:
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
            st.info("No se encontraron partidos hoy.")
    
    # Columna 2: Goleadores y Stats
    with col2:
        st.markdown('<p class="section-title">🏆 Top Goleadores</p>', unsafe_allow_html=True)
        
        liga_sel = st.selectbox("Liga", list(LIGAS.keys())[:6])
        
        # Placeholder para goleadores (requiere API adicional)
        st.markdown(render_goleador(1, "Jugador Ejemplo", 25), unsafe_allow_html=True)
        st.markdown(render_goleador(2, "Otro Jugador", 22), unsafe_allow_html=True)
        st.markdown(render_goleador(3, "Tercer Jugador", 20), unsafe_allow_html=True)
        
        # Stats
        st.markdown("---")
        st.markdown('<p class="section-title">📈 Stats del Día</p>', unsafe_allow_html=True)
        
        try:
            stats = db.get_estadisticas()
            st.markdown(render_metrica("Picks Publicados", str(stats.get("picks", 0))), unsafe_allow_html=True)
            st.markdown(render_metrica("Partidos Analizados", str(len(partidos) if 'partidos' in dir() else 0)), unsafe_allow_html=True)
        except DatabaseError:
            st.markdown(render_metrica("Picks Publicados", "0"), unsafe_allow_html=True)
    
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
            st.markdown('<div class="text-trend">• Sin picks publicados</div>', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-top:15px; margin-bottom:5px;">📈 Tendencias</p>', unsafe_allow_html=True)
        st.markdown('<div class="text-trend">📈 Cargando tendencias...</div>', unsafe_allow_html=True)
        
        st.markdown('<p style="color:#bfa15f; font-weight:bold; font-size:14px; margin-top:15px; margin-bottom:5px;">⚠️ Alertas</p>', unsafe_allow_html=True)
        st.markdown(render_alerta("Los datos se actualizan en tiempo real."), unsafe_allow_html=True)
        
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
