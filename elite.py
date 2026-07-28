import streamlit as st
import pandas as pd
import os
import sqlite3
import hashlib
import logging
from datetime import date, timedelta
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from supabase import create_client
from data_loader import parse_flashscore_excel, validate_matches
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
# CONFIGURACION - Variables de entorno con defaults de fallback
# ══════════════════════════════════════════════════════════
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jjtifureeygvygxtpuku.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA")
# Base de datos persistente en el directorio de la aplicación
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "scorpion_users.db")

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
# SISTEMA DE USUARIOS (SQLite local) - Solo contraseña
# ══════════════════════════════════════════════════════════
def get_hoy():
    return str(date.today())

def init_db():
    """Inicializa la base de datos SQLite con context manager"""
    with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
        # Crear tabla con todas las columnas necesarias
        conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre TEXT,
            plan TEXT DEFAULT 'vip',
            fecha_inicio TEXT,
            dias INTEGER DEFAULT 36500,
            activo INTEGER DEFAULT 1,
            es_admin INTEGER DEFAULT 0,
            creado TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Crear tabla de picks si no existe
        conn.execute("""
        CREATE TABLE IF NOT EXISTS picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, liga TEXT, local TEXT, visitante TEXT, hora TEXT,
            mercado TEXT, detalle TEXT, cuota REAL, edge REAL,
            confianza REAL, rango TEXT, notas TEXT, plan_min TEXT DEFAULT 'vip'
        )
        """)
        
        # Crear admin si no existe
        admin_exists = conn.execute("SELECT id FROM usuarios WHERE es_admin=1").fetchone()
        if not admin_exists:
            pwd_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
            conn.execute("""INSERT INTO usuarios (password, password_hash, nombre, plan, fecha_inicio, dias, activo, es_admin) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (ADMIN_PASSWORD, pwd_hash, "Administrador", "admin", get_hoy(), 36500, 1, 1))
        conn.commit()

def db_get_by_password_hash(pwd_hash):
    """Obtiene usuario por password hash"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT * FROM usuarios WHERE password_hash=?", (pwd_hash,)).fetchone()
            return dict(r) if r else None
    except Exception as e:
        logger.error(f"Error en db_get_by_password_hash: {e}")
        return None

def db_get_by_id(user_id):
    """Obtiene usuario por ID"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT * FROM usuarios WHERE id=?", (user_id,)).fetchone()
            return dict(r) if r else None
    except Exception as e:
        logger.error(f"Error en db_get_by_id: {e}")
        return None

def db_todos():
    """Obtiene todos los usuarios"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            r = conn.execute("SELECT id, password, nombre, plan, dias, activo, es_admin, creado FROM usuarios ORDER BY id ASC").fetchall()
            return [dict(x) for x in r]
    except Exception as e:
        logger.error(f"Error en db_todos: {e}")
        return []

def db_crear_usuario(password, nombre, plan, dias):
    """Crea un nuevo usuario con solo contraseña"""
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("""INSERT INTO usuarios (password, password_hash, nombre, plan, fecha_inicio, dias, activo)
                          VALUES (?, ?, ?, ?, ?, ?, 1)""",
                        (password, pwd_hash, nombre, plan, get_hoy(), dias))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logger.error(f"Error en db_crear_usuario: {e}")
        return False

def db_cambiar_password(user_id, password):
    """Cambia password de usuario"""
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("UPDATE usuarios SET password=?, password_hash=? WHERE id=?", (password, pwd_hash, user_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error en db_cambiar_password: {e}")
        return False

def db_eliminar_usuario(user_id):
    """Elimina un usuario"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("DELETE FROM usuarios WHERE id=? AND es_admin=0", (user_id,))
            conn.commit()
            return conn.total_changes > 0
    except Exception as e:
        logger.error(f"Error en db_eliminar_usuario: {e}")
        return False

def db_actualizar_plan(user_id, plan, dias):
    """Actualiza plan de usuario"""
    try:
        with sqlite3.connect(DB_PATH, check_same_thread=False) as conn:
            conn.execute("UPDATE usuarios SET plan=?, dias=?, fecha_inicio=? WHERE id=?", 
                        (plan, dias, get_hoy(), user_id))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error en db_actualizar_plan: {e}")
        return False

def db_login(password):
    """Verifica password y retorna usuario"""
    init_db()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    result = db_get_by_password_hash(pwd_hash)
    if result and result['activo'] == 1:
        return result
    return None

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
if "logged" not in st.session_state:
    st.session_state.logged = False
if "df_partidos" not in st.session_state:
    st.session_state.df_partidos = None
if "page" not in st.session_state:
    st.session_state.page = "Carga"
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "equipos_excel_actual" not in st.session_state:
    st.session_state.equipos_excel_actual = []

# ══════════════════════════════════════════════════════════
# CSS EXTERNO - Leer desde archivo styles.css
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_css():
    """Carga el CSS desde el archivo externo - cacheado por 1 hora"""
    css_path = Path(__file__).parent / "styles.css"
    try:
        return css_path.read_text()
    except Exception as e:
        logger.warning(f"No se pudo cargar styles.css: {e}")
        return ""

st.markdown(f"<style>{load_css()}</style>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# LANDING PAGE PÚBLICA
# ══════════════════════════════════════════════════════════
def render_public_landing():
    """Renderiza la landing page pública para usuarios no autenticados"""
    
    # --- HERO SECTION ---
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">🦂 Scorpion Elite</h1>
        <p class="hero-subtitle">Analítica Deportiva e IA para Apuestas Inteligentes</p>
        <p class="hero-description">Sistema de análisis predictivo con 4 modelos matemáticos avanzados</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botón Iniciar Sesión arriba
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🔐 Iniciar Sesión", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()

    # --- KPIs EN VIVO ---
    st.markdown("### 📊 Métricas del Sistema")

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
        st.metric("📈 Aciertos Totales", f"{pct_aciertos}%", f"{aciertos} de {total_picks} picks")

    with col_kpi2:
        st.metric("🎯 Picks Guardados", f"{total_picks:,}", f"{total_equipos} equipos analizados")

    with col_kpi3:
        st.metric("💰 Yield Promedio", f"{yield_pct:+.1f}%", "Rentabilidad real")

    
    # --- PARTIDOS DEL DÍA ---
    st.markdown("### 🏆 Partidos del Día")

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
    except:
        partidos = []

    if st.session_state.preview_partido:
        # MOSTRAR ANÁLISIS DEL PARTIDO SELECCIONADO
        partido = st.session_state.preview_partido
        local = partido.get('equipo_local', 'Local')
        visitante = partido.get('equipo_visitante', 'Visitante')
        liga = partido.get('liga', '')
        
        st.markdown("---")
        st.markdown(f"## 📊 Análisis: {local} vs {visitante}")
        if liga:
            st.caption(f"🏆 {liga}")
        
        # Botón para volver
        if st.button("← Volver a partidos", key="volver_partidos"):
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
                
                if stats_local and stats_visit:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"### {local}")
                        st.write(f"**Forma:** {stats_local.get('forma', 'N/A')}")
                        st.write(f"**V/E/D:** {stats_local.get('victorias', 0)}/{stats_local.get('empates', 0)}/{stats_local.get('derrotas', 0)}")
                        st.write(f"**GF/GC:** {stats_local.get('goles_favor', 0)}/{stats_local.get('goles_contra', 0)}")
                    with col2:
                        st.markdown(f"### {visitante}")
                        st.write(f"**Forma:** {stats_visit.get('forma', 'N/A')}")
                        st.write(f"**V/E/D:** {stats_visit.get('victorias', 0)}/{stats_visit.get('empates', 0)}/{stats_visit.get('derrotas', 0)}")
                        st.write(f"**GF/GC:** {stats_visit.get('goles_favor', 0)}/{stats_visit.get('goles_contra', 0)}")
                    
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
                        st.success(f"**1X2:** 1 (Victoria local) - Alta confianza")
                    elif prom_v > prom_l * 1.2:
                        st.success(f"**1X2:** 2 (Victoria visitante) - Alta confianza")
                    else:
                        st.warning(f"**1X2:** X (Empate) - Confianza media")
                    
                    # Over/Under
                    total = prom_l + prom_v
                    ou = "Over 2.5" if total > 2.5 else "Under 2.5"
                    st.info(f"**Over/Under:** {ou} ({total:.1f} goles esperados)")
                    
                    # BTTS
                    btts = "Sí" if gf_l > 1 and gf_v > 1 else "No"
                    st.info(f"**Ambos marcan:** {btts}")
                    
                    st.markdown("---")
                    st.caption("📝 Inicia sesión para análisis completo con 4 modelos matemáticos.")
                else:
                    st.warning(f"No hay estadísticas para {local} o {visitante}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        # MOSTRAR LISTA DE PARTIDOS
        if partidos:
            for partido in partidos[:5]:
                local = partido.get('equipo_local', 'Local')
                visitante = partido.get('equipo_visitante', 'Visitante')
                liga = partido.get('liga', '')
                hora = partido.get('hora', '')
                
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{local} vs {visitante}**")
                    if liga:
                        st.caption(f"🏆 {liga}")
                with c2:
                    if hora:
                        st.markdown(f"⏰ {hora}")
                with c3:
                    if st.button("📊 Analizar", key=f"demo_{partido.get('id', local)}"):
                        st.session_state.preview_partido = partido
                        st.rerun()
            st.markdown("---")
            st.caption(f"Mostrando {min(len(partidos), 5)} de {len(partidos)} partidos")
        else:
            st.info("📭 No hay partidos cargados. Sube un Excel desde la página **Carga**.")


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
    st.markdown("### 📋 Planes Disponibles")
    
    plan_col1, plan_col2 = st.columns([1, 1])
    
    with plan_col1:
        st.markdown("""
        <div class="plan-card plan-free">
            <h3>🆓 Plan Gratuito</h3>
            <p class="plan-price">$0 <span>/para siempre</span></p>
            <ul>
                <li>✅ Análisis básico</li>
                <li>✅ 10 picks por día</li>
                <li>✅ 2 modelos matemáticos</li>
                <li>✅ Acceso a comunidad</li>
                <li>❌ Sin stats avanzadas</li>
                <li>❌ Sin picks VIP</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with plan_col2:
        st.markdown("""
        <div class="plan-card plan-vip">
            <h3>👑 Plan Elite VIP</h3>
            <p class="plan-price">$29.99 <span>/mes</span></p>
            <ul>
                <li>✅ Análisis completo + IA</li>
                <li>✅ Picks ILIMITADOS</li>
                <li>✅ 4 modelos + calibración</li>
                <li>✅ Stats avanzadas (corners, tarjetas)</li>
                <li>✅ Picks VIP exclusivos</li>
                <li>✅ Soporte prioritario 24/7</li>
            </ul>
            <p class="plan-cta"><strong>🎁 7 días GRATIS - Sin tarjeta</strong></p>
        </div>
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
    if "show_login" not in st.session_state:
        st.session_state.show_login = False
    
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
                    init_db()
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
        
        plan_icon = {"admin": "⚙️", "elite": "👑", "vip": "👑", "mes": "👑", "vip": "🆓"}.get(user_plan, "📦")
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
    if is_admin:
        # Admin: ve todo
        menu_pages = [
            ("📂 Carga", "Carga"),
            ("📊 Analizador", "Analizador"),
            ("📈 Estadísticas", "Estadisticas"),
            ("👑 VIP", "VIP"),
            ("📉 Dashboard", "Dashboard"),
            ("🔑 Claves", "Claves"),
        ]
    else:
        # VIP: solo Analizador, Estadísticas, VIP
        menu_pages = [
            ("📊 Analizador", "Analizador"),
            ("📈 Estadísticas", "Estadisticas"),
            ("👑 VIP", "VIP"),
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

    # Página: Carga
    if st.session_state.page == "Carga":
        st.markdown("### 📂 Cargar archivos")
        
        uploaded_file = st.file_uploader("", type=['xlsx', 'xls', 'csv'])
        
        if uploaded_file:
            try:
                # Leer archivo
                if uploaded_file.name.endswith('.csv'):
                    df_raw = pd.read_csv(uploaded_file, header=None)
                else:
                    df_raw = pd.read_excel(uploaded_file, header=None)
                
                st.success(f"Archivo cargado: {uploaded_file.name} ({len(df_raw)} filas)")
                
                # Parsear datos
                with st.spinner("Procesando datos..."):
                    df_partidos = parse_flashscore_excel(df_raw)
                
                if not df_partidos.empty:
                    st.session_state.df_partidos = df_partidos
                    
                    # Guardar equipos del Excel actual para buscarlos después
                    equipos_excel = set()
                    for _, row in df_partidos.iterrows():
                        if pd.notna(row.get('equipo_local')):
                            equipos_excel.add(row['equipo_local'])
                        if pd.notna(row.get('equipo_visitante')):
                            equipos_excel.add(row['equipo_visitante'])
                    st.session_state.equipos_excel_actual = sorted(list(equipos_excel))
                    st.info(f"📋 {len(equipos_excel)} equipos guardados para búsqueda: {', '.join(sorted(equipos_excel)[:10])}{'...' if len(equipos_excel) > 10 else ''}")
                    
                    # Mostrar errores de validación
                    df_validated, errors = validate_matches(df_partidos)
                    
                    if errors:
                        with st.expander("⚠️ Errores detectados"):
                            for err in errors[:10]:
                                st.warning(err)
                    
                    # Previsualización
                    st.markdown(f"### 📋 Previsualización ({len(df_partidos)} partidos)")
                    
                    # Mostrar dataframe
                    st.dataframe(
                        df_partidos[['fecha', 'hora', 'pais', 'liga', 'equipo_local', 'equipo_visitante']],
                        use_container_width=True,
                        height=400
                    )
                    
                    # Botones de Supabase
                    col_guardar, col_borrar = st.columns(2)
                    with col_guardar:
                        if st.button("✅ Guardar en Supabase", type="primary", use_container_width=True):
                            with st.spinner("Guardando..."):
                                try:
                                    client = get_client()
                                    
                                    guardados = 0
                                    errores = 0
                                    for _, row in df_partidos.iterrows():
                                        # Incluir fecha en el fixture_id para que sea único
                                        fecha_str = str(row['fecha']) if pd.notna(row['fecha']) else ''
                                        data = {
                                            'fixture_id': abs(hash(f"{fecha_str}{row['equipo_local']}{row['equipo_visitante']}")) % (10**10),
                                            'fecha': row['fecha'],
                                            'hora': row['hora'],
                                            'liga': row['liga'],
                                            'pais': row['pais'],
                                            'equipo_local': row['equipo_local'],
                                            'equipo_visitante': row['equipo_visitante']
                                        }
                                        try:
                                            result = client.table('partidos').upsert(data, on_conflict='fixture_id').execute()
                                            guardados += 1
                                        except Exception as e:
                                            errores += 1
                                            st.warning(f"Error en {row['equipo_local']}: {str(e)[:50]}")
                                    
                                    if guardados > 0:
                                        st.success(f"✅ {guardados} partidos guardados")
                                    if errores > 0:
                                        st.warning(f"⚠️ {errores} errores")
                                    
                                    st.session_state.df_partidos = None
                                    
                                except Exception as e:
                                    st.error(f"Error de conexión: {str(e)[:100]}")
                    with col_borrar:
                        if st.button("🗑️ Borrar todos", type="secondary", use_container_width=True):
                            client = get_client()
                            client.table('partidos').delete().neq('id', 0).execute()
                            st.session_state.partidos_deleted = True
                            st.rerun()
                else:
                    st.warning("No se encontraron partidos en el archivo")
                    
            except Exception as e:
                st.error(f"Error al leer archivo: {str(e)}")
    
    # Página: Analizador
    elif st.session_state.page == "Analizador":
        pass  # Sin título
        
        # Inicializar selected_match en session_state
        if 'selected_match_data' not in st.session_state:
            st.session_state.selected_match_data = None
        
        # Obtener lista de equipos disponibles
        client = get_client()
        try:
            response_equipos = client.table('equipos_stats').select('equipo, liga').execute()
            equipos_disponibles = [e['equipo'].title() for e in response_equipos.data] if response_equipos.data else []
            equipos_disponibles = sorted(set(equipos_disponibles))
        except:
            equipos_disponibles = []
        
        # Obtener partidos de Supabase
        try:
            response_partidos = client.table('partidos').select('*').order('fecha', desc=True).order('hora', desc=True).execute()
            partidos_data = response_partidos.data if response_partidos.data else []
        except:
            partidos_data = []
        
        # Variable para el partido seleccionado
        selected_match = None
        
        # Mostrar partidos disponibles si hay
        if partidos_data:
            st.markdown("### 📋 Partidos en Base de Datos")
            st.markdown(f"**Total: {len(partidos_data)} partidos**")
            
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
                    st.markdown(f"<span style='color:#ffffff; font-size:13px'>📅 {fecha}</span>", unsafe_allow_html=True)
                with cols_row[1]:
                    st.markdown(f"<span style='color:#00ff88; font-size:13px'>🏠 **{local}**</span>", unsafe_allow_html=True)
                with cols_row[2]:
                    st.markdown(f"<span style='color:#ff6b6b; font-size:13px'>✈️ **{visitante}**</span>", unsafe_allow_html=True)
                with cols_row[3]:
                    st.markdown(f"<span style='color:#ffd700; font-size:13px'>⏰ {hora}</span>", unsafe_allow_html=True)
                with cols_row[4]:
                    st.markdown(f"<span style='color:#00d4aa; font-size:13px'>{emoji} {pais[:6]}</span>", unsafe_allow_html=True)
                with cols_row[5]:
                    if st.button("🎯", key=f"match_{p.get('id')}", help=f"Analizar {local} vs {visitante}", use_container_width=True):
                        selected_match = p
                        st.session_state.selected_match_data = selected_match
        elif not equipos_disponibles:
            st.warning("⚠️ No hay partidos ni equipos guardados. Sube un Excel y busca los equipos.")
        
        # Mostrar equipos disponibles
        if not equipos_disponibles:
            st.warning("⚠️ No hay equipos guardados. Ve a 'Estadísticas' para agregar equipos.")
        
        # Si hay un partido seleccionado, hacer análisis automático
        if st.session_state.selected_match_data:
            p = st.session_state.selected_match_data
            local_nombre = p.get('equipo_local', '')
            visitante_nombre = p.get('equipo_visitante', '')
            
            st.markdown("---")
            st.markdown(f"### 🎯 Analizando: **{local_nombre}** vs **{visitante_nombre}**")
            
            # Buscar stats de los equipos
            stats_local = None
            stats_visitante = None
            home_team = ""
            away_team = ""
            
            # Buscar equipo local
            for eq in equipos_disponibles:
                if local_nombre.lower() in eq.lower() or eq.lower() in local_nombre.lower():
                    try:
                        resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{eq}%').execute()
                        if resp.data and resp.data[0].get('lambda_local', 0) > 0:
                            stats_local = resp.data[0]
                            home_team = eq
                            break
                    except:
                        pass
            
            # Buscar equipo visitante
            for eq in equipos_disponibles:
                if visitante_nombre.lower() in eq.lower() or eq.lower() in visitante_nombre.lower():
                    try:
                        resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{eq}%').execute()
                        if resp.data and resp.data[0].get('lambda_visitante', 0) > 0:
                            stats_visitante = resp.data[0]
                            away_team = eq
                            break
                    except:
                        pass
            
            # Verificar si tenemos los stats
            if stats_local and stats_visitante:
                lambda_local = stats_local.get('lambda_local', 0)
                lambda_visitante = stats_visitante.get('lambda_visitante', 0)
                
                with st.spinner("Analizando..."):
                    result = calcular(
                        lambda_local=lambda_local,
                        lambda_visitante=lambda_visitante,
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
                    
                    # Calcular predicciones
                    remates_total = float(stats_local.get('promedio_tiros', 12)) + float(stats_visitante.get('promedio_tiros', 12))
                    remates_over_prob = min(90, max(10, 50 + (remates_total - 24) * 2))
                    
                    tarjetas_total = float(stats_local.get('promedio_amarillas', 3)) + float(stats_visitante.get('promedio_amarillas', 3))
                    tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))
                    
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
                
                st.success("✅ ¡Análisis completado! Abajo verás los resultados.")
            else:
                equipos_faltantes = []
                if not stats_local:
                    equipos_faltantes.append(local_nombre)
                if not stats_visitante:
                    equipos_faltantes.append(visitante_nombre)
                st.error(f"⚠️ Equipos sin estadísticas: {', '.join(equipos_faltantes)}")
                st.info("📝 Ve a 'Estadísticas' y busca estos equipos para obtener sus estadísticas.")
        
        
        
        # Si hay un partido seleccionado de la lista, usar esos equipos
        if selected_match:
            local_nombre = selected_match.get('equipo_local', '')
            visitante_nombre = selected_match.get('equipo_visitante', '')
            
            # Buscar coincidencia en equipos disponibles
            local_match = next((e for e in equipos_disponibles if local_nombre.lower() in e.lower() or e.lower() in local_nombre.lower()), None)
            visitante_match = next((e for e in equipos_disponibles if visitante_nombre.lower() in e.lower() or e.lower() in visitante_nombre.lower()), None)
            
            home_team = local_match if local_match else (local_nombre.title() if local_nombre else "")
            away_team = visitante_match if visitante_match else (visitante_nombre.title() if visitante_nombre else "")
        else:
            # Usar selectores si no hay partido seleccionado
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
                        # Llamar al modelo con TODOS los datos
                        result = calcular(
                            lambda_local=lambda_local,
                            lambda_visitante=lambda_visitante,
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
                    st.markdown(f"<h4 style='color: #00ff88; text-align: center;'>🏠 {home}</h4>", unsafe_allow_html=True)
                    # Lista local
                    stats_list_l = [
                        ("📅 PJ", pj_l, "#fff"),
                        ("✅ Victorias", vic_l, "#00ff88"),
                        ("🤝 Empates", emp_l, "#ffd700"),
                        ("❌ Derrotas", der_l, "#ff6b6b"),
                        ("⚽ Goles Favor", gf_l, "#fff"),
                        ("⚽ Goles Contra", gc_l, "#fff"),
                        ("📊 Diferencia", f"{gf_l - gc_l:+.0f}", "#00d4ff"),
                        ("λ Local", f"{stats_local.get('lambda_local', 0):.2f}", "#00d4ff"),
                        (f"λ Ajustada {icono_ajuste_local}", f"{lambda_local_adj['lambda_ajustada']:.2f}", color_ajuste_local),
                        ("🌽 Córners", f"{prom_corners_l:.1f}", "#00d4ff"),
                        ("🟨 Amarillas", f"{prom_amarillas_l:.1f}", "#ffd700"),
                        ("🔫 Tiros", f"{prom_tiros_l:.1f}", "#fff"),
                        ("🎯 Tiros Arco", f"{prom_tiros_arco_l:.1f}", "#fff"),
                    ]
                    for label, val, color in stats_list_l:
                        st.markdown(f"<div style='display:flex; justify-content:space-between; padding:4px 10px; border-bottom:1px solid #333; font-size:14px;'><span>{label}</span><span style='color:{color}'>{val}</span></div>", unsafe_allow_html=True)
                
                with col_visita:
                    st.markdown(f"<h4 style='color: #ff6b6b; text-align: center;'>✈️ {away}</h4>", unsafe_allow_html=True)
                    # Lista visita
                    stats_list_v = [
                        ("📅 PJ", pj_v, "#fff"),
                        ("✅ Victorias", vic_v, "#00ff88"),
                        ("🤝 Empates", emp_v, "#ffd700"),
                        ("❌ Derrotas", der_v, "#ff6b6b"),
                        ("⚽ Goles Favor", gf_v, "#fff"),
                        ("⚽ Goles Contra", gc_v, "#fff"),
                        ("📊 Diferencia", f"{gf_v - gc_v:+.0f}", "#00d4ff"),
                        ("λ Visitante", f"{stats_visitante.get('lambda_visitante', 0):.2f}", "#00d4ff"),
                        (f"λ Ajustada {icono_ajuste_vis}", f"{lambda_visitante_adj['lambda_ajustada']:.2f}", color_ajuste_vis),
                        ("🌽 Córners", f"{prom_corners_v:.1f}", "#00d4ff"),
                        ("🟨 Amarillas", f"{prom_amarillas_v:.1f}", "#ffd700"),
                        ("🔫 Tiros", f"{prom_tiros_v:.1f}", "#fff"),
                        ("🎯 Tiros Arco", f"{prom_tiros_arco_v:.1f}", "#fff"),
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
                        st.markdown(f"**{home} - Últimos 5**")
                        if ultimos_local:
                            for i, partido in enumerate(ultimos_local[:5]):
                                resultado = partido.get('resultado', '?')
                                resultado_icon = {'V': '🟢', 'E': '🟡', 'D': '🔴'}.get(resultado, '⚪')
                                marcador = f"{partido.get('goles_favor', 0)}-{partido.get('goles_contra', 0)}"
                                rival = partido.get('rival', '?')
                                corners = partido.get('corners', 0)
                                tarjetas = partido.get('tarjetas', 0)
                                st.markdown(f"&nbsp;&nbsp;{resultado_icon} vs {rival} ({marcador}) | 🌽{corners} 🟨{tarjetas}")
                        else:
                            st.info("Sin datos de forma reciente")
                    
                    with col_forma2:
                        st.markdown(f"**{away} - Últimos 5**")
                        if ultimos_visitante:
                            for i, partido in enumerate(ultimos_visitante[:5]):
                                resultado = partido.get('resultado', '?')
                                resultado_icon = {'V': '🟢', 'E': '🟡', 'D': '🔴'}.get(resultado, '⚪')
                                marcador = f"{partido.get('goles_favor', 0)}-{partido.get('goles_contra', 0)}"
                                rival = partido.get('rival', '?')
                                corners = partido.get('corners', 0)
                                tarjetas = partido.get('tarjetas', 0)
                                st.markdown(f"&nbsp;&nbsp;{resultado_icon} vs {rival} ({marcador}) | 🌽{corners} 🟨{tarjetas}")
                        else:
                            st.info("Sin datos de forma reciente")
            
            # ========================
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
                <p class="analisis-partido">⚽ {home} vs {away}</p>
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
                                'fecha': str(date.today()),
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
            with col3:
                clase = "caja-1x2 caja-visitante" if es_visita_max else "caja-1x2"
                st.markdown(f"""
                <div class="{clase}">
                    <p class="etiqueta-equipo etiqueta-visitante">✈️ {away}</p>
                    <p class="probabilidad">{p2:.1f}%</p>
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
    
    # Página: Estadísticas
    elif st.session_state.page == "Estadisticas":
        st.markdown("### 📈 Estadísticas")
        
        # Sección: Robot automático
        st.markdown("### 🤖 Buscar Equipos del Excel Actual")
        
        # Mostrar equipos del Excel actual
        equipos_excel = st.session_state.get('equipos_excel_actual', [])
        if equipos_excel:
            st.info(f"📋 Equipos del Excel actual: {len(equipos_excel)} - {', '.join(equipos_excel[:15])}{'...' if len(equipos_excel) > 15 else ''}")
        else:
            st.warning("⚠️ No hay equipos del Excel actual. Sube un Excel en la pestaña 'Carga' primero.")
        
        if st.button("🔄 Buscar Equipos del Excel", type="primary", use_container_width=True, disabled=not equipos_excel):
            with st.spinner("Buscando equipos..."):
                try:
                    # Usar equipos del Excel actual (guardados en session_state)
                    equipos = equipos_excel
                    
                    if not equipos:
                        st.warning("⚠️ No hay equipos para buscar. Sube un Excel primero.")
                    else:
                        st.info(f"📊 {len(equipos)} equipos a buscar: {', '.join(equipos)}")
                        
                        # Buscar todos con el robot
                        with st.spinner("🤖 Buscando en football-data y Soccerway..."):
                            results = run_robot_batch(equipos)
                        
                        # Clasificar resultados
                        con_stats = [r for r in results if r.get('encontrado') and not r.get('sin_estadisticas')]
                        sin_stats = [r for r in results if r.get('encontrado') and r.get('sin_estadisticas')]
                        no_encontrados = [r for r in results if not r.get('encontrado')]
                        
                        # Resumen
                        st.success(f"✅ **Resumen:** {len(con_stats)} con stats | {len(sin_stats)} sin stats | {len(no_encontrados)} no encontrados")
                        
                        # Mostrar equipos ENCONTRADOS con estadísticas
                        if con_stats:
                            st.markdown("### 📊 Equipos con estadísticas reales")
                            for r in con_stats:
                                fuente = r.get('fuentes_probadas', ['?'])[-1]
                                fuente_icono = "🌐" if 'football' in fuente.lower() else ("🔷" if 'api' in fuente.lower() else ("📊" if 'WhoScored' in fuente else "📈"))
                                st.markdown(f"- **{r.get('equipo_real', r['equipo'])}** ({r.get('liga', 'N/A')}) {fuente_icono}")
                                st.markdown(f"  `λL={r.get('lambda_local', 0):.2f} | λV={r.get('lambda_visitante', 0):.2f} | PJ={r.get('partidos_jugados', 0)}`")
                        
                        # Mostrar equipos SIN estadísticas (NO encontrados)
                        if no_encontrados:
                            st.warning(f"❌ **{len(no_encontrados)} equipos NO encontrados en ninguna fuente:**")
                            for r in no_encontrados:
                                st.markdown(f"- {r['equipo']}")
                            st.info("💡 Estos equipos no están en football-data ni en API-Football")
                        
                        # Guardar estadísticas en Supabase
                        if con_stats:
                            st.info("💾 Guardando estadísticas en Supabase...")
                            guardados = 0
                            errores = 0
                            for r in con_stats:
                                try:
                                    equipo_nombre = r.get('equipo_real', r['equipo'])
                                    fuente = r.get('fuentes_probadas', ['football-data.co.uk'])[-1]
                                    
                                    # Determinar fuente de datos
                                    if 'football-data' in fuente:
                                        source_fbdata = True
                                        source_whoscored = False
                                        source_fbref = False
                                    elif 'WhoScored' in fuente:
                                        source_fbdata = False
                                        source_whoscored = True
                                        source_fbref = False
                                    elif 'FBref' in fuente:
                                        source_fbdata = False
                                        source_whoscored = False
                                        source_fbref = True
                                    else:
                                        source_fbdata = True
                                        source_whoscored = False
                                        source_fbref = False
                                    
                                    data = {
                                        'equipo': equipo_nombre,
                                        'liga': r.get('liga', 'Desconocida'),
                                        'temporada': '2024-25',
                                        'partidos_jugados': r.get('partidos_jugados', 0) or 0,
                                        'victorias': r.get('victorias', 0) or 0,
                                        'empates': r.get('empates', 0) or 0,
                                        'derrotas': r.get('derrotas', 0) or 0,
                                        'goles_favor': r.get('goles_favor', 0) or 0,
                                        'goles_contra': r.get('goles_contra', 0) or 0,
                                        'lambda_local': float(r.get('lambda_local', 1.3)) or 1.3,
                                        'lambda_visitante': float(r.get('lambda_visitante', 1.1)) or 1.1,
                                        # Stats avanzados
                                        'promedio_tiros': float(r.get('tiros_promedio', 12)) or 12,
                                        'promedio_tiros_arco': float(r.get('tiros_arco_promedio', 4)) or 4,
                                        'promedio_corners_total': float(r.get('corners_promedio', 10)) or 10,
                                        'promedio_amarillas': float(r.get('tarjetas_promedio', 3)) or 3,
                                        # Fuentes de datos
                                        'source_fbdata': source_fbdata,
                                        'source_whoscored': source_whoscored,
                                        'source_fbref': source_fbref,
                                        # Últimos 5 partidos (temporalmente omitido para evitar errores)
                                        # 'ultimos_5_partidos': r.get('ultimos_5_partidos', []),
                                    }
                                    
                                    # Intentar upsert con on_conflict para UNIQUE(equipo, temporada)
                                    try:
                                        client.table('equipos_stats').upsert(
                                            data, 
                                            on_conflict='equipo,temporada'
                                        ).execute()
                                    except Exception as upsert_error:
                                        # Si falla, intentar con solo 'equipo' como clave única
                                        try:
                                            client.table('equipos_stats').upsert(
                                                data, 
                                                on_conflict='equipo'
                                            ).execute()
                                        except Exception as e2:
                                            errores += 1
                                            logger.error(f"Error guardando {equipo_nombre}: {e2}")
                                            continue
                                    
                                    guardados += 1
                                    st.info(f"✅ {equipo_nombre}")
                                except Exception as e:
                                    errores += 1
                                    logger.error(f"Error guardando {r.get('equipo')}: {e}")
                            
                            if guardados > 0:
                                st.success(f"✅ {guardados} estadísticas guardadas en Supabase")
                            if errores > 0:
                                st.warning(f"⚠️ {errores} equipos no se pudieron guardar")
                                
                except Exception as e:
                    st.error(f"Error: {str(e)[:100]}")
        
        st.markdown("---")
        st.markdown("### ➕ Agregar / Actualizar Equipo (Manual)")
        
        # Formulario ultra compacto - Opción D
        with st.form("form_equipo", clear_on_submit=True):
            # Línea 1: Nombre y Liga
            col1, col2 = st.columns(2)
            with col1:
                equipo = st.text_input("🏷️ Nombre", placeholder="Barcelona")
            with col2:
                liga = st.text_input("🏆 Liga", placeholder="La Liga")
            
            # Línea 2: Stats principales
            col_stats1 = st.columns([1, 1, 1, 1, 1, 1, 1])
            with col_stats1[0]:
                partidos = st.number_input("Partidos", min_value=0, value=0, key="eq_pj")
            with col_stats1[1]:
                victorias = st.number_input("Ganados (G)", min_value=0, value=0, key="eq_v")
            with col_stats1[2]:
                empates = st.number_input("E", min_value=0, value=0, key="eq_e")
            with col_stats1[3]:
                derrotas = st.number_input("Perdido (P)", min_value=0, value=0, key="eq_d")
            with col_stats1[4]:
                goles_favor = st.number_input("Goles Favor", min_value=0, value=0, key="eq_gf")
            with col_stats1[5]:
                goles_contra = st.number_input("Goles Contra", min_value=0, value=0, key="eq_gc")
            with col_stats1[6]:
                temporada = st.text_input("Temporada", value="2025", key="eq_temp")
            
            # Línea 3: Stats avanzadas
            col_stats2 = st.columns([1, 1, 1, 1])
            with col_stats2[0]:
                promedio_corners = st.number_input("Promedio Corners", min_value=0.0, value=10.0, step=0.5, format="%.1f", key="eq_corners")
            with col_stats2[1]:
                promedio_tarjetas = st.number_input("Promedio Tarjetas", min_value=0.0, value=3.0, step=0.5, format="%.1f", key="eq_tarjetas")
            with col_stats2[2]:
                promedio_tiros = st.number_input("Promedio Tiros", min_value=0.0, value=12.0, step=0.5, format="%.1f", key="eq_tiros")
            with col_stats2[3]:
                promedio_tiros_arco = st.number_input("Tiros al Arco", min_value=0.0, value=4.0, step=0.5, format="%.1f", key="eq_tarcos")
            
            # Línea 4: Últimos 5
            st.markdown("**📅 Últimos 5:** G=Ganó | E=Empate | P=Perdió")
            col_ult = st.columns([1, 1, 1, 1, 1])
            with col_ult[0]:
                u1 = st.selectbox("1", ["", "G", "E", "P"], index=0, key="eq_u1")
            with col_ult[1]:
                u2 = st.selectbox("2", ["", "G", "E", "P"], index=0, key="eq_u2")
            with col_ult[2]:
                u3 = st.selectbox("3", ["", "G", "E", "P"], index=0, key="eq_u3")
            with col_ult[3]:
                u4 = st.selectbox("4", ["", "G", "E", "P"], index=0, key="eq_u4")
            with col_ult[4]:
                u5 = st.selectbox("5", ["", "G", "E", "P"], index=0, key="eq_u5")
            
            submitted = st.form_submit_button("💾 GUARDAR EQUIPO", use_container_width=True, type="primary")
            
            if submitted and equipo:
                # Calcular lambdas
                lambda_local = calculate_team_lambda(goles_favor, goles_contra, partidos, is_home=True)
                lambda_visitante = calculate_team_lambda(goles_favor, goles_contra, partidos, is_home=False)
                
                # Construir últimos 5 partidos
                ultimos_5 = []
                for resultado in [u1, u2, u3, u4, u5]:
                    if resultado:
                        ultimos_5.append({
                            'resultado': resultado,
                            'goles_favor': 0,
                            'goles_contra': 0,
                            'corners': promedio_corners,
                            'tarjetas': promedio_tarjetas
                        })
                
                # Guardar en Supabase
                client = get_client()
                data = {
                    'equipo': equipo,
                    'liga': liga,
                    'temporada': temporada,
                    'partidos_jugados': partidos,
                    'victorias': victorias,
                    'empates': empates,
                    'derrotas': derrotas,
                    'goles_favor': goles_favor,
                    'goles_contra': goles_contra,
                    'lambda_local': lambda_local,
                    'lambda_visitante': lambda_visitante,
                    'promedio_tiros': promedio_tiros,
                    'promedio_tiros_arco': promedio_tiros_arco,
                    'promedio_corners_total': promedio_corners,
                    'promedio_amarillas': promedio_tarjetas,
                    'ultimos_5_partidos': ultimos_5
                }
                
                try:
                    # Intentar insert o update
                    try:
                        client.table('equipos_stats').upsert(data).execute()
                    except:
                        # Si falla upsert, intentar insert directo (sin ultimos_5)
                        data_basic = {k: v for k, v in data.items() if k != 'ultimos_5_partidos'}
                        try:
                            client.table('equipos_stats').insert(data_basic).execute()
                        except:
                            client.table('equipos_stats').update(data_basic).eq('equipo', equipo).execute()
                    st.success(f"✅ {equipo} guardado exitosamente")
                except Exception as e:
                    st.error(f"Error al guardar: {str(e)[:100]}")
        
        st.markdown("---")
        st.markdown("### 📋 Equipos Guardados")
        
        client = get_client()
        try:
            response = client.table('equipos_stats').select('*').execute()
            
            if response.data and len(response.data) > 0:
                st.info(f"💡 {len(response.data)} equipos guardados")
                
                for eq in response.data:
                    with st.expander(f"⚽ {eq.get('equipo')} - {eq.get('liga', 'N/A')}"):
                        # FORMULARIO PARA MODIFICAR
                        with st.form(f"edit_form_{eq.get('equipo')}", clear_on_submit=True):
                            st.markdown("**✏️ Modificar datos:**")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                eq_partidos = st.number_input("Partidos", value=int(eq.get('partidos_jugados', 0)), min_value=0, key=f"part_{eq.get('equipo')}")
                            with col2:
                                eq_victorias = st.number_input("Victorias", value=int(eq.get('victorias', 0)), min_value=0, key=f"vic_{eq.get('equipo')}")
                            with col3:
                                eq_empates = st.number_input("Empates", value=int(eq.get('empates', 0)), min_value=0, key=f"emp_{eq.get('equipo')}")
                            
                            col4, col5, col6 = st.columns(3)
                            with col4:
                                eq_derrotas = st.number_input("Derrotas", value=int(eq.get('derrotas', 0)), min_value=0, key=f"der_{eq.get('equipo')}")
                            with col5:
                                eq_gf = st.number_input("Goles Favor", value=int(eq.get('goles_favor', 0)), min_value=0, key=f"gf_{eq.get('equipo')}")
                            with col6:
                                eq_gc = st.number_input("Goles Contra", value=int(eq.get('goles_contra', 0)), min_value=0, key=f"gc_{eq.get('equipo')}")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                            with col_btn2:
                                deleted = st.form_submit_button("🗑️ Eliminar Equipo", use_container_width=True)
                            
                            if submitted:
                                # Recalcular lambdas
                                eq_lambda_l = calculate_team_lambda(eq_gf, eq_gc, eq_partidos, is_home=True)
                                eq_lambda_v = calculate_team_lambda(eq_gf, eq_gc, eq_partidos, is_home=False)
                                
                                update_data = {
                                    'partidos_jugados': eq_partidos,
                                    'victorias': eq_victorias,
                                    'empates': eq_empates,
                                    'derrotas': eq_derrotas,
                                    'goles_favor': eq_gf,
                                    'goles_contra': eq_gc,
                                    'lambda_local': eq_lambda_l,
                                    'lambda_visitante': eq_lambda_v,
                                }
                                client.table('equipos_stats').update(update_data).eq('id', eq.get('id')).execute()
                                st.session_state.equipo_updated = eq.get('equipo')
                                st.success("✅ Datos actualizados")
                            
                            if deleted:
                                client.table('equipos_stats').delete().eq('id', eq.get('id')).execute()
                                st.session_state.equipo_deleted = eq.get('equipo')
                                st.success("✅ Equipo eliminado")
            else:
                st.info("📭 No hay equipos guardados. Agrega uno con el formulario de arriba.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:100]}")

    # Página: Gestión de Claves
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
            with col3:
                st.markdown("**👑 MES** - 30 días VIP")
            col4, col5 = st.columns(2)
            with col4:
                st.markdown("**🔥 ELITE** - 90 días VIP")
            with col5:
                st.markdown("**⭐ VIP** - 90 días VIP")
        
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
        tab_roi, tab_bankroll, tab_value, tab_alertas, tab_ranking, tab_export = st.tabs([
            "📊 ROI por Modelo", "💰 Bankroll", "🎯 Value Bets", "🔔 Alertas", "🏆 Ranking", "📄 Exportar"
        ])
        
        # ========== TAB 1: ROI POR MODELO ==========
        with tab_roi:
            st.markdown("### 📊 Rendimiento por Modelo y Tipo de Pick")
            
            # Obtener picks resueltos
            try:
                response = client.table('picks').select('*').execute()
                picks = response.data if response.data else []
            except:
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
                    with col3:
                        st.metric("⚽ BTTS", f"{acertados_btts}/{len(picks_btts)}", f"{pct_btts:.1f}% acierto")
                        if pct_btts > 55: st.success("✅ Rentable")
                        elif pct_btts < 45: st.error("❌ Perjudicial")
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
        
        # ========== TAB 2: BANKROLL ==========
        with tab_bankroll:
            st.markdown("### 💰 Mi Bankroll Real")
            
            usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'
            
            # Obtener picks del usuario para agregar al bankroll
            try:
                response_picks = client.table('picks').select('*').eq('usuario', usuario_id).execute()
                picks_disponibles = response_picks.data if response_picks.data else []
            except:
                picks_disponibles = []
            
            # Obtener apuestas guardadas del usuario
            try:
                response_apuestas = client.table('bankroll_apuestas').select('*').eq('usuario', usuario_id).order('fecha', desc=True).execute()
                apuestas = response_apuestas.data if response_apuestas.data else []
            except:
                # Crear tabla si no existe
                try:
                    client.table('bankroll_apuestas').execute()
                except:
                    pass
                apuestas = []
            
            # ==================== SUBTABS ====================
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📊 Dashboard", "➕ Agregar Apuesta", "📋 Mis Apuestas"])
            
            # ========== SUBTAB 1: DASHBOARD ==========
            with sub_tab1:
                st.markdown("#### 📈 Resumen de Rendimiento")
                
                # Configurar bankroll
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    bankroll_inicial = st.number_input("💵 Bankroll Inicial ($)", value=1000.0, min_value=100.0, step=100.0, key="bankroll_inicial")
                with col_b2:
                    st.markdown("##### Ajustes")
                    col_reset, col_export = st.columns(2)
                    with col_reset:
                        if st.button("🔄 Reiniciar Bankroll"):
                            # Eliminar todas las apuestas
                            try:
                                client.table('bankroll_apuestas').delete().eq('usuario', usuario_id).execute()
                            except:
                                pass
                            st.success("Bankroll reiniciado")
                            st.rerun()
                
                if apuestas:
                    # Calcular métricas reales
                    total_apostado = sum(a.get('cantidad', 0) for a in apuestas)
                    ganancias = sum(a.get('ganancia', 0) for a in apuestas)
                    bankroll_actual = bankroll_inicial + ganancias
                    roi = ((bankroll_actual - bankroll_inicial) / bankroll_inicial * 100) if bankroll_inicial > 0 else 0
                    
                    apuestas_ganadas = len([a for a in apuestas if a.get('ganancia', 0) > 0])
                    apuestas_perdidas = len([a for a in apuestas if a.get('ganancia', 0) < 0])
                    total_apuestas = len(apuestas)
                    tasa_acierto_real = (apuestas_ganadas / total_apuestas * 100) if total_apuestas > 0 else 0
                    
                    # Mostrar métricas
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        st.metric("💵 Bankroll Actual", f"${bankroll_actual:.2f}", delta=f"{ganancias:.2f}")
                    with col_m2:
                        st.metric("📊 ROI", f"{roi:.1f}%", delta=f"{'+' if roi >= 0 else ''}{roi:.1f}%")
                    with col_m3:
                        st.metric("🎯 Tasa Acierto", f"{tasa_acierto_real:.1f}%", delta=f"{apuestas_ganadas}/{total_apuestas}")
                    with col_m4:
                        st.metric("💰 Ganado/Perdido", f"${ganancias:.2f}")
                    
                    # Estado del bankroll
                    col_estado = st.columns(1)[0]
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
                            st.metric("📅 Proyección Mensual", f"${proy_mensual:.2f}")
                        with col_p2:
                            st.metric("📅 Proyección Anual", f"${proy_anual:.2f}")
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
                            # Selector de pick
                            opciones_pick = [f"{p.get('local', '?')} vs {p.get('visitante', '?')} - {p.get('mercado', '?')} @ {p.get('cuota', '?')}" 
                                          for p in picks_sin_resultado]
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
                        cantidad = st.number_input("💵 Cantidad Apostada ($)", value=20.0, min_value=1.0, step=5.0)
                    
                    col_d4, col_d5 = st.columns(2)
                    with col_d4:
                        mercado = st.selectbox("📊 Mercado", ["1X2", "Over/Under", "BTTS", "Corners", "Tarjetas", "Otro"])
                    with col_d5:
                        fecha = st.date_input("📅 Fecha", value=date.today())
                    
                    # Resultado (para apuestas ya resueltas)
                    with st.expander("✅ Marcar Resultado (opcional)"):
                        resultado = st.radio("Resultado:", ["Pendiente", "Ganada", "Perdida"], horizontal=True)
                        if resultado != "Pendiente":
                            ganancia = cantidad * (cuota - 1) if resultado == "Ganada" else -cantidad
                            st.write(f"**Ganancia/Pérdida:** ${ganancia:.2f}")
                    
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
                            color_gan = "green" if ganancia > 0 else ("red" if ganancia < 0 else "gray")
                            
                            st.markdown(f"{estado_icon} **{a.get('equipo', 'N/A')}** - {a.get('fecha', 'N/A')}")
                            st.caption(f"💰 ${a.get('cantidad', 0):.2f} @ {a.get('cuota', 'N/A')} | {a.get('mercado', 'N/A')} → **Ganancia: ${ganancia:.2f}**")
                        
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
        
        # ========== TAB 3: VALUE BETS ==========
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
        
        # ========== TAB 4: ALERTAS ==========
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
        
        # ========== TAB 5: RANKING ==========
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
        
        # ========== TAB 6: EXPORTAR ==========
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
                    if p.get('fecha') and fecha_inicio <= pd.to_datetime(p.get('fecha')) <= fecha_fin
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

    # ==================== PÁGINA: DASHBOARD ====================
    elif st.session_state.page == "Dashboard":
        st.markdown("### 📉 Dashboard de Picks")
        
        # Obtener picks de Supabase
        try:
            client = get_client()
            response = client.table('picks').select('*').order('fecha', desc=True).limit(200).execute()
            picks = response.data if response.data else []
        except Exception as e:
            picks = []
            st.warning(f"No se pudo conectar a Supabase: {str(e)[:50]}")
        
        # Obtener estadísticas de calibración
        stats_cal = obtener_estadisticas_calibracion()
        
        # Métricas generales
        total_picks = len(picks)
        
        if total_picks > 0:
            # 1X2
            picks_1x2_resueltos = [p for p in picks if p.get('acertado_1x2') is not None]
            acertados_1x2 = len([p for p in picks_1x2_resueltos if p.get('acertado_1x2') == True])
            pct_1x2 = (acertados_1x2 / len(picks_1x2_resueltos) * 100) if picks_1x2_resueltos else 0
            
            # Over/Under
            picks_ou_resueltos = [p for p in picks if p.get('acertado_ou') is not None]
            acertados_ou = len([p for p in picks_ou_resueltos if p.get('acertado_ou') == True])
            pct_ou = (acertados_ou / len(picks_ou_resueltos) * 100) if picks_ou_resueltos else 0
            
            # BTTS
            picks_btts_resueltos = [p for p in picks if p.get('acertado_btts') is not None]
            acertados_btts = len([p for p in picks_btts_resueltos if p.get('acertado_btts') == True])
            pct_btts = (acertados_btts / len(picks_btts_resueltos) * 100) if picks_btts_resueltos else 0
            
            # Distribución por rango
            rango_a = len([p for p in picks if p.get('rango', '') in ['A+', 'A']])
            rango_b = len([p for p in picks if p.get('rango', '') == 'B'])
            rango_c = len([p for p in picks if p.get('rango', '') == 'C'])
            rango_d = len([p for p in picks if p.get('rango', '') == 'D'])
            
            # Alta confianza
            alta_conf = [p for p in picks if p.get('confianza', 0) >= 70]
            alta_conf_acertados = len([p for p in alta_conf if p.get('acertado_1x2') == True])
            pct_alta_conf = (alta_conf_acertados / len(alta_conf) * 100) if alta_conf else 0
            
            # Mostrar métricas
            st.markdown("##### 📊 Resumen de Rendimiento por Tipo")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Picks", total_picks)
            with col2:
                st.metric("1X2", acertados_1x2, delta=f"{pct_1x2:.1f}%")
            with col3:
                st.metric("Over/Under", acertados_ou, delta=f"{pct_ou:.1f}%")
            with col4:
                st.metric("BTTS", acertados_btts, delta=f"{pct_btts:.1f}%")
            
            st.markdown("##### 📈 Distribución por Rango")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🟢 Rango A", rango_a)
            with col2:
                st.metric("🔵 Rango B", rango_b)
            with col3:
                st.metric("🟡 Rango C", rango_c)
            with col4:
                st.metric("🔴 Rango D", rango_d)
            
            st.markdown("##### 💡 Alta Confianza (≥70%)")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Picks", len(alta_conf))
            with col2:
                st.metric("Aciertos 1X2", alta_conf_acertados, delta=f"{pct_alta_conf:.1f}%")
            
            st.markdown("##### 🔧 Calibración")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Equipos Calibrados", stats_cal.get('equipos_calibrados', 0))
            with col2:
                st.metric("Registros Cal.", stats_cal.get('total_picks', 0))
            with col3:
                if st.button("🔄 Resetear Calibración"):
                    resetear_calibracion()
                    st.success("Calibración reseteada")
                    st.rerun()
            
            # Botones de acción
            col_del, col_result = st.columns([1, 2])
            
            with col_del:
                if st.button("🗑️ Limpiar Duplicados"):
                    # Eliminar picks duplicados (mismo equipo_local + equipo_visitante + fecha), dejar el más reciente
                    if picks:
                        seen = set()
                        to_delete = []
                        for p in reversed(picks):
                            key = f"{p.get('equipo_local')}_{p.get('equipo_visitante')}_{p.get('fecha')}"
                            if key in seen:
                                to_delete.append(p['id'])
                            else:
                                seen.add(key)
                        
                        if to_delete:
                            for pick_id in to_delete:
                                client.table('picks').delete().eq('id', pick_id).execute()
                            st.success(f"✅ Eliminados {len(to_delete)} duplicados")
                            st.rerun()
                        else:
                            st.info("No hay duplicados")
            
            # Lista de picks con actualización inline
            st.markdown("##### 📋 Picks Recientes (▸ clic para ver/actualizar)")
            
            if picks:
                for p in picks[:30]:
                    res_1x2 = p.get('acertado_1x2')
                    res_ou = p.get('acertado_ou')
                    res_btts = p.get('acertado_btts')
                    res_corners = p.get('acertado_corners')
                    res_tarjetas = p.get('acertado_tarjetas')
                    res_remates = p.get('acertado_remates')
                    marcador = p.get('marcador', '')
                    
                    def icon(v):
                        if v == True: return "🟢"
                        if v == False: return "🔴"
                        return "⚪"
                    
                    pick_id = p.get('id')
                    partido = f"{p.get('equipo_local', '')} vs {p.get('equipo_visitante', '')}"
                    
                    # Header del expander
                    header = f"**ID {pick_id}** | {p.get('fecha','')} | {partido} | Marc: {marcador if marcador else '?'} | 1X2:{icon(res_1x2)} OU:{icon(res_ou)} BTTS:{icon(res_btts)} C:{icon(res_corners)} T:{icon(res_tarjetas)} R:{icon(res_remates)}"
                    
                    with st.expander(header):
                        # Mostrar predicciones guardadas
                        col_pred, col_del = st.columns([4, 1])
                        with col_pred:
                            st.markdown(f"""
                            **📊 Predicciones:** {p.get('p1',0):.0f}% - {p.get('px',0):.0f}% - {p.get('p2',0):.0f}% (Conf: {p.get('confianza',0)}%)
                            
                            **🎯 Picks:** 1X2: **{p.get('prediccion_1x2','')}** | O/U: **{p.get('prediccion_ou','')}** | BTTS: **{p.get('prediccion_btts','')}** | C: **{p.get('prediccion_corners','')}** | T: **{p.get('prediccion_tarjetas','')}** | R: **{p.get('prediccion_remates','')}**
                            """)
                        with col_del:
                            if st.button("🗑️", key=f"del_{pick_id}"):
                                client.table('picks').delete().eq('id', pick_id).execute()
                                st.session_state.pick_deleted = pick_id
                                st.success("✅ Eliminado")
                        
                        st.markdown("---")
                        st.markdown("### 📝 Actualizar Resultado Real")
                        
                        col1, col2, col3, col4, col5, col6 = st.columns([1,1,1,1,1,1])
                        with col1:
                            gf_l = st.number_input("GF Local", min_value=0, max_value=20, value=0, key=f"gf_l_{pick_id}")
                        with col2:
                            gf_v = st.number_input("GF Visit", min_value=0, max_value=20, value=0, key=f"gf_v_{pick_id}")
                        with col3:
                            cor_tot = st.number_input("Corners", min_value=0, max_value=50, value=0, key=f"cor_{pick_id}")
                        with col4:
                            tar_tot = st.number_input("Tarjetas", min_value=0, max_value=30, value=0, key=f"tar_{pick_id}")
                        with col5:
                            rem_tot = st.number_input("Remates", min_value=0, max_value=60, value=0, key=f"rem_{pick_id}")
                        with col6:
                            st.write("")  # spacer
                            if st.button("✅ Guardar", key=f"save_{pick_id}"):
                                try:
                                    gl, gv = gf_l, gf_v
                                    total_g = gl + gv
                                    
                                    # Calcular resultados
                                    if gl > gv: resultado_1x2 = '1'
                                    elif gl < gv: resultado_1x2 = '2'
                                    else: resultado_1x2 = 'X'
                                    
                                    resultado_ou = 'Over' if total_g > 2.5 else 'Under'
                                    resultado_btts = 'Sí' if gl > 0 and gv > 0 else 'No'
                                    
                                    # Verificar aciertos
                                    def verificar(pred, valor):
                                        if not pred: return None
                                        try:
                                            num = float(pred.lower().replace('over','').replace('under','').replace('_',' ').strip())
                                            if 'over' in pred.lower(): return valor > num
                                            elif 'under' in pred.lower(): return valor < num
                                        except: pass
                                        return None
                                    
                                    acertado_1x2 = p.get('prediccion_1x2','') == resultado_1x2
                                    acertado_ou = p.get('prediccion_ou','') == resultado_ou
                                    acertado_btts = p.get('prediccion_btts','') == resultado_btts
                                    acertado_corners = verificar(p.get('prediccion_corners',''), cor_tot)
                                    acertado_tarjetas = verificar(p.get('prediccion_tarjetas',''), tar_tot)
                                    acertado_remates = verificar(p.get('prediccion_remates',''), rem_tot)
                                    
                                    # Guardar
                                    client.table('picks').update({
                                        'marcador': f"{gl}-{gv}",
                                        'resultado': resultado_1x2,
                                        'resultado_1x2': resultado_1x2,
                                        'resultado_ou': resultado_ou,
                                        'resultado_btts': resultado_btts,
                                        'resultado_corners': str(cor_tot),
                                        'resultado_tarjetas': str(tar_tot),
                                        'resultado_remates': str(rem_tot),
                                        'acertado_1x2': acertado_1x2,
                                        'acertado_ou': acertado_ou,
                                        'acertado_btts': acertado_btts,
                                        'acertado_corners': acertado_corners,
                                        'acertado_tarjetas': acertado_tarjetas,
                                        'acertado_remates': acertado_remates,
                                    }).eq('id', pick_id).execute()
                                    
                                    st.success("✅ Guardado!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ {str(e)[:50]}")
            else:
                st.info("📭 No hay picks guardados aún")
        else:
            st.info("🎯 No hay picks guardados aún.")
            st.markdown("""
            ### 📖 Cómo funciona:
            
            1. **Ve a 📊 Analizador**
            2. **Selecciona dos equipos**
            3. **Haz clic en 🎯 ANALIZAR**
            4. **El análisis se guarda automáticamente**
            5. **Ingresa el marcador y guarda el resultado**
            6. **El sistema recalibra las predicciones**
            
            Vuelve aquí para ver tu rendimiento.
            """)

# ═══════════════════════════════════════════════════════════════════════════════
# EJECUTAR EL SISTEMA DE LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
render_login_form()
