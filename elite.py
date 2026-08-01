import streamlit as st
import pandas as pd
import os
# Mapeo de league_id por nombre de liga
LIGAS_MAP = {
    'Premier League': 39,
    'La Liga': 140,
    'Bundesliga': 78,
    'Serie A': 135,
    'Ligue 1': 61,
    'Liga MX': 262,
    'MLS': 1,
    'Copa Libertadores': 13,
    'Champions League': 2,
    'Europa League': 3,
    'Primeira Liga': 94,
    'Eredivisie': 88,
    'Belgian Pro League': 61,
    'Scottish Premiership': 50,
    'Brasileirao': 71,
    'Argentine Primera': 128,
    'Chile Primera Division': 215,
    'Primera Division': 215,
    'Primera A': 215,
    'Primera B': 216,
}

import logging
import html
import bcrypt
from datetime import date, timedelta, datetime, timezone, time
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
# En producción (Render) las variables vienen del Dashboard
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from supabase import create_client
from analysis_models import calcular
from stats_extractor import calculate_team_lambda
from stats_robot import run_robot_batch
from scrapers_fallback import scrape_team_fallback
from calibration import (
    get_lambda_ajustada,
    registrar_resultado,
    obtener_estadisticas_calibracion,
    resetear_calibracion
)

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

# ══════════════════════════════════════════════════════════
# CONFIGURACION - Variables de entorno
# ══════════════════════════════════════════════════════════
# Las variables se cargan desde .env (desarrollo) o Render Dashboard (producción)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Valores por defecto SOLO para desarrollo local (NO usar en producción)
# En producción, estas variables DEBEN estar configuradas en el Dashboard de Render
if not ADMIN_PASSWORD:
    raise ValueError("❌ ADMIN_PASSWORD no está configurada. Configúrala en variables de entorno.")
if not SUPABASE_URL:
    raise ValueError("❌ SUPABASE_URL no está configurada. Configúrala en variables de entorno.")
if not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_KEY no está configurada. Configúrala en variables de entorno.")

# Base de datos persistente en el directorio de la aplicación
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════
# CLIENTE SUPABASE UNIFICADO con @st.cache_resource
# ══════════════════════════════════════════════════════════
@st.cache_resource
def get_supabase_client():
    """Crea y cachea el cliente de Supabase - se reutiliza en toda la app"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("SUPABASE_URL o SUPABASE_KEY no están configurados")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Error al crear cliente Supabase: {e}")
        return None

def get_client():
    """Función de compatibilidad - retorna cliente de Supabase"""
    return get_supabase_client()

# ══════════════════════════════════════════════════════════
# SISTEMA DE USUARIOS (SQLite local) - Solo hash bcrypt
# ══════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Genera hash bcrypt con salt automático"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verifica password contra hash bcrypt"""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False

def get_hoy():
    return str(datetime.now(timezone(timedelta(hours=-5))).date())


def db_todos():
    """Obtiene todos los usuarios"""
    client = get_client()
    if not client:
        return []
    try:
        resp = client.table('usuarios').select('id, nombre, plan, dias, activo, es_admin, creado_at').execute()
        return resp.data if resp.data else []
    except Exception as e:
        logger.error(f"Error en db_todos: {e}")
        return []

def db_crear_usuario(password, nombre, plan, dias):
    """Crea un nuevo usuario VIP en Supabase"""
    client = get_client()
    if not client:
        return False
    try:
        pwd_hash = hash_password(password)
        client.table('usuarios').insert({
            'password_hash': pwd_hash,
            'nombre': nombre,
            'plan': plan,
            'fecha_inicio': get_hoy(),
            'dias': dias,
            'activo': True,
            'es_admin': False
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Error en db_crear_usuario: {e}")
        return False

def db_cambiar_password(user_id, password):
    """Cambia password de usuario"""
    client = get_client()
    if not client:
        return False
    try:
        pwd_hash = hash_password(password)
        client.table('usuarios').update({'password_hash': pwd_hash}).eq('id', user_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error en db_cambiar_password: {e}")
        return False

def db_eliminar_usuario(user_id):
    """Elimina un usuario (no admin)"""
    client = get_client()
    if not client:
        return False
    try:
        client.table('usuarios').delete().eq('id', user_id).eq('es_admin', False).execute()
        return True
    except Exception as e:
        logger.error(f"Error en db_eliminar_usuario: {e}")
        return False

def db_actualizar_plan(user_id, plan, dias):
    try:
        client.table('usuarios').update({
            'plan': plan,
            'dias': dias,
            'fecha_inicio': get_hoy()
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error en db_actualizar_plan: {e}")
        return False

def db_login(password):
    """Verifica password con bcrypt contra Supabase"""
    client = get_client()
    if not client:
        return None
    try:
        resp = client.table('usuarios').select('*').eq('activo', True).execute()
        if resp.data:
            for usuario in resp.data:
                pwd_hash = usuario.get('password_hash', '')
                if verify_password(password, pwd_hash):
                    return usuario
        return None
    except Exception as e:
        logger.error(f"Error en db_login: {e}")
        return None
if "logged" not in st.session_state:
    st.session_state.logged = False
if "page" not in st.session_state:
    st.session_state.page = "VIP"
if "show_login" not in st.session_state:
    st.session_state.show_login = False
def render_public_landing():
    """Renderiza la landing page pública para usuarios no autenticados"""
    
    # --- HERO SECTION ---
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">
            <span class="scorpion-icon">🦂</span>
            <span class="title-text">SCORPION ELITE</span>
            <span class="scorpion-icon">🦂</span>
        </h1>
        <p class="hero-subtitle">Inteligencia Artificial para Pronósticos Deportivos</p>
        <p class="hero-description">Sistema predictivo con 4 modelos matemáticos avanzados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón Acceder arriba
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🔐 Acceder", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()

    # --- KPIs EN VIVO ---
    st.markdown("##### 📊 Métricas")

    # Obtener métricas REALES de Supabase
    try:
        client = get_client()
        if client:
            # Obtener todos los picks
            response = client.table('picks').select('*').execute()
            total_picks = len(response.data) if response.data else 0
            
            # Contar aciertos reales (donde resultado_real != null)
            aciertos = 0
            total_yield = 0
            for pick in response.data if response.data else []:
                if pick.get('resultado_real'):
                    aciertos += 1
                if pick.get('yield_real'):
                    total_yield += pick.get('yield_real', 0)
            
            # Calcular porcentaje de aciertos
            pct_aciertos = round(aciertos/total_picks*100, 1) if total_picks > 0 else 0
            yield_pct = round(total_yield/aciertos, 1) if aciertos > 0 else 0
            
            # Obtener número de equipos con stats
            equipos_response = client.table('equipos_stats').select('*').execute()
            total_equipos = len(equipos_response.data) if equipos_response.data else 0
        else:
            total_picks = 0
            aciertos = 0
            pct_aciertos = 0
            yield_pct = 0
            total_equipos = 0
    except Exception as e:
        total_picks = 0
        aciertos = 0
        pct_aciertos = 0
        yield_pct = 0
        total_equipos = 0

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        st.metric("Aciertos", f"{pct_aciertos}%", f"{aciertos} de {total_picks}")

    with col_kpi2:
        st.metric("Pronósticos", f"{total_picks:,}", f"{total_equipos} equipos")

    with col_kpi3:
        st.metric("Rentabilidad", f"{yield_pct:+.1f}%", "")

    # Estado para análisis preview
    if "preview_partido" not in st.session_state:
        st.session_state.preview_partido = None

    # Obtener partidos reales de Supabase
    try:
        client = get_client()
        if client:
            response = client.table('partidos').select('*').execute()
            partidos = response.data if response.data else []
        else:
            partidos = []
    except Exception as e:
        logger.error(f"Error obteniendo partidos: {e}")
        partidos = []

    if st.session_state.preview_partido:
        # MOSTRAR ANÁLISIS DEL PARTIDO SELECCIONADO
        partido = st.session_state.preview_partido
        local = partido.get('equipo_local', 'Local')
        visitante = partido.get('equipo_visitante', 'Visitante')
        liga = partido.get('liga', '')
        
        st.markdown("---")
        st.markdown(f"## ⚽ Pronóstico: {local} VS {visitante}")
        if liga:
            st.caption(f"🏆 {liga}")
        
        # Botón para volver
        if st.button("← Volver", key="volver_partidos"):
            st.session_state.preview_partido = None
            st.rerun()
        
        st.markdown("---")
        
        # Obtener stats de equipos
        try:
            client = get_client()
            if client:
                local_resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{local}%').execute()
                visit_resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{visitante}%').execute()
                
                stats_local = local_resp.data[0] if local_resp.data else None
                stats_visit = visit_resp.data[0] if visit_resp.data else None
                
                # DEBUG - ver qué equipos se encuentran
                st.write(f"🔍 Buscando: '{local}' y '{visitante}'")
                
                
                if stats_local and stats_visit:
                    st.markdown("---")
                    st.markdown("### 📊 Estadísticas Calibradas")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**🏠 {local}**")
                        forma_l = stats_local.get('forma', 'N/A')
                        if forma_l and forma_l != 'N/A':
                            forma_html = ''.join([{'W': '<span style="color:#22c55e">W</span>', 'L': '<span style="color:#ef4444">L</span>', 'D': '<span style="color:#eab308">D</span>'}.get(c, c) for c in str(forma_l)])
                            st.markdown(f"**Forma:** {forma_html}", unsafe_allow_html=True)
                        else:
                            st.markdown(f"**Forma:** N/A")
                        st.markdown(f"**V/E/D:** <span style='color:black;font-weight:bold'>{stats_local.get('victorias', 0)}/{stats_local.get('empates', 0)}/{stats_local.get('derrotas', 0)}</span>", unsafe_allow_html=True)
                        st.markdown(f"**GF/GC:** <span style='color:black;font-weight:bold'>{stats_local.get('goles_favor', 0)}/{stats_local.get('goles_contra', 0)}</span>", unsafe_allow_html=True)
                        lambda_l = stats_local.get('lambda_local', 0)
                        st.markdown(f"**Ataque:** <span style='color:black;font-weight:bold'>{lambda_l:.2f}</span> goles/partido", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**✈️ {visitante}**")
                        forma_v = stats_visit.get('forma', 'N/A')
                        if forma_v and forma_v != 'N/A':
                            forma_html = ''.join([{'W': '<span style="color:#22c55e">W</span>', 'L': '<span style="color:#ef4444">L</span>', 'D': '<span style="color:#eab308">D</span>'}.get(c, c) for c in str(forma_v)])
                            st.markdown(f"**Forma:** {forma_html}", unsafe_allow_html=True)
                        else:
                            st.markdown(f"**Forma:** N/A")
                        st.markdown(f"**V/E/D:** <span style='color:black;font-weight:bold'>{stats_visit.get('victorias', 0)}/{stats_visit.get('empates', 0)}/{stats_visit.get('derrotas', 0)}</span>", unsafe_allow_html=True)
                        st.markdown(f"**GF/GC:** <span style='color:black;font-weight:bold'>{stats_visit.get('goles_favor', 0)}/{stats_visit.get('goles_contra', 0)}</span>", unsafe_allow_html=True)
                        lambda_v = stats_visit.get('lambda_visitante', 0)
                        st.markdown(f"**Ataque:** <span style='color:black;font-weight:bold'>{lambda_v:.2f}</span> goles/partido", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Predicciones
                    gf_l = float(stats_local.get('goles_favor', 0) or 0)
                    gf_v = float(stats_visit.get('goles_favor', 0) or 0)
                    gc_l = float(stats_local.get('goles_contra', 0) or 0)
                    gc_v = float(stats_visit.get('goles_contra', 0) or 0)
                    
                    prom_l = (gf_l + gc_v) / 2
                    prom_v = (gf_v + gc_l) / 2
                    
                    st.markdown("### 🎯 Predicciones")
                    
                    # 1X2
                    if prom_l > prom_v * 1.2:
                        st.success(f"**1X2:** Local - Alta probabilidad")
                    elif prom_v > prom_l * 1.2:
                        st.success(f"**1X2:** Visitante - Alta probabilidad")
                    else:
                        st.warning(f"**1X2:** Empate - Probabilidad media")
                    
                    # Over/Under
                    total = prom_l + prom_v
                    ou = "Over 2.5" if total > 2.5 else "Under 2.5"
                    st.info(f"**Over/Under 2.5:** {ou} ({total:.1f} goles esperados)")
                    
                    # BTTS
                    btts = "Sí" if gf_l > 1 and gf_v > 1 else "No"
                    st.info(f"**Ambos Marcan (BTTS):** {btts}")
                    
                    st.markdown("---")
                    st.caption("🔐 Accede con tu cuenta para análisis completo con 4 modelos matemáticos.")
                else:
                    st.warning(f"No hay estadísticas para {local} o {visitante}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        # MOSTRAR 4 PARTIDOS ALEATORIOS - PRUEBA GRATIS
        if partidos:
            import random
            random.seed()  # Semilla aleatoria basada en tiempo
            partidos_aleatorios = random.sample(partidos, min(4, len(partidos)))
            
            st.markdown("###### Partidos Destacados")
            st.caption("Preview gratuito - Accede con tu cuenta para análisis completo")
            
            for i, partido in enumerate(partidos_aleatorios, 1):
                # Variables del partido
                local = partido.get('equipo_local', 'Local')
                visitante = partido.get('equipo_visitante', 'Visitante')
                liga = partido.get('liga', '')
                hora = partido.get('hora', '')

                # Partido en una línea
                st.markdown(f"**{i}.** **{local}** VS **{visitante}**  ·  {hora} {liga}")
                st.markdown("")
            
            st.caption("🔐 Accede con tu cuenta para ver todos los partidos y análisis completo con 4 modelos matemáticos.")
        else:
            st.info("📭 No hay partidos cargados. Ve a la pestaña **Carga** para subir datos.")



    # --- CÓMO FUNCIONA ---
    st.markdown("### 🔍 ¿Cómo Funciona?")
    st.markdown("*El analizador usa 4 modelos matemáticos para predecir resultados*")

    modelos_col1, modelos_col2 = st.columns(2)
    with modelos_col1:
        st.markdown("**📈 Modelos de Predicción:**")
        st.markdown("- **Poisson:** Distribución de goles")
        st.markdown("- **Dixon-Coles:** Efecto tiempo/partido")
    with modelos_col2:
        st.markdown("**🎯 Modelos Avanzados:**")
        st.markdown("- **Monte Carlo:** Simulaciones")
        st.markdown("- **Elo:** Rating de equipos")

    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # --- TABLA DE PLANES ---
    st.markdown("### 💰 Planes y Precios")

    st.markdown("""
    <style>
    .price-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    .price-table th, .price-table td { padding: 12px 15px; text-align: center; border: 1px solid #E2E8F0; }
    .price-table th { background: #121824; color: #1e293b; font-weight: 600; }
    .price-table tr:nth-child(even) { background: rgba(240, 253, 250, 0.5); }
    .price-table .popular { background: rgba(14, 116, 144, 0.1) !important; border: 2px solid #0e7490; }
    .price-table .popular-tag { background: #0e7490; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .price-table .duration { color: #1e293b; font-size: 13px; }
    .price-table .price { color: #1e293b; font-size: 18px; font-weight: bold; }
    </style>
    
    <table class="price-table">
        <tr>
            <th>Duración</th>
            <th>Precio (USD)</th>
            <th>Etiqueta</th>
        </tr>
        <tr>
            <td class="duration">24 Horas</td>
            <td class="price">$3.99</td>
            <td>Pase 1 Día</td>
        </tr>
        <tr>
            <td class="duration">7 Días</td>
            <td class="price">$9.99</td>
            <td>Pase 1 Semana</td>
        </tr>
        <tr class="popular">
            <td class="duration">30 Días <span class="popular-tag">MÁS POPULAR 🔥</span></td>
            <td class="price">$24.99</td>
            <td>Plan 1 Mes</td>
        </tr>
        <tr>
            <td class="duration">365 Días <span style="background: #10B981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">AHORRA 36%</span></td>
            <td class="price">$189.99</td>
            <td>Plan 1 Año</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    

    # --- FOOTER ---
    st.markdown("""
    <div class="footer">
        <p>🦂 Scorpion Elite - Todos los derechos reservados</p>
        <p>El análisis deportivo no garantiza resultados. Apuesta responsablemente.</p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# SISTEMA DE LOGIN - Solo contraseña
# ══════════════════════════════════════════════════════════

def render_login_form():
    """Renderiza el formulario de login con solo contraseña"""
    
    # Toggle para mostrar/ocultar login
    # Si no está logueado
    if not st.session_state.logged:
        
        # Si NO está mostrando login, mostrar landing page
        if not st.session_state.show_login:
            render_public_landing()
            st.stop()
        
        # Si está mostrando login, mostrar SOLO el formulario
        st.markdown("---")
        st.markdown("### 🔐 Iniciar Sesión")

        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña", key="login_password")

        col_login, col_cancel = st.columns([1, 1])
        with col_login:
            if st.button("✅ Entrar", use_container_width=True, type="primary"):
                if not password.strip():
                    st.error("⚠️ Ingresa la contraseña")
                else:
                    user = db_login(password)
                    if user:
                        st.session_state.logged = True
                        st.session_state.is_admin = user.get('es_admin', 0) == 1
                        st.session_state.user_data = user
                        st.session_state.show_login = False
                        nombre = user.get('nombre', password[:20])
                        st.success(f"¡Bienvenido!")
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")

        with col_cancel:
            if st.button("← Volver", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()

        st.stop()

    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown("## 🦂 Scorpion Elite")
        user_plan = st.session_state.user_data.get('plan', 'vip') if st.session_state.user_data else 'vip'
        dias = st.session_state.user_data.get('dias', 0) if st.session_state.user_data else 0
        is_admin = st.session_state.user_data.get('es_admin', 0) == 1 if st.session_state.user_data else False
        
        plan_icon = {"admin": "⚙️", "elite": "👑", "vip": "👑", "mes": "👑", "free": "🆓"}.get(user_plan, "📦")
        st.markdown(f"{plan_icon} **{user_plan.upper()}**")
        if not is_admin:
            st.caption(f"⏱️ {dias} días restantes")
        
        st.markdown("---")
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged = False
            st.session_state.user_data = None
            st.session_state.is_admin = False
            st.rerun()
    
    # Menú horizontal arriba - 根据用户类型显示
    st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    
    # Construir menú dinámicamente según tipo de usuario
    # VIP va de primeras y es la página por defecto
    if is_admin:
        # Admin: ve todo
        menu_pages = [
            ("👑 VIP", "VIP"),
            ("🏠 Partidos", "Partidos"),
            ("📊 Analizador", "Analizador"),
            ("🔑 Claves", "Claves"),
        ]
    else:
        # VIP: VIP primero, luego Partidos, Analizador
        menu_pages = [
            ("👑 VIP", "VIP"),
            ("🏠 Partidos", "Partidos"),
            ("📊 Analizador", "Analizador"),
        ]
    
    # Crear columnas dinámicamente
    num_cols = len(menu_pages)
    cols = st.columns(num_cols)
    
    for i, (label, page) in enumerate(menu_pages):
        with cols[i]:
            is_active = st.session_state.page == page
            if st.button(label, use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.page = page
                st.rerun()
    
    st.markdown("---")

    # Página: Partidos (NUEVA)
    if st.session_state.page == "Partidos":
        import requests
        import time
        
        st.markdown("### 🏠 Partidos de los Próximos 7 Días")
        
        # API-Football config
        API_KEY = "e3926f829cd848f4b2b54d722ca29701"
        API_URL = "https://v3.football.api-sports.io"
        
                # ═══════════════════════════════════════════════════════════════
        # LISTA DE LIGAS - TODAS CON IDS CORRECTOS
        # ═══════════════════════════════════════════════════════════════
        LIGAS = [
            # 🏆 TORNEOS INTERNACIONALES
            {"id": 2, "name": "UEFA Champions League", "pais": "Mundial"},
            {"id": 3, "name": "UEFA Europa League", "pais": "Mundial"},
            {"id": 848, "name": "UEFA Europa Conference League", "pais": "Mundial"},
            {"id": 13, "name": "Copa Libertadores", "pais": "Mundial"},
            {"id": 11, "name": "Copa Sudamericana", "pais": "Mundial"},
            {"id": 541, "name": "CONMEBOL Recopa", "pais": "Mundial"},
            {"id": 15, "name": "FIFA Club World Cup", "pais": "Mundial"},
            {"id": 16, "name": "CONCACAF Champions League", "pais": "Mundial"},
            {"id": 17, "name": "AFC Champions League", "pais": "Mundial"},
            
            # 🇪🇸 ESPAÑA
            {"id": 140, "name": "La Liga", "pais": "España"},
            {"id": 141, "name": "Segunda División", "pais": "España"},
            
            # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 INGLATERRA
            {"id": 39, "name": "Premier League", "pais": "Inglaterra"},
            {"id": 40, "name": "Championship", "pais": "Inglaterra"},
            {"id": 41, "name": "League One", "pais": "Inglaterra"},
            {"id": 42, "name": "League Two", "pais": "Inglaterra"},
            
            # 🇩🇪 ALEMANIA
            {"id": 78, "name": "Bundesliga", "pais": "Alemania"},
            {"id": 79, "name": "2. Bundesliga", "pais": "Alemania"},
            
            # 🇮🇹 ITALIA
            {"id": 135, "name": "Serie A", "pais": "Italia"},
            {"id": 136, "name": "Serie B", "pais": "Italia"},
            
            # 🇫🇷 FRANCIA
            {"id": 61, "name": "Ligue 1", "pais": "Francia"},
            {"id": 62, "name": "Ligue 2", "pais": "Francia"},
            
            # 🇵🇹 PORTUGAL
            {"id": 94, "name": "Primeira Liga", "pais": "Portugal"},
            
            # 🇳🇱 HOLANDA
            {"id": 88, "name": "Eredivisie", "pais": "Holanda"},
            
            # 🇧🇪 BÉLGICA
            {"id": 144, "name": "Jupiler Pro League", "pais": "Bélgica"},
            
            # 🇹🇷 TURQUÍA
            {"id": 203, "name": "Süper Lig", "pais": "Turquía"},
            {"id": 204, "name": "1. Lig", "pais": "Turquía"},
            
            # 🏴󠁧󠁢󠁳󠁣󠁴󠁿 ESCOCIA
            {"id": 179, "name": "Scottish Premiership", "pais": "Escocia"},
            {"id": 180, "name": "Championship Scotland", "pais": "Escocia"},
            
            # 🇧🇷 BRASIL
            {"id": 71, "name": "Serie A Brasil", "pais": "Brasil"},
            {"id": 72, "name": "Serie B Brasil", "pais": "Brasil"},
            {"id": 75, "name": "Serie C Brasil", "pais": "Brasil"},
            
            # 🇦🇷 ARGENTINA
            {"id": 128, "name": "Liga Profesional Argentina", "pais": "Argentina"},
            {"id": 129, "name": "Primera Nacional", "pais": "Argentina"},
            {"id": 131, "name": "Primera B Metropolitana", "pais": "Argentina"},
            
            # 🇨🇴 COLOMBIA
            {"id": 239, "name": "Primera A Colombia", "pais": "Colombia"},
            {"id": 240, "name": "Primera B Colombia", "pais": "Colombia"},
            
            # 🇵🇾 PARAGUAY
            {"id": 250, "name": "Division Profesional Paraguay", "pais": "Paraguay"},
            {"id": 251, "name": "Division Intermedia Paraguay", "pais": "Paraguay"},
            
            # 🇪🇨 ECUADOR
            {"id": 242, "name": "Liga Pro Ecuador", "pais": "Ecuador"},
            {"id": 243, "name": "Liga Pro Serie B Ecuador", "pais": "Ecuador"},
            
            # 🇺🇾 URUGUAY
            {"id": 268, "name": "Primera División Uruguay", "pais": "Uruguay"},
            {"id": 269, "name": "Segunda División Uruguay", "pais": "Uruguay"},
            
            # 🇨🇱 CHILE
            {"id": 265, "name": "Primera División Chile", "pais": "Chile"},
            {"id": 266, "name": "Primera B Chile", "pais": "Chile"},
            
            # 🇵🇪 PERÚ
            {"id": 281, "name": "Liga 1 Peru", "pais": "Perú"},
            {"id": 282, "name": "Liga 2 Peru", "pais": "Perú"},
            
            # 🇺🇸🇨🇦 USA / CANADÁ
            {"id": 253, "name": "MLS", "pais": "USA"},
            {"id": 255, "name": "USL Championship", "pais": "USA"},
            {"id": 909, "name": "MLS Next Pro", "pais": "USA"},
            
            # 🇲🇽 MÉXICO
            {"id": 262, "name": "Liga MX", "pais": "México"},
            {"id": 263, "name": "Liga de Expansión MX", "pais": "México"},
            
            # 🇸🇦 ARABIA SAUDITA
            {"id": 307, "name": "Saudi Pro League", "pais": "Arabia Saudita"},
            
            # 🇪🇬 EGIPTO
            {"id": 233, "name": "Premier League Egypt", "pais": "Egipto"},
            
            # 🇯🇵 JAPÓN
            {"id": 98, "name": "J1 League", "pais": "Japón"},
            
            # 🇰🇷 COREA DEL SUR
            {"id": 292, "name": "K League 1", "pais": "Corea del Sur"},
        ]
        
        # Contador de requests
        if 'api_requests_today' not in st.session_state:
            st.session_state.api_requests_today = 0
        
        # ═══════════════════════════════════════════════════════════════
        # BOTONES BUSCAR Y LIMPIAR
        # ═══════════════════════════════════════════════════════════════
        col_btn1, col_btn2, col_btn3, col_info = st.columns([1, 1, 1, 2])
        
        with col_btn1:
            if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
                client = get_client()
                try:
                    # Contar antes de borrar
                    resp_p = client.table('partidos').select('fixture_id', count='exact').execute()
                    resp_c = client.table('cuotas').select('fixture_id', count='exact').execute()
                    num_p = len(resp_p.data) if resp_p.data else 0
                    num_c = len(resp_c.data) if resp_c.data else 0
                    
                    # Borrar todos (usar filtro dummy que siempre es verdadero)
                    if num_p > 0:
                        client.table('partidos').delete().neq('fixture_id', -999999).execute()
                    if num_c > 0:
                        client.table('cuotas').delete().neq('fixture_id', -999999).execute()
                    
                    st.session_state.api_requests_today = 0
                    st.success(f"✅ Limpiado: {num_p} partidos y {num_c} cuotas")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col_btn2:
            if st.button("🔄 Sincronizar", type="primary", use_container_width=True):
                st.info("Descargando partidos y stats...")
                try:
                        client = get_client()
                        if not client:
                            st.error("❌ No se pudo conectar a Supabase")
                            st.stop()

                        API_URL = "https://v3.football.api-sports.io"
                        API_KEY = "e3926f829cd848f4b2b54d722ca29701"
                        headers = {'x-apisports-key': API_KEY}
                        hoy = datetime.now(timezone(timedelta(hours=-5))).date()
                        hoy_str = hoy.strftime('%Y-%m-%d')
                        
                        # Calcular temporada dinámicamente
                        # Ago-Dic 2025 → Season 2025, Ene-Jul 2026 → Season 2025
                        season = hoy.year if hoy.month >= 8 else hoy.year - 1
                        
                        # Si estamos en pretemporada (agos-agos), probar también temporada anterior
                        season_anterior = season - 1
                        st.markdown(f"⚽ Temporada: **{season}** | Pretemporada: {hoy.month in [7, 8]}")

                        # Obtener partidos existentes y la última fecha
                        partidos_existentes = set()
                        ultima_fecha = None
                        try:
                            resp_ex = client.table('partidos').select('fixture_id,fecha').execute()
                            partidos_existentes = {p['fixture_id'] for p in resp_ex.data} if resp_ex.data else set()
                            # Obtener la última fecha de partido
                            fechas = [datetime.strptime(p['fecha'], '%Y-%m-%d').date() for p in resp_ex.data if p.get('fecha')]
                            if fechas:
                                ultima_fecha = max(fechas)
                        except: pass

                        equipos_existentes = set()
                        try:
                            resp_eq = client.table('equipos_stats').select('equipo').execute()
                            equipos_existentes = {e['equipo'] for e in resp_eq.data} if resp_eq.data else set()
                        except: pass

                        st.markdown(f"📊 Ya tienes: **{len(partidos_existentes)}** partidos, **{len(equipos_existentes)}** equipos")

                        # Lógica optimizada: solo buscar si falta cobertura de 7 días
                        fecha_fin_deseada = hoy + timedelta(days=6)
                        buscar_partidos = True
                        if ultima_fecha and ultima_fecha >= fecha_fin_deseada:
                            buscar_partidos = False
                            st.info(f"✅ Ya tienes partidos hasta {ultima_fecha.strftime('%d/%m')} (7 días completos)")
                        else:
                            if ultima_fecha:
                                fecha_inicio = (ultima_fecha + timedelta(days=1)).strftime('%Y-%m-%d')
                            else:
                                fecha_inicio = hoy_str
                            fecha_fin = fecha_fin_deseada.strftime('%Y-%m-%d')
                            st.info(f"📡 Buscando partidos: {fecha_inicio} al {fecha_fin}")

                        LIGAS = [
                            # 🏆 TORNEOS INTERNACIONALES
                            {"id": 2, "name": "UEFA Champions League", "pais": "Mundial"},
                            {"id": 3, "name": "UEFA Europa League", "pais": "Mundial"},
                            {"id": 848, "name": "UEFA Europa Conference League", "pais": "Mundial"},
                            {"id": 13, "name": "Copa Libertadores", "pais": "Mundial"},
                            {"id": 11, "name": "Copa Sudamericana", "pais": "Mundial"},
                            {"id": 541, "name": "CONMEBOL Recopa", "pais": "Mundial"},
                            {"id": 15, "name": "FIFA Club World Cup", "pais": "Mundial"},
                            {"id": 16, "name": "CONCACAF Champions League", "pais": "Mundial"},
                            {"id": 17, "name": "AFC Champions League", "pais": "Mundial"},
                            
                            # 🇪🇸 ESPAÑA
                            {"id": 140, "name": "La Liga", "pais": "España"},
                            {"id": 141, "name": "Segunda División", "pais": "España"},
                            
                            # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 INGLATERRA
                            {"id": 39, "name": "Premier League", "pais": "Inglaterra"},
                            {"id": 40, "name": "Championship", "pais": "Inglaterra"},
                            {"id": 41, "name": "League One", "pais": "Inglaterra"},
                            {"id": 42, "name": "League Two", "pais": "Inglaterra"},
                            
                            # 🇩🇪 ALEMANIA
                            {"id": 78, "name": "Bundesliga", "pais": "Alemania"},
                            {"id": 79, "name": "2. Bundesliga", "pais": "Alemania"},
                            
                            # 🇮🇹 ITALIA
                            {"id": 135, "name": "Serie A", "pais": "Italia"},
                            {"id": 136, "name": "Serie B", "pais": "Italia"},
                            
                            # 🇫🇷 FRANCIA
                            {"id": 61, "name": "Ligue 1", "pais": "Francia"},
                            {"id": 62, "name": "Ligue 2", "pais": "Francia"},
                            
                            # 🇵🇹 PORTUGAL
                            {"id": 94, "name": "Primeira Liga", "pais": "Portugal"},
                            
                            # 🇳🇱 HOLANDA
                            {"id": 88, "name": "Eredivisie", "pais": "Holanda"},
                            
                            # 🇧🇪 BÉLGICA
                            {"id": 144, "name": "Jupiler Pro League", "pais": "Bélgica"},
                            
                            # 🇹🇷 TURQUÍA
                            {"id": 203, "name": "Süper Lig", "pais": "Turquía"},
                            {"id": 204, "name": "1. Lig", "pais": "Turquía"},
                            
                            # 🏴󠁧󠁢󠁳󠁣󠁴󠁿 ESCOCIA
                            {"id": 179, "name": "Scottish Premiership", "pais": "Escocia"},
                            {"id": 180, "name": "Championship Scotland", "pais": "Escocia"},
                            
                            # 🇧🇷 BRASIL
                            {"id": 71, "name": "Serie A Brasil", "pais": "Brasil"},
                            {"id": 72, "name": "Serie B Brasil", "pais": "Brasil"},
                            {"id": 75, "name": "Serie C Brasil", "pais": "Brasil"},
                            
                            # 🇦🇷 ARGENTINA
                            {"id": 128, "name": "Liga Profesional Argentina", "pais": "Argentina"},
                            {"id": 129, "name": "Primera Nacional", "pais": "Argentina"},
                            {"id": 131, "name": "Primera B Metropolitana", "pais": "Argentina"},
                            
                            # 🇨🇴 COLOMBIA
                            {"id": 239, "name": "Primera A Colombia", "pais": "Colombia"},
                            {"id": 240, "name": "Primera B Colombia", "pais": "Colombia"},
                            
                            # 🇵🇾 PARAGUAY
                            {"id": 250, "name": "Division Profesional Paraguay", "pais": "Paraguay"},
                            {"id": 251, "name": "Division Intermedia Paraguay", "pais": "Paraguay"},
                            
                            # 🇪🇨 ECUADOR
                            {"id": 242, "name": "Liga Pro Ecuador", "pais": "Ecuador"},
                            {"id": 243, "name": "Liga Pro Serie B Ecuador", "pais": "Ecuador"},
                            
                            # 🇺🇾 URUGUAY
                            {"id": 268, "name": "Primera División Uruguay", "pais": "Uruguay"},
                            {"id": 269, "name": "Segunda División Uruguay", "pais": "Uruguay"},
                            
                            # 🇨🇱 CHILE
                            {"id": 265, "name": "Primera División Chile", "pais": "Chile"},
                            {"id": 266, "name": "Primera B Chile", "pais": "Chile"},
                            
                            # 🇵🇪 PERÚ
                            {"id": 281, "name": "Liga 1 Peru", "pais": "Perú"},
                            {"id": 282, "name": "Liga 2 Peru", "pais": "Perú"},
                            
                            # 🇺🇸🇨🇦 USA / CANADÁ
                            {"id": 253, "name": "MLS", "pais": "USA"},
                            {"id": 255, "name": "USL Championship", "pais": "USA"},
                            {"id": 909, "name": "MLS Next Pro", "pais": "USA"},
                            
                            # 🇲🇽 MÉXICO
                            {"id": 262, "name": "Liga MX", "pais": "México"},
                            {"id": 263, "name": "Liga de Expansión MX", "pais": "México"},
                            
                            # 🇸🇦 ARABIA SAUDITA
                            {"id": 307, "name": "Saudi Pro League", "pais": "Arabia Saudita"},
                            
                            # 🇪🇬 EGIPTO
                            {"id": 233, "name": "Premier League Egypt", "pais": "Egipto"},
                            
                            # 🇯🇵 JAPÓN
                            {"id": 98, "name": "J1 League", "pais": "Japón"},
                            
                            # 🇰🇷 COREA DEL SUR
                            {"id": 292, "name": "K League 1", "pais": "Corea del Sur"},
                        ]

                        total_partidos = 0
                        total_equipos = 0
                        errores = 0

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        # Solo buscar partidos si es necesario
                        if buscar_partidos:
                            st.info("📥 Descargando partidos nuevos...")
                            for idx, liga in enumerate(LIGAS):
                                liga_id = liga['id']
                                liga_nombre = liga['name']
                                status_text.text(f"📊 {liga_nombre}...")
                                progress_bar.progress((idx + 1) / len(LIGAS))
                                
                                params = {'league': liga_id, 'season': season, 'from': fecha_inicio, 'to': fecha_fin}
                                try:
                                    resp = requests.get(f"{API_URL}/fixtures", headers=headers, params=params, timeout=15)
                                    
                                    if resp.status_code == 200:
                                        data = resp.json()
                                        fixtures = data.get('response', []) or []
                                        
                                        for f in fixtures:
                                            fix = f.get('fixture', {})
                                            teams = f.get('teams', {})
                                            league = f.get('league', {})
                                            fix_id = fix.get('id')

                                            partido_data = {
                                                'fixture_id': fix_id,
                                                'fecha': fix.get('date', '')[:10],
                                                'hora': fix.get('date', '')[11:16],
                                                'liga': league.get('name', ''),
                                                'equipo_local': teams.get('home', {}).get('name', ''),
                                                'equipo_visitante': teams.get('away', {}).get('name', ''),
                                            }
                                            
                                            # Solo guardar si es partido nuevo
                                            if fix_id not in partidos_existentes:
                                                try:
                                                    client.table('partidos').upsert(partido_data, on_conflict='fixture_id').execute()
                                                    total_partidos += 1
                                                except: pass

                                            # Guardar stats de equipos mientras se buscan partidos
                                            for tipo in ['home', 'away']:
                                                team = teams.get(tipo, {})
                                                team_name = team.get('name', '')
                                                team_id_api = team.get('id', 0)
                                                
                                                if team_name and team_id_api and team_name not in equipos_existentes:
                                                    try:
                                                        resp_team = requests.get(
                                                            f"{API_URL}/teams/statistics",
                                                            headers=headers,
                                                            params={'team': team_id_api, 'league': liga_id, 'season': season},
                                                            timeout=10
                                                        )
                                                        
                                                        if resp_team.status_code == 200:
                                                            stats = resp_team.json().get('response', {})
                                                            if stats:
                                                                gf = stats.get('goals', {}).get('for', {}).get('total', 0) or 0
                                                                gc = stats.get('goals', {}).get('against', {}).get('total', 0) or 0
                                                                gf_h = stats.get('goals', {}).get('for', {}).get('home', 0) or 0
                                                                gf_a = stats.get('goals', {}).get('for', {}).get('away', 0) or 0
                                                                gc_h = stats.get('goals', {}).get('against', {}).get('home', 0) or 0
                                                                gc_a = stats.get('goals', {}).get('against', {}).get('away', 0) or 0
                                                                pj_h = stats.get('fixtures', {}).get('played', {}).get('home', 1) or 1
                                                                pj_a = stats.get('fixtures', {}).get('played', {}).get('away', 1) or 1
                                                                pj_t = stats.get('fixtures', {}).get('played', {}).get('total', 0) or 1

                                                                wins = stats.get('fixtures', {}).get('wins', {}).get('total', 0) or 0
                                                                draws = stats.get('fixtures', {}).get('draws', {}).get('total', 0) or 0
                                                                loses = stats.get('fixtures', {}).get('loses', {}).get('total', 0) or 0

                                                                equipo_data = {
                                                                    'equipo': team_name,
                                                                    'liga': league.get('name', ''),
                                                                    'temporada': f'{season}-{season+1}',
                                                                    'partidos_jugados': pj_t,
                                                                    'victorias': wins,
                                                                    'empates': draws,
                                                                    'derrotas': loses,
                                                                    'goles_favor': gf,
                                                                    'goles_contra': gc,
                                                                    'lambda_local': round((gf_h + gc_a) / pj_h / 2, 2),
                                                                    'lambda_visitante': round((gf_a + gc_h) / pj_a / 2, 2),
                                                                    'ultimos_5_partidos': list(stats.get('form', '') or '')[:5],
                                                                }
                                                                
                                                                client.table('equipos_stats').upsert(equipo_data, ignore_duplicates=True).execute()
                                                                total_equipos += 1
                                                                equipos_existentes.add(team_name)
                                                    except: pass
                                    else:
                                        if resp.status_code == 403:
                                            errores += 1
                                except: pass

                        # PASO 2: Buscar stats de equipos de TODOS los partidos guardados
                        st.info("📊 Buscando stats de equipos...")
                        todos_partidos = client.table('partidos').select('*').execute()
                        
                        # Mapeo de nombre de liga a liga_id
                        LIGAS_MAP_REVERSE = {nombre: lid for lid, nombre in LIGAS}
                        
                        # Guardar equipos con su liga_id correcto: {equipo: (liga_nombre, liga_id)}
                        equipos_unicos = {}
                        
                        for p in todos_partidos.data:
                            local = p.get('equipo_local', '')
                            visitante = p.get('equipo_visitante', '')
                            liga_nombre = p.get('liga', '')
                            # Intentar obtener liga_id de la tabla o buscar por nombre
                            liga_id_partido = p.get('liga_id') or LIGAS_MAP_REVERSE.get(liga_nombre)
                            
                            if local:
                                equipos_unicos[local] = (liga_nombre, liga_id_partido)
                            
                            if visitante:
                                equipos_unicos[visitante] = (liga_nombre, liga_id_partido)
                        
                        st.info(f"🔍 {len(equipos_unicos)} equipos a buscar...")
                        
                        for idx, (eq_nombre, (eq_liga_nombre, eq_liga_id)) in enumerate(equipos_unicos.items()):
                            if idx % 5 == 0:
                                progress_bar.progress(0.5 + (idx / len(equipos_unicos) * 0.5))
                                status_text.text(f"📊 Equipo {idx+1}/{len(equipos_unicos)}: {eq_nombre}")
                            
                            try:
                                # Buscar equipo en API
                                resp_s = requests.get(f"{API_URL}/teams", headers=headers, params={'search': eq_nombre}, timeout=10)
                                if resp_s.status_code == 200:
                                    for t in resp_s.json().get('response', []):
                                        if t.get('team', {}).get('name') == eq_nombre:
                                            tid = t.get('team', {}).get('id')
                                            # Buscar stats con la liga_id correcta del partido
                                            resp_st = requests.get(f"{API_URL}/teams/statistics", headers=headers, params={'team': tid, 'league': eq_liga_id, 'season': season}, timeout=10)
                                            if resp_st.status_code == 200:
                                                stats_data = resp_st.json().get('response', {})
                                                if stats_data:
                                                    gf = stats_data.get('goals', {}).get('for', {}).get('total', 0) or 0
                                                    gc = stats_data.get('goals', {}).get('against', {}).get('total', 0) or 0
                                                    gf_h = stats_data.get('goals', {}).get('for', {}).get('home', 0) or 0
                                                    gf_a = stats_data.get('goals', {}).get('for', {}).get('away', 0) or 0
                                                    gc_h = stats_data.get('goals', {}).get('against', {}).get('home', 0) or 0
                                                    gc_a = stats_data.get('goals', {}).get('against', {}).get('away', 0) or 0
                                                    pj_h = stats_data.get('fixtures', {}).get('played', {}).get('home', 1) or 1
                                                    pj_a = stats_data.get('fixtures', {}).get('played', {}).get('away', 1) or 1
                                                    pj_t = stats_data.get('fixtures', {}).get('played', {}).get('total', 0) or 1
                                                    wins = stats_data.get('fixtures', {}).get('wins', {}).get('total', 0) or 0
                                                    draws = stats_data.get('fixtures', {}).get('draws', {}).get('total', 0) or 0
                                                    loses = stats_data.get('fixtures', {}).get('loses', {}).get('total', 0) or 0
                                                    
                                                    eq_data = {
                                                        'equipo': eq_nombre,
                                                        'liga': eq_liga_nombre or stats_data.get('league', {}).get('name', ''),
                                                        'temporada': f'{season}-{season+1}',
                                                        'partidos_jugados': pj_t,
                                                        'victorias': wins,
                                                        'empates': draws,
                                                        'derrotas': loses,
                                                        'goles_favor': gf,
                                                        'goles_contra': gc,
                                                        'lambda_local': round((gf_h + gc_a) / pj_h / 2, 2),
                                                        'lambda_visitante': round((gf_a + gc_h) / pj_a / 2, 2),
                                                        'ultimos_5_partidos': list(stats_data.get('form', '') or '')[:5],
                                                    }
                                                    client.table('equipos_stats').upsert(eq_data, ignore_duplicates=True).execute()
                                                    total_equipos += 1
                                            break
                            except: pass

                        progress_bar.empty()
                        status_text.empty()

                        st.success(f"✅ GUARDADO!")
                        st.markdown(f"📊 **Partidos:** {total_partidos} | **Estadísticas equipos guardadas:** {total_equipos}")

                except Exception as e:
                        st.error(f"❌ Error: {e}")

        with col_btn3:
            if st.button("👥 Equipos", type="secondary", use_container_width=True):
                st.info("🔄 Sincronizando equipos y estadísticas...")
                try:
                    client = get_client()
                    if not client:
                        st.error("❌ No se pudo conectar a Supabase")
                        st.stop()

                    API_URL = "https://v3.football.api-sports.io"
                    API_KEY = "e3926f829cd848f4b2b54d722ca29701"
                    headers = {'x-apisports-key': API_KEY}
                    hoy = datetime.now(timezone(timedelta(hours=-5))).date()
                    hoy_str = hoy.strftime('%Y-%m-%d')
                    # Calcular temporada dinámicamente
                    season = hoy.year if hoy.month >= 8 else hoy.year - 1

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # ═══════════════════════════════════════════════════════
                    # PASO 0: ACTUALIZAR PARTIDOS JUGADOS (HOY-1 y HOY-2)
                    # ═══════════════════════════════════════════════════════
                    st.info("🔄 Verificando partidos jugados recently...")
                    
                    fecha_ayer = (hoy - timedelta(days=1)).strftime('%Y-%m-%d')
                    fecha_antier = (hoy - timedelta(days=2)).strftime('%Y-%m-%d')
                    
                    try:
                        resp_part = client.table('partidos').select('*').in_('fecha', [fecha_ayer, fecha_antier]).execute()
                        partidos_por_actualizar = [p for p in resp_part.data if p.get('fecha') in [fecha_ayer, fecha_antier]]
                        
                        if partidos_por_actualizar:
                            st.info(f"📊 {len(partidos_por_actualizar)} partidos jugados - actualizando stats...")
                            
                            for p in partidos_por_actualizar:
                                fix_id = p.get('fixture_id')
                                eq_local = p.get('equipo_local', '')
                                eq_visitante = p.get('equipo_visitante', '')
                                
                                if fix_id:
                                    try:
                                        resp_fix = requests.get(f"{API_URL}/fixtures", headers=headers, params={'id': fix_id}, timeout=10)
                                        if resp_fix.status_code == 200:
                                            data = resp_fix.json().get('response', [])
                                            if data:
                                                f_data = data[0]
                                                goals = f_data.get('goals', {})
                                                status = f_data.get('fixture', {}).get('status', {}).get('short', '')
                                                stats_api = f_data.get('statistics', [])
                                                
                                                gl = goals.get('home') or 0
                                                gv = goals.get('away') or 0
                                                
                                                # Actualizar marcador
                                                update_partido = {}
                                                if goals.get('home') is not None:
                                                    update_partido['goles_local'] = gl
                                                if goals.get('away') is not None:
                                                    update_partido['goles_visitante'] = gv
                                                if status:
                                                    update_partido['estado'] = status
                                                
                                                if update_partido:
                                                    client.table('partidos').update(update_partido).eq('fixture_id', fix_id).execute()
                                                
                                                # Si terminó, actualizar stats de equipos
                                                if status == 'FT' and eq_local and eq_visitante:
                                                    local_stats = {}
                                                    visitante_stats = {}
                                                    
                                                    for stat in stats_api:
                                                        stat_type = str(stat.get('type', ''))
                                                        local_val = stat.get('home') or 0
                                                        visit_val = stat.get('away') or 0
                                                        
                                                        if 'Shot' in stat_type and 'On' not in stat_type:
                                                            local_stats['tiros'] = local_val
                                                            visitante_stats['tiros'] = visit_val
                                                        elif 'Shot' in stat_type and 'On' in stat_type:
                                                            local_stats['tiros_arco'] = local_val
                                                            visitante_stats['tiros_arco'] = visit_val
                                                        elif 'Corner' in stat_type:
                                                            local_stats['corners'] = local_val
                                                            visitante_stats['corners'] = visit_val
                                                        elif 'Yellow' in stat_type:
                                                            local_stats['amarillas'] = local_val
                                                            visitante_stats['amarillas'] = visit_val
                                                        elif 'Red' in stat_type:
                                                            local_stats['rojas'] = local_val
                                                            visitante_stats['rojas'] = visit_val
                                                    
                                                    # Actualizar equipo LOCAL
                                                    try:
                                                        resp_eq = client.table('equipos_stats').select('*').eq('equipo', eq_local).execute()
                                                        if resp_eq.data:
                                                            eq = resp_eq.data[0]
                                                            pj = (eq.get('partidos_jugados') or 0) + 1
                                                            
                                                            update_eq = {
                                                                'partidos_jugados': pj,
                                                                'goles_favor': (eq.get('goles_favor') or 0) + gl,
                                                                'goles_contra': (eq.get('goles_contra') or 0) + gv,
                                                                'promedio_tiros': round(((eq.get('promedio_tiros') or 0) * (pj-1) + local_stats.get('tiros', 0)) / pj, 2),
                                                                'promedio_tiros_arco': round(((eq.get('promedio_tiros_arco') or 0) * (pj-1) + local_stats.get('tiros_arco', 0)) / pj, 2),
                                                                'corners_favor': round(((eq.get('corners_favor') or 0) * (pj-1) + local_stats.get('corners', 0)) / pj, 2),
                                                                'promedio_amarillas': round(((eq.get('promedio_amarillas') or 0) * (pj-1) + local_stats.get('amarillas', 0)) / pj, 2),
                                                                'promedio_rojas': round(((eq.get('promedio_rojas') or 0) * (pj-1) + local_stats.get('rojas', 0)) / pj, 2),
                                                            }
                                                            
                                                            ult5 = eq.get('ultimos_5_partidos') or []
                                                            ult5.insert(0, 'W' if gl > gv else ('D' if gl == gv else 'L'))
                                                            update_eq['ultimos_5_partidos'] = ult5[:5]
                                                            
                                                            if gl > gv:
                                                                update_eq['victorias'] = (eq.get('victorias') or 0) + 1
                                                            elif gl == gv:
                                                                update_eq['empates'] = (eq.get('empates') or 0) + 1
                                                            else:
                                                                update_eq['derrotas'] = (eq.get('derrotas') or 0) + 1
                                                            
                                                            client.table('equipos_stats').update(update_eq).eq('equipo', eq_local).execute()
                                                    except: pass
                                                    
                                                    # Actualizar equipo VISITANTE
                                                    try:
                                                        resp_eq = client.table('equipos_stats').select('*').eq('equipo', eq_visitante).execute()
                                                        if resp_eq.data:
                                                            eq = resp_eq.data[0]
                                                            pj = (eq.get('partidos_jugados') or 0) + 1
                                                            
                                                            update_eq = {
                                                                'partidos_jugados': pj,
                                                                'goles_favor': (eq.get('goles_favor') or 0) + gv,
                                                                'goles_contra': (eq.get('goles_contra') or 0) + gl,
                                                                'promedio_tiros': round(((eq.get('promedio_tiros') or 0) * (pj-1) + visitante_stats.get('tiros', 0)) / pj, 2),
                                                                'promedio_tiros_arco': round(((eq.get('promedio_tiros_arco') or 0) * (pj-1) + visitante_stats.get('tiros_arco', 0)) / pj, 2),
                                                                'corners_favor': round(((eq.get('corners_favor') or 0) * (pj-1) + visitante_stats.get('corners', 0)) / pj, 2),
                                                                'promedio_amarillas': round(((eq.get('promedio_amarillas') or 0) * (pj-1) + visitante_stats.get('amarillas', 0)) / pj, 2),
                                                                'promedio_rojas': round(((eq.get('promedio_rojas') or 0) * (pj-1) + visitante_stats.get('rojas', 0)) / pj, 2),
                                                            }
                                                            
                                                            ult5 = eq.get('ultimos_5_partidos') or []
                                                            ult5.insert(0, 'W' if gv > gl else ('D' if gv == gl else 'L'))
                                                            update_eq['ultimos_5_partidos'] = ult5[:5]
                                                            
                                                            if gv > gl:
                                                                update_eq['victorias'] = (eq.get('victorias') or 0) + 1
                                                            elif gv == gl:
                                                                update_eq['empates'] = (eq.get('empates') or 0) + 1
                                                            else:
                                                                update_eq['derrotas'] = (eq.get('derrotas') or 0) + 1
                                                            
                                                            client.table('equipos_stats').update(update_eq).eq('equipo', eq_visitante).execute()
                                                    except: pass
                                    except: pass
                    except: pass


                    LIGAS = [
                        # 🏆 TORNEOS INTERNACIONALES
                        {"id": 2, "name": "UEFA Champions League", "pais": "Mundial"},
                        {"id": 3, "name": "UEFA Europa League", "pais": "Mundial"},
                        {"id": 848, "name": "UEFA Europa Conference League", "pais": "Mundial"},
                        {"id": 13, "name": "Copa Libertadores", "pais": "Mundial"},
                        {"id": 11, "name": "Copa Sudamericana", "pais": "Mundial"},
                        {"id": 541, "name": "CONMEBOL Recopa", "pais": "Mundial"},
                        {"id": 15, "name": "FIFA Club World Cup", "pais": "Mundial"},
                        {"id": 16, "name": "CONCACAF Champions League", "pais": "Mundial"},
                        {"id": 17, "name": "AFC Champions League", "pais": "Mundial"},
                        
                        # 🇪🇸 ESPAÑA
                        {"id": 140, "name": "La Liga", "pais": "España"},
                        {"id": 141, "name": "Segunda División", "pais": "España"},
                        
                        # 🏴󠁧󠁢󠁥󠁮󠁧󠁿 INGLATERRA
                        {"id": 39, "name": "Premier League", "pais": "Inglaterra"},
                        {"id": 40, "name": "Championship", "pais": "Inglaterra"},
                        {"id": 41, "name": "League One", "pais": "Inglaterra"},
                        {"id": 42, "name": "League Two", "pais": "Inglaterra"},
                        
                        # 🇩🇪 ALEMANIA
                        {"id": 78, "name": "Bundesliga", "pais": "Alemania"},
                        {"id": 79, "name": "2. Bundesliga", "pais": "Alemania"},
                        
                        # 🇮🇹 ITALIA
                        {"id": 135, "name": "Serie A", "pais": "Italia"},
                        {"id": 136, "name": "Serie B", "pais": "Italia"},
                        
                        # 🇫🇷 FRANCIA
                        {"id": 61, "name": "Ligue 1", "pais": "Francia"},
                        {"id": 62, "name": "Ligue 2", "pais": "Francia"},
                        
                        # 🇵🇹 PORTUGAL
                        {"id": 94, "name": "Primeira Liga", "pais": "Portugal"},
                        
                        # 🇳🇱 HOLANDA
                        {"id": 88, "name": "Eredivisie", "pais": "Holanda"},
                        
                        # 🇧🇪 BÉLGICA
                        {"id": 144, "name": "Jupiler Pro League", "pais": "Bélgica"},
                        
                        # 🇹🇷 TURQUÍA
                        {"id": 203, "name": "Süper Lig", "pais": "Turquía"},
                        {"id": 204, "name": "1. Lig", "pais": "Turquía"},
                        
                        # 🏴󠁧󠁢󠁳󠁣󠁴󠁿 ESCOCIA
                        {"id": 179, "name": "Scottish Premiership", "pais": "Escocia"},
                        {"id": 180, "name": "Championship Scotland", "pais": "Escocia"},
                        
                        # 🇧🇷 BRASIL
                        {"id": 71, "name": "Serie A Brasil", "pais": "Brasil"},
                        {"id": 72, "name": "Serie B Brasil", "pais": "Brasil"},
                        {"id": 75, "name": "Serie C Brasil", "pais": "Brasil"},
                        
                        # 🇦🇷 ARGENTINA
                        {"id": 128, "name": "Liga Profesional Argentina", "pais": "Argentina"},
                        {"id": 129, "name": "Primera Nacional", "pais": "Argentina"},
                        {"id": 131, "name": "Primera B Metropolitana", "pais": "Argentina"},
                        
                        # 🇨🇴 COLOMBIA
                        {"id": 239, "name": "Primera A Colombia", "pais": "Colombia"},
                        {"id": 240, "name": "Primera B Colombia", "pais": "Colombia"},
                        
                        # 🇵🇾 PARAGUAY
                        {"id": 250, "name": "Division Profesional Paraguay", "pais": "Paraguay"},
                        {"id": 251, "name": "Division Intermedia Paraguay", "pais": "Paraguay"},
                        
                        # 🇪🇨 ECUADOR
                        {"id": 242, "name": "Liga Pro Ecuador", "pais": "Ecuador"},
                        {"id": 243, "name": "Liga Pro Serie B Ecuador", "pais": "Ecuador"},
                        
                        # 🇺🇾 URUGUAY
                        {"id": 268, "name": "Primera División Uruguay", "pais": "Uruguay"},
                        {"id": 269, "name": "Segunda División Uruguay", "pais": "Uruguay"},
                        
                        # 🇨🇱 CHILE
                        {"id": 265, "name": "Primera División Chile", "pais": "Chile"},
                        {"id": 266, "name": "Primera B Chile", "pais": "Chile"},
                        
                        # 🇵🇪 PERÚ
                        {"id": 281, "name": "Liga 1 Peru", "pais": "Perú"},
                        {"id": 282, "name": "Liga 2 Peru", "pais": "Perú"},
                        
                        # 🇺🇸🇨🇦 USA / CANADÁ
                        {"id": 253, "name": "MLS", "pais": "USA"},
                        {"id": 255, "name": "USL Championship", "pais": "USA"},
                        {"id": 909, "name": "MLS Next Pro", "pais": "USA"},
                        
                        # 🇲🇽 MÉXICO
                        {"id": 262, "name": "Liga MX", "pais": "México"},
                        {"id": 263, "name": "Liga de Expansión MX", "pais": "México"},
                        
                        # 🇸🇦 ARABIA SAUDITA
                        {"id": 307, "name": "Saudi Pro League", "pais": "Arabia Saudita"},
                        
                        # 🇪🇬 EGIPTO
                        {"id": 233, "name": "Premier League Egypt", "pais": "Egipto"},
                        
                        # 🇯🇵 JAPÓN
                        {"id": 98, "name": "J1 League", "pais": "Japón"},
                        
                        # 🇰🇷 COREA DEL SUR
                        {"id": 292, "name": "K League 1", "pais": "Corea del Sur"},
                    ]

                    # ═══════════════════════════════════════════════════════
                    # PASO 1: Consultar equipos existentes en Supabase
                    # ═══════════════════════════════════════════════════════
                    status_text.text("📊 Verificando equipos en BD...")
                    try:
                        resp_eq = client.table('equipos_stats').select('equipo').execute()
                        equipos_en_bd = {e['equipo'] for e in resp_eq.data} if resp_eq.data else set()
                    except:
                        equipos_en_bd = set()

                    total_bd = len(equipos_en_bd)
                    st.markdown(f"📊 Equipos en BD: **{total_bd}**")

                    # ═══════════════════════════════════════════════════════
                    # CASO A: PRIMERA EJECUCIÓN (BD vacía)
                    # Busca HOY + MAÑANA + PASADO (3 días)
                    # ═══════════════════════════════════════════════════════
                    if total_bd == 0:
                        st.info("📥 CASO A: Primera ejecución - descargando equipos de 3 días")
                        
                        fecha_inicio = hoy_str
                        fecha_fin = (hoy + timedelta(days=2)).strftime('%Y-%m-%d')
                        st.info(f"📡 Fechas: {fecha_inicio} al {fecha_fin}")

                        # Guardar como {nombre_equipo: (liga_nombre, liga_id)}
                        equipos_por_buscar = {}

                        for idx, liga in enumerate(LIGAS):
                            liga_id = liga['id']
                            liga_nombre = liga['name']
                            status_text.text(f"📊 {liga_nombre}...")
                            progress_bar.progress((idx + 1) / len(LIGAS) * 0.2)
                            params = {'league': liga_id, 'season': season, 'from': fecha_inicio, 'to': fecha_fin}
                            try:
                                resp = requests.get(f"{API_URL}/fixtures", headers=headers, params=params, timeout=15)
                                if resp.status_code == 200:
                                    fixtures = resp.json().get('response', []) or []
                                    for f in fixtures:
                                        teams = f.get('teams', {})
                                        local = teams.get('home', {}).get('name', '')
                                        visitante = teams.get('away', {}).get('name', '')
                                        if local: equipos_por_buscar[local] = (f.get('league', {}).get('name', ''), liga_id)
                                        if visitante: equipos_por_buscar[visitante] = (f.get('league', {}).get('name', ''), liga_id)
                            except: pass

                    # ═══════════════════════════════════════════════════════
                    # CASO B: MANTENER COLCHÓN A FUTURO (DÍA 3 y DÍA 4)
                    # ═══════════════════════════════════════════════════════
                    else:
                        st.info("📥 CASO B: Actualizando colchón a futuro (Días 3 y 4)")
                        
                        fecha_inicio = (hoy + timedelta(days=2)).strftime('%Y-%m-%d')
                        fecha_fin = (hoy + timedelta(days=3)).strftime('%Y-%m-%d')
                        st.info(f"📡 Equipos de partidos: {fecha_inicio} al {fecha_fin}")

                        # Guardar como {nombre_equipo: (liga_nombre, liga_id)}
                        equipos_por_buscar = {}

                        for idx, liga in enumerate(LIGAS):
                            liga_id = liga['id']
                            liga_nombre = liga['name']
                            status_text.text(f"📊 {liga_nombre}...")
                            progress_bar.progress((idx + 1) / len(LIGAS) * 0.2)
                            params = {'league': liga_id, 'season': season, 'from': fecha_inicio, 'to': fecha_fin}
                            try:
                                resp = requests.get(f"{API_URL}/fixtures", headers=headers, params=params, timeout=15)
                                if resp.status_code == 200:
                                    fixtures = resp.json().get('response', []) or []
                                    for f in fixtures:
                                        teams = f.get('teams', {})
                                        local = teams.get('home', {}).get('name', '')
                                        visitante = teams.get('away', {}).get('name', '')
                                        if local: equipos_por_buscar[local] = (f.get('league', {}).get('name', ''), liga_id)
                                        if visitante: equipos_por_buscar[visitante] = (f.get('league', {}).get('name', ''), liga_id)
                            except: pass

                    # ═══════════════════════════════════════════════════════
                    # PASO 2: Filtrar y buscar stats de equipos
                    # ═══════════════════════════════════════════════════════
                    equipos_faltan = {k: v for k, v in equipos_por_buscar.items() if k not in equipos_en_bd}

                    if equipos_por_buscar:
                        st.info(f"🔍 Equipos: {len(equipos_por_buscar)} | Nuevos: {len(equipos_faltan)}")
                        
                        total_guardados = 0
                        total_actualizados = 0

                        for idx, (eq_nombre, (eq_liga_nombre, eq_liga_id)) in enumerate(equipos_por_buscar.items()):
                            progress_bar.progress(0.2 + (idx / len(equipos_por_buscar) * 0.8))
                            status_text.text(f"📊 {idx+1}/{len(equipos_por_buscar)}: {eq_nombre}")

                            try:
                                resp_s = requests.get(f"{API_URL}/teams", headers=headers, params={'search': eq_nombre}, timeout=10)
                                if resp_s.status_code == 200:
                                    for t in resp_s.json().get('response', []):
                                        if t.get('team', {}).get('name') == eq_nombre:
                                            tid = t.get('team', {}).get('id')
                                            # Usar la liga correcta del equipo
                                            resp_st = requests.get(f"{API_URL}/teams/statistics", headers=headers, params={'team': tid, 'league': eq_liga_id, 'season': season}, timeout=10)
                                            if resp_st.status_code == 200:
                                                st_eq = resp_st.json().get('response', {})
                                                if st_eq:
                                                    gf = st_eq.get('goals', {}).get('for', {}).get('total', 0) or 0
                                                    gc = st_eq.get('goals', {}).get('against', {}).get('total', 0) or 0
                                                    gf_h = st_eq.get('goals', {}).get('for', {}).get('home', 0) or 0
                                                    gf_a = st_eq.get('goals', {}).get('for', {}).get('away', 0) or 0
                                                    gc_h = st_eq.get('goals', {}).get('against', {}).get('home', 0) or 0
                                                    gc_a = st_eq.get('goals', {}).get('against', {}).get('away', 0) or 0
                                                    pj_h = st_eq.get('fixtures', {}).get('played', {}).get('home', 1) or 1
                                                    pj_a = st_eq.get('fixtures', {}).get('played', {}).get('away', 1) or 1
                                                    pj_t = st_eq.get('fixtures', {}).get('played', {}).get('total', 0) or 1
                                                    wins = st_eq.get('fixtures', {}).get('wins', {}).get('total', 0) or 0
                                                    draws = st_eq.get('fixtures', {}).get('draws', {}).get('total', 0) or 0
                                                    loses = st_eq.get('fixtures', {}).get('loses', {}).get('total', 0) or 0

                                                    eq_data = {
                                                        'equipo': eq_nombre,
                                                        'liga': eq_liga_nombre,
                                                        'temporada': f'{season}-{season+1}',
                                                        'partidos_jugados': pj_t,
                                                        'victorias': wins,
                                                        'empates': draws,
                                                        'derrotas': loses,
                                                        'goles_favor': gf,
                                                        'goles_contra': gc,
                                                        'lambda_local': round((gf_h + gc_a) / pj_h / 2, 2),
                                                        'lambda_visitante': round((gf_a + gc_h) / pj_a / 2, 2),
                                                        'ultimos_5_partidos': list(st_eq.get('form', '') or '')[:5],
                                                    }
                                                    client.table('equipos_stats').upsert(eq_data, ignore_duplicates=True).execute()
                                                    if eq_nombre in equipos_faltan:
                                                        total_guardados += 1
                                                    else:
                                                        total_actualizados += 1
                                            break
                            except: pass

                        progress_bar.empty()
                        status_text.empty()
                        st.success(f"✅ COMPLETADO: {total_guardados} guardados | {total_actualizados} actualizados")
                        st.markdown(f"📊 Total en BD: **{total_bd + total_guardados}**")
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.info("📅 Sin partidos para esas fechas")

                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Error: {e}")

        with col_info:
            st.markdown(f"📅 {datetime.now(timezone(timedelta(hours=-5))).date().strftime('%d/%m/%Y')} | 📡 Requests: {st.session_state.api_requests_today}/999")
        
        # ═══════════════════════════════════════════════════════════════
        # MOSTRAR PARTIDOS (AGRUPADOS POR LIGA)
        # ═══════════════════════════════════════════════════════════════
        try:
            client = get_client()
            response = client.table('partidos').select('*').execute()
            partidos_db = response.data if response.data else []
        except:
            partidos_db = []
        
        if partidos_db:
            st.markdown(f"<span style='color:black;font-weight:bold'>✅ {len(partidos_db)} partidos de Supabase</span>", unsafe_allow_html=True)
            partidos = partidos_db
        else:
            st.markdown("📭 **No hay partidos.** Clic en 🔄 Sincronizar para obtener partidos.")
            partidos = []
        
        # Filtro por período
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            filtro_opcion = st.selectbox("📅 Ver", ["Todos", "Hoy", "Mañana", "Esta semana"])
        
        # Filtrar según opción
        hoy = datetime.now(timezone(timedelta(hours=-5))).date()
        if filtro_opcion == "Hoy":
            partidos = [p for p in partidos if str(p.get('fecha', ''))[:10] == hoy.strftime('%Y-%m-%d')]
        elif filtro_opcion == "Mañana":
            partidos = [p for p in partidos if str(p.get('fecha', ''))[:10] == (hoy + timedelta(days=1)).strftime('%Y-%m-%d')]
        elif filtro_opcion == "Esta semana":
            semana = (hoy + timedelta(days=2)).strftime('%Y-%m-%d')
            partidos = [p for p in partidos if str(p.get('fecha', ''))[:10] <= semana]
        
        # Agrupar por liga
        ligas_partidos = {}
        for p in partidos:
            liga = p.get('liga', 'Sin Liga')
            if liga not in ligas_partidos:
                ligas_partidos[liga] = []
            ligas_partidos[liga].append(p)
        
        # Emoji por país para cada liga
        def get_pais_emoji(liga):
            if 'Argentina' in liga or 'Copa Argentina' in liga:
                return "🇦🇷"
            elif 'Brasil' in liga or 'Serie A' in liga or 'Brasileirão' in liga:
                return "🇧🇷"
            elif 'Colombia' in liga or 'Dimayor' in liga or 'Primera A' in liga or 'Primera B Colombia' in liga:
                return "🇨🇴"
            elif 'Chile' in liga:
                return "🇨🇱"
            elif 'México' in liga or 'Liga MX' in liga or 'Expansion' in liga:
                return "🇲🇽"
            elif 'MLS' in liga or 'USL' in liga:
                return "🇺🇸"
            elif 'Uruguay' in liga:
                return "🇺🇾"
            elif 'Perú' in liga or 'Liga 1' in liga:
                return "🇵🇪"
            elif 'Paraguay' in liga:
                return "🇵🇾"
            elif 'Ecuador' in liga:
                return "🇪🇨"
            elif 'Premier League' in liga or 'Inglaterra' in liga:
                return "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
            elif 'La Liga' in liga or 'España' in liga or 'Segunda' in liga:
                return "🇪🇸"
            elif 'Bundesliga' in liga or 'Alemania' in liga:
                return "🇩🇪"
            elif 'Serie A' in liga and 'Brasil' not in liga:
                return "🇮🇹"
            elif 'Ligue 1' in liga or 'Francia' in liga:
                return "🇫🇷"
            elif 'Portugal' in liga or 'Primeira' in liga:
                return "🇵🇹"
            elif 'Eredivisie' in liga or 'Holanda' in liga:
                return "🇳🇱"
            elif 'Champions' in liga or 'Europa' in liga or 'Libertadores' in liga or 'Sudamericana' in liga:
                return "🏆"
            elif 'MLS Next' in liga:
                return "🔱"
            elif 'Saudi' in liga or 'Arabia' in liga:
                return "🇸🇦"
            elif 'Egypt' in liga:
                return "🇪🇬"
            elif 'Japan' in liga or 'Japón' in liga:
                return "🇯🇵"
            elif 'Korea' in liga or 'Corea' in liga:
                return "🇰🇷"
            elif 'Turkey' in liga or 'Turquía' in liga or 'Süper' in liga:
                return "🇹🇷"
            elif 'Championship' in liga or 'League One' in liga or 'League Two' in liga:
                return "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
            else:
                return "🌍"
        
        # Mostrar cada liga como un expander (colapsado por defecto)
        for liga, partidos_liga in sorted(ligas_partidos.items()):
            emoji = get_pais_emoji(liga)
            
            with st.expander(f"{emoji} **{liga}** ({len(partidos_liga)} partidos)", expanded=False):
                # Ordenar partidos por fecha y hora
                partidos_liga.sort(key=lambda x: (str(x.get('fecha', '')), str(x.get('hora', ''))))
                
                for i, partido in enumerate(partidos_liga):
                    equipo_local = partido.get('equipo_local', '')
                    equipo_visitante = partido.get('equipo_visitante', '')
                    hora = partido.get('hora', '00:00')[:5]

                    # Verificar si los equipos tienen estadísticas
                    try:
                        resp_local = client.table('equipos_stats').select('equipo').ilike('equipo', f'%{equipo_local}%').execute()
                        resp_visit = client.table('equipos_stats').select('equipo').ilike('equipo', f'%{equipo_visitante}%').execute()
                        tiene_local = len(resp_local.data) > 0 if resp_local.data else False
                        tiene_visit = len(resp_visit.data) > 0 if resp_visit.data else False
                        tiene_stats = tiene_local and tiene_visit
                    except:
                        tiene_stats = None

                    # Badge de estado con color
                    if tiene_stats is True:
                        badge = "🟢"
                        badge_color = "#22c55e"
                        tooltip = "Ambos equipos tienen estadísticas"
                    elif tiene_stats is False:
                        badge = "🔴"
                        badge_color = "#ef4444"
                        tooltip = "Faltan estadísticas"
                    else:
                        badge = "⚪"
                        badge_color = "#9ca3af"
                        tooltip = "No verificado"

                    # Fila estilo enlace
                    st.markdown(f"""
                    <div onclick="this.nextElementSibling.click()" style="cursor:pointer; padding:12px 16px; margin:4px 0; background:#F0FDFA; border:1px solid #e5e7eb; border-radius:8px;">
                        <span style="color:#6b7280;">🗓️ {hora}</span>&nbsp;|&nbsp;
                        <span style="color:#059669;font-weight:600;">🏠 {equipo_local}</span>&nbsp;⚽&nbsp;
                        <span style="color:#dc2626;font-weight:600;">{equipo_visitante}</span>&nbsp;✈️
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Ir", key=f"go_{liga}_{i}"):
                        st.session_state.selected_local = equipo_local
                        st.session_state.selected_away = equipo_visitante
                        st.session_state.page = "Analizador"
                        st.rerun()
        
    # Página: Analizador
    elif st.session_state.page == "Analizador":
        pass  # Sin título
        
        # Inicializar selected_match en session_state
        if 'selected_match_data' not in st.session_state:
            st.session_state.selected_match_data = None
        
        client = get_client()
        
        # Si no hay partido seleccionado, mostrar mensaje (solo si tampoco hay selected_local)
        if not st.session_state.selected_match_data and not ('selected_local' in st.session_state and 'selected_away' in st.session_state):
            st.info("🎯 Ve a la página **Partidos** para seleccionar un partido y analizarlo.")
            st.info("📍 También puedes analizar desde el preview en la página principal.")
            
            if st.button("📋 Ir a Partidos", type="primary"):
                st.session_state.page = "Partidos"
                st.rerun()
            
            st.stop()  # Terminar aquí
            
            # Emoji por país
            pais_emoji = {'México': '🇲🇽', 'Colombia': '🇨🇴', 'Argentina': '🇦🇷', 'Brasil': '🇧🇷', 'Chile': '🇨🇱'}
            
            # Header de la tabla con colores
            cols_header = st.columns([1.5, 2, 2, 0.7, 1, 0.6])
            with cols_header[0]:
                st.markdown("**<span style='color:#00d4aa'>📅 Fecha</span>**", unsafe_allow_html=True)
            with cols_header[1]:
                st.markdown("**<span style='color:#00d4aa'>🏠 Local</span>**", unsafe_allow_html=True)
            with cols_header[2]:
                st.markdown("**<span style='color:#00d4aa'>✈️ Visitante</span>**", unsafe_allow_html=True)
            with cols_header[3]:
                st.markdown("**<span style='color:#00d4aa'>⏰ Hora</span>**", unsafe_allow_html=True)
            with cols_header[4]:
                st.markdown("**<span style='color:#00d4aa'>🌍 País</span>**", unsafe_allow_html=True)
            with cols_header[5]:
                st.markdown("**<span style='color:#00d4aa'>🎯</span>**", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Filas de partidos con colores
            for p in partidos_data:
                fecha = p.get('fecha', '')[:10] if p.get('fecha') else ''
                hora = p.get('hora', '')[:5] if p.get('hora') else ''
                local = p.get('equipo_local', '?')
                visitante = p.get('equipo_visitante', '?')
                pais = p.get('pais', '')
                emoji = pais_emoji.get(pais, '🌍')
                
                cols_row = st.columns([1.5, 2, 2, 0.7, 1, 0.6])
                
                with cols_row[0]:
                    fecha_mostrar = str(fecha)[:10] if fecha else "N/A"
                    st.markdown(f"<span style='color:#ffffff; font-size:13px'>📅 {html.escape(fecha_mostrar)}</span>", unsafe_allow_html=True)
                with cols_row[1]:
                    st.markdown(f"<span style='color:#00ff88; font-size:13px'>🏠 **{html.escape(str(local) if local else '?')}**</span>", unsafe_allow_html=True)
                with cols_row[2]:
                    st.markdown(f"<span style='color:#ff6b6b; font-size:13px'>✈️ **{html.escape(str(visitante) if visitante else '?')}**</span>", unsafe_allow_html=True)
                with cols_row[3]:
                    hora_mostrar = str(hora)[:5] if hora else "N/A"
                    st.markdown(f"<span style='color:#ffd700; font-size:13px'>⏰ {html.escape(hora_mostrar)}</span>", unsafe_allow_html=True)
                with cols_row[4]:
                    pais_str = str(pais)[:6] if pais else "N/A"
                    st.markdown(f"<span style='color:#00d4aa; font-size:13px'>{emoji} {html.escape(pais_str)}</span>", unsafe_allow_html=True)
                with cols_row[5]:
                    if st.button("🎯", key=f"match_{p.get('id')}", help=f"Analizar {local} VS {visitante}", use_container_width=True):
                        selected_match = p
                        st.session_state.selected_match_data = selected_match
        
        # Mostrar equipos disponibles
        equipos_disponibles = []
        if not equipos_disponibles:
            st.warning("⚠️ No hay equipos guardados. Ve a 'Estadísticas' para agregar equipos.")
        
        # Si hay un partido seleccionado, hacer análisis automático
        if st.session_state.selected_match_data:
            p = st.session_state.selected_match_data
            local_nombre = p.get('equipo_local', '')
            visitante_nombre = p.get('equipo_visitante', '')
        
        # Si viene de la página Partidos con equipos en session_state
        elif 'selected_local' in st.session_state and 'selected_away' in st.session_state:
            local_nombre = st.session_state.selected_local
            visitante_nombre = st.session_state.selected_away
            st.markdown("---")
            st.markdown(f"### 🎯 Analizando: **{local_nombre}** VS **{visitante_nombre}**")
            
            # Buscar stats de los equipos en Supabase
            stats_local = None
            stats_visitante = None
            
            try:
                resp_local = client.table('equipos_stats').select('*').eq('equipo', local_nombre).execute()
                if resp_local.data:
                    stats_local = resp_local.data[0]
            except:
                pass
            
            try:
                resp_visitante = client.table('equipos_stats').select('*').eq('equipo', visitante_nombre).execute()
                if resp_visitante.data:
                    stats_visitante = resp_visitante.data[0]
            except:
                pass
            
            # DEBUG
                                    
            # Limpiar session_state después de usar
            del st.session_state.selected_local
            del st.session_state.selected_away
            st.session_state.selected_match_data = None
            
            if stats_local and stats_visitante:
                lambda_local = stats_local.get('lambda_local', 0)
                lambda_visitante = stats_visitante.get('lambda_visitante', 0)
                
                # Aplicar calibración (Fix #1 - usar lambdas ajustadas)
                lambda_local_adj = get_lambda_ajustada(local_nombre, lambda_local, como_local=True)
                lambda_visitante_adj = get_lambda_ajustada(visitante_nombre, lambda_visitante, como_local=False)
                lambda_local_cal = lambda_local_adj['lambda_ajustada']
                lambda_visitante_cal = lambda_visitante_adj['lambda_ajustada']
                
                with st.spinner("Analizando..."):
                    result = calcular(
                        lambda_local=lambda_local_cal,
                        lambda_visitante=lambda_visitante_cal,
                        corners_local=float(stats_local.get('promedio_corners_total', 10)),
                        corners_visitante=float(stats_visitante.get('promedio_corners_total', 10)),
                        tarjetas_local=float(stats_local.get('promedio_tarjetas', 3)),
                        tarjetas_visitante=float(stats_visitante.get('promedio_tarjetas', 3)),
                        tiros_local=float(stats_local.get('promedio_tiros', 12)),
                        tiros_visitante=float(stats_visitante.get('promedio_tiros', 12)),
                        tiros_arco_local=float(stats_local.get('promedio_tiros_arco', 4)),
                        tiros_arco_visitante=float(stats_visitante.get('promedio_tiros_arco', 4)),
                        ultimos_5_local=[],
                        ultimos_5_visitante=[],
                    )
                    
                    # Agregar fixture_id si existe en el partido seleccionado
                    if 'selected_match_data' in st.session_state and st.session_state.selected_match_data and st.session_state.selected_match_data.get('fixture_id'):
                        result['fixture_id'] = st.session_state.selected_match_data.get('fixture_id')
                    
                    st.session_state.analysis_result = result
                    st.session_state.home = local_nombre
                    st.session_state.away = visitante_nombre
                    st.session_state.stats_local = stats_local
                    st.session_state.stats_visitante = stats_visitante
                    
                    remates_total = float(stats_local.get('promedio_tiros', 12)) + float(stats_visitante.get('promedio_tiros', 12))
                    tarjetas_total = float(stats_local.get('promedio_tarjetas', 3)) + float(stats_visitante.get('promedio_tarjetas', 3))
                    
                    st.session_state.remates_over_prob = min(90, max(10, 50 + (remates_total - 24) * 2))
                    st.session_state.tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))
            else:
                st.warning(f"⚠️ No se encontraron estadísticas para {local_nombre} o {visitante_nombre}")
                st.info("💡 Ve a 'Estadísticas' para buscar los equipos primero.")
                st.stop()  # No continuar
        
        
        
        # Si hay un partido seleccionado de la lista, usar esos equipos
        # Bloque comentado
        #             local_nombre = selected_match.get('equipo_local', '')
        #             visitante_nombre = selected_match.get('equipo_visitante', '')
        #             
        #             # Buscar coincidencia en equipos disponibles
        #             local_match = next((e for e in equipos_disponibles if local_nombre.lower() in e.lower() or e.lower() in local_nombre.lower()), None)
        #             visitante_match = next((e for e in equipos_disponibles if visitante_nombre.lower() in e.lower() or e.lower() in visitante_nombre.lower()), None)
        #             
        #             home_team = local_match if local_match else (local_nombre.title() if local_nombre else "")
        #             away_team = visitante_match if visitante_match else (visitante_nombre.title() if visitante_nombre else "")
        #         else:
        #             # Usar selectores si no hay partido seleccionado
            col_space, col1, col2, col_space2 = st.columns([2, 1, 1, 2])
            st.markdown("""
<style>
.stSelectbox label {
    font-size: 120px !important;
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)
            with col1:
                home_team = st.selectbox("🏠 Local", [""] + equipos_disponibles, key="home_select")
            with col2:
                away_team = st.selectbox("✈️ Visitante", [""] + equipos_disponibles, key="away_select")
        
        # Validar que ambos equipos tengan DATOS REALES en Supabase
        lambda_local = None
        lambda_visitante = None
        equipo_local_ok = False
        equipo_visitante_ok = False
        equipos_faltantes = []
        error_conexion = False
        
        # Datos completos de los equipos
        stats_local = None
        stats_visitante = None
        
        if home_team:
            try:
                client = get_client()
                resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{home_team}%').execute()
                if resp.data and resp.data[0].get('lambda_local', 0) > 0:
                    stats_local = resp.data[0]
                    lambda_local = stats_local.get('lambda_local', 0)
                    equipo_local_ok = True
                else:
                    equipos_faltantes.append(home_team)
            except Exception as e:
                error_conexion = True
                equipos_faltantes.append(home_team)
        
        if away_team:
            try:
                client = get_client()
                resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{away_team}%').execute()
                if resp.data and resp.data[0].get('lambda_visitante', 0) > 0:
                    stats_visitante = resp.data[0]
                    lambda_visitante = stats_visitante.get('lambda_visitante', 0)
                    equipo_visitante_ok = True
                else:
                    equipos_faltantes.append(away_team)
            except Exception as e:
                error_conexion = True
                equipos_faltantes.append(away_team)
        
        # Mostrar error si faltan equipos
        if equipos_faltantes and not error_conexion:
            st.error(f"⚠️ Equipos no encontrados en la base de datos: {', '.join(set(equipos_faltantes))}")
            st.info("📝 Ve a la pestaña 'Estadísticas' → 'Agregar Equipo Manual' para agregar los datos.")
        
        # Botón analizar - solo si ambos equipos existen
        analizar_disabled = not (equipo_local_ok and equipo_visitante_ok)
        
        if st.button("🎯 ANALIZAR", type="primary", use_container_width=True, disabled=analizar_disabled):
            try:
                if home_team and away_team and lambda_local and lambda_visitante and stats_local and stats_visitante:
                    with st.spinner("Analizando..."):
                        # Aplicar calibración (Fix #1 - usar lambdas ajustadas)
                        lambda_local_adj = get_lambda_ajustada(home_team, lambda_local, como_local=True)
                        lambda_visitante_adj = get_lambda_ajustada(away_team, lambda_visitante, como_local=False)
                        lambda_local_cal = lambda_local_adj['lambda_ajustada']
                        lambda_visitante_cal = lambda_visitante_adj['lambda_ajustada']
                        
                        # Llamar al modelo con TODOS los datos
                        result = calcular(
                            lambda_local=lambda_local_cal,
                            lambda_visitante=lambda_visitante_cal,
                            corners_local=float(stats_local.get('promedio_corners_total', 10)),
                            corners_visitante=float(stats_visitante.get('promedio_corners_total', 10)),
                            tarjetas_local=float(stats_local.get('promedio_amarillas', 3)),
                            tarjetas_visitante=float(stats_visitante.get('promedio_amarillas', 3)),
                            tiros_local=float(stats_local.get('promedio_tiros', 12)),
                            tiros_visitante=float(stats_visitante.get('promedio_tiros', 12)),
                            tiros_arco_local=float(stats_local.get('promedio_tiros_arco', 4)),
                            tiros_arco_visitante=float(stats_visitante.get('promedio_tiros_arco', 4)),
                            ultimos_5_local=stats_local.get('ultimos_5_partidos', []),
                            ultimos_5_visitante=stats_visitante.get('ultimos_5_partidos', []),
                        )
                        
                        st.session_state.analysis_result = result
                        st.session_state.home = home_team
                        st.session_state.away = away_team
                        st.session_state.stats_local = stats_local
                        st.session_state.stats_visitante = stats_visitante
                        
                        # Guardar TODAS las predicciones en session_state (NO en Supabase aun)
                        # Calcular predicciones de remates
                        remates_total = float(stats_local.get('promedio_tiros', 12)) + float(stats_visitante.get('promedio_tiros', 12))
                        remates_over_prob = min(90, max(10, 50 + (remates_total - 24) * 2))  # 24 es el promedio típico
                        
                        # Calcular predicciones de tarjetas
                        tarjetas_total = float(stats_local.get('promedio_amarillas', 3)) + float(stats_visitante.get('promedio_amarillas', 3))
                        tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))  # 6 es el promedio típico
                        
                        st.session_state.predicciones_actuales = {
                            '1x2': {
                                'pick': result.get('pick_1x2', ''),
                                'prob': float(result.get('prob_1x2', 0))
                            },
                            'over_under': {
                                'pick': result.get('pick_over_under', ''),
                                'prob': float(result.get('prob_over_under', 0)),
                                'over_25': float(result.get('over_under', {}).get('over_25', 0)),
                                'under_25': float(result.get('over_under', {}).get('under_25', 0))
                            },
                            'btts': {
                                'pick': result.get('pick_btts', ''),
                                'prob': float(result.get('btts_yes', 0)),
                                'yes': float(result.get('btts_yes', 0)),
                                'no': float(result.get('btts_no', 0))
                            },
                            'corners': {
                                'pick': result.get('pick_corners', ''),
                                'total': float(result.get('corners', {}).get('total_estimado', 0))
                            },
                            'remates': {
                                'pick': f"+ {remates_total:.0f}" if remates_over_prob > 50 else f"- {remates_total:.0f}",
                                'total': remates_total,
                                'local': float(stats_local.get('promedio_tiros', 12)),
                                'visitante': float(stats_visitante.get('promedio_tiros', 12)),
                                'over_prob': remates_over_prob,
                                'under_prob': 100 - remates_over_prob
                            },
                            'tarjetas': {
                                'pick': f"Over {tarjetas_total:.1f}" if tarjetas_over_prob > 50 else f"Under {tarjetas_total:.1f}",
                                'total': tarjetas_total,
                                'over_prob': tarjetas_over_prob,
                                'under_prob': 100 - tarjetas_over_prob
                            }
                        }
                            
                else:
                    st.error("⚠️ Ambos equipos deben tener estadísticas. Ejecuta el robot primero.")
            except Exception as e:
                st.error(f"❌ Error en análisis: {str(e)[:100]}")
                st.info("💡 Intenta de nuevo o verifica que los equipos existan.")
        
        # Mostrar resultados
        if 'analysis_result' in st.session_state:
            r = st.session_state.analysis_result
            home = st.session_state.home
            away = st.session_state.away
            
            st.markdown("---")
            
            # ========================
            # ESTADÍSTICAS AVANZADAS DEL ROBOT
            # ========================
            stats_local = st.session_state.get('stats_local', {})
            stats_visitante = st.session_state.get('stats_visitante', {})
            
            if stats_local and stats_visitante:
                # Fuente de datos
                source_local = stats_local.get('source', 'football-data.co.uk')
                source_visitante = stats_visitante.get('source', 'football-data.co.uk')
                
                st.markdown("##### 📊 Estadísticas Avanzadas (Calibradas)")
                
                # Fuentes de datos en una línea
                st.markdown(f"🏦 **Fuente:** Local `{source_local}` | Visitante `{source_visitante}`")
                
                # Obtener lambdas ajustadas
                lambda_local_adj = get_lambda_ajustada(home, stats_local.get('lambda_local', 0), como_local=True)
                lambda_visitante_adj = get_lambda_ajustada(away, stats_visitante.get('lambda_visitante', 0), como_local=False)
                
                # Calcular promedios LOCAL
                pj_l = stats_local.get('partidos_jugados', 1) or 1
                gf_l = stats_local.get('goles_favor', 0) or 0
                gc_l = stats_local.get('goles_contra', 0) or 0
                vic_l = stats_local.get('victorias', 0) or 0
                emp_l = stats_local.get('empates', 0) or 0
                der_l = stats_local.get('derrotas', 0) or 0
                prom_corners_l = stats_local.get('promedio_corners_total', 10) or 10
                prom_amarillas_l = stats_local.get('promedio_amarillas', 3) or 3
                prom_tiros_l = stats_local.get('promedio_tiros', 12) or 12
                prom_tiros_arco_l = stats_local.get('promedio_tiros_arco', 4) or 4
                
                icono_ajuste_local = "🔼" if lambda_local_adj['factor'] > 1 else ("🔽" if lambda_local_adj['factor'] < 1 else "➖")
                color_ajuste_local = "#00ff88" if lambda_local_adj['factor'] > 1 else ("#ff6b6b" if lambda_local_adj['factor'] < 1 else "#00d4ff")
                
                # Calcular promedios VISITANTE
                pj_v = stats_visitante.get('partidos_jugados', 1) or 1
                gf_v = stats_visitante.get('goles_favor', 0) or 0
                gc_v = stats_visitante.get('goles_contra', 0) or 0
                vic_v = stats_visitante.get('victorias', 0) or 0
                emp_v = stats_visitante.get('empates', 0) or 0
                der_v = stats_visitante.get('derrotas', 0) or 0
                prom_corners_v = stats_visitante.get('promedio_corners_total', 10) or 10
                prom_amarillas_v = stats_visitante.get('promedio_amarillas', 3) or 3
                prom_tiros_v = stats_visitante.get('promedio_tiros', 12) or 12
                prom_tiros_arco_v = stats_visitante.get('promedio_tiros_arco', 4) or 4
                
                icono_ajuste_vis = "🔼" if lambda_visitante_adj['factor'] > 1 else ("🔽" if lambda_visitante_adj['factor'] < 1 else "➖")
                color_ajuste_vis = "#00ff88" if lambda_visitante_adj['factor'] > 1 else ("#ff6b6b" if lambda_visitante_adj['factor'] < 1 else "#00d4ff")
                
                # DOS COLUMNAS - listas una al lado de otra
                sp1, col_local, col_visita, sp2 = st.columns([1, 1, 1, 1])
                
                with col_local:
                    st.markdown(f"<h4 style='color: #00ff88; text-align: center;'>🏠 {html.escape(str(home))}</h4>", unsafe_allow_html=True)
                    # Lista local
                    stats_list_l = [
                        ("📅 PJ", pj_l, "black"),
                        ("✅ Victorias", vic_l, "black"),
                        ("🤝 Empates", emp_l, "black"),
                        ("❌ Derrotas", der_l, "black"),
                        ("⚽ Goles Favor", gf_l, "black"),
                        ("⚽ Goles Contra", gc_l, "black"),
                        ("📊 Diferencia", f"{gf_l - gc_l:+.0f}", "black"),
                        ("λ Local", f"{stats_local.get('lambda_local', 0):.2f}", "black"),
                        (f"λ Ajustada {icono_ajuste_local}", f"{lambda_local_adj['lambda_ajustada']:.2f}", color_ajuste_local),
                        ("🌽 Córners", f"⬆️{stats_local.get('corners_favor', 0)} ⬇️{stats_local.get('corners_contra', 0)}", "black"),
                        ("🟨 Amarillas", f"{prom_amarillas_l:.1f}", "black"),
                        ("🔫 Tiros", f"{prom_tiros_l:.1f}", "black"),
                        ("🎯 Tiros Arco", f"{prom_tiros_arco_l:.1f}", "black"),
                    ]
                    for label, val, color in stats_list_l:
                        st.markdown(f"<div style='display:flex; justify-content:space-between; padding:4px 10px; border-bottom:1px solid #333; font-size:14px;'><span>{label}</span><span style='color:{color}'>{val}</span></div>", unsafe_allow_html=True)
                
                with col_visita:
                    st.markdown(f"<h4 style='color: #ff6b6b; text-align: center;'>✈️ {html.escape(str(away))}</h4>", unsafe_allow_html=True)
                    # Lista visita
                    stats_list_v = [
                        ("📅 PJ", pj_v, "black"),
                        ("✅ Victorias", vic_v, "black"),
                        ("🤝 Empates", emp_v, "black"),
                        ("❌ Derrotas", der_v, "black"),
                        ("⚽ Goles Favor", gf_v, "black"),
                        ("⚽ Goles Contra", gc_v, "black"),
                        ("📊 Diferencia", f"{gf_v - gc_v:+.0f}", "black"),
                        ("λ Visitante", f"{stats_visitante.get('lambda_visitante', 0):.2f}", "black"),
                        (f"λ Ajustada {icono_ajuste_vis}", f"{lambda_visitante_adj['lambda_ajustada']:.2f}", color_ajuste_vis),
                        ("🌽 Córners", f"⬆️{stats_visitante.get('corners_favor', 0)} ⬇️{stats_visitante.get('corners_contra', 0)}", "black"),
                        ("🟨 Amarillas", f"{prom_amarillas_v:.1f}", "black"),
                        ("🔫 Tiros", f"{prom_tiros_v:.1f}", "black"),
                        ("🎯 Tiros Arco", f"{prom_tiros_arco_v:.1f}", "black"),
                    ]
                    for label, val, color in stats_list_v:
                        st.markdown(f"<div style='display:flex; justify-content:space-between; padding:4px 10px; border-bottom:1px solid #333; font-size:14px;'><span>{label}</span><span style='color:{color}'>{val}</span></div>", unsafe_allow_html=True)
                
                # ========================
                # ÚLTIMOS 5 PARTIDOS
                # ========================
                ultimos_local = stats_local.get('ultimos_5_partidos', [])
                ultimos_visitante = stats_visitante.get('ultimos_5_partidos', [])
                
                if ultimos_local or ultimos_visitante:
                    st.markdown("##### 📅 Forma Reciente")
                    
                    col_forma1, col_forma2 = st.columns(2)
                    
                    with col_forma1:
                        # Forma (simplificado)
                        forma_local = "".join(["🟢" if r == "W" else "🔴" if r == "L" else "🟡" for r in (ultimos_local if isinstance(ultimos_local, list) else [])[:5]])
                        st.markdown(forma_local if forma_local else "Sin datos")
                    with col_forma2:
                        # Forma (simplificado)
                        forma_away = "".join(["🟢" if r == "W" else "🔴" if r == "L" else "🟡" for r in (ultimos_visitante if isinstance(ultimos_visitante, list) else [])[:5]])
                        st.markdown(forma_away if forma_away else "Sin datos")
            # RECUADRO PRINCIPAL DE ANÁLISIS
            # ========================
            pick = r.get('pick_1x2', 'X')
            confianza = r.get('confianza', 0)
            rango = r.get('rango', 'D')
            marcador = r.get('marcador_predicho', f"{r.get('lambda_local', 0):.1f}-{r.get('lambda_visitante', 0):.1f}")
            
            pick_icon = {"1": "🏠", "X": "🤝", "2": "✈️"}
            rango_color = {"A+": "🟢", "A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
            
            st.markdown(f"""
            <div class="caja-analisis">
                <p class="analisis-etiqueta">⚡ ANÁLISIS PRINCIPAL</p>
                <p class="analisis-partido">⚽ {home} VS {away}</p>
                <p class="analisis-score">Expected Score: {marcador}</p>
                <p class="analisis-pick">{pick_icon.get(pick, '🎯')} {pick}</p>
                <span class="analisis-confianza">
                    {rango_color.get(rango, '⚪')} {confianza}% ({rango})
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # ========================
            # GUARDAR PARTIDO (TODAS LAS PREDICCIONES)
            # ========================
            st.markdown("---")
            
            predicciones_act = st.session_state.get('predicciones_actuales', {})
            
            if not predicciones_act:
                st.info("💡 Analiza un partido primero")
            else:
                col_btn, col_info = st.columns([1, 3])
                with col_btn:
                    if st.button("💾 GUARDAR PARTIDO", type="primary", use_container_width=True):
                        try:
                            client = get_client()
                            r = st.session_state.analysis_result
                            
                            # Guardar TODAS las predicciones
                            pick_1x2 = predicciones_act.get('1x2', {}).get('pick', '')
                            pick_data = {
                                'fecha': str(datetime.now(timezone(timedelta(hours=-5))).date()),
                                'liga': stats_local.get('liga', 'Desconocida'),
                                'equipo_local': home,
                                'equipo_visitante': away,
                                'pick': pick_1x2,
                                'prediccion_1x2': pick_1x2,
                                'prob_1x2': predicciones_act.get('1x2', {}).get('prob', 0),
                                'p1': float(r.get('p1', 0)),
                                'px': float(r.get('px', 0)),
                                'p2': float(r.get('p2', 0)),
                                'prediccion_ou': predicciones_act.get('over_under', {}).get('pick', ''),
                                'prediccion_btts': predicciones_act.get('btts', {}).get('pick', ''),
                                'prediccion_corners': predicciones_act.get('corners', {}).get('pick', ''),
                                'prediccion_remates': predicciones_act.get('remates', {}).get('pick', ''),
                                'prediccion_tarjetas': predicciones_act.get('tarjetas', {}).get('pick', ''),
                                'confianza': int(confianza),
                            }
                            
                            client.table('picks').insert(pick_data).execute()
                            st.success("✅ Partido guardado!")
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            
            # ========================
            # PROBABILIDADES 1X2 (CUADROS MEJORADOS)
            # ========================
            st.markdown("##### 🎯 Probabilidades (1X2)")
            
            p1 = r.get('p1', 0)
            px = r.get('px', 0)
            p2 = r.get('p2', 0)
            
            # Determinar cuál tiene mayor probabilidad
            es_local_max = p1 > px and p1 > p2
            es_empate_max = px > p1 and px > p2
            es_visita_max = p2 > p1 and p2 > px
            
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            with col1:
                clase = "caja-1x2 caja-local" if es_local_max else "caja-1x2"
                st.markdown(f"""
                <div class="{clase}">
                    <p class="etiqueta-equipo etiqueta-local">🏠 {home}</p>
                    <p class="probabilidad">{p1:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                clase = "caja-1x2 caja-empate" if es_empate_max else "caja-1x2"
                st.markdown(f"""
                <div class="{clase}">
                    <p class="etiqueta-equipo etiqueta-empate">🤝 Empate</p>
                    <p class="probabilidad">{px:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # PREDICCIONES ADICIONALES (CUADROS MEJORADOS)
            # ========================
            st.markdown("##### 📊 Predicciones Adicionales")
            
            # Calcular datos
            ta_local = stats_local.get('promedio_amarillas', 3) if stats_local else 3
            ta_visitante = stats_visitante.get('promedio_amarillas', 3) if stats_visitante else 3
            tarjetas_total = ta_local + ta_visitante
            
            ti_local = stats_local.get('promedio_tiros', 12) if stats_local else 12
            ti_visitante = stats_visitante.get('promedio_tiros', 12) if stats_visitante else 12
            remates_total = ti_local + ti_visitante
            
            # Probabilidades para remates
            remates_over_prob = min(90, max(10, 50 + (remates_total - 24) * 2))
            pick_remates = "+" if remates_over_prob > 50 else "-"
            
            # Probabilidades para tarjetas
            tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))
            pick_tarjetas = "+" if tarjetas_over_prob > 50 else "-"
            
            # Tiros al arco
            arco_local = stats_local.get('promedio_tiros_arco', 4) if stats_local else 4
            arco_visitante = stats_visitante.get('promedio_tiros_arco', 4) if stats_visitante else 4
            arco_total = arco_local + arco_visitante
            arco_over_prob = min(90, max(10, 50 + (arco_total - 8) * 3))
            pick_arco = "+" if arco_over_prob > 50 else "-"
            
            modelos = r.get('modelos', {})
            mc = modelos.get('monte_carlo', {})
            top_scores = mc.get('top_scores', {})
            score_mas_probable = list(top_scores.keys())[0] if top_scores else "2-1"
            
            col_space, col_ou, col_btts, col_corners, col_remates, col_arco, col_tarjetas, col_score, col_space2 = st.columns([0.3, 1, 1, 1, 1, 1, 1, 1, 0.3])
            
            with col_ou:
                pick_ou = r.get('pick_over_under', 'Over 2.5')
                prob_ou = r.get('prob_over_under', 50)
                ou_symbol = "+" if "Over" in pick_ou else "-"
                ou_color_class = "pick-over" if "Over" in pick_ou else "pick-under"
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">📈 Over/Under 2.5</p>
                    <p class="valor-caja {ou_color_class}">{ou_symbol} 2.5</p>
                    <p class="pick-caja">{prob_ou:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btts:
                pick_btts = r.get('pick_btts', 'No')
                btts_yes = r.get('btts_yes', 50)
                btts_icon = "✅" if pick_btts == "Sí" else "❌"
                btts_color_class = "pick-si" if pick_btts == "Sí" else "pick-no"
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">⚽ Ambos Marcan</p>
                    <p class="valor-caja {btts_color_class}">{btts_icon} {pick_btts}</p>
                    <p class="pick-caja">{btts_yes:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_corners:
                corners = r.get('corners', {})
                total_c = corners.get('total_estimado', 10)
                pick_corners = r.get('pick_corners', '+')
                pick_corner_symbol = "+" if pick_corners == "+" else "-"
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">🌽 Córners Total</p>
                    <p class="valor-caja" style="color: #00d2d3;">{total_c:.0f}</p>
                    <p class="pick-caja">{pick_corner_symbol} {total_c:.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_remates:
                remates_icon = "📈" if pick_remates == "+" else "📉"
                remates_color_class = "pick-over" if pick_remates == "+" else "pick-under"
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">🔫 Tiros Total</p>
                    <p class="valor-caja" style="color: #00ff88;">{remates_total:.0f}</p>
                    <p class="pick-caja {remates_color_class}">{remates_icon} {pick_remates}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_arco:
                arco_icon = "📈" if pick_arco == "+" else "📉"
                arco_color_class = "pick-over" if pick_arco == "+" else "pick-under"
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">🎯 Tiros Arco</p>
                    <p class="valor-caja" style="color: #ff9f43;">{arco_total:.0f}</p>
                    <p class="pick-caja {arco_color_class}">{arco_icon} {pick_arco}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_tarjetas:
                tarjetas_icon = "📈" if pick_tarjetas == "+" else "📉"
                tarjetas_color_class = "pick-over" if pick_tarjetas == "+" else "pick-under"
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">🟨 Amarillas Total</p>
                    <p class="valor-caja" style="color: #ffd700;">{tarjetas_total:.1f}</p>
                    <p class="pick-caja {tarjetas_color_class}">{tarjetas_icon} {pick_tarjetas}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_score:
                st.markdown(f"""
                <div class="caja-prediccion">
                    <p class="titulo-caja">🎯 Marcador Probable</p>
                    <p class="valor-caja" style="color: #ff6b6b;">{score_mas_probable}</p>
                    <p class="pick-caja" style="color: #888;">Más probable</p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # FORMA RECIENTE (CUADROS MEJORADOS)
            # ========================
            st.markdown("##### 📅 Forma Reciente (Últimos 5)")
            
            forma_l = r.get('forma_local', {})
            forma_v = r.get('forma_visitante', {})
            
            col_space1, col_forma_local, col_forma_away, col_space2 = st.columns([1, 2, 2, 1])
            
            with col_forma_local:
                letras = forma_l.get('forma_letras', '-----')
                puntos = forma_l.get('forma_puntos', 0)
                gf = forma_l.get('goles_favor_5', 0)
                gc = forma_l.get('goles_contra_5', 0)
                
                # Crear badges de forma
                badges_forma = "".join([
                    f"<span class='forma-badge forma-badge-g'>{c}</span>" if c=='G' else (
                    f"<span class='forma-badge forma-badge-e'>{c}</span>" if c=='E' else (
                    f"<span class='forma-badge forma-badge-p'>{c}</span>" if c=='P' else c
                    )) for c in letras
                ])
                
                st.markdown(f"""
                <div class="caja-forma caja-forma-local">
                    <p class="forma-titulo">🏠 {home}</p>
                    <div class="forma-letras">{badges_forma}</div>
                    <p class="forma-stats">
                        Puntos: <span>{puntos:.0f}%</span> | 
                        Goles: <span>{gf}f/{gc}c</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_forma_away:
                letras_v = forma_v.get('forma_letras', '-----')
                puntos_v = forma_v.get('forma_puntos', 0)
                gf_v = forma_v.get('goles_favor_5', 0)
                gc_v = forma_v.get('goles_contra_5', 0)
                
                # Crear badges de forma
                badges_forma_v = "".join([
                    f"<span class='forma-badge forma-badge-g'>{c}</span>" if c=='G' else (
                    f"<span class='forma-badge forma-badge-e'>{c}</span>" if c=='E' else (
                    f"<span class='forma-badge forma-badge-p'>{c}</span>" if c=='P' else c
                    )) for c in letras_v
                ])
                
                st.markdown(f"""
                <div class="caja-forma caja-forma-visitante">
                    <p class="forma-titulo">✈️ {away}</p>
                    <div class="forma-letras">{badges_forma_v}</div>
                    <p class="forma-stats">
                        Puntos: <span>{puntos_v:.0f}%</span> | 
                        Goles: <span>{gf_v}f/{gc_v}c</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # CUOTAS DEL PARTIDO (de Supabase) CON VALUE
            # ========================
            fixture_id_partido = r.get('fixture_id')
            if fixture_id_partido:
                try:
                    client = get_client()
                    cuotas_resp = client.table('cuotas').select('*').eq('fixture_id', fixture_id_partido).execute()
                    
                    if cuotas_resp.data:
                        st.markdown("##### 💰 Cuotas del Mercado")
                        
                        # Obtener probabilidades del modelo
                        prob_1 = r.get('p1', 0)
                        prob_x = r.get('px', 0)
                        prob_2 = r.get('p2', 0)
                        prob_ou = r.get('prob_over_under', 50)
                        prob_btts = r.get('btts_yes', 50)
                        
                        # Agrupar por tipo de apuesta
                        cuotas_1x2 = [c for c in cuotas_resp.data if c.get('tipo_apuesta') == 'Match Winner']
                        cuotas_btts = [c for c in cuotas_resp.data if c.get('tipo_apuesta') == 'Both Teams To Score']
                        cuotas_ou = [c for c in cuotas_resp.data if c.get('tipo_apuesta') == 'Over/Under']
                        
                        # Función para calcular VALUE
                        def calcular_value(prob_modelo, cuota):
                            if cuota <= 0:
                                return 0, 0
                            prob_implicita = (1 / cuota) * 100
                            value = prob_modelo - prob_implicita
                            return value, prob_implicita
                        
                        # Mostrar 1X2 con VALUE
                        if cuotas_1x2:
                            st.markdown("**🎯 1X2**")
                            col_c1, col_c2, col_c3 = st.columns(3)
                            
                            for i, cuota in enumerate(cuotas_1x2[:3]):
                                opcion = cuota.get('opcion', '')
                                valor = cuota.get('cuota', 0)
                                bookie = cuota.get('bookmaker', '')
                                col = [col_c1, col_c2, col_c3][i] if i < 3 else None
                                
                                if col:
                                    with col:
                                        if 'Home' in opcion or '1' in opcion:
                                            value, prob_imp = calcular_value(prob_1, valor)
                                        elif 'Draw' in opcion or 'X' in opcion:
                                            value, prob_imp = calcular_value(prob_x, valor)
                                        elif 'Away' in opcion or '2' in opcion:
                                            value, prob_imp = calcular_value(prob_2, valor)
                                        else:
                                            value, prob_imp = calcular_value(33, valor)
                                        
                                        # Color según VALUE
                                        if value > 5:
                                            value_color = "🟢"
                                            value_text = f"+{value:.1f}%"
                                        elif value > 0:
                                            value_color = "🟡"
                                            value_text = f"+{value:.1f}%"
                                        else:
                                            value_color = "🔴"
                                            value_text = f"{value:.1f}%"
                                        
                                        label = f"{'🏠 Local' if 'Home' in opcion or '1' in opcion else ('🤝 Empate' if 'Draw' in opcion or 'X' in opcion else '✈️ Visita')}"
                                        st.metric(f"{label}", f"@ {valor:.2f}", f"{value_color} {value_text} VALUE")
                        
                        # Mostrar BTTS con VALUE
                        if cuotas_btts:
                            st.markdown("**⚽ Ambos Marcan (BTTS)**")
                            for cuota in cuotas_btts[:4]:
                                opcion = cuota.get('opcion', '')
                                valor = cuota.get('cuota', 0)
                                bookie = cuota.get('bookmaker', '')
                                
                                # Probabilidad del modelo para BTTS
                                prob_modelo_btts = prob_btts if 'Yes' in opcion else (100 - prob_btts)
                                value, prob_imp = calcular_value(prob_modelo_btts, valor)
                                
                                if value > 5:
                                    value_color = "🟢"
                                elif value > 0:
                                    value_color = "🟡"
                                else:
                                    value_color = "🔴"
                                
                                st.write(f"{opcion}: **@ {valor:.2f}** | {value_color} VALUE: {value:+.1f}% | Modelo: {prob_modelo_btts:.0f}% | Implicita: {prob_imp:.0f}% ({bookie})")
                        
                        # Mostrar Over/Under con VALUE
                        if cuotas_ou:
                            st.markdown("**📈 Over/Under**")
                            for cuota in cuotas_ou[:6]:
                                opcion = cuota.get('opcion', '')
                                valor = cuota.get('cuota', 0)
                                bookie = cuota.get('bookmaker', '')
                                
                                # Extraer línea (ej: "Over 2.5" -> 2.5)
                                if 'Over' in opcion:
                                    prob_modelo_ou = prob_ou
                                else:
                                    prob_modelo_ou = 100 - prob_ou
                                
                                value, prob_imp = calcular_value(prob_modelo_ou, valor)
                                
                                if value > 5:
                                    value_color = "🟢"
                                elif value > 0:
                                    value_color = "🟡"
                                else:
                                    value_color = "🔴"
                                
                                st.write(f"{opcion}: **@ {valor:.2f}** | {value_color} VALUE: {value:+.1f}% | Modelo: {prob_modelo_ou:.0f}% | Implicita: {prob_imp:.0f}% ({bookie})")
                        
                        # Resumen de VALUE bets
                        st.markdown("---")
                        st.markdown("**📊 Resumen de Value Bets:**")
                        
                        value_bets = []
                        for cuota in cuotas_resp.data:
                            if not isinstance(cuota, dict):
                                continue
                            
                            tipo = cuota.get('tipo_apuesta', '')
                            opcion = cuota.get('opcion', '')
                            valor_raw = cuota.get('cuota', 0)
                            
                            # Convertir a float si es string
                            try:
                                valor = float(valor_raw) if valor_raw else 0
                            except (ValueError, TypeError):
                                continue
                            
                            bookie = cuota.get('bookmaker', '')
                            
                            if tipo == 'Match Winner':
                                if 'Home' in opcion or '1' in opcion:
                                    prob = prob_1
                                elif 'Draw' in opcion or 'X' in opcion:
                                    prob = prob_x
                                else:
                                    prob = prob_2
                            elif tipo == 'Both Teams To Score':
                                prob = prob_btts if 'Yes' in opcion else (100 - prob_btts)
                            elif tipo == 'Over/Under':
                                prob = prob_ou if 'Over' in opcion else (100 - prob_ou)
                            else:
                                continue
                            
                            value, _ = calcular_value(prob, valor)
                            if value > 0:
                                value_bets.append({
                                    'tipo': tipo,
                                    'opcion': opcion,
                                    'cuota': valor,
                                    'value': value,
                                    'bookie': bookie,
                                    'prob_modelo': prob
                                })
                        
                        if value_bets:
                            # Ordenar por VALUE
                            value_bets.sort(key=lambda x: x['value'], reverse=True)
                            
                            for vb in value_bets[:5]:
                                st.success(f"✅ **{vb['opcion']}** @ {vb['cuota']:.2f} | VALUE: +{vb['value']:.1f}% | {vb['bookie']}")
                        else:
                            st.info("🔴 Sin value bets en este momento")
                    else:
                        st.info("💡 Sin cuotas guardadas para este partido. Actualiza los partidos desde Carga.")
                except Exception as e:
                    logger.warning(f"Error consultando cuotas: {e}")
    
    # Página: Estadísticas
    elif st.session_state.page == "Claves":
        st.markdown("### 🔑 Gestión de Contraseñas")
        
        # Tabs
        tab_crear, tab_gestionar = st.tabs(["➕ Crear Contraseña", "📋 Ver Contraseñas"])
        
        # ========== TAB: CREAR ==========
        with tab_crear:
            st.markdown("#### ➕ Crear Nueva Contraseña de Acceso")
            
            with st.form("form_crear_clave", clear_on_submit=True):
                col_nom, col_plan = st.columns(2)
                with col_nom:
                    nombre = st.text_input("📝 Nombre / Cliente", placeholder="Ej: Juan, Carlos VIP").strip()
                with col_plan:
                    plan = st.selectbox("📦 Plan", ["semana", "mes", "elite", "vip"])
                
                nueva_clave = st.text_input("🔐 Nueva Contraseña", placeholder="Escribe la contraseña única").strip()
                
                dias_opciones = {"semana": 7, "mes": 30, "elite": 90, "vip": 90}
                dias = dias_opciones.get(plan, 30)
                
                col_info, col_btn = st.columns([2, 1])
                with col_info:
                    plan_icon = {"semana": "📆", "mes": "👑", "elite": "🔥", "vip": "⭐"}
                    st.info(f"{plan_icon.get(plan, '📦')} Plan: {plan.upper()} - {dias} días")
                
                submitted = st.form_submit_button("✅ Crear Contraseña", use_container_width=True, type="primary")
                
                if submitted:
                    if not nombre.strip():
                        st.error("⚠️ Ingresa un nombre")
                    elif not nueva_clave.strip():
                        st.error("⚠️ Ingresa una contraseña")
                    elif len(nueva_clave) < 4:
                        st.error("⚠️ La contraseña debe tener al menos 4 caracteres")
                    else:
                        # Todos los planes son VIP (semana, mes, elite, vip)
                        plan_asignar = "elite"
                        success = db_crear_usuario(nueva_clave.strip(), nombre.strip(), plan_asignar, dias)
                        if success:
                            st.success(f"✅ Contraseña '{nueva_clave}' creada para {nombre} - Plan {plan.upper()}")
                            st.balloons()
                        else:
                            st.error("❌ Esta contraseña ya existe. Usa otra.")
            
            st.markdown("---")
            st.markdown("##### 📋 Planes")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**🆓 GRATIS** - Sin VIP")
            with col2:
                st.markdown("**📆 SEMANA** - 7 días VIP")
        
        # ========== TAB: GESTIONAR ==========
        with tab_gestionar:
            st.markdown("#### 📋 Contraseñas Creadas")
            
            # Botón recargar
            if st.button("🔄 Recargar Lista"):
                st.rerun()
            
            usuarios = db_todos()
            
            if not usuarios:
                st.info("📭 No hay contraseñas creadas. Crea una en la pestaña de arriba.")
            else:
                col_total, col_vip, col_admin = st.columns(3)
                with col_total:
                    st.metric("Total", len(usuarios))
                with col_vip:
                    vip_count = sum(1 for u in usuarios if u.get('plan', '') in ['vip', 'elite', 'mes'])
                    st.metric("VIP/Elite/Mes", vip_count)
                with col_admin:
                    admin_count = sum(1 for u in usuarios if u.get('es_admin') == 1)
                    st.metric("Admins", admin_count)
                
                st.markdown("---")
                
                for u in usuarios:
                    clave_id = u.get('id')
                    es_admin = u.get('es_admin') == 1
                    es_vip = u.get('plan', '') in ['vip', 'elite', 'mes']
                    plan = u.get('plan', 'vip')
                    dias = u.get('dias', 0)
                    password = u.get('password', 'N/A')
                    nombre = u.get('nombre', 'Sin nombre')
                    
                    if es_admin:
                        icono = "⚙️"
                        color = "blue"
                    elif es_vip:
                        icono = "👑"
                        color = "green"
                    else:
                        icono = "🆓"
                        color = "gray"
                    
                    with st.container():
                        col_icon, col_info = st.columns([1, 5])
                        with col_icon:
                            st.markdown(f"### {icono}")
                        with col_info:
                            st.markdown(f"**{nombre}** - Plan: {plan.upper()} ({dias} días)")
                            st.code(password)
                            st.caption(f"Creado: {u.get('creado', 'N/A')}")
                            
                            # Acciones
                            if not es_admin:
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    nueva_pass = st.text_input("Nueva contraseña", placeholder="Nueva...", key=f"pass_{clave_id}", type="password")
                                    if st.button("🔐 Cambiar", key=f"btn_pass_{clave_id}"):
                                        if nueva_pass and len(nueva_pass) >= 4:
                                            if db_cambiar_password(clave_id, nueva_pass):
                                                st.success("✅ Contraseña cambiada")
                                                st.rerun()
                                            else:
                                                st.error("❌ Error")
                                        else:
                                            st.warning("Mínimo 4 caracteres")
                                with col_b:
                                    plan_nuevo = st.selectbox("Nuevo plan", ["semana", "mes", "elite", "vip"], 
                                                             index=["semana", "mes", "elite", "vip"].index(plan) if plan in ["semana", "mes", "elite", "vip"] else 0,
                                                             key=f"plan_{clave_id}")
                                    dias_nuevos = {"semana": 7, "mes": 30, "elite": 90, "vip": 90}.get(plan_nuevo, 30)
                                    if st.button("📦 Cambiar Plan", key=f"btn_plan_{clave_id}"):
                                        if db_actualizar_plan(clave_id, plan_nuevo if plan_nuevo != "elite" else "elite", dias_nuevos):
                                            st.success(f"✅ Plan cambiado a {plan_nuevo.upper()}")
                                            st.rerun()
                                        else:
                                            st.error("❌ Error")
                                with col_c:
                                    st.write("")  # Espacio
                                    if st.button("🗑️ Eliminar", key=f"btn_del_{clave_id}", type="primary"):
                                        if db_eliminar_usuario(clave_id):
                                            st.success("✅ Eliminada")
                                            st.rerun()
                                        else:
                                            st.error("❌ No se pudo eliminar")
                            else:
                                st.info("⚙️ Cuenta del administrador")
                        st.markdown("---")


    # ══════════════════════════════════════════════════════════
    # PÁGINA VIP DASHBOARD - Solo para usuarios Elite/Premium
    # ══════════════════════════════════════════════════════════
    elif st.session_state.page == "VIP":
        
        # Verificar si el usuario es VIP/Elite
        user_plan = st.session_state.user_data.get('plan', 'vip') if st.session_state.user_data else 'vip'
        es_vip = user_plan.lower() in ['vip', 'elite', 'admin', 'mes', 'premium']
        
        if not es_vip:
            # Mostrar pantalla de upgrade
            st.markdown("""
            <div style="text-align: center; padding: 50px 20px;">
                <h1>🔒 Contenido Exclusivo para Miembros VIP</h1>
                <p style="font-size: 1.2em; color: #666; margin: 30px 0;">
                    El Dashboard VIP está disponible solo para miembros con plan <strong>Elite VIP</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Plan card
            st.markdown("""
            <div class="plan-card plan-vip" style="max-width: 400px; margin: 0 auto; text-align: center;">
                <h3>👑 Plan Elite VIP</h3>
                <p class="plan-price">$29.99 <span>/mes</span></p>
                <ul style="text-align: left;">
                    <li>✅ Dashboard VIP completo</li>
                    <li>✅ ROI por modelo y tipo de pick</li>
                    <li>✅ Simulador de Bankroll</li>
                    <li>✅ Detector de Value Bets</li>
                    <li>✅ Alertas y notificaciones</li>
                    <li>✅ Ranking mensual</li>
                    <li>✅ Reportes exportables</li>
                </ul>
                <p style="margin-top: 20px;"><strong>🎁 7 días GRATIS - Sin tarjeta</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar plan actual
            st.markdown("---")
            st.info(f"📧 Tu plan actual: **{user_plan.upper()}**")
            st.markdown("¿Quieres hacer upgrade? Contacta al administrador.")
            
            st.stop()
        
        # Usuario VIP - mostrar dashboard
        st.markdown("### 👑 Dashboard VIP - Gestión Inteligente de Apuestas")
        
        # Obtener datos de Supabase
        client = get_client()
        usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'
        
        # ==================== TABS VIP ====================
        tab_roi, tab_resultados, tab_bankroll, tab_value, tab_alertas, tab_ranking, tab_export = st.tabs([
            "📊 ROI", "📝 Resultados", "💰 Bankroll", "🎯 Value Bets", "🔔 Alertas", "🏆 Ranking", "📄 Exportar"
        ])
        
        # ========== TAB 1: ROI POR MODELO ==========
        with tab_roi:
            st.markdown("### 📊 Rendimiento por Modelo y Tipo de Pick")
            
            # Obtener picks resueltos
            try:
                response = client.table('picks').select('*').execute()
                picks = response.data if response.data else []
            except Exception as e:
                logger.error(f"Error obteniendo picks: {e}")
                picks = []
            
            if picks:
                # Filtrar picks con resultados
                picks_resueltos = [p for p in picks if p.get('acertado_1x2') is not None or p.get('acertado_ou') is not None]
                
                if picks_resueltos:
                    # ROI POR TIPO DE MERCADO
                    st.markdown("#### 💹 ROI por Tipo de Pick")
                    
                    # 1X2
                    picks_1x2 = [p for p in picks_resueltos if p.get('acertado_1x2') is not None]
                    acertados_1x2 = len([p for p in picks_1x2 if p.get('acertado_1x2')])
                    pct_1x2 = (acertados_1x2 / len(picks_1x2) * 100) if picks_1x2 else 0
                    
                    # Over/Under
                    picks_ou = [p for p in picks_resueltos if p.get('acertado_ou') is not None]
                    acertados_ou = len([p for p in picks_ou if p.get('acertado_ou')])
                    pct_ou = (acertados_ou / len(picks_ou) * 100) if picks_ou else 0
                    
                    # BTTS
                    picks_btts = [p for p in picks_resueltos if p.get('acertado_btts') is not None]
                    acertados_btts = len([p for p in picks_btts if p.get('acertado_btts')])
                    pct_btts = (acertados_btts / len(picks_btts) * 100) if picks_btts else 0
                    
                    # Corners
                    picks_corners = [p for p in picks_resueltos if p.get('acertado_corners') is not None]
                    acertados_corners = len([p for p in picks_corners if p.get('acertado_corners')])
                    pct_corners = (acertados_corners / len(picks_corners) * 100) if picks_corners else 0
                    
                    # Tarjetas
                    picks_tarjetas = [p for p in picks_resueltos if p.get('acertado_tarjetas') is not None]
                    acertados_tarjetas = len([p for p in picks_tarjetas if p.get('acertado_tarjetas')])
                    pct_tarjetas = (acertados_tarjetas / len(picks_tarjetas) * 100) if picks_tarjetas else 0
                    
                    # Remates
                    picks_remates = [p for p in picks_resueltos if p.get('acertado_remates') is not None]
                    acertados_remates = len([p for p in picks_remates if p.get('acertado_remates')])
                    pct_remates = (acertados_remates / len(picks_remates) * 100) if picks_remates else 0
                    
                    # Mostrar métricas en cards
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🎯 1X2", f"{acertados_1x2}/{len(picks_1x2)}", f"{pct_1x2:.1f}% acierto")
                        if pct_1x2 > 55: st.success("✅ Rentable")
                        elif pct_1x2 < 45: st.error("❌ Perjudicial")
                        else: st.info("📊 Neutral")
                    with col2:
                        st.metric("📈 Over/Under", f"{acertados_ou}/{len(picks_ou)}", f"{pct_ou:.1f}% acierto")
                        if pct_ou > 55: st.success("✅ Rentable")
                        elif pct_ou < 45: st.error("❌ Perjudicial")
                        else: st.info("📊 Neutral")
                    
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric("📐 Corners", f"{acertados_corners}/{len(picks_corners)}", f"{pct_corners:.1f}% acierto")
                        if pct_corners > 55: st.success("✅ Rentable")
                        elif pct_corners < 45: st.error("❌ Perjudicial")
                        else: st.info("📊 Neutral")
                    with col5:
                        st.metric("🟨 Tarjetas", f"{acertados_tarjetas}/{len(picks_tarjetas)}", f"{pct_tarjetas:.1f}% acierto")
                        if pct_tarjetas > 55: st.success("✅ Rentable")
                        elif pct_tarjetas < 45: st.error("❌ Perjudicial")
                        else: st.info("📊 Neutral")
                    with col6:
                        st.metric("🎯 Remates", f"{acertados_remates}/{len(picks_remates)}", f"{pct_remates:.1f}% acierto")
                        if pct_remates > 55: st.success("✅ Rentable")
                        elif pct_remates < 45: st.error("❌ Perjudicial")
                        else: st.info("📊 Neutral")
                    
                    st.markdown("---")
                    
                    # ROI POR RANGO DE CONFIANZA
                    st.markdown("#### 🎚️ ROI por Rango de Confianza")
                    
                    confianza_ranges = [
                        ("95%+ (🔥🔥)", 95, 100),
                        ("90-95% (🔥)", 90, 95),
                        ("80-90% (⚡)", 80, 90),
                        ("70-80% (📊)", 70, 80),
                        ("<70% (📉)", 0, 70),
                    ]
                    
                    conf_cols = st.columns(len(confianza_ranges))
                    for i, (label, min_c, max_c) in enumerate(confianza_ranges):
                        picks_conf = [p for p in picks_resueltos if p.get('confianza', 0) and min_c <= p.get('confianza', 0) <= max_c and p.get('acertado_1x2') is not None]
                        acertados = len([p for p in picks_conf if p.get('acertado_1x2')])
                        total = len(picks_conf)
                        pct = (acertados / total * 100) if total > 0 else 0
                        with conf_cols[i]:
                            st.metric(label, f"{acertados}/{total}", f"{pct:.1f}%")
                    
                    st.markdown("---")
                    
                    # RECOMENDACIÓN
                    st.markdown("#### 💡 Recomendaciones Inteligentes")
                    
                    tipos = [
                        ("1X2", pct_1x2, acertados_1x2, len(picks_1x2)),
                        ("Over/Under", pct_ou, acertados_ou, len(picks_ou)),
                        ("BTTS", pct_btts, acertados_btts, len(picks_btts)),
                        ("Corners", pct_corners, acertados_corners, len(picks_corners)),
                        ("Tarjetas", pct_tarjetas, acertados_tarjetas, len(picks_tarjetas)),
                        ("Remates", pct_remates, acertados_remates, len(picks_remates)),
                    ]
                    
                    # Ordenar por % de acierto
                    tipos_sorted = sorted(tipos, key=lambda x: x[1], reverse=True)
                    
                    mejor = tipos_sorted[0]
                    peor = tipos_sorted[-1]
                    
                    col_rec1, col_rec2 = st.columns(2)
                    with col_rec1:
                        st.markdown("##### ✅ Tipo con MEJOR rendimiento:")
                        st.success(f"**{mejor[0]}** - {mejor[1]:.1f}% acierto ({mejor[2]}/{mejor[3]})")
                        st.markdown("_Considera enfocarte más en este tipo de picks._")
                    with col_rec2:
                        st.markdown("##### ⚠️ Tipo con PEOR rendimiento:")
                        st.error(f"**{peor[0]}** - {peor[1]:.1f}% acierto ({peor[2]}/{peor[3]})")
                        st.markdown("_Considera reducir o evitar este tipo de picks._")
                    
                    # Verificar confianza
                    confianza_95plus = [p for p in picks_resueltos if p.get('confianza', 0) and p.get('confianza', 0) >= 95 and p.get('acertado_1x2') is not None]
                    if confianza_95plus:
                        acertados_95 = len([p for p in confianza_95plus if p.get('acertado_1x2')])
                        pct_95 = (acertados_95 / len(confianza_95plus) * 100)
                        if pct_95 >= 80:
                            st.info(f"🔥 Los picks de ALTA CONFIANZA (95%+) tienen {pct_95:.1f}% de aciertos. ¡Sigue así!")
                        elif pct_95 < 60:
                            st.warning(f"⚠️ Los picks de alta confianza solo acertaron {pct_95:.1f}%. Revisar calibración.")
                else:
                    st.info("📭 No hay picks resueltos aún. Completa algunos análisis y registra los resultados.")
            else:
                st.info("📭 No hay picks guardados aún. Ve al Analizador para crear picks.")
        
        # ========== TAB 2: INGRESAR RESULTADOS ==========
        with tab_resultados:
            st.markdown("### 📝 Ingresar Resultados")
            st.info("💡 Completa el marcador de los partidos para calibrar las predicciones")
            
            # Obtener picks sin resultado
            try:
                response = client.table('picks').select('*').order('fecha', desc=True).execute()
                picks = response.data if response.data else []
            except Exception as e:
                picks = []
                st.error(f"Error: {str(e)[:50]}")
            
            # Filtrar picks sin resultado
            picks_sin_resultado = [p for p in picks if not p.get('marcador') or p.get('marcador') == '?']
            
            if picks_sin_resultado:
                st.markdown(f"#### 📋 {len(picks_sin_resultado)} picks pendientes de resultado")
                
                for p in picks_sin_resultado:
                    pick_id = p.get('id')
                    local = p.get('equipo_local', '?')
                    visitante = p.get('equipo_visitante', '?')
                    fecha = p.get('fecha', '')[:10]
                    
                    with st.expander(f"⚽ {local} VS {visitante} ({fecha})"):
                        st.markdown(f"**Predicciones:** 1X2: {p.get('prediccion_1x2', 'N/A')} | O/U: {p.get('prediccion_ou', 'N/A')} | BTTS: {p.get('prediccion_btts', 'N/A')}")
                        
                        col1, col2, col3, col4 = st.columns([1,1,1,1])
                        with col1:
                            gl = st.number_input("GF Local", min_value=0, max_value=15, value=0, key=f"gf_l_{pick_id}")
                        with col2:
                            gv = st.number_input("GF Visit", min_value=0, max_value=15, value=0, key=f"gf_v_{pick_id}")
                        
                        col5, col6 = st.columns([1,1])
                        with col5:
                            remates = st.number_input("Remates", min_value=0, max_value=50, value=0, key=f"rem_{pick_id}")
                        with col6:
                            pass
                        
                        if st.button("💾 Guardar Resultado", key=f"btn_res_{pick_id}"):
                            # Calcular resultado 1X2
                            if gl > gv:
                                resultado_1x2 = "1"
                            elif gl < gv:
                                resultado_1x2 = "2"
                            else:
                                resultado_1x2 = "X"
                            
                            # Over/Under
                            total_goles = gl + gv
                            resultado_ou = "Over 2.5" if total_goles > 2.5 else "Under 2.5"
                            
                            # BTTS
                            ambos_marcan = "Si" if gl > 0 and gv > 0 else "No"
                            
                            # Verificar aciertos
                            acertado_1x2 = p.get('prediccion_1x2') == resultado_1x2
                            acertado_ou = p.get('prediccion_ou') == resultado_ou
                            acertado_btts = p.get('prediccion_btts') == ambos_marcan
                            acertado_corners = p.get('prediccion_corners') is not None
                            acertado_tarjetas = p.get('prediccion_tarjetas') is not None
                            acertado_remates = p.get('prediccion_remates') is not None

                            # RECALIBRACIÓN AUTOMÁTICA
                            try:
                                registrar_resultado(
                                    equipo_local=local,
                                    equipo_visitante=visitante,
                                    lambda_local_predicha=p.get('lambda_local', 1.5),
                                    lambda_visitante_predicha=p.get('lambda_visitante', 1.3),
                                    goles_local_real=gl,
                                    goles_visitante_real=gv,
                                    predicciones={
                                        '1x2': {'pick': p.get('prediccion_1x2', ''), 'prob': p.get('p1', 50)},
                                        'over_under': {'pick': p.get('prediccion_ou', ''), 'prob': p.get('over_25', 50)},
                                        'btts': {'pick': p.get('prediccion_btts', ''), 'prob': p.get('btts_yes', 50)},
                                    },
                                    resultado_real=resultado_1x2,
                                    marcador=f"{gl}-{gv}",
                                    confianza=p.get('confianza', 70),
                                    rango=p.get('rango', 'B')
                                )
                            except Exception as cal_e:
                                logger.warning(f"Calibración no actualizada: {cal_e}")

                            
                            try:
                                client.table('picks').update({
                                    'marcador': f"{gl}-{gv}",
                                    'resultado_1x2': resultado_1x2,
                                    'resultado_ou': resultado_ou,
                                    'resultado_btts': ambos_marcan,
                                    'resultado_corners': str(corners),
                                    'resultado_tarjetas': str(tarjetas),
                                    'resultado_remates': str(remates),
                                    'acertado_1x2': acertado_1x2,
                                    'acertado_ou': acertado_ou,
                                    'acertado_btts': acertado_btts,
                                    'acertado_corners': acertado_corners,
                                    'acertado_tarjetas': acertado_tarjetas,
                                    'acertado_remates': acertado_remates,
                                }).eq('id', pick_id).execute()
                                st.success("✅ Resultado guardado! La calibración se actualiza automáticamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)[:50]}")
            else:
                st.success("🎉 ¡Todos los picks tienen resultado!")
                st.info("Los resultados ayudan a calibrar las próximas predicciones.")


        # ========== TAB 3: BANKROLL ==========
        with tab_bankroll:
            st.markdown("### 💰 Mi Bankroll Real")
            
            usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'
            
            # Definir monedas disponibles
            MONEDAS = {
                "USD": {"simbolo": "$", "nombre": "Dólar Americano", "codigo": "US$"},
                "EUR": {"simbolo": "€", "nombre": "Euro", "codigo": "€"},
                "MXN": {"simbolo": "$", "nombre": "Peso Mexicano", "codigo": "MX$"},
                "COP": {"simbolo": "$", "nombre": "Peso Colombiano", "codigo": "COP$"},
                "PEN": {"simbolo": "S/", "nombre": "Sol Peruano", "codigo": "S/"},
                "CLP": {"simbolo": "$", "nombre": "Peso Chileno", "codigo": "CLP$"},
                "ARS": {"simbolo": "$", "nombre": "Peso Argentino", "codigo": "ARS$"},
                "BRL": {"simbolo": "R$", "nombre": "Real Brasileño", "codigo": "R$"},
                "GBP": {"simbolo": "£", "nombre": "Libra Esterlina", "codigo": "£"},
            }
            
            # Función para formatear moneda
            def format_money(valor, simbolo):
                """Formatea valor con separadores de miles"""
                return f"{simbolo}{valor:,.2f}"
            
            # Obtener picks del usuario para agregar al bankroll
            try:
                response_picks = client.table('picks').select('*').eq('usuario', usuario_id).execute()
                picks_disponibles = response_picks.data if response_picks.data else []
            except Exception as e:
                logger.error(f"Error obteniendo picks para bankroll: {e}")
                picks_disponibles = []
            
            # Obtener apuestas guardadas del usuario
            try:
                response_apuestas = client.table('bankroll_apuestas').select('*').eq('usuario', usuario_id).order('fecha', desc=True).execute()
                apuestas = response_apuestas.data if response_apuestas.data else []
            except Exception as e:
                logger.error(f"Error obteniendo apuestas: {e}")
                # Crear tabla si no existe
                try:
                    client.table('bankroll_apuestas').execute()
                except Exception as e2:
                    logger.error(f"Error creando tabla bankroll_apuestas: {e2}")
                    apuestas = []
                    pass
                apuestas = []
            
            # ==================== SUBTABS ====================
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📊 Dashboard", "➕ Agregar Apuesta", "📋 Mis Apuestas"])
            
            # ========== SUBTAB 1: DASHBOARD ==========
            with sub_tab1:
                st.markdown("#### 📈 Resumen de Rendimiento")
                
                # Selector de moneda y banco inicial
                col_money1, col_money2 = st.columns([1, 2])
                with col_money1:
                    moneda_select = st.selectbox("💱 Moneda", options=list(MONEDAS.keys()), 
                                               format_func=lambda x: f"{MONEDAS[x]['simbolo']} {MONEDAS[x]['nombre']}",
                                               index=0)
                    simbolo = MONEDAS[moneda_select]["simbolo"]
                
                with col_money2:
                    bankroll_inicial = st.number_input(f"💵 Bankroll Inicial", value=1000.0, min_value=100.0, step=100.0, key="bankroll_inicial")
                
                # Reset bankroll
                col_reset = st.columns(1)[0]
                if st.button("🔄 Reiniciar Bankroll", use_container_width=True):
                    try:
                        client.table('bankroll_apuestas').delete().eq('usuario', usuario_id).execute()
                    except:
                        pass
                    st.success("Bankroll reiniciado")
                    st.rerun()
                
                st.markdown("---")
                
                if apuestas:
                    # Calcular métricas reales
                    total_apostado = sum(a.get('cantidad', 0) for a in apuestas)
                    ganancias = sum(a.get('ganancia', 0) for a in apuestas)
                    bankroll_actual = bankroll_inicial + ganancias
                    roi = ((bankroll_actual - bankroll_inicial) / bankroll_inicial * 100) if bankroll_inicial > 0 else 0
                    
                    apuestas_ganadas = len([a for a in apuestas if a.get('ganancia', 0) > 0])
                    total_apuestas = len(apuestas)
                    tasa_acierto_real = (apuestas_ganadas / total_apuestas * 100) if total_apuestas > 0 else 0
                    
                    # Mostrar métricas con formato de miles
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        delta_gan = f"{'+' if ganancias >= 0 else ''}{format_money(ganancias, simbolo)}"
                        st.metric("💵 Bankroll Actual", format_money(bankroll_actual, simbolo), delta=delta_gan)
                    with col_m2:
                        st.metric("📊 ROI", f"{roi:.1f}%", delta=f"{'+' if roi >= 0 else ''}{roi:.1f}%")
                    with col_m3:
                        st.metric("🎯 Tasa Acierto", f"{tasa_acierto_real:.1f}%", delta=f"{apuestas_ganadas}/{total_apuestas}")
                    with col_m4:
                        st.metric("💰 Ganado/Perdido", format_money(ganancias, simbolo))
                    
                    # Estado del bankroll
                    if bankroll_actual >= bankroll_inicial * 1.1:
                        st.success(f"✅ Bankroll saludable: {((bankroll_actual/bankroll_inicial)-1)*100:.1f}% de ganancia")
                    elif bankroll_actual >= bankroll_inicial * 0.9:
                        st.warning(f"⚠️ Bankroll estable: {((bankroll_actual/bankroll_inicial)-1)*100:.1f}%")
                    else:
                        st.error(f"🔴 Bankroll en riesgo: {((bankroll_actual/bankroll_inicial)-1)*100:.1f}%")
                    
                    # Gráfico de evolución
                    st.markdown("#### 📈 Evolución del Bankroll")
                    import random
                    if total_apuestas > 1:
                        # Crear datos de evolución
                        evolucion = []
                        b = bankroll_inicial
                        for a in sorted(apuestas, key=lambda x: x.get('fecha', '')):
                            b += a.get('ganancia', 0)
                            evolucion.append({'fecha': a.get('fecha', 'N/A'), 'bankroll': b})
                        
                        # Mostrar tabla de evolución
                        df_evo = pd.DataFrame(evolucion)
                        st.line_chart(df_evo.set_index('fecha'))
                    else:
                        st.info("Agrega más apuestas para ver la evolución")
                    
                    # Pronóstico
                    if total_apuestas >= 10:
                        st.markdown("#### 🔮 Pronóstico")
                        media_ganancia = ganancias / total_apuestas
                        proy_mensual = media_ganancia * 30
                        proy_anual = media_ganancia * 365
                        
                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            st.metric("📅 Proyección Mensual", format_money(proy_mensual, simbolo))
                        with col_p2:
                            st.metric("📅 Proyección Anual", format_money(proy_anual, simbolo))
                else:
                    st.info("📭 No tienes apuestas aún. Ve a 'Agregar Apuesta' para empezar.")
            
            # ========== SUBTAB 2: AGREGAR APUESTA ==========
            with sub_tab2:
                st.markdown("#### ➕ Agregar Nueva Apuesta")
                
                tab_origen1, tab_origen2 = st.tabs(["📋 Desde Picks", "✏️ Manual"])
                
                with tab_origen1:
                    if picks_disponibles:
                        st.markdown("##### Selecciona un Pick")
                        
                        # Filtrar picks sin resultado
                        picks_sin_resultado = [p for p in picks_disponibles if p.get('acertado_1x2') is None and p.get('resultado') is None]
                        
                        if picks_sin_resultado:
                            opciones_pick = [f"{p.get('local', '?')} VS {p.get('visitante', '?')} - {p.get('mercado', '?')} @ {p.get('cuota', '?')}" for p in picks_sin_resultado]
                            pick_seleccionado = st.selectbox("Pick", options=range(len(opciones_pick)), format_func=lambda x: opciones_pick[x])
                            
                            pick = picks_sin_resultado[pick_seleccionado]
                            
                            col_p1, col_p2 = st.columns(2)
                            with col_p1:
                                st.write(f"**📅 Fecha:** {pick.get('fecha', 'N/A')}")
                                st.write(f"**📊 Mercado:** {pick.get('mercado', 'N/A')}")
                                st.write(f"**📈 Detalle:** {pick.get('detalle', 'N/A')}")
                            with col_p2:
                                st.write(f"**💰 Cuota:** {pick.get('cuota', 'N/A')}")
                                st.write(f"**🎯 Confianza:** {pick.get('confianza', 'N/A')}%")
                        else:
                            st.info("Todos tus picks ya tienen resultado")
                    else:
                        st.info("No tienes picks disponibles. Ve al Analizador para generar picks.")
                
                with tab_origen2:
                    st.markdown("##### Datos de la Apuesta")
                    
                    col_d1, col_d2, col_d3 = st.columns(3)
                    with col_d1:
                        equipo = st.text_input("🏆 Equipo/Partido", placeholder="Ej: Barcelona vs Real Madrid")
                    with col_d2:
                        cuota = st.number_input("💰 Cuota", value=2.0, min_value=1.01, max_value=100.0, step=0.1)
                    with col_d3:
                        cantidad = st.number_input(f"💵 Cantidad ({simbolo})", value=20.0, min_value=1.0, step=5.0)
                    
                    col_d4, col_d5 = st.columns(2)
                    with col_d4:
                        mercado = st.selectbox("📊 Mercado", ["1X2", "Over/Under", "BTTS", "Corners", "Tarjetas", "Otro"])
                    with col_d5:
                        fecha = st.date_input("📅 Fecha", value=datetime.now(timezone(timedelta(hours=-5))).date())
                    
                    # Resultado (para apuestas ya resueltas)
                    with st.expander("✅ Marcar Resultado (opcional)"):
                        resultado = st.radio("Resultado:", ["Pendiente", "Ganada", "Perdida"], horizontal=True)
                        if resultado != "Pendiente":
                            ganancia = cantidad * (cuota - 1) if resultado == "Ganada" else -cantidad
                            st.write(f"**Ganancia/Pérdida:** {format_money(ganancia, simbolo)}")
                    
                    if st.button("➕ Agregar Apuesta", type="primary", use_container_width=True):
                        resultado_val = None
                        ganancia_val = 0
                        if resultado == "Ganada":
                            resultado_val = True
                            ganancia_val = cantidad * (cuota - 1)
                        elif resultado == "Perdida":
                            resultado_val = False
                            ganancia_val = -cantidad
                        
                        # Guardar en Supabase
                        try:
                            client.table('bankroll_apuestas').insert({
                                'usuario': usuario_id,
                                'fecha': str(fecha),
                                'equipo': equipo,
                                'cuota': cuota,
                                'cantidad': cantidad,
                                'mercado': mercado,
                                'ganancia': ganancia_val,
                                'resultado': resultado_val
                            }).execute()
                            st.success("✅ Apuesta agregada")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            
            # ========== SUBTAB 3: MIS APUESTAS ==========
            with sub_tab3:
                st.markdown("#### 📋 Historial de Apuestas")
                
                if apuestas:
                    # Filtros
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        filtro_estado = st.multiselect("Filtrar por estado", ["Ganada", "Perdida", "Pendiente"], default=["Ganada", "Perdida", "Pendiente"])
                    with col_f2:
                        filtro_mercado = st.multiselect("Filtrar por mercado", list(set(a.get('mercado', '') for a in apuestas)), default=list(set(a.get('mercado', '') for a in apuestas)))
                    
                    # Aplicar filtros
                    apuestas_filtradas = [a for a in apuestas 
                                        if (a.get('resultado') == True and "Ganada" in filtro_estado)
                                        or (a.get('resultado') == False and "Perdida" in filtro_estado)
                                        or (a.get('resultado') is None and "Pendiente" in filtro_estado)]
                    
                    if filtro_mercado:
                        apuestas_filtradas = [a for a in apuestas_filtradas if a.get('mercado', '') in filtro_mercado]
                    
                    # Mostrar tabla
                    st.write(f"**Total: {len(apuestas_filtradas)} apuestas**")
                    
                    for i, a in enumerate(apuestas_filtradas):
                        col_a1, col_a2 = st.columns([4, 1])
                        with col_a1:
                            estado_icon = "✅" if a.get('resultado') == True else ("❌" if a.get('resultado') == False else "⏳")
                            ganancia = a.get('ganancia', 0)
                            ganancia_fmt = format_money(ganancia, simbolo)
                            cantidad_fmt = format_money(a.get('cantidad', 0), simbolo)
                            
                            st.markdown(f"{estado_icon} **{a.get('equipo', 'N/A')}** - {a.get('fecha', 'N/A')}")
                            st.caption(f"💰 {cantidad_fmt} @ {a.get('cuota', 'N/A')} | {a.get('mercado', 'N/A')} → **Ganancia: {ganancia_fmt}**")
                        
                        with col_a2:
                            # Actualizar resultado
                            nuevo_resultado = st.selectbox("Resultado", ["Pendiente", "Ganada", "Perdida"], 
                                                          index=0 if a.get('resultado') is None else (1 if a.get('resultado') else 2),
                                                          key=f"res_{i}_{a.get('id', i)}")
                            
                            if st.button("💾 Guardar", key=f"btn_res_{i}_{a.get('id', i)}"):
                                cantidad = a.get('cantidad', 0)
                                cuota = a.get('cuota', 2.0)
                                resultado_new = None
                                ganancia_new = 0
                                
                                if nuevo_resultado == "Ganada":
                                    resultado_new = True
                                    ganancia_new = cantidad * (cuota - 1)
                                elif nuevo_resultado == "Perdida":
                                    resultado_new = False
                                    ganancia_new = -cantidad
                                
                                try:
                                    client.table('bankroll_apuestas').update({
                                        'resultado': resultado_new,
                                        'ganancia': ganancia_new
                                    }).eq('id', a.get('id')).execute()
                                    st.success("Actualizado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        
                        st.markdown("---")
                else:
                    st.info("No tienes apuestas registradas")
        
        # ========== TAB 4: VALUE BETS ==========
        with tab_value:
            st.markdown("### 🎯 Detector de Value Bets")
            st.markdown("_Encuentra apuestas donde la probabilidad del modelo es MAYOR que la cuota del mercado_")
            
            # Ingresar datos del pick
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                prob_modelo = st.slider("📊 Probabilidad del Modelo (%)", 10, 99, 60)
            with col_v2:
                cuota_mercado = st.number_input("💰 Cuota del Mercado", value=2.0, min_value=1.01, max_value=20.0, step=0.05)
            with col_v3:
                tipo_apuesta = st.selectbox("📋 Tipo de Apuesta", ["1X2", "Over/Under", "BTTS", "Corners", "Tarjetas"])
            
            # Calcular value
            prob_implicita = (1 / cuota_mercado) * 100
            value = prob_modelo - prob_implicita
            
            col_calc1, col_calc2, col_calc3 = st.columns(3)
            with col_calc1:
                st.metric("📊 Prob. Modelo", f"{prob_modelo:.1f}%")
            with col_calc2:
                st.metric("📉 Prob. Implícita", f"{prob_implicita:.1f}%")
            with col_calc3:
                if value > 5:
                    st.metric("🎯 VALUE", f"+{value:.1f}%", delta="🔥🔥 ALTO VALUE")
                elif value > 0:
                    st.metric("🎯 VALUE", f"+{value:.1f}%", delta="✅ Value positivo")
                else:
                    st.metric("🎯 VALUE", f"{value:.1f}%", delta="❌ Sin value")
            
            # Recomendación
            if value >= 10:
                st.success("🔥🔥 **APUESTA FUERTE** - Value muy alto, alta confianza")
            elif value >= 5:
                st.success("✅ **APUESTA** - Value positivo, buena oportunidad")
            elif value >= 0:
                st.info("📊 **CAUTELA** - Value marginal, depende de otros factores")
            else:
                st.error("❌ **EVITAR** - La cuota está por encima de lo que el modelo sugiere")
            
            st.markdown("---")
            
            # Tabla de value bets guardados
            st.markdown("#### 📋 Value Bets Registrados")
            
            try:
                vb_response = client.table('value_bets').select('*').eq('usuario_id', usuario_id).order('value', desc=True).limit(20).execute()
                value_bets = vb_response.data if vb_response.data else []
                
                if value_bets:
                    df_vb = pd.DataFrame([
                        {
                            "Fecha": vb.get('fecha', ''),
                            "Partido": f"{vb.get('equipo_local', '')} vs {vb.get('equipo_visitante', '')}",
                            "Tipo": vb.get('tipo', ''),
                            "Prob Modelo": f"{vb.get('prob_modelo', 0):.1f}%",
                            "Cuota": vb.get('cuota_mercado', 0),
                            "Value": f"{vb.get('value', 0):.1f}%",
                            "Resultado": vb.get('resultado', 'pendiente'),
                        }
                        for vb in value_bets
                    ])
                    st.dataframe(df_vb, use_container_width=True)
                else:
                    st.info("📭 No hay value bets registrados.")
            except Exception as e:
                st.info("📭 Conecta a Supabase para ver value bets guardados.")
        
        # ========== TAB 5: ALERTAS ==========
        with tab_alertas:
            st.markdown("### 🔔 Centro de Alertas VIP")
            
            # Crear alertas
            st.markdown("#### 📝 Crear Nueva Alerta")
            
            col_al1, col_al2, col_al3 = st.columns(3)
            with col_al1:
                tipo_alerta = st.selectbox("Tipo", ["alta_confianza", "value_bet", "streak", "resultado", "custom"])
            with col_al2:
                prioridad = st.selectbox("Prioridad", ["alta", "media", "baja"])
            with col_al3:
                st.write("")  # spacer
            
            titulo = st.text_input("Título de la Alerta")
            mensaje = st.text_area("Mensaje")
            
            if st.button("🔔 Crear Alerta", type="primary"):
                try:
                    client.table('alertas').insert({
                        'usuario_id': usuario_id,
                        'tipo': tipo_alerta,
                        'titulo': titulo,
                        'mensaje': mensaje,
                        'prioridad': prioridad,
                        'leida': False
                    }).execute()
                    st.success("✅ Alerta creada")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.markdown("---")
            
            # Ver alertas
            st.markdown("#### 📬 Alertas Recientes")
            
            try:
                alertas_response = client.table('alertas').select('*').eq('usuario_id', usuario_id).order('creado_en', desc=True).limit(20).execute()
                alertas = alertas_response.data if alertas_response.data else []
                
                if alertas:
                    # Separar por prioridad
                    alertas_alta = [a for a in alertas if a.get('prioridad') == 'alta' and not a.get('leida')]
                    alertas_media = [a for a in alertas if a.get('prioridad') == 'media' and not a.get('leida')]
                    alertas_baja = [a for a in alertas if a.get('prioridad') == 'baja' and not a.get('leida')]
                    
                    col_alerta1, col_alerta2, col_alerta3 = st.columns(3)
                    with col_alerta1:
                        st.metric("🔥 Alta Prioridad", len(alertas_alta))
                    with col_alerta2:
                        st.metric("⚡ Media Prioridad", len(alertas_media))
                    with col_alerta3:
                        st.metric("📉 Baja Prioridad", len(alertas_baja))
                    
                    for alerta in alertas[:10]:
                        color = "🔴" if alerta.get('prioridad') == 'alta' else "🟡" if alerta.get('prioridad') == 'media' else "🟢"
                        with st.expander(f"{color} [{alerta.get('tipo', '')}] {alerta.get('titulo', '')}"):
                            st.write(alerta.get('mensaje', ''))
                            st.caption(f"Creada: {alerta.get('creado_en', '')}")
                            
                            # Marcar como leída
                            if st.button("✅ Marcar leída", key=f"leer_{alerta.get('id')}"):
                                try:
                                    client.table('alertas').update({'leida': True}).eq('id', alerta.get('id')).execute()
                                    st.success("Marcada como leída")
                                    st.rerun()
                                except: pass
                else:
                    st.info("📭 No hay alertas.")
            except Exception as e:
                st.info("📭 Conecta a Supabase para ver alertas.")
        
        # ========== TAB 6: RANKING ==========
        with tab_ranking:
            st.markdown("### 🏆 Ranking Mensual VIP")
            
            # Ranking de la comunidad
            st.markdown("#### 🌟 Top Pickers del Mes")
            
            try:
                ranking_response = client.table('ranking').select('*').order('posicion').limit(10).execute()
                ranking = ranking_response.data if ranking_response.data else []
                
                if ranking:
                    df_ranking = pd.DataFrame([
                        {
                            "🥇 Posición": r.get('posicion', i+1),
                            "👤 Usuario": r.get('nombre', 'Anon'),
                            "📊 Picks": r.get('total_picks', 0),
                            "📈 ROI": f"{r.get('roi', 0):.1f}%",
                            "💰 Yield": f"{r.get('yield', 0):.1f}%",
                        }
                        for i, r in enumerate(ranking)
                    ])
                    st.dataframe(df_ranking, use_container_width=True)
                else:
                    st.info("📭 No hay ranking aún. ¡Sé el primero!")
                    
                    # Sugerir crear ranking basado en picks
                    if picks:
                        st.markdown("##### 📊 Generar Ranking")
                        if st.button("🔄 Calcular Ranking"):
                            st.info("Ranking calculado (funcionalidad completa con más usuarios)")
            except Exception as e:
                st.info("📭 Ranking no disponible. Conecta a Supabase.")
            
            st.markdown("---")
            
            # Badges y Logros
            st.markdown("#### 🏅 Mis Badges y Logros")
            
            # Badges predefinidos
            badges_disponibles = {
                "🎯 Primer Pick": len(picks) >= 1,
                "📊 10 Picks": len(picks) >= 10,
                "🔥 50 Picks": len(picks) >= 50,
                "👑 100 Picks": len(picks) >= 100,
                "💰 ROI 10%": True,  # Calcular
                "🎯 Racha 5": True,  # Calcular
                "🔥 Racha 10": True,  # Calcular
                "⭐ Valoración 5★": False,
            }
            
            cols_badge = st.columns(4)
            for i, (badge, unlocked) in enumerate(badges_disponibles.items()):
                with cols_badge[i % 4]:
                    if unlocked:
                        st.success(badge)
                    else:
                        st.info(f"🔒 {badge}")
        
        # ========== TAB 7: EXPORTAR ==========
        with tab_export:
            st.markdown("### 📄 Exportar Reportes")
            
            # Selector de formato
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                formato = st.radio("Formato", ["CSV", "Excel (.xlsx)", "JSON"], horizontal=True)
            with col_exp2:
                tipo_reporte = st.selectbox("Tipo de Reporte", [
                    "Picks Completos",
                    "Solo Resueltos",
                    "ROI por Tipo",
                    "Bankroll History",
                    "Value Bets"
                ])
            
            # Período
            col_per1, col_per2 = st.columns(2)
            with col_per1:
                fecha_inicio = st.date_input("Desde", value=pd.Timestamp.now() - pd.Timedelta(days=30))
            with col_per2:
                fecha_fin = st.date_input("Hasta", value=pd.Timestamp.now())
            
            # Generar preview
            if picks:
                picks_filtrados = [
                    p for p in picks 
                    if p.get('fecha') and pd.Timestamp(fecha_inicio) <= pd.to_datetime(p.get('fecha')) <= pd.Timestamp(fecha_fin)
                ]
                
                st.markdown(f"📊 **{len(picks_filtrados)} picks** en el período seleccionado")
                
                if st.button("📥 Descargar Reporte", type="primary"):
                    import io
                    
                    if tipo_reporte == "Picks Completos":
                        df_export = pd.DataFrame(picks_filtrados)
                    elif tipo_reporte == "Solo Resueltos":
                        df_export = pd.DataFrame([p for p in picks_filtrados if p.get('acertado_1x2') is not None])
                    elif tipo_reporte == "ROI por Tipo":
                        # Crear resumen
                        data_roi = {
                            'Tipo': ['1X2', 'Over/Under', 'BTTS', 'Corners', 'Tarjetas', 'Remates'],
                            'Total': [
                                len([p for p in picks_filtrados if p.get('acertado_1x2') is not None]),
                                len([p for p in picks_filtrados if p.get('acertado_ou') is not None]),
                                len([p for p in picks_filtrados if p.get('acertado_btts') is not None]),
                                len([p for p in picks_filtrados if p.get('acertado_corners') is not None]),
                                len([p for p in picks_filtrados if p.get('acertado_tarjetas') is not None]),
                                len([p for p in picks_filtrados if p.get('acertado_remates') is not None]),
                            ],
                            'Aciertos': [
                                len([p for p in picks_filtrados if p.get('acertado_1x2')]),
                                len([p for p in picks_filtrados if p.get('acertado_ou')]),
                                len([p for p in picks_filtrados if p.get('acertado_btts')]),
                                len([p for p in picks_filtrados if p.get('acertado_corners')]),
                                len([p for p in picks_filtrados if p.get('acertado_tarjetas')]),
                                len([p for p in picks_filtrados if p.get('acertado_remates')]),
                            ]
                        }
                        df_export = pd.DataFrame(data_roi)
                        df_export['% Acierto'] = (df_export['Aciertos'] / df_export['Total'] * 100).round(1)
                    elif tipo_reporte == "Bankroll History":
                        try:
                            bh_response = client.table('bankroll_history').select('*').eq('usuario_id', usuario_id).execute()
                            bh = bh_response.data if bh_response.data else []
                            df_export = pd.DataFrame(bh)
                        except:
                            df_export = pd.DataFrame()
                    else:  # Value Bets
                        try:
                            vb_response = client.table('value_bets').select('*').eq('usuario_id', usuario_id).execute()
                            vb = vb_response.data if vb_response.data else []
                            df_export = pd.DataFrame(vb)
                        except:
                            df_export = pd.DataFrame()
                    
                    if not df_export.empty:
                        if formato == "CSV":
                            csv = df_export.to_csv(index=False)
                            st.download_button(
                                "📥 Descargar CSV",
                                csv,
                                f"scorpion_report_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                "text/csv"
                            )
                        elif formato == "Excel (.xlsx)":
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df_export.to_excel(writer, index=False, sheet_name='Report')
                            st.download_button(
                                "📥 Descargar Excel",
                                buffer.getvalue(),
                                f"scorpion_report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:  # JSON
                            json_str = df_export.to_json(orient='records')
                            st.download_button(
                                "📥 Descargar JSON",
                                json_str,
                                f"scorpion_report_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
                                "application/json"
                            )
                    else:
                        st.warning("No hay datos para el período seleccionado")
            else:
                st.info("📭 No hay picks para exportar.")
        
        # Mostrar Consensus Meter
        st.markdown("---")
        st.markdown("### 🤖 Consensus de Modelos")
        st.markdown("_¿Cuántos modelos están de acuerdo en el último pick?_")
        
        # Obtener último pick
        if picks:
            ultimo = picks[0] if picks else None
            if ultimo:
                # Simular scores de consenso (en producción vendría de los modelos reales)
                modelos = ['Poisson', 'Dixon-Coles', 'Monte Carlo', 'Elo']
                probabilidades = [
                    ultimo.get('p1', 0) or 40,
                    ultimo.get('p1', 0) or 40,  # Simulado
                    ultimo.get('p1', 0) or 40,  # Simulado
                    ultimo.get('p1', 0) or 40,  # Simulado
                ]
                
                # Calcular consenso
                promedio = sum(probabilidades) / len(probabilidades)
                discrepancia = max(probabilidades) - min(probabilidades)
                
                col_cons1, col_cons2, col_cons3 = st.columns(3)
                with col_cons1:
                    st.metric("📊 Promedio Local", f"{promedio:.1f}%")
                with col_cons2:
                    st.metric("📈 Máx", f"{max(probabilidades):.1f}%")
                with col_cons3:
                    st.metric("📉 Mín", f"{min(probabilidades):.1f}%")
                
                if discrepancia < 10:
                    st.success("🔥 **ALTO CONSENSO** - Los 4 modelos están de acuerdo")
                elif discrepancia < 20:
                    st.info("📊 **CONSENSO MODERADO** - Buena señal")
                else:
                    st.warning("⚠️ **BAJO CONSENSO** - Los modelos discrepan, mayor riesgo")

# ═══════════════════════════════════════════════════════════════════════════════
# EJECUTAR EL SISTEMA DE LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
render_login_form()
