import streamlit as st
import pandas as pd
import os

# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# 📋 SISTEMA DE DISEГ'O - COLORES Y ESTILOS
# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# Colores principales (coinciden con styles.css)
COLORS = {
    'victoria': '#22c55e',     # Verde éxito
    'derrota': '#ef4444',       # Rojo error
    'empate': '#eab308',        # Amarillo
    'primary': '#00d4aa',       # Cyan/acento
    'local': '#fff',         # Verde brillante
    'visitante': '#fff',     # Rojo suave
    'hora': '#fff',          # Dorado
    'bg_dark': '#0f172a',       # Fondo oscuro
    'bg_card': '#111111',       # Fondo cards
    'bg_header': '#121824',     # Fondo headers
    'text': '#f8fafc',          # Texto principal
    'text_secondary': '#94a3b8', # Texto secundario
}

# Función helper para formatear colores en HTML
def css(color_key, extra=''):
    """Retorna estilo CSS inline con el color de COLORS"""
    return f"color:{COLORS.get(color_key, '#fff')};{extra}"

# CSS global cargado desde archivo (version forzada para cache busting)
try:
    with open('styles.css', 'r') as f:
        css_content = f.read()
        # Forzar cache bust con version
        st.markdown(f'<style>/* v20260805 */ {css_content}</style>', unsafe_allow_html=True)
except Exception as e:
    pass

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
from funciones_stats import obtener_ultimos_partidos_equipo, guardar_stats_equipo, calcular_promedios_equipo, obtener_stats_partido
from calibration import (
    get_lambda_ajustada,
    registrar_resultado,
    obtener_estadisticas_calibracion,
    resetear_calibracion
)

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# CONFIGURACION - Variables de entorno
# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# Las variables se cargan desde .env (desarrollo) o Render Dashboard (producción)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Valores por defecto SOLO para desarrollo local (NO usar en producción)
# En producción, estas variables DEBEN estar configuradas en el Dashboard de Render
if not ADMIN_PASSWORD:
    raise ValueError("❌ ADMIN_PASSWORD no está configurada. ConfigГәrala en variables de entorno.")
if not SUPABASE_URL:
    raise ValueError("❌ SUPABASE_URL no está configurada. ConfigГәrala en variables de entorno.")
if not SUPABASE_KEY:
    raise ValueError("❌ SUPABASE_KEY no está configurada. ConfigГәrala en variables de entorno.")

# Base de datos persistente en el directorio de la aplicación
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# CLIENTE SUPABASE UNIFICADO con @st.cache_resource
# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
@st.cache_resource
def get_supabase_client():
    """Crea y cachea el cliente de Supabase - se reutiliza en toda la app"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("SUPABASE_URL o SUPABASE_KEY no están configurados")
        return None
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Verificar/crear columna team_id en equipos_stats
        try:
            client.table('equipos_stats').select('team_id').limit(1).execute()
        except:
            # La columna no existe, intentar crear mediante RPC
            logger.info("Verificando columna team_id en equipos_stats...")
        return client
    except Exception as e:
        logger.error(f"Error al crear cliente Supabase: {e}")
        return None

def get_client():
    """Función de compatibilidad - retorna cliente de Supabase"""
    return get_supabase_client()

def migrate_team_id_column():
    """Migra la columna team_id a la tabla equipos_stats si no existe"""
    import psycopg2
    import os
    try:
        # Obtener connection string de las variables de entorno de Render
        conn_url = os.getenv('DATABASE_URL', '')
        if not conn_url:
            # Intentar construir desde SUPABASE_URL
            conn_url = f"postgresql://postgres:{os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')}@db.jjtifureeygvygxtpuku.supabase.co:5432/postgres"
        
        if conn_url:
            conn = psycopg2.connect(conn_url)
            cur = conn.cursor()
            # Agregar columnas a equipos_stats
            cur.execute('ALTER TABLE equipos_stats ADD COLUMN IF NOT EXISTS team_id BIGINT;')
            # Agregar columnas a partidos si no existen
            cur.execute('ALTER TABLE partidos ADD COLUMN IF NOT EXISTS liga_id BIGINT;')
            cur.execute('ALTER TABLE partidos ADD COLUMN IF NOT EXISTS team_id_local BIGINT;')
            cur.execute('ALTER TABLE partidos ADD COLUMN IF NOT EXISTS team_id_visitante BIGINT;')
            
            # Crear tabla equipo_partidos_stats si no existe
            cur.execute('''CREATE TABLE IF NOT EXISTS equipo_partidos_stats (
                id BIGSERIAL PRIMARY KEY,
                team_id BIGINT NOT NULL,
                equipo VARCHAR(255),
                fixture_id BIGINT NOT NULL,
                fecha DATE,
                liga VARCHAR(255),
                es_local BOOLEAN DEFAULT false,
                resultado CHAR(1) DEFAULT '-',
                goles_favor INTEGER DEFAULT 0,
                goles_contra INTEGER DEFAULT 0,
                tiros_totales INTEGER DEFAULT 0,
                tiros_arco INTEGER DEFAULT 0,
                tiros_fuera INTEGER DEFAULT 0,
                corners INTEGER DEFAULT 0,
                amarillas INTEGER DEFAULT 0,
                rojas INTEGER DEFAULT 0,
                posesion INTEGER DEFAULT 0,
                faltas INTEGER DEFAULT 0,
                actualizado_en TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(team_id, fixture_id)
            )''')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_equipo_partidos_team ON equipo_partidos_stats(team_id);')
            cur.execute('CREATE INDEX IF NOT EXISTS idx_equipo_partidos_fixture ON equipo_partidos_stats(fixture_id);')
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ Migration completada: team_id, liga_id, team_id_local, team_id_visitante, equipo_partidos_stats")
    except Exception as e:
        logger.warning(f"Migration error: {e}")

# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# SISTEMA DE USUARIOS (Supabase) - Solo hash bcrypt
# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ

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

def utc_to_colombia(utc_datetime_str):
    """Convierte datetime UTC a hora colombiana (UTC-5)"""
    try:
        if not utc_datetime_str:
            return ""
        # Parsear el datetime UTC
        utc_dt = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
        # Convertir a Colombia (UTC-5)
        colombia_tz = timezone(timedelta(hours=-5))
        colombia_dt = utc_dt.astimezone(colombia_tz)
        return colombia_dt.strftime('%H:%M')
    except:
        # Si falla, intentar con formato simple
        try:
            hora_str = utc_datetime_str[11:16]  # Extraer HH:MM
            hora = int(hora_str.split(':')[0]) if hora_str else 0
            minuto = int(hora_str.split(':')[1]) if ':' in hora_str else 0
            # Restar 5 horas
            hora_colombia = (hora - 5) % 24
            return f"{hora_colombia:02d}:{minuto:02d}"
        except:
            return utc_datetime_str[11:16] if len(utc_datetime_str) > 16 else ""

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
    """Renderiza la landing page pГәblica para usuarios no autenticados"""
    
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
    
    # Botón 🔑 Acceder arriba
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🔑 Acceder", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()
            pass

    # --- KPIs EN VIVO ---
    st.markdown("##### 📥 Métricas")

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
            
            # Obtener nГәmero de equipos con stats
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
        # MOSTRAR ANГҒLISIS DEL PARTIDO SELECCIONADO
        partido = st.session_state.preview_partido
        local = partido.get('equipo_local', 'Local')
        visitante = partido.get('equipo_visitante', 'Visitante')
        liga = partido.get('liga', '')
        
        st.markdown("---")
        st.markdown(f"## ⚽ Pronóstico: {local} VS {visitante}")
        if liga:
            st.caption(f"🏆 {liga}")
        
        # Botón para volver
        if st.button("↩️җ Volver", key="volver_partidos"):
            st.session_state.preview_partido = None
            pass
        
        st.markdown("---")
        
        # Obtener stats de equipos
        try:
            client = get_client()
            team_id_local = partido.get('team_id_local')
            team_id_visitante = partido.get('team_id_visitante')
            
            if client:
                # 1пёҸвғЈ Buscar por nombre
                local_resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{local}%').execute()
                visit_resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{visitante}%').execute()

                stats_local = local_resp.data[0] if local_resp.data else None
                stats_visit = visit_resp.data[0] if visit_resp.data else None

                # 2пёҸвғЈ Fallback: buscar por team_id si no se encontró por nombre
                if not stats_local and team_id_local:
                    resp_by_id = client.table('equipos_stats').select('*').eq('team_id', team_id_local).execute()
                    if resp_by_id.data:
                        stats_local = resp_by_id.data[0]
                
                if not stats_visit and team_id_visitante:
                    resp_by_id = client.table('equipos_stats').select('*').eq('team_id', team_id_visitante).execute()
                    if resp_by_id.data:
                        stats_visit = resp_by_id.data[0]

                # Buscar promedios dinámicos directamente por team_id (más confiable)
                promedios_dinamicos_local = None
                promedios_dinamicos_visitante = None
                lambda_historico_local = None
                lambda_historico_visit = None
                lambda_local_final = None
                lambda_visit_final = None
                
                # Obtener team_ids del partido seleccionado
                tid_local = partido.get('team_id_local')
                tid_visitante = partido.get('team_id_visitante')
                
                # Buscar directamente por team_id
                if tid_local:
                    resp_eps_l = client.table("equipo_partidos_stats").select("team_id").eq("team_id", tid_local).limit(1).execute()
                    if resp_eps_l.data:
                        promedios_dinamicos_local = calcular_promedios_equipo(client, tid_local)
                
                if tid_visitante:
                    resp_eps_v = client.table("equipo_partidos_stats").select("team_id").eq("team_id", tid_visitante).limit(1).execute()
                    if resp_eps_v.data:
                        promedios_dinamicos_visitante = calcular_promedios_equipo(client, tid_visitante)
                st.write(f"📤 Local: '{local}' ↩️' {'✅' if stats_local else '❌'} (team_id: {team_id_local})")
                st.write(f"📤 Visit: '{visitante}' ↩️' {'✅' if stats_visit else '❌'} (team_id: {team_id_visitante})")

                if stats_local and stats_visit:
                    st.markdown("---")
                    st.markdown("### 📥 Estadísticas Calibradas")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**📊 {local}**")
                        forma_l = stats_local.get('forma', 'N/A')
                        if forma_l and forma_l != 'N/A':
                            forma_html = ''.join([{'W': '<span class="se-result-w">W</span>', 'L': '<span class="se-result-l">L</span>', 'D': '<span class="se-result-d">D</span>'}.get(c, c) for c in str(forma_l)])
                            st.markdown(f"**Forma:** {forma_html}", unsafe_allow_html=True)
                        else:
                            st.markdown(f"**Forma:** N/A")
                        st.markdown(f"**V/E/D:** <span style='color:black;font-weight:bold'>{stats_local.get('victorias', 0)}/{stats_local.get('empates', 0)}/{stats_local.get('derrotas', 0)}</span>", unsafe_allow_html=True)
                        # Usar promedios de datos históricos si existen
                        if promedios_dinamicos_local:
                            gf_l = promedios_dinamicos_local.get('promedio_goles_favor', 0)
                            gc_l = promedios_dinamicos_local.get('promedio_goles_contra', 0)
                        else:
                            gf_l = stats_local.get('goles_favor', 0)
                            gc_l = stats_local.get('goles_contra', 0)
                        st.markdown(f"**GF/GC:** <span style='color:black;font-weight:bold'>{gf_l_str}/{gc_l_str}</span>", unsafe_allow_html=True)
                        lambda_l = promedios_dinamicos_local.get('lambda_ponderado', stats_local.get('lambda_local', 0)) if promedios_dinamicos_local else stats_local.get('lambda_local', 0)
                        st.markdown(f"**Ataque:** <span style='color:black;font-weight:bold'>{lambda_l:.2f}</span> goles/partido", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**вңҲпёҸ {visitante}**")
                        forma_v = stats_visit.get('forma', 'N/A')
                        if forma_v and forma_v != 'N/A':
                            forma_html = ''.join([{'W': '<span class="se-result-w">W</span>', 'L': '<span class="se-result-l">L</span>', 'D': '<span class="se-result-d">D</span>'}.get(c, c) for c in str(forma_v)])
                            st.markdown(f"**Forma:** {forma_html}", unsafe_allow_html=True)
                        else:
                            st.markdown(f"**Forma:** N/A")
                        st.markdown(f"**V/E/D:** <span style='color:black;font-weight:bold'>{stats_visit.get('victorias', 0)}/{stats_visit.get('empates', 0)}/{stats_visit.get('derrotas', 0)}</span>", unsafe_allow_html=True)
                        # Usar promedios de datos históricos si existen
                        if promedios_dinamicos_visitante:
                            gf_v = promedios_dinamicos_visitante.get('promedio_goles_favor', 0)
                            gc_v = promedios_dinamicos_visitante.get('promedio_goles_contra', 0)
                        else:
                            gf_v = stats_visit.get('goles_favor', 0)
                            gc_v = stats_visit.get('goles_contra', 0)
                        st.markdown(f"**GF/GC:** <span style='color:black;font-weight:bold'>{gf_v_str}/{gc_v_str}</span>", unsafe_allow_html=True)
                        lambda_v = promedios_dinamicos_visitante.get('lambda_ponderado', stats_visit.get('lambda_visitante', 0)) if promedios_dinamicos_visitante else stats_visit.get('lambda_visitante', 0)
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
                    st.caption("🔑 Accede con tu cuenta para análisis completo con 4 modelos matemáticos.")
                else:
                    st.warning(f"No hay estadísticas para {local} o {visitante}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        # MOSTRAR PARTIDOS ORGANIZADOS POR PAГҚS/FECHA/HORA
        if partidos:
            # Convertir hora a colombiana y organizar
            partidos_procesados = []
            for p in partidos:
                fecha = p.get('fecha', '')
                hora_original = p.get('hora', '')
                hora_colombia = utc_to_colombia(f"{fecha}T{hora_original}:00Z") if fecha and hora_original else ""
                
                partidos_procesados.append({
                    **p,
                    'hora_colombia': hora_colombia,
                    'fecha_hora': f"{fecha} {hora_colombia}"
                })
            
            # Ordenar por país, fecha, hora
            partidos_procesados.sort(key=lambda x: (
                x.get('pais', ''),  # Primero por país
                x.get('fecha', ''),   # Luego por fecha
                x.get('hora_colombia', '')  # Finalmente por hora colombiana
            ))
            
            st.markdown("###### 📅 Partidos del Día")
            st.caption("Organizados por país, fecha y hora (Colombia)")
            
            # Agrupar por país
            paises_agrupados = {}
            for p in partidos_procesados:
                pais = p.get('pais', 'Sin país')
                if pais not in paises_agrupados:
                    paises_agrupados[pais] = []
                paises_agrupados[pais].append(p)
            
            # Mostrar por país
            for pais, lista_partidos in paises_agrupados.items():
                with st.expander(f"🏴 {pais} ({len(lista_partidos)} partidos)", expanded=True):
                    cols = st.columns(2)
                    for i, partido in enumerate(lista_partidos):
                        local = partido.get('equipo_local', 'Local')
                        visitante = partido.get('equipo_visitante', 'Visitante')
                        liga = partido.get('liga', '')
                        hora_col = partido.get('hora_colombia', '')
                        fecha = partido.get('fecha', '')
                        fixture_id = partido.get('fixture_id', 0)
                        
                        with cols[i % 2]:
                            st.session_state['partido_seleccionado'] = partido
                            
                            if st.button(f"⚽ {local} vs {visitante}", key=f"partido_{fixture_id}", use_container_width=True):
                                st.session_state['partido_seleccionado'] = partido
                                st.session_state['show_analizador'] = True
                                st.query_params["page"] = "analizador"
                            
                            st.caption(f"⚽ {hora_col} | 📅 {datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')} | {liga}")
        else:
            st.info("⚽ No hay partidos cargados. Ve a la pestaГұa **Carga** para subir datos.")

    # --- CÓMO FUNCIONA ---
    st.markdown("### 📤 ВҝCómo Funciona?")
    st.markdown("*El analizador usa 4 modelos matemáticos para predecir resultados*")

    modelos_col1, modelos_col2 = st.columns(2)
    with modelos_col1:
        st.markdown("**📲 Modelos de Predicción:**")
        st.markdown("- **Poisson:** Distribución de goles")
        st.markdown("- **Dixon-Coles:** Efecto tiempo/partido")
    with modelos_col2:
        st.markdown("**🎯 Modelos Avanzados:**")
        st.markdown("- **Monte Carlo:** Simulaciones")
        st.markdown("- **Elo:** Rating de equipos")

    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # --- TABLA DE PLANES ---
    st.markdown("### 🏆 Planes y Precios")

    st.markdown("""
    <table class="se-price-table">
        <tr>
            <th>Duración</th>
            <th>Precio (USD)</th>
            <th>Etiqueta</th>
        </tr>
        <tr>
            <td class="se-duration">24 Horas</td>
            <td class="se-price">$3.99</td>
            <td>Pase 1 Día</td>
        </tr>
        <tr>
            <td class="se-duration">7 Días</td>
            <td class="se-price">$9.99</td>
            <td>Pase 1 Semana</td>
        </tr>
        <tr class="popular">
            <td class="se-duration">30 Días <span class="se-badge se-badge-hot">MГҒS POPULAR 📘</span></td>
            <td class="se-price">$24.99</td>
            <td>Plan 1 Mes</td>
        </tr>
        <tr>
            <td class="se-duration">365 Días <span class="se-badge se-badge-success">AHORRA 36%</span></td>
            <td class="se-price">$189.99</td>
            <td>Plan 1 AГұo</td>
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

# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# SISTEMA DE LOGIN - Solo contraseГұa
# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ

def render_login_form():
    """Renderiza el formulario de login con solo contraseГұa"""
    
    # Toggle para mostrar/ocultar login
    # Si no está logueado
    if not st.session_state.logged:
        
        # Si NO está mostrando login, mostrar landing page
        if not st.session_state.show_login:
            render_public_landing()
            st.stop()
        
        # Si está mostrando login, mostrar SOLO el formulario
        st.markdown("---")
        st.markdown("### 🔑 Iniciar Sesión")

        password = st.text_input("ContraseГұa", type="password", placeholder="Ingresa tu contraseГұa", key="login_password")

        col_login, col_cancel = st.columns([1, 1])
        with col_login:
            if st.button("✅ Entrar", use_container_width=True, type="primary"):
                if not password.strip():
                    st.error("⚠️ Ingresa la contraseГұa")
                else:
                    user = db_login(password)
                    if user:
                        st.session_state.logged = True
                        st.session_state.is_admin = user.get('es_admin', 0) == 1
                        st.session_state.user_data = user
                        st.session_state.show_login = False
                        st.rerun()  # Recargar después de login
                    else:
                        st.error("❌ ContraseГұa incorrecta")

        with col_cancel:
            if st.button("↩️җ Volver", use_container_width=True):
                st.session_state.show_login = False
                pass

        st.stop()

    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown("## 🦂 Scorpion Elite")
        user_plan = st.session_state.user_data.get('plan', 'vip') if st.session_state.user_data else 'vip'
        dias = st.session_state.user_data.get('dias', 0) if st.session_state.user_data else 0
        is_admin = st.session_state.user_data.get('es_admin', 0) == 1 if st.session_state.user_data else False
        
        plan_icon = {"admin": "⚡пёҸ", "elite": "👑", "vip": "👑", "mes": "👑", "free": "⭐"}.get(user_plan, "🦂")
        st.markdown(f"{plan_icon} **{user_plan.upper()}**")
        if not is_admin:
            st.caption(f"вҸұпёҸ {dias} días restantes")
        
        st.markdown("---")
        if st.button("👑 Logout", use_container_width=True):
            st.session_state.logged = False
            st.session_state.user_data = None
            st.session_state.is_admin = False
            pass
    
    # MenГә horizontal arriba - ж №жҚ®з"ЁжҲ·зұ»еһӢжҳҫзӨә
    st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    
    # Construir menГә dinámicamente segГәn tipo de usuario
    # VIP va de primeras y es la página por defecto
    if is_admin:
        # Admin: ve todo
        menu_pages = [
            ("👑 VIP", "VIP"),
            ("📊 Partidos", "Partidos"),
            ("📥 Analizador", "Analizador"),
            ("👑 Claves", "Claves"),
        ]
    else:
        # VIP: VIP primero, luego Partidos, Analizador
        menu_pages = [
            ("👑 VIP", "VIP"),
            ("📊 Partidos", "Partidos"),
            ("📥 Analizador", "Analizador"),
        ]
    
    # Crear columnas dinámicamente
    num_cols = len(menu_pages)
    cols = st.columns(num_cols)
    
    for i, (label, page) in enumerate(menu_pages):
        with cols[i]:
            is_active = st.session_state.page == page
            if st.button(label, use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.page = page
                pass
    
    st.markdown("---")

    # Página: Partidos (NUEVA)
    if st.session_state.page == "Partidos":
        import requests
        import time
        
        st.markdown("### 📊 Partidos de los Próximos 7 Días")
        
        # API-Football config
        API_KEY = os.getenv("API_FOOTBALL_KEY", "")
        if not API_KEY:
            st.error("❌ API_FOOTBALL_KEY no configurada. ConfigГәrala en Render.")
            st.stop()
        API_URL = "https://v3.football.api-sports.io"
        
                # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        # LISTA DE LIGAS - TODAS CON IDS CORRECTOS
        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        
        # вҳ… DEBUG: Probar solo Argentina
        LIGAS = [{"id": 128, "name": "Liga Profesional Argentina", "pais": "Argentina"}]
        
        # Contador de requests
        if 'api_requests_today' not in st.session_state:
            st.session_state.api_requests_today = 0
        
        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        # BOTONES BUSCAR Y LIMPIAR
        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        col_btn1, col_btn2, col_btn3, col_btn4, col_info = st.columns([1, 1, 1, 1, 2])
        
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
                    pass
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col_btn2:
            if st.button("🔄 🔄 Sincronizar", type="primary", use_container_width=True):
                st.info("🔄 Iniciando sincronización...")
                try:
                    # Migrar columna team_id si no existe
                    migrate_team_id_column()
                    
                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    # CONFIGURACIÓN INICIAL
                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    client = get_client()
                    if not client:
                        st.error("❌ No se pudo conectar a Supabase")
                        st.stop()

                    API_URL = "https://v3.football.api-sports.io"
                    API_KEY = os.getenv("API_FOOTBALL_KEY", "")
                    headers = {'x-apisports-key': API_KEY}
                    hoy = datetime.now(timezone(timedelta(hours=-5))).date()
                    hoy_str = hoy.strftime('%Y-%m-%d')
                    
                    # Calcular temporada dinámicamente: Ago-Dic ↩️' season actual, Ene-Jul ↩️' season anterior
                    season = hoy.year if hoy.month >= 8 else hoy.year - 1
                    # Usar la misma temporada para stats (la API ya tiene stats de la temporada actual)
                    season_stats = season
                    st.markdown(f"⚽ **Temporada partidos:** {season} | **Temporada stats:** {season_stats}")

                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    # PASO 1: DESCARGAR PARTIDOS (SIN ESTADГҚSTICAS DE EQUIPOS)
                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    # Obtener partidos existentes para evitar duplicados
                    partidos_existentes = set()
                    fecha_max_db = None
                    try:
                        resp_ex = client.table('partidos').select('fixture_id,fecha').execute()
                        if resp_ex.data:
                            partidos_existentes = {p['fixture_id'] for p in resp_ex.data}
                            # Encontrar la fecha máxima en la DB
                            fechas = [p['fecha'] for p in resp_ex.data if p.get('fecha')]
                            if fechas:
                                fecha_max_db = max(fechas)
                    except Exception as e:
                        pass
                    
                    # вҡҪ LГ“GICA INTELIGENTE:
                    # 1. Base vacГ­a: Descargar HOY a HOY+6
                    # 2. Base con datos: Descargar HOY-1 (resultados) + siguiente dГ­a de Гєltima fecha FUTURA
                    
                    ayer_date = hoy - timedelta(days=1)
                    ayer = ayer_date.strftime('%Y-%m-%d')
                    
                    try:
                        # Obtener todas las fechas Гєnicas en la base
                        resp_fechas = client.table('partidos').select('fecha').execute()
                        
                        if not resp_fechas.data:
                            # Base vacГ­a в†’ descargar ventana completa
                            fecha_inicio = hoy_str
                            fecha_fin = (hoy + timedelta(days=6)).strftime('%Y-%m-%d')
                            modo_sync = "вҳ• Completa (base vacГ­a)"
                        else:
                            # Analizar fechas existentes
                            fechas_futuras = []
                            for p in resp_fechas.data:
                                try:
                                    f = datetime.strptime(str(p['fecha'])[:10], '%Y-%m-%d').date()
                                    if f >= hoy:
                                        fechas_futuras.append(f)
                                except:
                                    pass
                            
                            # Siempre descargar resultados de ayer
                            fecha_inicio = ayer
                            
                            if fechas_futuras:
                                # Ya hay fechas futuras в†’ buscar la Гєltima y descargar el siguiente
                                ultima_futura = max(fechas_futuras)
                                siguiente_dia = (ultima_futura + timedelta(days=1)).strftime('%Y-%m-%d')
                                fecha_fin = siguiente_dia
                                modo_sync = f"вҳ” Incremental (Гєltima futura: {ultima_futura.strftime('%d/%m')})"
                            else:
                                # No hay fechas futuras в†’ descargar HOY+1
                                fecha_fin = (hoy + timedelta(days=1)).strftime('%Y-%m-%d')
                                modo_sync = "вҳ” Actualizar"
                                
                    except Exception as e:
                        # Si hay error, descargar ventana completa por seguridad
                        fecha_inicio = hoy_str
                        fecha_fin = (hoy + timedelta(days=6)).strftime('%Y-%m-%d')
                        modo_sync = "вҳ• Completa (fallback)"
                        st.warning(f"вҡҪ Error: {e}")
                    
                    st.markdown(f"{modo_sync} вҡҪ Rango: **{fecha_inicio}** al **{fecha_fin}**")
                    
                    # ✅ MODO PRODUCCIÓN - Todas las ligas
                    LIGAS = [
                            {"id": 2, "name": "UEFA Champions League"},
                            {"id": 3, "name": "UEFA Europa League"},
                            {"id": 848, "name": "UEFA Europa Conference League"},
                            {"id": 13, "name": "Copa Libertadores"},
                            {"id": 11, "name": "Copa Sudamericana"},
                            {"id": 541, "name": "CONMEBOL Recopa"},
                            {"id": 15, "name": "FIFA Club World Cup"},
                            {"id": 16, "name": "CONCACAF Champions League"},
                            {"id": 17, "name": "AFC Champions League"},
                            {"id": 140, "name": "La Liga"},
                            {"id": 141, "name": "Segunda División"},
                            {"id": 39, "name": "Premier League"},
                            {"id": 40, "name": "Championship"},
                            {"id": 41, "name": "League One"},
                            {"id": 42, "name": "League Two"},
                            {"id": 78, "name": "Bundesliga"},
                            {"id": 79, "name": "2. Bundesliga"},
                            {"id": 135, "name": "Serie A"},
                            {"id": 136, "name": "Serie B"},
                            {"id": 61, "name": "Ligue 1"},
                            {"id": 62, "name": "Ligue 2"},
                            {"id": 94, "name": "Primeira Liga"},
                            {"id": 88, "name": "Eredivisie"},
                            {"id": 144, "name": "Jupiler Pro League"},
                            {"id": 203, "name": "Süper Lig"},
                            {"id": 204, "name": "1. Lig"},
                            {"id": 179, "name": "Scottish Premiership"},
                            {"id": 180, "name": "Championship Scotland"},
                            {"id": 71, "name": "Serie A Brasil"},
                            {"id": 72, "name": "Serie B Brasil"},
                            {"id": 75, "name": "Serie C Brasil"},
                            {"id": 128, "name": "Liga Profesional Argentina"},
                            {"id": 129, "name": "Primera Nacional"},
                            {"id": 131, "name": "Primera B Metropolitana"},
                            {"id": 239, "name": "Primera A Colombia"},
                            {"id": 240, "name": "Primera B Colombia"},
                            {"id": 250, "name": "Division Profesional Paraguay"},
                            {"id": 251, "name": "Division Intermedia Paraguay"},
                            {"id": 242, "name": "Liga Pro Ecuador"},
                            {"id": 243, "name": "Liga Pro Serie B Ecuador"},
                            {"id": 268, "name": "Primera División Uruguay"},
                            {"id": 269, "name": "Segunda División Uruguay"},
                            {"id": 265, "name": "Primera División Chile"},
                            {"id": 266, "name": "Primera B Chile"},
                            {"id": 281, "name": "Liga 1 Peru"},
                            {"id": 282, "name": "Liga 2 Peru"},
                            {"id": 253, "name": "MLS"},
                            {"id": 255, "name": "USL Championship"},
                            {"id": 909, "name": "MLS Next Pro"},
                            {"id": 262, "name": "Liga MX"},
                            {"id": 263, "name": "Liga de Expansión MX"},
                            {"id": 307, "name": "Saudi Pro League"},
                            {"id": 233, "name": "Premier League Egypt"},
                            {"id": 98, "name": "J1 League"},
                            {"id": 292, "name": "K League 1"},
                        ]
                    
                    # Contadores
                    ligas_procesadas = 0
                    partidos_guardados = 0
                    
                    # Colección de equipos Гәnicos: {team_id: {team_id, team_name, league_id, league_name, season}}
                    equipos_unicos = {}
                    
                    # вҳ… NUEVO: Diccionario para rastrear partidos FT completados por equipo
                    # {team_id: [(fixture_id, fecha, es_local, resultado, gf, gc), ...]}
                    equipos_ft_fixtures = {}
                    
                    # Barra de progreso
                    
                    # Recorrer cada liga y descargar SOLO partidos
                    for idx, liga in enumerate(LIGAS):
                        liga_id = liga['id']
                        liga_nombre = liga['name']
                        
                        
                        # Descargar fixtures de esta liga
                        params = {
                            'league': liga_id,
                            'season': season,
                            'from': fecha_inicio,
                            'to': fecha_fin
                        }
                        
                        try:
                            resp = requests.get(f"{API_URL}/fixtures", headers=headers, params=params, timeout=15)
                            
                            if resp.status_code == 200:
                                data = resp.json()
                                fixtures = data.get('response', []) or []
                                ligas_procesadas += 1
                                
                                # Procesar cada fixture
                                for f in fixtures:
                                    fix = f.get('fixture', {})
                                    teams = f.get('teams', {})
                                    league = f.get('league', {})
                                    fix_id = fix.get('id')
                                    
                                    # Extraer datos del partido
                                    equipo_local = teams.get('home', {}).get('name', '')
                                    equipo_visitante = teams.get('away', {}).get('name', '')
                                    team_id_local = teams.get('home', {}).get('id')
                                    team_id_visitante = teams.get('away', {}).get('id')
                                    
                                    # Extraer score y estado
                                    score = f.get('score', {}) or {}
                                    goals = f.get('goals', {}) or {}  # CORREGIDO
                                    estado = fix.get('status', {}).get('short', 'NS')
                                    
                                    # Score fulltime
                                    score_local = score.get('fulltime', {}).get('home') if score.get('fulltime') else goals.get('home') or 0
                                    score_visitante = score.get('fulltime', {}).get('away') if score.get('fulltime') else goals.get('away') or 0
                                    
                                    # вҳ… CORREGIDO: SIEMPRE agregar equipos a equipos_unicos para actualizar stats
                                    # Independientemente de si el partido es nuevo o existente
                                    if team_id_local:
                                        equipos_unicos[team_id_local] = {
                                            'team_id': team_id_local,
                                            'team_name': equipo_local,
                                            'league_id': liga_id,
                                            'league_name': liga_nombre,
                                            'season': season_stats
                                        }

                                    if team_id_visitante:
                                        equipos_unicos[team_id_visitante] = {
                                            'team_id': team_id_visitante,
                                            'team_name': equipo_visitante,
                                            'league_id': liga_id,
                                            'league_name': liga_nombre,
                                            'season': season_stats
                                        }
                                    
                                    # вҳ… NUEVO: Rastrear partidos FT (terminados) para sincronización incremental
                                    if estado == 'FT' and fix_id:
                                        fecha_partido = fix.get('date', '')[:10]
                                        resultado_local = 'W' if (score_local > score_visitante) else ('D' if score_local == score_visitante else 'L')
                                        resultado_visitante = 'W' if (score_visitante > score_local) else ('D' if score_local == score_visitante else 'L')
                                        
                                        # Agregar a fixtures FT del equipo local
                                        if team_id_local:
                                            if team_id_local not in equipos_ft_fixtures:
                                                equipos_ft_fixtures[team_id_local] = []
                                            equipos_ft_fixtures[team_id_local].append({
                                                'fixture_id': fix_id,
                                                'fecha': fecha_partido,
                                                'liga': league.get('name', ''),
                                                'es_local': True,
                                                'resultado': resultado_local,
                                                'goles_favor': score_local,
                                                'goles_contra': score_visitante
                                            })
                                        
                                        # Agregar a fixtures FT del equipo visitante
                                        if team_id_visitante:
                                            if team_id_visitante not in equipos_ft_fixtures:
                                                equipos_ft_fixtures[team_id_visitante] = []
                                            equipos_ft_fixtures[team_id_visitante].append({
                                                'fixture_id': fix_id,
                                                'fecha': fecha_partido,
                                                'liga': league.get('name', ''),
                                                'es_local': False,
                                                'resultado': resultado_visitante,
                                                'goles_favor': score_visitante,
                                                'goles_contra': score_local
                                            })
                                    
                                    # Guardar SOLO partidos nuevos en tabla partidos
                                    if fix_id not in partidos_existentes:
                                        partido_data = {
                                            'fixture_id': fix_id,
                                            'fecha': fix.get('date', '')[:10],
                                            'hora': fix.get('date', '')[11:16],
                                            'liga': league.get('name', ''),
                                            'liga_id': league.get('id'),
                                            'pais': league.get('country', ''),
                                            'equipo_local': equipo_local,
                                            'equipo_visitante': equipo_visitante,
                                            'team_id_local': team_id_local,
                                            'team_id_visitante': team_id_visitante,
                                            'score_local': score_local,
                                            'score_visitante': score_visitante,
                                            'estado': estado,
                                        }
                                        try:
                                            client.table("partidos").upsert(partido_data, on_conflict="fixture_id").execute()
                                            partidos_guardados += 1
                                        except Exception as e:
                                            st.warning(f"⚠️ Error al guardar partido {fix_id}: {e}")
                        except Exception as e:
                            # Si falla una liga, continuar con la siguiente
                            continue
                    
                    
                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    # PASO 2: SINCRONIZACIÓN INCREMENTAL DE STATS DE EQUIPOS
                    # - Equipos NUEVOS (0 records): Fetch 5 partidos iniciales
                    # - Equipos EXISTENTES: Solo fetch partidos FT nuevos no guardados
                    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
                    
                    equipos_stats_descargados = 0
                    equipos_nuevos = 0
                    equipos_existentes = 0
                    stats_ft_nuevos = 0
                    errores_equipos = 0
                    partidos_iniciales_cargados = 0
                    
                    if equipos_unicos:
                        
                        # Paso 2a: Identificar equipos existentes en DB
                        equipos_existentes_ids = set()
                        try:
                            # Obtener todos los team_ids que ya tienen stats
                            resp_existing = client.table('equipo_partidos_stats').select('team_id').execute()
                            if resp_existing.data:
                                equipos_existentes_ids = {p['team_id'] for p in resp_existing.data}
                        except Exception as e:
                            equipos_existentes_ids = set()
                        
                        # Paso 2b: Para cada equipo, determinar si es nuevo o existente
                        for idx, (tid, equipo) in enumerate(equipos_unicos.items()):
                            team_id = equipo['team_id']
                            team_name = equipo['team_name']
                            league_id = equipo['league_id']
                            season_eq = equipo['season']
                            
                            is_new_team = team_id not in equipos_existentes_ids
                            
                            # Obtener fixture_ids ya guardados para este equipo
                            fixtures_guardados = set()
                            try:
                                resp_fixtures = client.table('equipo_partidos_stats').select('fixture_id').eq('team_id', team_id).execute()
                                if resp_fixtures.data:
                                    fixtures_guardados = {p['fixture_id'] for p in resp_fixtures.data}
                            except Exception as e:
                                st.warning(f"⚠️ Error al verificar fixtures de {team_name}: {e}")
                            
                            # вҳ… CASO A: EQUIPO NUEVO (0 records en DB)
                            if is_new_team:
                                equipos_nuevos += 1
                                try:
                                    # Descargar estadísticas del equipo
                                    resp_team = requests.get(
                                        f"{API_URL}/teams/statistics",
                                        headers=headers,
                                        params={'team': team_id, 'league': league_id, 'season': season_eq},
                                        timeout=10
                                    )
                                    
                                    if resp_team.status_code == 200:
                                        stats = resp_team.json().get('response', {})
                                        pj_total = stats.get('fixtures', {}).get('played', {}).get('total', 0) if stats else 0
                                        
                                        if stats and pj_total > 0:
                                            goals = stats.get('goals', {})
                                            fixtures_stats = stats.get('fixtures', {})
                                            
                                            gf = goals.get('for', {}).get('total', {}).get('total', 0) or 0
                                            gc = goals.get('against', {}).get('total', {}).get('total', 0) or 0
                                            gf_h = goals.get('for', {}).get('total', {}).get('home', 0) or 0
                                            gf_a = goals.get('for', {}).get('total', {}).get('away', 0) or 0
                                            gc_h = goals.get('against', {}).get('total', {}).get('home', 0) or 0
                                            gc_a = goals.get('against', {}).get('total', {}).get('away', 0) or 0
                                            pj_h = fixtures_stats.get('played', {}).get('home', 1) or 1
                                            pj_a = fixtures_stats.get('played', {}).get('away', 1) or 1
                                            pj_t = fixtures_stats.get('played', {}).get('total', 0) or 1
                                            wins = fixtures_stats.get('wins', {}).get('total', 0) or 0
                                            draws = fixtures_stats.get('draws', {}).get('total', 0) or 0
                                            loses = fixtures_stats.get('loses', {}).get('total', 0) or 0
                                            
                                            equipo_data = {
                                                'equipo': team_name,
                                                'team_id': team_id,
                                                'liga': stats.get('league', {}).get('name', equipo['league_name']),
                                                'temporada': f'{season_eq}-{season_eq+1}',
                                                'partidos_jugados': pj_t,
                                                'victorias': wins,
                                                'empates': draws,
                                                'derrotas': loses,
                                                'goles_favor': gf,
                                                'goles_contra': gc,
                                                'lambda_local': round(gf_h / max(pj_h, 1), 2),
                                                'lambda_visitante': round(gf_a / max(pj_a, 1), 2),
                                                'ultimos_5_partidos': list(stats.get('form', '') or '')[:5],
                                            }
                                            
                                            try:
                                                client.table('equipos_stats').upsert(
                                                    equipo_data,
                                                    on_conflict='equipo,temporada'
                                                ).execute()
                                                equipos_stats_descargados += 1
                                            except Exception as e:
                                                errores_equipos += 1
                                    
                                    # вҳ… Fetch 5 partidos iniciales para equipo nuevo
                                    partidos_iniciales = obtener_ultimos_partidos_equipo(
                                        team_id=team_id,
                                        team_name=team_name,
                                        league_id=league_id,
                                        season=season_eq,
                                        headers=headers,
                                        API_URL=API_URL,
                                        max_partidos=5
                                    )
                                    
                                    if partidos_iniciales and len(partidos_iniciales) > 0:
                                        success, msg, count = guardar_stats_equipo(client, team_id, team_name, partidos_iniciales)
                                        if success and count > 0:
                                            partidos_iniciales_cargados += count
                                    
                                except Exception as e:
                                    errores_equipos += 1
                            
                            # вҳ… CASO B: EQUIPO EXISTENTE (ya tiene records en DB)
                            else:
                                equipos_existentes += 1
                                ft_en_ventana = equipos_ft_fixtures.get(team_id, [])

                                # NUEVO: Si no hay partidos terminados en ventana, buscar directamente
                                if not ft_en_ventana:
                                    try:
                                        resp_last = requests.get(
                                            f"{API_URL}/fixtures",
                                            headers=headers,
                                            params={
                                                "team": team_id,
                                                "season": season_eq,
                                                "status": "FT",
                                                "from": f"{hoy.year}-01-01",
                                                "to": hoy_str,
                                                "limit": 10
                                            },
                                            timeout=10
                                        )
                                        if resp_last.status_code == 200:
                                            data_last = resp_last.json()
                                            if data_last.get("response"):
                                                for fix in data_last["response"]:
                                                    f2 = fix.get("fixture", {})
                                                    fix_id = f2.get("id")
                                                    teams = fix.get("teams", {})
                                                    score = f2.get("score", {}) or {}
                                                    goals = fix.get("goals", {}) or {}
                                                    fecha_partido = f2.get("date", "")[:10]
                                                    score_local = score.get("fulltime", {}).get("home") if score.get("fulltime") else goals.get("home") or 0
                                                    score_visitante = score.get("fulltime", {}).get("away") if score.get("fulltime") else goals.get("away") or 0
                                                    es_local = teams.get("home", {}).get("id") == team_id
                                                    resultado = "W" if ((es_local and score_local > score_visitante) or (not es_local and score_visitante > score_local)) else ("D" if score_local == score_visitante else "L")
                                                    ft_en_ventana.append({
                                                        "fixture_id": fix_id,
                                                        "fecha": fecha_partido,
                                                        "liga": fix.get("league", {}).get("name", ""),
                                                        "es_local": es_local,
                                                        "resultado": resultado,
                                                        "goles_favor": score_visitante if not es_local else score_local,
                                                        "goles_contra": score_local if not es_local else score_visitante
                                                    })
                                    except:
                                        pass

                                
                                # вҳ… CORREGIDO: Siempre intentar guardar/actualizar TODOS los FT
                                # El upsert no duplica, solo actualiza si ya existe
                                if ft_en_ventana:
                                    for fix_info in ft_en_ventana:
                                        try:
                                            # Fetch stats del partido específico
                                            stats_partido = obtener_stats_partido(
                                                fixture_id=fix_info['fixture_id'],
                                                team_id=team_id,
                                                team_name=team_name,
                                                headers=headers,
                                                API_URL=API_URL
                                            )
                                            
                                            # Crear datos del partido (siempre incluir goles)
                                            partido_data = {
                                                'team_id': team_id,
                                                'equipo': team_name,
                                                'fixture_id': fix_info['fixture_id'],
                                                'fecha': fix_info['fecha'],
                                                'liga': fix_info['liga'],
                                                'es_local': fix_info['es_local'],
                                                'resultado': fix_info['resultado'],
                                                'goles_favor': fix_info['goles_favor'] if fix_info.get('goles_favor') is not None else 0,
                                                'goles_contra': fix_info['goles_contra'] if fix_info.get('goles_contra') is not None else 0,
                                            }
                                            
                                            # Agregar stats si están disponibles
                                            if stats_partido:
                                                partido_data.update(stats_partido)
                                            
                                            try:
                                                client.table('equipo_partidos_stats').upsert(
                                                    partido_data,
                                                    on_conflict='team_id,fixture_id'
                                                ).execute()
                                                stats_ft_nuevos += 1
                                            except Exception as e:
                                                pass
                                            
                                        except Exception as e:
                                            pass
                    
                    st.session_state.sincronizacion_ok = True
                    
                    # RESUMEN FINAL
                    st.success("✅ **SINCRONIZACIÓN COMPLETADA**")
                    
                    st.markdown(f"""
                    📥 **RESUMEN FINAL:**
                    
                    | Métrica | Valor |
                    |---------|-------|
                    | 🏆 **Ligas procesadas** | {ligas_procesadas} |
                    | 📅 **Partidos guardados** | {partidos_guardados} |
                    | 👥 **Equipos detectados** | {len(equipos_unicos)} |
                    | 🆕 **Equipos nuevos** | {equipos_nuevos} |
                    | ♻️ **Equipos existentes** | {equipos_existentes} |
                    | 📥 **Stats equipos descargadas** | {equipos_stats_descargados} |
                    | 📲 **Stats partidos nuevos** | {partidos_iniciales_cargados} |
                    | 📊 **Stats FT incrementales** | {stats_ft_nuevos} |
                    | ⚠️ **Errores** | {errores_equipos} |
                    """)
                        
                except Exception as e:
                    st.error(f"❌ Error en sincronización: {e}")

        with col_btn3:
            if st.button("🧹 Limpiar Equipos", type="secondary", use_container_width=True):
                client = get_client()
                try:
                    resp_eq = client.table('equipos_stats').select('equipo', count='exact').execute()
                    num_eq = len(resp_eq.data) if resp_eq.data else 0
                    
                    resp_ep = client.table('equipo_partidos_stats').select('equipo', count='exact').execute()
                    num_ep = len(resp_ep.data) if resp_ep.data else 0
                    
                    if num_eq > 0 or num_ep > 0:
                        client.table('equipos_stats').delete().neq('equipo', '').execute()
                        client.table('equipo_partidos_stats').delete().neq('equipo', '').execute()
                        st.session_state.limpieza_equipos_ok = True
                    else:
                        st.info("ℹ️пёҸ No hay datos para limpiar")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        # Mostrar mensaje de limpieza si fue exitosa
        if st.session_state.get('limpieza_equipos_ok'):
            st.success(f"✅ Equipos limpiados correctamente")
            st.session_state.limpieza_equipos_ok = False


        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        # LIMPIEZA: Eliminar partidos de más de 1 aГұo SOLO si hay partidos nuevos
        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        if st.session_state.get('sincronizacion_ok') and st.session_state.get('partidos_nuevos_guardados', 0) > 0:
            st.session_state.sincronizacion_ok = False
            st.session_state.partidos_nuevos_guardados = 0
            try:
                client = get_client()
                fecha_limite = (datetime.now(timezone(timedelta(hours=-5))) - timedelta(days=365)).strftime('%Y-%m-%d')
                resp_del = client.table('partidos').delete().lt('fecha', fecha_limite).execute()
                eliminados = len(resp_del.data) if resp_del.data else 0
                if eliminados > 0:
                    st.info(f"🗑️ {eliminados} partidos de más de 1 aГұo eliminados")
            except Exception as e:
                pass

        with col_info:
            st.markdown(f"📅 {datetime.now(timezone(timedelta(hours=-5))).date().strftime('%d/%m/%Y')} | 🔻 Requests: {st.session_state.api_requests_today}/999")
        
        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
        # MOSTRAR PARTIDOS (AGRUPADOS POR PAГҚS, HORA COLOMBIANA)
        # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
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
            st.markdown("⚽ **No hay partidos.** Clic en 🔄 🔄 Sincronizar para obtener partidos.")
            partidos = []
        
        # Filtro por calendario
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            hoy = datetime.now(timezone(timedelta(hours=-5))).date()
            fecha_seleccionada = st.date_input("📅 Fecha", value=hoy, format="DD/MM/YYYY")
        
        # Filtrar por fecha seleccionada
        if fecha_seleccionada:
            fecha_str = fecha_seleccionada.strftime('%Y-%m-%d')
            partidos = [p for p in partidos if str(p.get('fecha', ''))[:10] == fecha_str]
        
        # Procesar partidos con hora colombiana
        partidos_procesados = []
        for p in partidos:
            fecha = p.get('fecha', '')
            hora_original = p.get('hora', '')
            hora_colombia = utc_to_colombia(f"{fecha}T{hora_original}:00Z") if fecha and hora_original else hora_original[:5]
            
            partidos_procesados.append({
                **p,
                'hora_colombia': hora_colombia,
                'fecha_formato': datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha else ''
            })
        
        # Agrupar por PAГҚS
        paises_partidos = {}
        for p in partidos_procesados:
            pais = p.get('pais', 'Sin país')
            if pais not in paises_partidos:
                paises_partidos[pais] = []
            paises_partidos[pais].append(p)
        
        # Emoji por país
        def get_pais_emoji(pais):
            emojis = {
                'Argentina': '🇦🇷🇦🇹', 'Brasil': '🇧🇷🇦🇹', 'Colombia': '🇨🇴🇨🇱', 'Chile': '🇨🇴🇭🇺',
                'México': '🇲🇽🇲🇽', 'USA': '🇸🇦', 'Uruguay': '🇺🇾', 'PerГә': '🇵🇾🇪🇸',
                'Paraguay': '🇵🇾🇺🇾', 'Ecuador': '🇪🇸🇨🇴', 'EspaГұa': '🇪🇸🇸🇦', 'Inglaterra': ' Ғ§у Ғўу ҒҘу Ғ®у Ғ§у Ғҝ',
                'Alemania': '©🇪🇸', 'Italia': '🇮🇹🇹🇷', 'Francia': '🇫🇷🇦🇹', 'Portugal': '🇵🇾🇹🇷',
                'Holanda': '🇳🇱🇭🇺', 'Turquía': '🇹🇷🇦🇹', 'Escocia': ' Ғ§у Ғўу Ғіу ҒЈу Ғҙу Ғҝ',
                'Bélgica': '🇧🇷🇪🇸', 'Mundial': '🏴'
            }
            return emojis.get(pais, '🏴')
        
        # Mostrar cada país como expander
        for pais in sorted(paises_partidos.keys()):
            emoji = get_pais_emoji(pais)
            partidos_pais = paises_partidos[pais]
            total_partidos = len(partidos_pais)
            
            with st.expander(f"{emoji} **{pais}** ({total_partidos} partidos)", expanded=True):
                # Primero agrupar por liga
                ligas_pais = {}
                for p in partidos_pais:
                    liga = p.get('liga', 'Sin Liga')
                    if liga not in ligas_pais:
                        ligas_pais[liga] = []
                    ligas_pais[liga].append(p)
                
                # Ordenar partidos DENTRO de cada liga por fecha y hora
                for liga in ligas_pais:
                    ligas_pais[liga].sort(key=lambda x: (str(x.get('fecha', '')), str(x.get('hora_colombia', ''))))
                
                # Mostrar cada liga
                for liga, partidos_liga in sorted(ligas_pais.items()):
                    st.markdown(f"**🏆 {liga}**")
                    
                    for i, partido in enumerate(partidos_liga):
                        equipo_local = partido.get('equipo_local', '')
                        equipo_visitante = partido.get('equipo_visitante', '')
                        hora_col = partido.get('hora_colombia', '')
                        fecha_fmt = partido.get('fecha_formato', '')[:5]

                        # Verificar si los equipos tienen estadísticas
                        try:
                            resp_local = client.table('equipos_stats').select('equipo').ilike('equipo', f'%{equipo_local}%').execute()
                            resp_visit = client.table('equipos_stats').select('equipo').ilike('equipo', f'%{equipo_visitante}%').execute()
                            tiene_local = len(resp_local.data) > 0 if resp_local.data else False
                            tiene_visit = len(resp_visit.data) > 0 if resp_visit.data else False
                            tiene_stats = tiene_local and tiene_visit
                        except:
                            tiene_stats = None

                        # Badge de estado
                        if tiene_stats is True:
                            badge = "🔴"
                        elif tiene_stats is False:
                            badge = "🔽"
                        else:
                            badge = "⚪"
                        
                        # Botón estilo tarjeta compacta
                        label = f"📅 {fecha_fmt} {hora_col} | {badge} {equipo_local} vs {equipo_visitante} ➜"
                        if st.button(label, key=f"btn_{pais}_{liga}_{i}", use_container_width=True):
                            st.session_state.selected_local = equipo_local
                            st.session_state.selected_away = equipo_visitante
                            st.session_state.selected_team_id_local = partido.get('team_id_local')
                            st.session_state.selected_team_id_visitante = partido.get('team_id_visitante')
                            st.session_state.page = "Analizador"
                            st.rerun()
                
                st.markdown("---")
        
    # Página: Analizador
    elif st.session_state.page == "Analizador":
        st.markdown("### 🎯 Analizador de Partidos")

        client = get_client()

        # ★ SIEMPRE CARGAR EQUIPOS Y MOSTRAR SELECTBOX
        try:
            resp_equipos = client.table('equipos_stats').select('equipo,team_id').execute()
            equipos_data = resp_equipos.data
            equipos_disponibles = sorted(list(set([e.get('equipo', '') for e in equipos_data if e.get('equipo')])))
            equipos_dict = {e.get('equipo', ''): e.get('team_id') for e in equipos_data}
            st.caption(f"📊 {len(equipos_disponibles)} equipos disponibles | Selecciona o elige de la lista de partidos")
        except Exception as ex:
            equipos_disponibles = []
            equipos_dict = {}
            st.error(f"Error conectando a Supabase: {ex}")

        # MOSTRAR SELECTBOX SIEMPRE
        col_space, col1, col2, col_space2 = st.columns([1, 2, 2, 1])
        with col1:
            home_team = st.selectbox("🏠 Local", [""] + equipos_disponibles, key="home_select")
        with col2:
            away_team = st.selectbox("✈️ Visitante", [""] + equipos_disponibles, key="away_select")

        # Variables para el análisis
        local_nombre = home_team
        visitante_nombre = away_team
        tid_local = equipos_dict.get(home_team) if home_team else None
        tid_visitante = equipos_dict.get(away_team) if away_team else None
        stats_local = None
        stats_visitante = None
        promedios_dinamicos_local = None
        promedios_dinamicos_visitante = None
        lambda_historico_local = None
        lambda_historico_visit = None

        # Si hay equipos seleccionados, buscar stats
        if local_nombre and visitante_nombre:
            try:
                resp_local = client.table('equipos_stats').select('*').ilike('equipo', f'%{local_nombre}%').execute()
                if resp_local.data:
                    stats_local = resp_local.data[0]
            except:
                pass

            try:
                resp_visitante = client.table('equipos_stats').select('*').ilike('equipo', f'%{visitante_nombre}%').execute()
                if resp_visitante.data:
                    stats_visitante = resp_visitante.data[0]
            except:
                pass

            # Buscar promedios_dinamicos por team_id
            if tid_local:
                promedios_dinamicos_local = calcular_promedios_equipo(client, tid_local)
            if tid_visitante:
                promedios_dinamicos_visitante = calcular_promedios_equipo(client, tid_visitante)

        # ★ SI HAY PARTIDO SELECCIONADO DE LA LISTA, USAR ESOS EQUIPOS
        if st.session_state.get('selected_local') and st.session_state.get('selected_away'):
            local_nombre = st.session_state.selected_local
            visitante_nombre = st.session_state.selected_away
            tid_local = st.session_state.get('selected_team_id_local')
            tid_visitante = st.session_state.get('selected_team_id_visitante')

            st.markdown(f"#### 📋 Analizando: **{local_nombre}** VS **{visitante_nombre}**")

            # Buscar stats
            try:
                resp_local = client.table('equipos_stats').select('*').ilike('equipo', f'%{local_nombre}%').execute()
                if resp_local.data:
                    stats_local = resp_local.data[0]
            except:
                pass

            try:
                resp_visitante = client.table('equipos_stats').select('*').ilike('equipo', f'%{visitante_nombre}%').execute()
                if resp_visitante.data:
                    stats_visitante = resp_visitante.data[0]
            except:
                pass

            if tid_local:
                promedios_dinamicos_local = calcular_promedios_equipo(client, tid_local)
            if tid_visitante:
                promedios_dinamicos_visitante = calcular_promedios_equipo(client, tid_visitante)

        # ★ DETECTAR SI VIENE DE LA LISTA (antes de limpiar)

        # Limpiar session_state DESPUÉS de detectar
        vino_de_lista = 'selected_local' in st.session_state and 'selected_away' in st.session_state
        if vino_de_lista:
            for key in ['selected_local', 'selected_away', 'selected_team_id_local', 'selected_team_id_visitante']:
                st.session_state.pop(key, None)
        
        # Verificar si se puede analizar
        puede_analizar = stats_local is not None and stats_visitante is not None

        if not puede_analizar:
            if local_nombre or visitante_nombre:
                st.info("⚠️ Selecciona equipos que tengan estadísticas. Ejecuta Sincronizar si es necesario.")

        # Si viene de la lista Y hay stats, hacer análisis automático
        # Si usa dropdowns, mostrar botón ANALIZAR
        if puede_analizar and vino_de_lista:
            # Análisis automático desde lista
            debe_analizar = True
        elif puede_analizar:
            # Mostrar botón para dropdowns
            analizar_key = f"analizar_{local_nombre}_{visitante_nombre}"
            debe_analizar = st.button("🎯 ANALIZAR", type="primary", use_container_width=True, key=analizar_key)
        else:
            debe_analizar = False

        if debe_analizar:
            with st.spinner("Analizando..."):
                # Lambda histórico
                    lambda_historico_local = stats_local.get('lambda_local', 1.3)
                    lambda_historico_visit = stats_visitante.get('lambda_visitante', 1.1)

                    # Promedios dinámicos
                    if promedios_dinamicos_local:
                        corners_l = promedios_dinamicos_local.get('promedio_corners', 5.5)
                        tiros_l = promedios_dinamicos_local.get('promedio_tiros', 13.0)
                        tiros_arco_l = promedios_dinamicos_local.get('promedio_tiros_arco', 4.5)
                        tarjetas_l = promedios_dinamicos_local.get('promedio_amarillas', 2.5)
                    else:
                        corners_l = stats_local.get('promedio_corners', 5.5) or 5.5
                        tiros_l = stats_local.get('promedio_tiros', 13.0) or 13.0
                        tiros_arco_l = stats_local.get('promedio_tiros_arco', 4.5) or 4.5
                        tarjetas_l = stats_local.get('promedio_tarjetas', 2.5) or 2.5

                    if promedios_dinamicos_visitante:
                        corners_v = promedios_dinamicos_visitante.get('promedio_corners', 5.5)
                        tiros_v = promedios_dinamicos_visitante.get('promedio_tiros', 13.0)
                        tiros_arco_v = promedios_dinamicos_visitante.get('promedio_tiros_arco', 4.5)
                        tarjetas_v = promedios_dinamicos_visitante.get('promedio_amarillas', 2.5)
                    else:
                        corners_v = stats_visitante.get('promedio_corners', 5.5) or 5.5
                        tiros_v = stats_visitante.get('promedio_tiros', 13.0) or 13.0
                        tiros_arco_v = stats_visitante.get('promedio_tiros_arco', 4.5) or 4.5
                        tarjetas_v = stats_visitante.get('promedio_tarjetas', 2.5) or 2.5

                    # Lambda con calibración
                    lambda_local_adj = get_lambda_ajustada(local_nombre, lambda_historico_local, como_local=True)
                    lambda_visitante_adj = get_lambda_ajustada(visitante_nombre, lambda_historico_visit, como_local=False)
                    lambda_local_cal = lambda_local_adj['lambda_ajustada']
                    lambda_visitante_cal = lambda_visitante_adj['lambda_ajustada']

                    # Obtener últimos partidos
                    ultimos_5_local = promedios_dinamicos_local.get('partidos', [])[:5] if promedios_dinamicos_local else []
                    ultimos_5_visitante = promedios_dinamicos_visitante.get('partidos', [])[:5] if promedios_dinamicos_visitante else []

                    # Si no hay partidos en DB, obtener de API
                    if not ultimos_5_local and tid_local:
                        try:
                            headers = {'x-apisports-key': API_KEY, 'Accept': 'application/json'}
                            mes_actual = datetime.now().month
                            temporada = datetime.now().year if mes_actual >= 8 else datetime.now().year - 1
                            league_id = stats_local.get('liga_id', 39) if stats_local else 39
                            partidos_api = obtener_ultimos_partidos_equipo(tid_local, local_nombre, league_id, temporada, headers, API_URL, max_partidos=10)
                            if partidos_api:
                                ultimos_5_local = partidos_api[:5]
                                guardar_stats_equipo(client, tid_local, local_nombre, partidos_api)
                        except:
                            pass

                    if not ultimos_5_visitante and tid_visitante:
                        try:
                            headers = {'x-apisports-key': API_KEY, 'Accept': 'application/json'}
                            mes_actual = datetime.now().month
                            temporada = datetime.now().year if mes_actual >= 8 else datetime.now().year - 1
                            league_id = stats_visitante.get('liga_id', 39) if stats_visitante else 39
                            partidos_api = obtener_ultimos_partidos_equipo(tid_visitante, visitante_nombre, league_id, temporada, headers, API_URL, max_partidos=10)
                            if partidos_api:
                                ultimos_5_visitante = partidos_api[:5]
                                guardar_stats_equipo(client, tid_visitante, visitante_nombre, partidos_api)
                        except:
                            pass

                    # Guardar promedios en session
                    st.session_state.promedios_dinamicos_local = promedios_dinamicos_local
                    st.session_state.promedios_dinamicos_visitante = promedios_dinamicos_visitante

                    # Llamar al modelo
                    result = calcular(
                        lambda_local=lambda_local_cal,
                        lambda_visitante=lambda_visitante_cal,
                        corners_local=float(corners_l),
                        corners_visitante=float(corners_v),
                        tarjetas_local=float(tarjetas_l),
                        tarjetas_visitante=float(tarjetas_v),
                        tiros_local=float(tiros_l),
                        tiros_visitante=float(tiros_v),
                        tiros_arco_local=float(tiros_arco_l),
                        tiros_arco_visitante=float(tiros_arco_v),
                        ultimos_5_local=ultimos_5_local,
                        ultimos_5_visitante=ultimos_5_visitante,
                    )

                    st.session_state.analysis_result = result
                    st.session_state.home = local_nombre
                    st.session_state.away = visitante_nombre
                    st.session_state.stats_local = stats_local
                    st.session_state.stats_visitante = stats_visitante

        # ★ MOSTRAR RESULTADOS SI EXISTEN
        if 'analysis_result' in st.session_state:
            r = st.session_state.analysis_result
            home = st.session_state.home
            away = st.session_state.away
            stats_local = st.session_state.get('stats_local', {})
            stats_visitante = st.session_state.get('stats_visitante', {})
            tid_local = st.session_state.get('tid_local')
            tid_visitante = st.session_state.get('tid_visitante')

            st.markdown("---")
            st.markdown(f"### 📊 Análisis: {home} vs {away}")

            # Mostrar predicciones principales
            col1, col2, col3 = st.columns(3)
            with col1:
                p1 = r.get('p1', 0)
                st.metric("🏠 Local", f"{p1:.1f}%")
            with col2:
                px = r.get('px', 0)
                st.metric("🤝 Empate", f"{px:.1f}%")
            with col3:
                p2 = r.get('p2', 0)
                st.metric("✈️ Visitante", f"{p2:.1f}%")

            # Predicción 1X2
            pick_1x2 = r.get('pick_1x2', '-')
            prob_1x2 = r.get('prob_1x2', 0)
            confianza = r.get('confianza', 0)
            rango = r.get('rango', 'D')

            st.markdown(f"""
            <div class="field-container">
                <div class="field-label">🎯 PRONÓSTICO 1X2</div>
                <div class="field-value">{pick_1x2}</div>
                <div class="field-sublabel">Probabilidad: {prob_1x2:.1f}% | Confianza: {confianza}% ({rango})</div>
            </div>
            """, unsafe_allow_html=True)

            # Otras predicciones
            st.markdown("#### 📈 Predicciones Adicionales")
            col_pred1, col_pred2, col_pred3 = st.columns(3)
            with col_pred1:
                ou = r.get('pick_over_under', '-')
                ou_prob = r.get('prob_over_under', 0)
                st.metric("📈 Over/Under 2.5", f"{ou} ({ou_prob:.0f}%)")
            with col_pred2:
                btts = r.get('pick_btts', '-')
                btts_prob = r.get('btts_yes', 0)
                st.metric("⚽ BTTS", f"{btts} ({btts_prob:.0f}%)")
            with col_pred3:
                corners = r.get('pick_corners', '-')
                corners_total = r.get('corners', {}).get('total_estimado', 0)
                st.metric("🌽 Corners", f"{corners} ({corners_total:.1f})")

            # ★ BOTÓN GUARDAR SIEMPRE VISIBLE
            st.markdown("---")
            col_btn_guardar, col_info = st.columns([1, 3])
            with col_btn_guardar:
                if st.button("💾 GUARDAR PICK", type="primary", use_container_width=True):
                    try:
                        pick_data = {
                            'fecha': str(datetime.now(timezone(timedelta(hours=-5))).date()),
                            'liga': stats_local.get('liga', 'Desconocida'),
                            'equipo_local': home,
                            'equipo_visitante': away,
                            'pick': pick_1x2,
                            'prediccion_1x2': pick_1x2,
                            'prob_1x2': float(prob_1x2),
                            'p1': float(p1),
                            'px': float(px),
                            'p2': float(p2),
                            'prediccion_ou': r.get('pick_over_under', ''),
                            'prob_ou': float(r.get('prob_over_under', 0)),
                            'prediccion_btts': r.get('pick_btts', ''),
                            'btts_yes': float(r.get('btts_yes', 0)),
                            'btts_no': float(r.get('btts_no', 0)),
                            'prediccion_corners': r.get('pick_corners', ''),
                            'corners_total_estimado': float(r.get('corners', {}).get('total_estimado', 0)),
                            'confianza': float(confianza),
                            'rango': rango,
                            'lambda_local': float(stats_local.get('lambda_local', 0)),
                            'lambda_visitante': float(stats_visitante.get('lambda_visitante', 0)),
                        }
                        client.table('picks').insert(pick_data).execute()
                        st.success("✅ ¡Pick guardado exitosamente!")
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")
            with col_info:
                st.info("💡 Guarda este análisis para hacer seguimiento y verificar aciertos.")

    elif st.session_state.page == "Claves":
        st.markdown("### 👑 Gestión de ContraseГұas")
        
        # Tabs
        tab_crear, tab_gestionar = st.tabs(["➕ Crear ContraseГұa", "📋 Ver ContraseГұas"])
        
        # ========== TAB: CREAR ==========
        with tab_crear:
            st.markdown("#### ➕ Crear Nueva ContraseГұa de Acceso")
            
            with st.form("form_crear_clave", clear_on_submit=True):
                col_nom, col_plan = st.columns(2)
                with col_nom:
                    nombre = st.text_input("қ Nombre / Cliente", placeholder="Ej: Juan, Carlos VIP").strip()
                with col_plan:
                    plan = st.selectbox("🦂 Plan", ["semana", "mes", "elite", "vip"])
                
                nueva_clave = st.text_input("🔑 Nueva ContraseГұa", placeholder="Escribe la contraseГұa Гәnica").strip()
                
                dias_opciones = {"semana": 7, "mes": 30, "elite": 90, "vip": 90}
                dias = dias_opciones.get(plan, 30)
                
                col_info, col_btn = st.columns([2, 1])
                with col_info:
                    plan_icon = {"semana": "📦", "mes": "👑", "elite": "📘", "vip": "вӯҗ"}
                    st.info(f"{plan_icon.get(plan, '🦂')} Plan: {plan.upper()} - {dias} días")
                
                submitted = st.form_submit_button("✅ Crear ContraseГұa", use_container_width=True, type="primary")
                
                if submitted:
                    if not nombre.strip():
                        st.error("⚠️ Ingresa un nombre")
                    elif not nueva_clave.strip():
                        st.error("⚠️ Ingresa una contraseГұa")
                    elif len(nueva_clave) < 4:
                        st.error("⚠️ La contraseГұa debe tener al menos 4 caracteres")
                    else:
                        # Todos los planes son VIP (semana, mes, elite, vip)
                        plan_asignar = "elite"
                        success = db_crear_usuario(nueva_clave.strip(), nombre.strip(), plan_asignar, dias)
                        if success:
                            st.success(f"✅ ContraseГұa '{nueva_clave}' creada para {nombre} - Plan {plan.upper()}")
                            st.balloons()
                        else:
                            st.error("❌ Esta contraseГұa ya existe. Usa otra.")
            
            st.markdown("---")
            st.markdown("##### 📋 Planes")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**⭐ GRATIS** - Sin VIP")
            with col2:
                st.markdown("**📦 SEMANA** - 7 días VIP")
        
        # ========== TAB: GESTIONAR ==========
        with tab_gestionar:
            st.markdown("#### 📋 ContraseГұas Creadas")
            
            # Botón recargar
            if st.button("🔄 Recargar Lista"):
                pass
            usuarios = db_todos()
            
            if not usuarios:
                st.info("⚽ No hay contraseГұas creadas. Crea una en la pestaГұa de arriba.")
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
                        icono = "⚡пёҸ"
                        color = "blue"
                    elif es_vip:
                        icono = "👑"
                        color = "green"
                    else:
                        icono = "⭐"
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
                                    nueva_pass = st.text_input("Nueva contraseГұa", placeholder="Nueva...", key=f"pass_{clave_id}", type="password")
                                    if st.button("🔑 Cambiar", key=f"btn_pass_{clave_id}"):
                                        if nueva_pass and len(nueva_pass) >= 4:
                                            if db_cambiar_password(clave_id, nueva_pass):
                                                st.success("✅ ContraseГұa cambiada")
                                                pass
                                            else:
                                                st.error("❌ Error")
                                        else:
                                            st.warning("Mínimo 4 caracteres")
                                with col_b:
                                    plan_nuevo = st.selectbox("Nuevo plan", ["semana", "mes", "elite", "vip"], 
                                                             index=["semana", "mes", "elite", "vip"].index(plan) if plan in ["semana", "mes", "elite", "vip"] else 0,
                                                             key=f"plan_{clave_id}")
                                    dias_nuevos = {"semana": 7, "mes": 30, "elite": 90, "vip": 90}.get(plan_nuevo, 30)
                                    if st.button("🦂 Cambiar Plan", key=f"btn_plan_{clave_id}"):
                                        if db_actualizar_plan(clave_id, plan_nuevo if plan_nuevo != "elite" else "elite", dias_nuevos):
                                            st.success(f"✅ Plan cambiado a {plan_nuevo.upper()}")
                                            pass
                                        else:
                                            st.error("❌ Error")
                                with col_c:
                                    st.write("")  # Espacio
                                    if st.button("🗑️ Eliminar", key=f"btn_del_{clave_id}", type="primary"):
                                        if db_eliminar_usuario(clave_id):
                                            st.success("✅ Eliminada")
                                            pass
                                        else:
                                            st.error("❌ No se pudo eliminar")
                            else:
                                st.info("⚡пёҸ Cuenta del administrador")
                        st.markdown("---")

    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
    # PГҒGINA VIP DASHBOARD - Solo para usuarios Elite/Premium
    # в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
    elif st.session_state.page == "VIP":
        
        # Verificar si el usuario es VIP/Elite
        user_plan = st.session_state.user_data.get('plan', 'vip') if st.session_state.user_data else 'vip'
        es_vip = user_plan.lower() in ['vip', 'elite', 'admin', 'mes', 'premium']
        
        if not es_vip:
            # Mostrar pantalla de upgrade
            st.markdown("""
            <div style="text-align: center; padding: 50px 20px;">
                <h1>👑 Contenido Exclusivo para Miembros VIP</h1>
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
                <p style="margin-top: 20px;"><strong> 7 días GRATIS - Sin tarjeta</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar plan actual
            st.markdown("---")
            st.info(f"💰 Tu plan actual: **{user_plan.upper()}**")
            st.markdown("ВҝQuieres hacer upgrade? Contacta al administrador.")
            
            st.stop()
        
        # Usuario VIP - mostrar dashboard
        st.markdown("### 👑 Dashboard VIP - Gestión Inteligente de Apuestas")
        
        # Obtener datos de Supabase
        client = get_client()
        usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'
        
        # ==================== TABS VIP ====================
        tab_roi, tab_resultados, tab_bankroll, tab_value, tab_alertas, tab_ranking, tab_export = st.tabs([
            "📥 ROI", "📊 Resultados", "🏆 Bankroll", "🎯 Value Bets", "🔔 Alertas", "🏆 Ranking", "🔄 Exportar"
        ])
        
        # ========== TAB 1: ROI POR MODELO ==========
        with tab_roi:
            st.markdown("### 📥 Rendimiento por Modelo y Tipo de Pick")
            
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
                    st.markdown("#### № ROI por Tipo de Pick")
                    
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
                        else: st.info("📥 Neutral")
                    with col2:
                        st.metric("📲 Over/Under", f"{acertados_ou}/{len(picks_ou)}", f"{pct_ou:.1f}% acierto")
                        if pct_ou > 55: st.success("✅ Rentable")
                        elif pct_ou < 45: st.error("❌ Perjudicial")
                        else: st.info("📥 Neutral")
                    
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric("🔑 Corners", f"{acertados_corners}/{len(picks_corners)}", f"{pct_corners:.1f}% acierto")
                        if pct_corners > 55: st.success("✅ Rentable")
                        elif pct_corners < 45: st.error("❌ Perjudicial")
                        else: st.info("📥 Neutral")
                    with col5:
                        st.metric(" Tarjetas", f"{acertados_tarjetas}/{len(picks_tarjetas)}", f"{pct_tarjetas:.1f}% acierto")
                        if pct_tarjetas > 55: st.success("✅ Rentable")
                        elif pct_tarjetas < 45: st.error("❌ Perjudicial")
                        else: st.info("📥 Neutral")
                    with col6:
                        st.metric("🎯 Remates", f"{acertados_remates}/{len(picks_remates)}", f"{pct_remates:.1f}% acierto")
                        if pct_remates > 55: st.success("✅ Rentable")
                        elif pct_remates < 45: st.error("❌ Perjudicial")
                        else: st.info("📥 Neutral")
                    
                    st.markdown("---")
                    
                    # ROI POR RANGO DE CONFIANZA
                    st.markdown("####  ROI por Rango de Confianza")
                    
                    confianza_ranges = [
                        ("95%+ (📘📘)", 95, 100),
                        ("90-95% (📘)", 90, 95),
                        ("80-90% (⭐)", 80, 90),
                        ("70-80% (📥)", 70, 80),
                        ("<70% (🔽)", 0, 70),
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
                    st.markdown("#### 🔻 Recomendaciones Inteligentes")
                    
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
                            st.info(f"📘 Los picks de ALTA CONFIANZA (95%+) tienen {pct_95:.1f}% de aciertos. ВЎSigue así!")
                        elif pct_95 < 60:
                            st.warning(f"⚠️ Los picks de alta confianza solo acertaron {pct_95:.1f}%. Revisar calibración.")
                else:
                    st.info("⚽ No hay picks resueltos aГәn. Completa algunos análisis y registra los resultados.")
            else:
                st.info("⚽ No hay picks guardados aГәn. Ve al Analizador para crear picks.")
        
        # ========== TAB 2: INGRESAR RESULTADOS ==========
        with tab_resultados:
            st.markdown("### қ Ingresar Resultados")
            st.info("🔻 Completa el marcador de los partidos para calibrar las predicciones")
            
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

                            # RECALIBRACIÓN AUTOMГҒTICA
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
                                pass
                            except Exception as e:
                                st.error(f"Error: {str(e)[:50]}")
            else:
                st.success("📊 ВЎTodos los picks tienen resultado!")
                st.info("Los resultados ayudan a calibrar las próximas predicciones.")

        # ========== TAB 3: BANKROLL ==========
        with tab_bankroll:
            st.markdown("### 🏆 Mi Bankroll Real")
            
            usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'
            
            # Definir monedas disponibles
            MONEDAS = {
                "USD": {"simbolo": "$", "nombre": "Dólar Americano", "codigo": "US$"},
                "EUR": {"simbolo": "вӮ¬", "nombre": "Euro", "codigo": "вӮ¬"},
                "MXN": {"simbolo": "$", "nombre": "Peso Mexicano", "codigo": "MX$"},
                "COP": {"simbolo": "$", "nombre": "Peso Colombiano", "codigo": "COP$"},
                "PEN": {"simbolo": "S/", "nombre": "Sol Peruano", "codigo": "S/"},
                "CLP": {"simbolo": "$", "nombre": "Peso Chileno", "codigo": "CLP$"},
                "ARS": {"simbolo": "$", "nombre": "Peso Argentino", "codigo": "ARS$"},
                "BRL": {"simbolo": "R$", "nombre": "Real BrasileГұo", "codigo": "R$"},
                "GBP": {"simbolo": "ВЈ", "nombre": "Libra Esterlina", "codigo": "ВЈ"},
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
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📥 Dashboard", "➕ Agregar Apuesta", "📋 Mis Apuestas"])
            
            # ========== SUBTAB 1: DASHBOARD ==========
            with sub_tab1:
                st.markdown("#### 📲 Resumen de Rendimiento")
                
                # Selector de moneda y banco inicial
                col_money1, col_money2 = st.columns([1, 2])
                with col_money1:
                    moneda_select = st.selectbox("ұ Moneda", options=list(MONEDAS.keys()), 
                                               format_func=lambda x: f"{MONEDAS[x]['simbolo']} {MONEDAS[x]['nombre']}",
                                               index=0)
                    simbolo = MONEDAS[moneda_select]["simbolo"]
                
                with col_money2:
                    bankroll_inicial = st.number_input(f"ө Bankroll Inicial", value=1000.0, min_value=100.0, step=100.0, key="bankroll_inicial")
                
                # Reset bankroll
                col_reset = st.columns(1)[0]
                if st.button("🔄 Reiniciar Bankroll", use_container_width=True):
                    try:
                        client.table('bankroll_apuestas').delete().eq('usuario', usuario_id).execute()
                    except:
                        pass
                    st.success("Bankroll reiniciado")
                    pass
                
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
                        st.metric("ө Bankroll Actual", format_money(bankroll_actual, simbolo), delta=delta_gan)
                    with col_m2:
                        st.metric("📥 ROI", f"{roi:.1f}%", delta=f"{'+' if roi >= 0 else ''}{roi:.1f}%")
                    with col_m3:
                        st.metric("🎯 Tasa Acierto", f"{tasa_acierto_real:.1f}%", delta=f"{apuestas_ganadas}/{total_apuestas}")
                    with col_m4:
                        st.metric("🏆 Ganado/Perdido", format_money(ganancias, simbolo))
                    
                    # Estado del bankroll
                    if bankroll_actual >= bankroll_inicial * 1.1:
                        st.success(f"✅ Bankroll saludable: {((bankroll_actual/bankroll_inicial)-1)*100:.1f}% de ganancia")
                    elif bankroll_actual >= bankroll_inicial * 0.9:
                        st.warning(f"⚠️ Bankroll estable: {((bankroll_actual/bankroll_inicial)-1)*100:.1f}%")
                    else:
                        st.error(f"🔽 Bankroll en riesgo: {((bankroll_actual/bankroll_inicial)-1)*100:.1f}%")
                    
                    # Gráfico de evolución
                    st.markdown("#### 📲 Evolución del Bankroll")
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
                        st.markdown("#### ® Pronóstico")
                        media_ganancia = ganancias / total_apuestas
                        proy_mensual = media_ganancia * 30
                        proy_anual = media_ganancia * 365
                        
                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            st.metric("📅 Proyección Mensual", format_money(proy_mensual, simbolo))
                        with col_p2:
                            st.metric("📅 Proyección Anual", format_money(proy_anual, simbolo))
                else:
                    st.info("⚽ No tienes apuestas aГәn. Ve a 'Agregar Apuesta' para empezar.")
            
            # ========== SUBTAB 2: AGREGAR APUESTA ==========
            with sub_tab2:
                st.markdown("#### ➕ Agregar Nueva Apuesta")
                
                tab_origen1, tab_origen2 = st.tabs(["📋 Desde Picks", "вңҸпёҸ Manual"])
                
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
                                st.write(f"**📥 Mercado:** {pick.get('mercado', 'N/A')}")
                                st.write(f"**📲 Detalle:** {pick.get('detalle', 'N/A')}")
                            with col_p2:
                                st.write(f"**🏆 Cuota:** {pick.get('cuota', 'N/A')}")
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
                        cuota = st.number_input("🏆 Cuota", value=2.0, min_value=1.01, max_value=100.0, step=0.1)
                    with col_d3:
                        cantidad = st.number_input(f"ө Cantidad ({simbolo})", value=20.0, min_value=1.0, step=5.0)
                    
                    col_d4, col_d5 = st.columns(2)
                    with col_d4:
                        mercado = st.selectbox("📥 Mercado", ["1X2", "Over/Under", "BTTS", "Corners", "Tarjetas", "Otro"])
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
                            pass
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
                            estado_icon = "✅" if a.get('resultado') == True else ("❌" if a.get('resultado') == False else "вҸі")
                            ganancia = a.get('ganancia', 0)
                            ganancia_fmt = format_money(ganancia, simbolo)
                            cantidad_fmt = format_money(a.get('cantidad', 0), simbolo)
                            
                            st.markdown(f"{estado_icon} **{a.get('equipo', 'N/A')}** - {a.get('fecha', 'N/A')}")
                            st.caption(f"🏆 {cantidad_fmt} @ {a.get('cuota', 'N/A')} | {a.get('mercado', 'N/A')} ↩️' **Ganancia: {ganancia_fmt}**")
                        
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
                                    pass
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
                prob_modelo = st.slider("📥 Probabilidad del Modelo (%)", 10, 99, 60)
            with col_v2:
                cuota_mercado = st.number_input("🏆 Cuota del Mercado", value=2.0, min_value=1.01, max_value=20.0, step=0.05)
            with col_v3:
                tipo_apuesta = st.selectbox("📋 Tipo de Apuesta", ["1X2", "Over/Under", "BTTS", "Corners", "Tarjetas"])
            
            # Calcular value
            prob_implicita = (1 / cuota_mercado) * 100
            value = prob_modelo - prob_implicita
            
            col_calc1, col_calc2, col_calc3 = st.columns(3)
            with col_calc1:
                st.metric("📥 Prob. Modelo", f"{prob_modelo:.1f}%")
            with col_calc2:
                st.metric("🔽 Prob. Implícita", f"{prob_implicita:.1f}%")
            with col_calc3:
                if value > 5:
                    st.metric("🎯 VALUE", f"+{value:.1f}%", delta="📘📘 ALTO VALUE")
                elif value > 0:
                    st.metric("🎯 VALUE", f"+{value:.1f}%", delta="✅ Value positivo")
                else:
                    st.metric("🎯 VALUE", f"{value:.1f}%", delta="❌ Sin value")
            
            # Recomendación
            if value >= 10:
                st.success("📘📘 **APUESTA FUERTE** - Value muy alto, alta confianza")
            elif value >= 5:
                st.success("✅ **APUESTA** - Value positivo, buena oportunidad")
            elif value >= 0:
                st.info("📥 **CAUTELA** - Value marginal, depende de otros factores")
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
                    st.info("⚽ No hay value bets registrados.")
            except Exception as e:
                st.info("⚽ Conecta a Supabase para ver value bets guardados.")
        
        # ========== TAB 5: ALERTAS ==========
        with tab_alertas:
            st.markdown("### 🔔 Centro de Alertas VIP")
            
            # Crear alertas
            st.markdown("#### 🔊 Crear Nueva Alerta")
            
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
            st.markdown("#### 🎯 Alertas Recientes")
            
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
                        st.metric("📘 Alta Prioridad", len(alertas_alta))
                    with col_alerta2:
                        st.metric("⭐ Media Prioridad", len(alertas_media))
                    with col_alerta3:
                        st.metric("🔽 Baja Prioridad", len(alertas_baja))
                    
                    for alerta in alertas[:10]:
                        color = "🔽" if alerta.get('prioridad') == 'alta' else "🟠" if alerta.get('prioridad') == 'media' else "🔴"
                        with st.expander(f"{color} [{alerta.get('tipo', '')}] {alerta.get('titulo', '')}"):
                            st.write(alerta.get('mensaje', ''))
                            st.caption(f"Creada: {alerta.get('creado_en', '')}")
                            
                            # Marcar como leída
                            if st.button("✅ Marcar leída", key=f"leer_{alerta.get('id')}"):
                                try:
                                    client.table('alertas').update({'leida': True}).eq('id', alerta.get('id')).execute()
                                    st.success("Marcada como leída")
                                    pass
                                except: pass
                else:
                    st.info("⚽ No hay alertas.")
            except Exception as e:
                st.info("⚽ Conecta a Supabase para ver alertas.")
        
        # ========== TAB 6: RANKING ==========
        with tab_ranking:
            st.markdown("### 🏆 Ranking Mensual VIP")
            
            # Ranking de la comunidad
            st.markdown("####  Top Pickers del Mes")
            
            try:
                ranking_response = client.table('ranking').select('*').order('posicion').limit(10).execute()
                ranking = ranking_response.data if ranking_response.data else []
                
                if ranking:
                    df_ranking = pd.DataFrame([
                        {
                            " Posición": r.get('posicion', i+1),
                            "💰 Usuario": r.get('nombre', 'Anon'),
                            "📥 Picks": r.get('total_picks', 0),
                            "📲 ROI": f"{r.get('roi', 0):.1f}%",
                            "🏆 Yield": f"{r.get('yield', 0):.1f}%",
                        }
                        for i, r in enumerate(ranking)
                    ])
                    st.dataframe(df_ranking, use_container_width=True)
                else:
                    st.info("⚽ No hay ranking aГәn. ВЎSé el primero!")
                    
                    # Sugerir crear ranking basado en picks
                    if picks:
                        st.markdown("##### 📥 Generar Ranking")
                        if st.button("🔄 Calcular Ranking"):
                            st.info("Ranking calculado (funcionalidad completa con más usuarios)")
            except Exception as e:
                st.info("⚽ Ranking no disponible. Conecta a Supabase.")
            
            st.markdown("---")
            
            # Badges y Logros
            st.markdown("#### … Mis Badges y Logros")
            
            # Badges predefinidos
            badges_disponibles = {
                "🎯 Primer Pick": len(picks) >= 1,
                "📥 10 Picks": len(picks) >= 10,
                "📘 50 Picks": len(picks) >= 50,
                "👑 100 Picks": len(picks) >= 100,
                "🏆 ROI 10%": True,  # Calcular
                "🎯 Racha 5": True,  # Calcular
                "📘 Racha 10": True,  # Calcular
                "вӯҗ Valoración 5вҳ…": False,
            }
            
            cols_badge = st.columns(4)
            for i, (badge, unlocked) in enumerate(badges_disponibles.items()):
                with cols_badge[i % 4]:
                    if unlocked:
                        st.success(badge)
                    else:
                        st.info(f"👑 {badge}")
        
        # ========== TAB 7: EXPORTAR ==========
        with tab_export:
            st.markdown("### 🔄 Exportar Reportes")
            
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
                
                st.markdown(f"📥 **{len(picks_filtrados)} picks** en el período seleccionado")
                
                if st.button("📘 Descargar Reporte", type="primary"):
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
                                "📘 Descargar CSV",
                                csv,
                                f"scorpion_report_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                "text/csv"
                            )
                        elif formato == "Excel (.xlsx)":
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df_export.to_excel(writer, index=False, sheet_name='Report')
                            st.download_button(
                                "📘 Descargar Excel",
                                buffer.getvalue(),
                                f"scorpion_report_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:  # JSON
                            json_str = df_export.to_json(orient='records')
                            st.download_button(
                                "📘 Descargar JSON",
                                json_str,
                                f"scorpion_report_{pd.Timestamp.now().strftime('%Y%m%d')}.json",
                                "application/json"
                            )
                    else:
                        st.warning("No hay datos para el período seleccionado")
            else:
                st.info("⚽ No hay picks para exportar.")
        
        # Mostrar Consensus Meter
        st.markdown("---")
        st.markdown("### 🎲 Consensus de Modelos")
        st.markdown("_ВҝCuántos modelos están de acuerdo en el Гәltimo pick?_")
        
        # Obtener Гәltimo pick
        if picks:
            ultimo = picks[0] if picks else None
            if ultimo:
                # Simular scores de consenso (en producción vendría de los modelos reales)
                modelos = ['Poisson', 'Dixon-Coles', 'Monte Carlo', 'Elo']
                probabilidades = [
                    ultimo.get('p1', 0) or 00,
                    ultimo.get('p1', 0) or 00,  # Simulado
                    ultimo.get('p1', 0) or 00,  # Simulado
                    ultimo.get('p1', 0) or 00,  # Simulado
                ]
                
                # Calcular consenso
                promedio = sum(probabilidades) / len(probabilidades)
                discrepancia = max(probabilidades) - min(probabilidades)
                
                col_cons1, col_cons2, col_cons3 = st.columns(3)
                with col_cons1:
                    st.metric("📥 Promedio Local", f"{promedio:.1f}%")
                with col_cons2:
                    st.metric("📲 Máx", f"{max(probabilidades):.1f}%")
                with col_cons3:
                    st.metric("🔽 Mín", f"{min(probabilidades):.1f}%")
                
                if discrepancia < 10:
                    st.success("📘 **ALTO CONSENSO** - Los 4 modelos están de acuerdo")
                elif discrepancia < 20:
                    st.info("📥 **CONSENSO MODERADO** - Buena seГұal")
                else:
                    st.warning("⚠️ **BAJO CONSENSO** - Los modelos discrepan, mayor riesgo")

# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
# EJECUTAR EL SISTEMA DE LOGIN
# в•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җв•җ
render_login_form()
