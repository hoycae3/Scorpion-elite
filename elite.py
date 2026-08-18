import streamlit as st
import pandas as pd
import os
import re
import time
import requests
import logging
import html
import math
import random
import io
import bcrypt
import psycopg2
from datetime import timedelta, datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# set_page_config debe ser el primer comando de Streamlit
st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

from app_helpers import (
    COLORS,
    LIGAS_MAP,
    hash_password,
    verify_password,
    get_hoy,
    utc_to_colombia,
    get_pais_emoji,
    crear_badges,
    fila_dato,
    safe_fmt,
    safe_fmt_int,
    calcular_value,
    format_money,
)

# Configurar logging (antes del try que usa logger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS global cargado desde archivo (version forzada para cache busting)
try:
    with open('styles.css', 'r') as f:
        css_content = f.read()
        # Forzar cache bust con version
        st.markdown(f'<style>/* v20260817e */ {css_content}</style>', unsafe_allow_html=True)
except Exception as e:
    logger.warning(f"Error en linea 43: {e}")

# Cargar variables de entorno desde .env si existe
# En producción (Render) las variables vienen del Dashboard
load_dotenv()

from analysis_models import calcular, pp
from funciones_stats import obtener_ultimos_partidos_equipo, guardar_stats_equipo, calcular_promedios_equipo, obtener_stats_partido, obtener_stats_totales_partido, cargar_cuotas_fixture
from calibration import (
    get_lambda_ajustada,
    obtener_factores_completos,
    registrar_resultado,
)


@st.cache_data(ttl=30)  # Cachear conteos por 30 segundos
def get_conteos_cached():
    """Obtiene conteos básicos (cached para velocidad)"""
    client = get_client()
    try:
        part_count = len(client.table('partidos').select('fixture_id').execute().data or [])
        eq_count = len(client.table('equipos_stats').select('team_id').execute().data or [])
        picks_count = len(client.table('picks').select('id').execute().data or [])
        return part_count, eq_count, picks_count
    except Exception as e:
        return 0, 0, 0


@st.cache_data(ttl=60)  # Cachear partidos por 60 segundos
def get_partidos_cache():
    """Obtiene partidos (cached para velocidad)"""
    client = get_client()
    try:
        return client.table('partidos').select('*').execute().data or []
    except Exception as e:
        return []

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
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Verificar/crear columna team_id en equipos_stats
        try:
            client.table('equipos_stats').select('team_id').limit(1).execute()
        except Exception as e:
            # La columna no existe, intentar crear mediante RPC
            logger.info("Verificando columna team_id en equipos_stats...")
        return client
    except Exception as e:
        logger.error(f"Error al crear cliente Supabase: {e}")
        return None

def get_client():
    """Función de compatibilidad - retorna cliente de Supabase"""
    return get_supabase_client()


def recalcular_lambda_equipo(client, team_id):
    """
    Recalcula lambda_local y lambda_visitante de UN solo equipo desde su historial.
    Usar después de guardar un FT para mantener el lambda actualizado.
    """
    try:
        partidos = client.table('equipo_partidos_stats').select(
            'goles_favor, es_local'
        ).eq('team_id', team_id).execute()

        if not partidos.data:
            return

        partidos_local = [p for p in partidos.data if p.get('es_local') == True]
        partidos_visit = [p for p in partidos.data if p.get('es_local') == False]

        if partidos_local:
            gf_local = sum(p.get('goles_favor', 0) or 0 for p in partidos_local)
            lambda_local = round(gf_local / len(partidos_local), 2)
        else:
            lambda_local = 1.3

        if partidos_visit:
            gf_visit = sum(p.get('goles_favor', 0) or 0 for p in partidos_visit)
            lambda_visit = round(gf_visit / len(partidos_visit), 2)
        else:
            lambda_visit = 1.1

        client.table('equipos_stats').update({
            'lambda_local': lambda_local,
            'lambda_visitante': lambda_visit
        }).eq('team_id', team_id).execute()
    except Exception as e:
        logger.warning(f"Error recalculando lambda de equipo {team_id}: {e}")


def recalcular_lambdas_desde_historial(client):
    """
    Recalcula lambda_local y lambda_visitante desde equipo_partidos_stats.
    
    Esta función lee todos los partidos del historial y calcula:
    - lambda_local = goles_favor_LOCAL / partidos_LOCAL
    - lambda_visitante = goles_favor_VISITANTE / partidos_VISITANTE
    
    Esto corrige valores corruptos que se guardaron incorrectamente.
    """
    try:
        # Obtener todos los equipos únicos
        equipos = client.table('equipos_stats').select('team_id, equipo').execute()
        
        if not equipos.data:
            return 0, "No hay equipos para actualizar"
        
        actualizados = 0
        errores = 0
        
        for equipo in equipos.data:
            team_id = equipo.get('team_id')
            if not team_id:
                continue
            
            try:
                recalcular_lambda_equipo(client, team_id)
                actualizados += 1
            except Exception as e:
                errores += 1
        
        return actualizados, f"Actualizados: {actualizados}, Errores: {errores}"
        
    except Exception as e:
        return 0, f"Error general: {str(e)}"


def migrate_team_id_column():
    """Migra la columna team_id a la tabla equipos_stats si no existe"""
    try:
        # Obtener connection string de las variables de entorno de Render
        conn_url = os.getenv('DATABASE_URL', '')
        if not conn_url and os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
            supabase_host = os.getenv('SUPABASE_URL').replace('https://', '').replace('http://', '')
            conn_url = f"postgresql://postgres:{os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')}@db.{supabase_host}:5432/postgres"
        
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

def migrate_picks_columns():
    """Agrega columnas faltantes (arco, confianza) a la tabla picks si no existen.
    La tabla picks en producción se creó antes de añadir las predicciones de tiros
    a arco, por lo que estas columnas faltan y provocan PGRST204 al guardar picks."""
    try:
        conn_url = os.getenv('DATABASE_URL', '')
        if not conn_url and os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_ROLE_KEY'):
            supabase_host = os.getenv('SUPABASE_URL').replace('https://', '').replace('http://', '')
            conn_url = f"postgresql://postgres:{os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')}@db.{supabase_host}:5432/postgres"

        if conn_url:
            conn = psycopg2.connect(conn_url)
            cur = conn.cursor()
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS prediccion_arco VARCHAR(20);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_total_estimado DECIMAL(5,2);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_local DECIMAL(5,2);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_visitante DECIMAL(5,2);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_over_prob DECIMAL(5,2);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_under_prob DECIMAL(5,2);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS resultado_arco VARCHAR(20);')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS acertado_arco BOOLEAN;')
            cur.execute('ALTER TABLE picks ADD COLUMN IF NOT EXISTS confianza INTEGER;')
            # Forzar recarga del caché de esquema de PostgREST (Supabase) para que
            # reconozca las columnas nuevas inmediatamente, evitando PGRST204.
            cur.execute("NOTIFY pgrst, 'reload schema'")
            conn.commit()
            cur.close()
            conn.close()
            logger.info("✅ Migration completada: columnas arco y confianza en picks")
    except Exception as e:
        logger.warning(f"Migration picks error: {e}")

# ══════════════════════════════════════════════════════════
# SISTEMA DE USUARIOS (Supabase) - Solo hash bcrypt
# (hash_password, verify_password, get_hoy importados de app_helpers)
# ══════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════
# 🔧 FUNCIONES HELPER (módulo-level, no se redefinen en cada rerun)
# (get_pais_emoji, crear_badges, fila_dato, safe_fmt, safe_fmt_int,
#  calcular_value, format_money, utc_to_colombia importados de app_helpers)
# ══════════════════════════════════════════════════════════

def obtener_promedios_dinamicos(client, equipo_nombre, team_id=None):
    if team_id:
        resp_check = client.table('equipo_partidos_stats').select('team_id').eq('team_id', team_id).limit(1).execute()
        if resp_check.data:
            return calcular_promedios_equipo(client, team_id)
    resp_eps = client.table('equipo_partidos_stats').select('team_id').ilike('equipo', f'%{equipo_nombre}%').limit(5).execute()
    if resp_eps.data:
        return calcular_promedios_equipo(client, resp_eps.data[0]['team_id'])
    palabras = equipo_nombre.split()
    for palabra in palabras:
        if len(palabra) > 3:
            resp_eps = client.table('equipo_partidos_stats').select('team_id').ilike('equipo', f'%{palabra}%').limit(1).execute()
            if resp_eps.data:
                return calcular_promedios_equipo(client, resp_eps.data[0]['team_id'])
    return None

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
    client = get_client()
    if not client:
        return False
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
    
    # Botón 🔑 Acceder arriba
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🔑 Acceder", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.rerun()

    # --- KPIs EN VIVO ---
    st.markdown("##### 📥 Métricas")

    # Obtener métricas REALES de Supabase
    try:
        client = get_client()
        if client:
            # Obtener picks (solo campos necesarios para KPIs)
            response = client.table('picks').select(
                'acertado_1x2,prediccion_1x2,confianza,rango'
            ).execute()
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

    # Obtener partidos (con cache en session_state para velocidad)
    # Solo recargar si no existe o si pasó más de 30 segundos
    cache_key = 'partidos_cache'
    cache_time_key = 'partidos_cache_time'
    should_refresh = (
        cache_key not in st.session_state or
        cache_time_key not in st.session_state or
        (time.time() - st.session_state.get(cache_time_key, 0)) > 30
    )
    
    if should_refresh:
        try:
            client = get_client()
            if client:
                # Solo traer campos necesarios (menos datos)
                response = client.table('partidos').select(
                    'fixture_id,fecha,hora,equipo_local,equipo_visitante,liga,estado'
                ).execute()
                st.session_state[cache_key] = response.data or []
            else:
                st.session_state[cache_key] = []
        except Exception as e:
            logger.error(f"Error obteniendo partidos: {e}")
            st.session_state[cache_key] = []
        st.session_state[cache_time_key] = time.time()
    
    partidos = st.session_state.get(cache_key, [])

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
        if st.button("↩️ Volver", key="volver_partidos"):
            st.session_state.preview_partido = None
        
        st.markdown("---")
        
        # Obtener stats de equipos
        try:
            client = get_client()
            team_id_local = partido.get('team_id_local')
            team_id_visitante = partido.get('team_id_visitante')
            
            if client:
                # 1️⃣ Buscar por nombre
                local_resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{local}%').execute()
                visit_resp = client.table('equipos_stats').select('*').ilike('equipo', f'%{visitante}%').execute()

                stats_local = local_resp.data[0] if local_resp.data else None
                stats_visit = visit_resp.data[0] if visit_resp.data else None

                # 2️⃣ Fallback: buscar por team_id si no se encontró por nombre
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
                        gf_l_str = safe_fmt(gf_l)
                        gc_l_str = safe_fmt(gc_l)
                        st.markdown(f"**GF/GC:** <span style='color:black;font-weight:bold'>{gf_l_str}/{gc_l_str}</span>", unsafe_allow_html=True)
                        lambda_l = promedios_dinamicos_local.get('lambda_ponderado', stats_local.get('lambda_local', 0)) if promedios_dinamicos_local else stats_local.get('lambda_local', 0)
                        st.markdown(f"**Ataque:** <span style='color:black;font-weight:bold'>{lambda_l:.2f}</span> goles/partido", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"**✈️ {visitante}**")
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
                        gf_v_str = safe_fmt(gf_v)
                        gc_v_str = safe_fmt(gc_v)
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
        # MOSTRAR SOLO 4 PARTIDOS ALEATORIOS EN LANDING
        if partidos:
            # La hora ya viene en zona horaria de Colombia (UTC-5) desde la sync
            partidos_procesados = []
            for p in partidos:
                fecha = p.get('fecha', '')
                hora_colombia = p.get('hora', '')[:5]

                partidos_procesados.append({
                    **p,
                    'hora_colombia': hora_colombia,
                    'fecha_hora': f"{fecha} {hora_colombia}"
                })
            
            # Mostrar solo 4 partidos aleatorios
            if len(partidos_procesados) >= 4:
                partidos_aleatorios = random.sample(partidos_procesados, 4)
            else:
                partidos_aleatorios = partidos_procesados
            
            st.markdown("###### 🎯 ⚽ Partidos Destacados")
            st.caption("Análisis gratuito sin registro")
            
            cols = st.columns(2)
            for i, partido in enumerate(partidos_aleatorios):
                local = partido.get('equipo_local', 'Local')
                visitante = partido.get('equipo_visitante', 'Visitante')
                liga = partido.get('liga', '')
                hora_col = partido.get('hora_colombia', '')
                fecha = partido.get('fecha', '')
                fixture_id = partido.get('fixture_id', 0)
                
                with cols[i % 2]:
                    if st.button(f"⚽ {local} vs {visitante}", key=f"landing_{fixture_id}_{i}", use_container_width=True):
                        st.session_state['partido_seleccionado'] = partido
                        st.session_state['show_analizador'] = True
                        st.query_params["page"] = "analizador"
                    
                    st.caption(f"⚽ {hora_col} | {liga}")
        else:
            st.info("⚽ No hay partidos disponibles.")

    # --- CÓMO FUNCIONA ---
    st.markdown("### 📤 ¿Cómo Funciona?")
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
            <td class="se-duration">30 Días <span class="se-badge se-badge-hot">MÁS POPULAR 📘</span></td>
            <td class="se-price">$24.99</td>
            <td>Plan 1 Mes</td>
        </tr>
        <tr>
            <td class="se-duration">365 Días <span class="se-badge se-badge-success">AHORRA 36%</span></td>
            <td class="se-price">$189.99</td>
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
    # ===== INICIALIZAR SESSION_STATE =====
    if 'selected_match_data' not in st.session_state:
        st.session_state.selected_match_data = None
    if 'selected_local' not in st.session_state:
        st.session_state.selected_local = None
    if 'selected_away' not in st.session_state:
        st.session_state.selected_away = None
    if 'home' not in st.session_state:
        st.session_state.home = ''
    if 'away' not in st.session_state:
        st.session_state.away = ''
    if 'logged' not in st.session_state:
        st.session_state.logged = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    # ===== FIN INICIALIZACION =====

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
                        st.rerun()  # Recargar después de login
                    else:
                        st.error("❌ Contraseña incorrecta")

        with col_cancel:
            if st.button("↩️ Volver", use_container_width=True):
                st.session_state.show_login = False

        st.stop()

    # Sidebar con información del usuario
    # Migración de columnas de picks (arco, confianza) - una sola vez por sesión
    if not st.session_state.get('picks_migrated'):
        migrate_picks_columns()
        st.session_state.picks_migrated = True

    with st.sidebar:
        st.markdown("## 🦂 Scorpion Elite")
        user_plan = st.session_state.user_data.get('plan', 'vip') if st.session_state.user_data else 'vip'
        dias = st.session_state.user_data.get('dias', 0) if st.session_state.user_data else 0
        is_admin = st.session_state.user_data.get('es_admin', 0) == 1 if st.session_state.user_data else False
        
        plan_icon = {"admin": "⚡️", "elite": "👑", "vip": "👑", "mes": "👑", "free": "⭐"}.get(user_plan, "🦂")
        st.markdown(f"{plan_icon} **{user_plan.upper()}**")
        if not is_admin:
            st.caption(f"⏱️ {dias} días restantes")
        
        st.markdown("---")
        if st.button("👑 Logout", use_container_width=True):
            st.session_state.logged = False
            st.session_state.user_data = None
            st.session_state.is_admin = False
    
    # Menú horizontal arriba - según tipo de usuario
    st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    
    # Construir menú dinámicamente según tipo de usuario
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
    
    st.markdown("---")

    # Página: Partidos (NUEVA)
    if st.session_state.page == "Partidos":
        render_partidos_page()
    elif st.session_state.page == "Analizador":
        render_analizador_page()
    elif st.session_state.page == "Claves":
        render_claves_page()
    elif st.session_state.page == "VIP":
        render_vip_page()


def calcular_resultados_partido(score_local, score_visitante):
    """Calcula los resultados reales (1X2, O/U, BTTS) de un partido finalizado."""
    total_goles = score_local + score_visitante
    if score_local > score_visitante:
        resultado_real = "1"
    elif score_local < score_visitante:
        resultado_real = "2"
    else:
        resultado_real = "X"
    resultado_ou_real = "Over 2.5" if total_goles > 2.5 else "Under 2.5"
    btts_real = "Si" if (score_local > 0 and score_visitante > 0) else "No"
    return resultado_real, resultado_ou_real, btts_real


def apuesta_ganada(apuesta, pick, resultado_real, resultado_ou_real, btts_real, stats_reales=None):
    """Determina si una apuesta del bankroll fue ganada según el mercado apostado."""
    mercado = apuesta.get('mercado', '')
    if mercado == '1X2':
        return pick.get('prediccion_1x2') == resultado_real
    prediccion_ou = pick.get('prediccion_ou', '')
    if 'Over' in prediccion_ou or 'Under' in prediccion_ou:
        return prediccion_ou == resultado_ou_real
    prediccion_btts = pick.get('prediccion_btts', '')
    if 'Si' in prediccion_btts or 'No' in prediccion_btts:
        return prediccion_btts == btts_real
    if stats_reales:
        if mercado == 'Corners':
            pred = pick.get('prediccion_corners', '')
            real = stats_reales.get('corners_total', 0)
            return _evaluar_over_under(pred, real, 9.5)
        if mercado == 'Tarjetas':
            pred = pick.get('prediccion_tarjetas', '')
            real = stats_reales.get('tarjetas_total', 0)
            return _evaluar_over_under(pred, real, 6)
        if mercado == 'Remates':
            pred = pick.get('prediccion_remates', '')
            real = stats_reales.get('remates_total', 0)
            return _evaluar_over_under(pred, real, 24)
        if mercado == 'Tiros Arco':
            pred = pick.get('prediccion_arco', '')
            real = stats_reales.get('tiros_arco_total', 0)
            return _evaluar_over_under(pred, real, 8)
    return False


def _evaluar_over_under(prediccion, real, linea_default):
    """Evalua si un pick Over/Under acerto comparando con el valor real."""
    if not prediccion or real is None:
        return False
    pred_lower = str(prediccion).lower()
    if 'over' in pred_lower:
        return real > linea_default
    if 'under' in pred_lower:
        return real < linea_default
    return False


def actualizar_bankroll_apuestas(client, fix_id, pick, resultado_real, resultado_ou_real, btts_real, stats_reales=None):
    """Marca apuestas del bankroll como ganadas/perdidas para un fixture."""
    apuestas = client.table('bankroll_apuestas').select('*').eq('fixture_id', fix_id).execute()
    if not apuestas.data:
        return
    for apuesta in apuestas.data:
        apuesta_id = apuesta.get('id')
        cantidad = apuesta.get('cantidad', 0)
        cuota = apuesta.get('cuota', 2.0)
        gano = apuesta_ganada(apuesta, pick, resultado_real, resultado_ou_real, btts_real, stats_reales)
        ganancia = cantidad * (cuota - 1) if gano else -cantidad
        client.table('bankroll_apuestas').update({
            'resultado': gano,
            'ganancia': ganancia
        }).eq('id', apuesta_id).execute()


def sincronizar_partidos():
    """Ejecuta la sincronización de partidos desde API-Football."""
    # Barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.info("🔄 Iniciando sincronización...")
    try:
        # Migrar columna team_id si no existe
        migrate_team_id_column()

        # ═══════════════════════════════════════════════════════════════
        # CONFIGURACIÓN INICIAL
        # ═══════════════════════════════════════════════════════════════
        client = get_client()
        if not client:
            st.error("❌ No se pudo conectar a Supabase")
            st.stop()

        API_URL = "https://v3.football.api-sports.io"
        API_KEY = os.getenv("API_FOOTBALL_KEY", "")
        headers = {'x-apisports-key': API_KEY}
        hoy = datetime.now(timezone(timedelta(hours=-5))).date()
        hoy_str = hoy.strftime('%Y-%m-%d')

        # Contador de picks auto-actualizados (inicializado aquí porque se usa en PASO 1)
        picks_actualizados_auto = 0

        # Calcular temporada dinámicamente: Ago-Dic ↩️' season actual, Ene-Jul ↩️' season anterior
        season = hoy.year if hoy.month >= 8 else hoy.year - 1
        # Usar la misma temporada para stats (la API ya tiene stats de la temporada actual)
        season_stats = season
        st.markdown(f"⚽ **Temporada partidos:** {season} | **Temporada stats:** {season_stats}")

        # ═══════════════════════════════════════════════════════════════
        # PASO 1: DESCARGAR PARTIDOS (SIN ESTADÍSTICAS DE EQUIPOS)
        # ═══════════════════════════════════════════════════════════════
        # Obtener partidos existentes para evitar duplicados
        partidos_existentes = set()
        partidos_existentes_fechas = {}  # ★ fixture_id → fecha (para detectar reprogramados)
        fecha_max_db = None
        try:
            resp_ex = client.table('partidos').select('fixture_id,fecha,estado').execute()
            if resp_ex.data:
                partidos_existentes = {p['fixture_id'] for p in resp_ex.data}
                # ★ Guardar fecha+estado de cada partido existente
                partidos_existentes_fechas = {
                    p['fixture_id']: {'fecha': str(p.get('fecha', ''))[:10], 'estado': p.get('estado', '')}
                    for p in resp_ex.data
                }
                # Encontrar la fecha máxima en la DB
                fechas = [p['fecha'] for p in resp_ex.data if p.get('fecha')]
                if fechas:
                    fecha_max_db = max(fechas)
        except Exception as e:
            logger.warning(f"Error en linea 1024: {e}")

        # ⚽ LÓGICA INTELIGENTE:
        # 1. Base vacía: Descargar HOY a HOY+6
        # 2. Base con datos: Descargar HOY-1 (resultados) + siguiente día de última fecha FUTURA

        ayer_date = hoy - timedelta(days=1)
        ayer = ayer_date.strftime('%Y-%m-%d')

        try:
            # Obtener todas las fechas únicas en la base
            resp_fechas = client.table('partidos').select('fecha').execute()

            if not resp_fechas.data:
                # Base vacía → descargar ventana completa
                fecha_inicio = hoy_str
                fecha_fin = (hoy + timedelta(days=6)).strftime('%Y-%m-%d')
                modo_sync = "☕ Completa (base vacía)"
            else:
                # Analizar fechas existentes
                fechas_futuras = []
                for p in resp_fechas.data:
                    try:
                        f = datetime.strptime(str(p['fecha'])[:10], '%Y-%m-%d').date()
                        if f >= hoy:
                            fechas_futuras.append(f)
                    except Exception as e:
                        logger.warning(f"Error en linea 1051: {e}")

                # Siempre descargar resultados de ayer
                fecha_inicio = ayer

                if fechas_futuras:
                    # Ya hay fechas futuras → buscar la última y descargar el siguiente día
                    ultima_futura = max(fechas_futuras)
                    siguiente_dia = (ultima_futura + timedelta(days=1)).strftime('%Y-%m-%d')
                    fecha_fin = siguiente_dia
                    modo_sync = f"☔ Incremental (última futura: {ultima_futura.strftime('%d/%m')})"
                else:
                    # No hay fechas futuras → descargar HOY+1
                    fecha_fin = (hoy + timedelta(days=1)).strftime('%Y-%m-%d')
                    modo_sync = "☔ Actualizar"

        except Exception as e:
            # Si hay error, descargar ventana completa por seguridad
            fecha_inicio = hoy_str
            fecha_fin = (hoy + timedelta(days=6)).strftime('%Y-%m-%d')
            modo_sync = "☕ Completa (fallback)"
            st.warning(f"⚽ Error: {e}")

        st.markdown(f"{modo_sync} ⚽ Rango: **{fecha_inicio}** al **{fecha_fin}**")

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
        partidos_actualizados = 0  # ★ Partidos existentes cuya fecha/estado cambió
        errores_api = 0  # Ligas donde la API devolvió error (429/403/500)
        primer_error_api = None  # Guardar el primer error para mostrarlo
        fixtures_totales = 0  # ★ Diagnóstico: total de fixtures que devolvió la API
        fixtures_duplicados = 0  # ★ Diagnóstico: fixtures que ya estaban en la DB
        fechas_api = set()  # ★ Diagnóstico: fechas que devolvió la API

        # Colección de equipos únicos: {team_id: {team_id, team_name, league_id, league_name, season}}
        equipos_unicos = {}

        # ★ NUEVO: Diccionario para rastrear partidos FT completados por equipo
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
                    fixtures_totales += len(fixtures)  # ★ Diagnóstico

                    # ★ Diagnóstico: rastrear fechas que devuelve la API
                    for f in fixtures:
                        fix = f.get('fixture', {})
                        f_date = fix.get('date', '')[:10]
                        fechas_api.add(f_date)

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

                        # Convertir fecha-hora UTC a zona horaria de Colombia (UTC-5)
                        # La API devuelve date en UTC; sin esto, un partido a las 19:00 de México
                        # (00:00 UTC del día siguiente) se guarda con fecha del día siguiente.
                        fecha_utc_str = fix.get('date', '')
                        colombia_tz = timezone(timedelta(hours=-5))
                        try:
                            utc_dt = datetime.fromisoformat(fecha_utc_str.replace('Z', '+00:00'))
                            col_dt = utc_dt.astimezone(colombia_tz)
                            fecha_col = col_dt.strftime('%Y-%m-%d')
                            hora_col = col_dt.strftime('%H:%M')
                        except (ValueError, TypeError):
                            fecha_col = fecha_utc_str[:10]
                            hora_col = fecha_utc_str[11:16]

                        es_partido_nuevo = fix_id not in partidos_existentes
                        if not es_partido_nuevo:
                            fixtures_duplicados += 1  # ★ Diagnóstico

                        # ★ Solo agregar equipos a equipos_unicos si:
                        # - El partido es nuevo (necesita stats para el analizador), O
                        # - El partido terminó FT (necesita procesar resultado para CASO B)
                        # Esto evita descargar stats de equipos de partidos que ya existen sin FT
                        if es_partido_nuevo or estado == 'FT':
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

                        # ★ NUEVO: Rastrear partidos FT (terminados) para sincronización incremental
                        if estado == 'FT' and fix_id:
                            fecha_partido = fecha_col
                            resultado_local = 'G' if (score_local > score_visitante) else ('E' if score_local == score_visitante else 'P')
                            resultado_visitante = 'G' if (score_visitante > score_local) else ('E' if score_local == score_visitante else 'P')

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

                        # ★ Guardar/actualizar partido en tabla partidos
                        # Siempre hacer upsert para actualizar fecha/estado/score de partidos
                        # reprogramados (mismo fixture_id, fecha diferente)
                        partido_data = {
                            'fixture_id': fix_id,
                            'fecha': fecha_col,
                            'hora': hora_col,
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
                            if es_partido_nuevo:
                                partidos_guardados += 1
                            else:
                                # ★ Detectar si la fecha o estado cambiaron (partido reprogramado)
                                existente = partidos_existentes_fechas.get(fix_id, {})
                                if existente.get('fecha', '') != fecha_col or existente.get('estado', '') != estado:
                                    partidos_actualizados += 1
                            # Actualizar progreso (10-30%)
                            progress_bar.progress(int(10 + (partidos_guardados / max(1, len(equipos_unicos)) * 20)))
                            status_text.info(f"📥 Guardando partidos... ({partidos_guardados} guardados, {partidos_actualizados} actualizados)")

                            # 🎯 AUTO-ACTUALIZAR PICKS: Si el partido ya terminó (FT), calcular resultados automáticamente
                            if estado == 'FT' and score_local is not None and score_visitante is not None:
                                try:
                                    resultado_real, resultado_ou_real, btts_real = calcular_resultados_partido(score_local, score_visitante)

                                    # 📊 Obtener stats totales del partido (córners, tarjetas, remates)
                                    stats_reales = obtener_stats_totales_partido(fix_id, headers, API_URL)

                                    # Buscar picks pendientes para este partido (por fixture_id O por nombres de equipos)
                                    picks_existentes = client.table('picks').select('*').is_('resultado_1x2', None).execute()

                                    for pick in picks_existentes.data:
                                        pick_fixture = pick.get('fixture_id', 0)
                                        pick_local = pick.get('equipo_local', '').lower().strip()
                                        pick_visit = pick.get('equipo_visitante', '').lower().strip()

                                        # Coincide por fixture_id O por nombres de equipos
                                        if (pick_fixture == fix_id or
                                            (equipo_local.lower().strip() == pick_local and
                                             equipo_visitante.lower().strip() == pick_visit)):
                                            pick_id = pick.get('id')
                                            acertado_1x2 = pick.get('prediccion_1x2') == resultado_real
                                            acertado_ou = pick.get('prediccion_ou') == resultado_ou_real
                                            acertado_btts = pick.get('prediccion_btts') == btts_real

                                            # Evaluar aciertos de córners, tarjetas, remates
                                            update_data = {
                                                'marcador': f"{score_local}-{score_visitante}",
                                                'resultado_1x2': resultado_real,
                                                'resultado_ou': resultado_ou_real,
                                                'resultado_btts': btts_real,
                                                'acertado_1x2': acertado_1x2,
                                                'acertado_ou': acertado_ou,
                                                'acertado_btts': acertado_btts,
                                                'fixture_id': fix_id,
                                            }

                                            if stats_reales:
                                                acertado_corners = _evaluar_over_under(
                                                    pick.get('prediccion_corners', ''),
                                                    stats_reales.get('corners_total'),
                                                    9.5
                                                )
                                                acertado_tarjetas = _evaluar_over_under(
                                                    pick.get('prediccion_tarjetas', ''),
                                                    stats_reales.get('tarjetas_total'),
                                                    6
                                                )
                                                acertado_remates = _evaluar_over_under(
                                                    pick.get('prediccion_remates', ''),
                                                    stats_reales.get('remates_total'),
                                                    24
                                                )
                                                acertado_arco = _evaluar_over_under(
                                                    pick.get('prediccion_arco', ''),
                                                    stats_reales.get('tiros_arco_total'),
                                                    8
                                                )
                                                update_data['resultado_corners'] = str(stats_reales.get('corners_total'))
                                                update_data['resultado_tarjetas'] = str(stats_reales.get('tarjetas_total'))
                                                update_data['resultado_remates'] = str(stats_reales.get('remates_total'))
                                                update_data['resultado_arco'] = str(stats_reales.get('tiros_arco_total'))
                                                update_data['acertado_corners'] = acertado_corners
                                                update_data['acertado_tarjetas'] = acertado_tarjetas
                                                update_data['acertado_remates'] = acertado_remates
                                                update_data['acertado_arco'] = acertado_arco

                                            _actualizar_pick_resiliente(client, update_data, pick_id)
                                            picks_actualizados_auto += 1

                                            # 🎰 AUTO-ACTUALIZAR BANKROLL
                                            try:
                                                actualizar_bankroll_apuestas(client, fix_id, pick, resultado_real, resultado_ou_real, btts_real, stats_reales)
                                            except Exception as e:
                                                logger.warning(f"Error actualizando bankroll fixture {fix_id}: {e}")
                                except Exception as e:
                                    logger.warning(f"Error auto-actualizando picks fixture {fix_id}: {e}")
                        except Exception as e:
                            st.warning(f"⚠️ Error al guardar partido {fix_id}: {e}")
                else:
                    # La API devolvió error (429=cuota agotada, 403=key inválida, 500=error servidor)
                    errores_api += 1
                    if primer_error_api is None:
                        mensaje_error = {
                            429: "❌ Cuota de API-Football agotada (límite diario alcanzado)",
                            403: "❌ API key inválida o expirada",
                            401: "❌ API key no autorizada",
                        }.get(resp.status_code, f"❌ API devolvió error {resp.status_code}")
                        primer_error_api = mensaje_error
            except Exception as e:
                # Si falla una liga, continuar con la siguiente
                continue

        # ═══════════════════════════════════════════════════════════════
        # ═══════════════════════════════════════════════════════════════
        # PASO 2: SINCRONIZACIÓN INCREMENTAL DE STATS DE EQUIPOS
        # - Equipos NUEVOS (0 records): Fetch 5 partidos iniciales
        # - Equipos EXISTENTES: Solo fetch partidos FT nuevos no guardados
        # ═══════════════════════════════════════════════════════════════

        equipos_stats_descargados = 0
        equipos_nuevos = 0
        equipos_existentes = 0
        stats_ft_nuevos = 0
        errores_equipos = 0
        partidos_iniciales_cargados = 0
        api_calls_ahorradas = 0  # ★ API calls evitadas por filtrado de FT ya guardados

        if equipos_unicos:

            # Paso 2a: Identificar equipos existentes en DB (tabla principal equipos_stats)
            equipos_existentes_ids = set()
            try:
                # Obtener todos los team_ids que ya tienen stats en equipos_stats
                resp_existing = client.table('equipos_stats').select('team_id').execute()
                if resp_existing.data:
                    equipos_existentes_ids = {p['team_id'] for p in resp_existing.data if p.get('team_id')}
            except Exception as e:
                logger.warning(f"Error identificando equipos existentes: {e}")
                equipos_existentes_ids = set()

            # Paso 2b: Para cada equipo, determinar si es nuevo o existente
            for idx, (tid, equipo) in enumerate(equipos_unicos.items()):
                team_id = equipo['team_id']
                team_name = equipo['team_name']
                league_id = equipo['league_id']
                season_eq = equipo['season']

                is_new_team = team_id not in equipos_existentes_ids

                # ★ CASO A: EQUIPO NUEVO (0 records en DB)
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
                                    # Actualizar progreso (30-70%)
                                    progress_bar.progress(int(30 + (equipos_stats_descargados / max(1, len(equipos_unicos)) * 40)))
                                    status_text.info(f"📊 Descargando stats equipos... ({equipos_stats_descargados}/{len(equipos_unicos)})")
                                except Exception as e:
                                    errores_equipos += 1

                        # ★ Fetch 5 partidos iniciales para equipo nuevo
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

                # ★ CASO B: EQUIPO EXISTENTE (ya tiene records en DB)
                else:
                    equipos_existentes += 1
                    ft_en_ventana = equipos_ft_fixtures.get(team_id, [])

                    # ★ OPTIMIZACIÓN: Filtrar FT ya guardados ANTES de buscar más
                    # Solo para equipos existentes (ya tienen registros)
                    fixtures_guardados = set()
                    try:
                        resp_fixtures = client.table('equipo_partidos_stats').select('fixture_id').eq('team_id', team_id).execute()
                        if resp_fixtures.data:
                            fixtures_guardados = {p['fixture_id'] for p in resp_fixtures.data}
                    except Exception as e:
                        st.warning(f"⚠️ Error al verificar fixtures de {team_name}: {e}")

                    # Filtrar los FT de la ventana que YA están guardados (0 API calls)
                    if ft_en_ventana:
                        antes = len(ft_en_ventana)
                        ft_en_ventana = [
                            f for f in ft_en_ventana
                            if f.get('fixture_id') not in fixtures_guardados
                        ]
                        api_calls_ahorradas += (antes - len(ft_en_ventana))

                    # ★ Solo buscar más FT vía API si hay FT pendientes en la ventana
                    # (evita 575 llamadas API innecesarias que causan timeout en Render)
                    if not ft_en_ventana:
                        # No hay FT pendientes en la ventana → saltar este equipo (0 API calls)
                        continue

                    # ★ Si hay FT pendientes en la ventana, procesarlos
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
                                # Recalcular lambda del equipo con el nuevo resultado
                                recalcular_lambda_equipo(client, team_id)
                            except Exception as e:
                                st.warning(f"⚠️ Error guardando FT {fix_info['fixture_id']} de {team_name}: {e}")

                        except Exception as e:
                            st.warning(f"⚠️ Error procesando FT {fix_info.get('fixture_id')} de {team_name}: {e}")

        # Actualizar progreso antes del resumen (70-90%)
        progress_bar.progress(90)
        status_text.info("📋 Generando resumen...")

        st.session_state.sincronizacion_ok = True

        # Completar barra de progreso
        progress_bar.progress(100)
        status_text.success("✅ **SINCRONIZACIÓN COMPLETADA**")

        # Mensaje especial si se actualizaron picks
        if picks_actualizados_auto > 0:
            st.success(f"🎯 Se actualizaron {picks_actualizados_auto} picks con los resultados de partidos terminados!")

        # ⚠️ Avisar si la API devolvió errores (cuota agotada, key inválida, etc.)
        if errores_api > 0:
            st.error(f"{primer_error_api} — Fallaron {errores_api} de las ligas. Revisa tu API key o cuota diaria de API-Football.")

        # RESUMEN FINAL
        st.markdown(f"""
        📥 **RESUMEN FINAL:**

        | Métrica | Valor |
        |---------|-------|
        | 🏆 **Ligas procesadas** | {ligas_procesadas} |
        | 📅 **Partidos guardados** | {partidos_guardados} |
        | 🔄 **Partidos actualizados (fecha/estado)** | {partidos_actualizados} |
        | 🔍 **Partidos descargados de API** | {fixtures_totales} |
        | ♻️ **Partidos ya en DB (duplicados)** | {fixtures_duplicados} |
        | 📆 **Fechas que devolvió la API** | {', '.join(sorted(fechas_api)) if fechas_api else 'Ninguna'} |
        | 👥 **Equipos detectados** | {len(equipos_unicos)} |
        | 🆕 **Equipos nuevos** | {equipos_nuevos} |
        | ♻️ **Equipos existentes** | {equipos_existentes} |
        | 📥 **Stats equipos descargadas** | {equipos_stats_descargados} |
        | 📲 **Stats partidos nuevos** | {partidos_iniciales_cargados} |
        | 📊 **Stats FT incrementales** | {stats_ft_nuevos} |
        | 💰 **API calls ahorradas** | {api_calls_ahorradas} |
        | 🎯 **Picks actualizados** | {picks_actualizados_auto} |
        | ⚠️ **Errores equipos** | {errores_equipos} |
        | 🚫 **Errores de API** | {errores_api} |
        """)

    except Exception as e:
        progress_bar.progress(100)
        status_text.error(f"❌ Error en sincronización: {e}")



def render_partidos_page():
    st.markdown("### 📊 Partidos de los Próximos 7 Días")

    # ========== ESTADO DE SINCRONIZACION ==========
    try:
        client = get_client()
        if client:
            # Partidos
            resp_part = client.table('partidos').select('fixture_id', count='exact').execute()
            num_partidos = len(resp_part.data) if resp_part.data else 0

            # Equipos unicos
            resp_eq = client.table('equipos_stats').select('team_id', count='exact').execute()
            num_equipos = len(resp_eq.data) if resp_eq.data else 0

            # Fecha ultimo partido
            resp_fechas = client.table('partidos').select('fecha').order('fecha', desc=True).limit(1).execute()
            ult_fecha = resp_fechas.data[0]['fecha'] if resp_fechas.data else 'Nunca'

            # Equipos con stats reales (lambda_local no nulo)
            resp_stats = client.table('equipos_stats').select('team_id', count='exact').not_.is_('lambda_local', 'null').execute()
            num_stats = len(resp_stats.data) if resp_stats.data else 0

            # Mostrar estado
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("Partidos", num_partidos)
            with col_s2:
                st.metric("Equipos", num_equipos)
            with col_s3:
                st.metric("Con Stats", num_stats)
            with col_s4:
                st.metric("Ultima sync", str(ult_fecha)[:10] if ult_fecha != 'Nunca' else 'Nunca')

            if num_partidos == 0:
                st.info("Sincroniza para descargar partidos")
    except Exception as e:
        logger.warning(f"Error en linea 941: {e}")

    # API-Football config
    API_KEY = os.getenv("API_FOOTBALL_KEY", "")
    if not API_KEY:
        st.error("❌ API_FOOTBALL_KEY no configurada. Configúrala en Render.")
        st.stop()

    # Contador de requests
    if 'api_requests_today' not in st.session_state:
        st.session_state.api_requests_today = 0

    # ═══════════════════════════════════════════════════════════════
    # BOTONES BUSCAR Y LIMPIAR
    # ═══════════════════════════════════════════════════════════════
    col_btn1, col_btn2, col_btn3, col_btn4, col_btn5, col_info = st.columns([1, 1, 1, 1, 1, 2])

    with col_btn1:
        if st.button("🗑️ Limpiar", type="secondary", use_container_width=True):
            client = get_client()
            try:
                # Contar antes de borrar (optimizado)
                num_p = len(client.table('partidos').select('fixture_id').execute().data or [])
                num_c = len(client.table('cuotas').select('fixture_id').execute().data or [])

                # Borrar todos (usar filtro dummy que siempre es verdadero)
                if num_p > 0:
                    client.table('partidos').delete().neq('fixture_id', -999999).execute()
                if num_c > 0:
                    client.table('cuotas').delete().neq('fixture_id', -999999).execute()

                st.session_state.api_requests_today = 0
                st.success(f"✅ Limpiado: {num_p} partidos y {num_c} cuotas")
                time.sleep(2)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    with col_btn2:
        if st.button("🔄 🔄 Sincronizar", type="primary", use_container_width=True):
            sincronizar_partidos()

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
                    st.info("ℹ️️ No hay datos para limpiar")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # Mostrar mensaje de limpieza si fue exitosa
    if st.session_state.get('limpieza_equipos_ok'):
        st.success(f"✅ Equipos limpiados correctamente")
        st.session_state.limpieza_equipos_ok = False

    # ═══════════════════════════════════════════════════════════════
    # RECALCULAR LAMBDAS: Corrige lambda_local y lambda_visitante desde historial
    # ═══════════════════════════════════════════════════════════════
    with col_btn4:
        if st.button("🔄 Recalcular Lambdas", type="secondary", use_container_width=True):
            client = get_client()
            if client:
                with st.spinner("Recalculando lambdas desde historial..."):
                    actualizados, mensaje = recalcular_lambdas_desde_historial(client)
                    st.info(f"ℹ️ {mensaje}")
                    if actualizados > 0:
                        st.success(f"✅ {actualizados} equipos actualizados correctamente")

    # ═══════════════════════════════════════════════════════════════
    # CARGAR CUOTAS: Descarga odds de API-Football para partidos próximos
    # ═══════════════════════════════════════════════════════════════
    with col_btn5:
        if st.button("💰 Cargar Cuotas", type="secondary", use_container_width=True):
            client = get_client()
            if client:
                API_URL = "https://v3.football.api-sports.io"
                API_KEY = os.getenv("API_FOOTBALL_KEY", "")
                headers = {'x-apisports-key': API_KEY}
                hoy = datetime.now(timezone(timedelta(hours=-5))).date()
                fecha_limite = (hoy + timedelta(days=7)).strftime('%Y-%m-%d')
                hoy_str = hoy.strftime('%Y-%m-%d')

                try:
                    # Partidos próximos (no terminados) en los próximos 7 días
                    resp_part = client.table('partidos').select(
                        'fixture_id, fecha, liga, equipo_local, equipo_visitante, estado'
                    ).gte('fecha', hoy_str).lte('fecha', fecha_limite).neq('estado', 'FT').execute()

                    partidos = resp_part.data or []

                    if not partidos:
                        st.info("ℹ️ No hay partidos próximos (7 días) para cargar cuotas. Sincroniza primero.")
                    else:
                        # Ver cuotas ya existentes para no recargar
                        fix_ids = [p['fixture_id'] for p in partidos if p.get('fixture_id')]
                        resp_cuotas = client.table('cuotas').select('fixture_id').in_('fixture_id', fix_ids).execute()
                        fix_con_cuotas = {c['fixture_id'] for c in (resp_cuotas.data or [])}
                        a_cargar = [p for p in partidos if p.get('fixture_id') not in fix_con_cuotas]

                        total = len(a_cargar)
                        if total == 0:
                            st.success(f"✅ Todos los {len(partidos)} partidos próximos ya tienen cuotas")
                        else:
                            st.info(f"💰 Cargando cuotas para {total} partidos (de {len(partidos)} próximos)...")
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            cuotas_total = 0
                            errores = 0
                            sin_cuotas = 0
                            primer_mensaje = ""  # Diagnóstico del primer partido

                            for i, p in enumerate(a_cargar):
                                fix_id = p.get('fixture_id')
                                status_text.info(
                                    f"💰 Cargando cuotas... ({i+1}/{total}) | "
                                    f"{p.get('equipo_local','')} vs {p.get('equipo_visitante','')} | "
                                    f"✅ {cuotas_total} cuotas"
                                )
                                n, sc, msg = cargar_cuotas_fixture(
                                    fixture_id=fix_id,
                                    fecha=p.get('fecha'),
                                    liga=p.get('liga', ''),
                                    equipo_local=p.get('equipo_local', ''),
                                    equipo_visitante=p.get('equipo_visitante', ''),
                                    headers=headers,
                                    API_URL=API_URL,
                                    client=client,
                                )
                                # Guardar diagnóstico del primer partido
                                if i == 0 and msg:
                                    primer_mensaje = msg
                                if n > 0:
                                    cuotas_total += n
                                elif n == 0:
                                    sin_cuotas += 1
                                else:
                                    errores += 1
                                st.session_state.api_requests_today = st.session_state.get('api_requests_today', 0) + 1
                                progress_bar.progress(int((i + 1) / total * 100))

                            status_text.empty()
                            resumen = f"✅ **CARGA DE CUOTAS COMPLETADA**\n\n"
                            resumen += f"💰 {cuotas_total} cuotas guardadas de {total} partidos\n"
                            if sin_cuotas > 0:
                                resumen += f"📋 {sin_cuotas} partidos sin cuotas disponibles\n"
                            if errores > 0:
                                resumen += f"⚠️ {errores} partidos con error de API\n"
                            resumen += f"📊 {st.session_state.api_requests_today}/999 requests usados hoy"
                            # Mostrar diagnóstico si el primer partido falló
                            if cuotas_total == 0 and primer_mensaje:
                                resumen += f"\n\n🔍 **DIAGNÓSTICO** (primer partido):"
                            st.success(resumen)
                            # Mostrar el dump crudo en un code block separado para que sea legible
                            if cuotas_total == 0 and primer_mensaje:
                                st.warning("⚠️ Estructura cruda de la API (primer partido):")
                                st.code(primer_mensaje, language='text')
                            time.sleep(3)
                except Exception as e:
                    st.error(f"❌ Error cargando cuotas: {e}")
                    logger.warning(f"Error en cargar cuotas: {e}")

    # ═══════════════════════════════════════════════════════════════
    # LIMPIEZA: Eliminar partidos de más de 1 año SOLO si hay partidos nuevos
    # ═══════════════════════════════════════════════════════════════
    if st.session_state.get('sincronizacion_ok') and st.session_state.get('partidos_nuevos_guardados', 0) > 0:
        st.session_state.sincronizacion_ok = False
        st.session_state.partidos_nuevos_guardados = 0
        try:
            client = get_client()
            fecha_limite = (datetime.now(timezone(timedelta(hours=-5))) - timedelta(days=365)).strftime('%Y-%m-%d')
            resp_del = client.table('partidos').delete().lt('fecha', fecha_limite).execute()
            eliminados = len(resp_del.data) if resp_del.data else 0
            if eliminados > 0:
                st.info(f"🗑️ {eliminados} partidos de más de 1 año eliminados")
        except Exception as e:
            logger.warning(f"Error en linea 1680: {e}")

    with col_info:
        st.markdown(f"📅 {datetime.now(timezone(timedelta(hours=-5))).date().strftime('%d/%m/%Y')} | 🔻 Requests: {st.session_state.api_requests_today}/999")

    # ═══════════════════════════════════════════════════════════════
    # MOSTRAR PARTIDOS (AGRUPADOS POR PAÍS, HORA COLOMBIANA)
    # ═══════════════════════════════════════════════════════════════
    try:
        client = get_client()
        response = client.table('partidos').select('*').execute()
        partidos_db = response.data if response.data else []
    except Exception as e:
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

    # Procesar partidos (la hora ya viene en zona horaria de Colombia desde la sync)
    partidos_procesados = []
    for p in partidos:
        fecha = p.get('fecha', '')
        hora_colombia = p.get('hora', '')[:5]

        partidos_procesados.append({
            **p,
            'hora_colombia': hora_colombia,
            'fecha_formato': datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y') if fecha else ''
        })

    # Agrupar por PAÍS
    paises_partidos = {}
    for p in partidos_procesados:
        pais = p.get('pais', 'Sin país')
        if pais not in paises_partidos:
            paises_partidos[pais] = []
        paises_partidos[pais].append(p)

    # Emoji por país
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
                    except Exception as e:
                        tiene_stats = None

                    # Badge de estado
                    if tiene_stats is True:
                        badge = "🟢"
                    elif tiene_stats is False:
                        badge = "🟡"
                    else:
                        badge = "🔴"

                    # Botón estilo tarjeta compacta
                    label = f"📅 {fecha_fmt} {hora_col} | {badge} {equipo_local} vs {equipo_visitante}"
                    if st.button(label, key=f"btn_{pais}_{liga}_{i}", use_container_width=True):
                        st.session_state.selected_local = equipo_local
                        st.session_state.selected_away = equipo_visitante
                        st.session_state.selected_team_id_local = partido.get('team_id_local')
                        st.session_state.selected_team_id_visitante = partido.get('team_id_visitante')
                        st.session_state.selected_fixture_id = partido.get('fixture_id')
                        st.session_state.page = "Analizador"
                        st.rerun()

            st.markdown("---")

# Página: Analizador

def render_cuotas_mercado(r):
    """Muestra cuotas del mercado y value bets para un partido."""
    fixture_id_partido = r.get('fixture_id')
    if fixture_id_partido:
        try:
            client = get_client()
            cuotas_resp = client.table('cuotas').select('*').eq('fixture_id', fixture_id_partido).execute()

            if cuotas_resp.data:
                st.markdown("##### 🏆 Cuotas del Mercado")

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
                                    value_color = "🔴"
                                    value_text = f"+{value:.1f}%"
                                elif value > 0:
                                    value_color = "🟠"
                                    value_text = f"+{value:.1f}%"
                                else:
                                    value_color = "🔽"
                                    value_text = f"{value:.1f}%"

                                label = f"{'📊 Local' if 'Home' in opcion or '1' in opcion else ('⚖️ Empate' if 'Draw' in opcion or 'X' in opcion else '✈️ Visita')}"
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
                            value_color = "🔴"
                        elif value > 0:
                            value_color = "🟠"
                        else:
                            value_color = "🔽"

                        st.write(f"{opcion}: **@ {valor:.2f}** | {value_color} VALUE: {value:+.1f}% | Modelo: {prob_modelo_btts:.0f}% | Implicita: {prob_imp:.0f}% ({bookie})")

                # Mostrar Over/Under con VALUE
                if cuotas_ou:
                    st.markdown("**📲 Over/Under**")
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
                            value_color = "🔴"
                        elif value > 0:
                            value_color = "🟠"
                        else:
                            value_color = "🔽"

                        st.write(f"{opcion}: **@ {valor:.2f}** | {value_color} VALUE: {value:+.1f}% | Modelo: {prob_modelo_ou:.0f}% | Implicita: {prob_imp:.0f}% ({bookie})")

                # Resumen de VALUE bets
                st.markdown("---")
                st.markdown("**📥 Resumen de Value Bets:**")

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
                    st.info("🔽 Sin value bets en este momento")
            else:
                st.info("🔻 Sin cuotas guardadas para este partido. Ve a Partidos → 💰 Cargar Cuotas.")
        except Exception as e:
            logger.warning(f"Error consultando cuotas: {e}")
    else:
        st.info("🔻 Sin cuotas para este partido. Ve a Partidos → 💰 Cargar Cuotas para descargar odds.")


def _construir_pick_data(r, home, away, stats_local):
    """Construye el dict de datos del pick a partir del resultado del análisis."""
    usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'
    fixture_id = st.session_state.get('selected_fixture_id', 0)
    return {
        'fecha': str(datetime.now(timezone(timedelta(hours=-5))).date()),
        'usuario': usuario_id,
        'fixture_id': fixture_id,
        'pick': r.get('pick_1x2', '1'),
        'liga': stats_local.get('liga', 'Desconocida') if stats_local else 'N/A',
        'equipo_local': home,
        'equipo_visitante': away,
        'prediccion_1x2': r.get('pick_1x2', '1'),
        'prob_1x2': float(r.get('prob_1x2', 50)),
        'p1': float(r.get('p1', 33)),
        'px': float(r.get('px', 33)),
        'p2': float(r.get('p2', 33)),
        'prediccion_ou': r.get('pick_over_under', 'Over'),
        'prob_ou': float(r.get('prob_over_under', 50)),
        'prediccion_btts': r.get('pick_btts', 'Si'),
        'btts_yes': float(r.get('btts_yes', 50)),
        'prediccion_corners': r.get('pick_corners', 'Over'),
        'corners_total_estimado': float(r.get('corners', {}).get('total_estimado', 10)),
        'prediccion_remates': r.get('pick_tiros', 'Over'),
        'remates_total_estimado': float(r.get('tiros', {}).get('total_estimado', 24)),
        'prediccion_tarjetas': r.get('pick_tarjetas', 'Over'),
        'tarjetas_total_estimado': float(r.get('tarjetas', {}).get('total_estimado', 5)),
        'prediccion_arco': r.get('pick_tiros_arco', 'Over'),
        'arco_total_estimado': float(r.get('tiros_arco', {}).get('total_estimado', 8)),
        'confianza': int(r.get('confianza', 50)),
        'rango': r.get('rango', 'C'),
    }


def _insertar_pick_resiliente(client, pick_data):
    """Inserta un pick siendo resiliente a columnas faltantes en la DB.

    Si el insert falla con PGRST204 (columna no encontrada en el caché del
    esquema de PostgREST), quita la columna problemática y reintenta.
    Esto permite guardar el pick aunque la tabla picks en producción no tenga
    todas las columnas nuevas (arco, confianza, etc.) migradas todavía.
    Retorna el registro creado (incluye el id autogenerado)."""
    data = dict(pick_data)
    while True:
        try:
            resp = client.table('picks').insert(data).execute()
            return resp.data[0] if resp.data else data
        except Exception as e:
            col_faltante = _extraer_columna_faltante(str(e))
            if col_faltante and col_faltante in data:
                logger.warning(f"Columna '{col_faltante}' no existe en picks, reintentando sin ella")
                del data[col_faltante]
                continue
            raise


def _actualizar_pick_resiliente(client, update_data, pick_id):
    """Actualiza un pick siendo resiliente a columnas faltantes (ver _insertar_pick_resiliente)."""
    data = dict(update_data)
    while True:
        try:
            client.table('picks').update(data).eq('id', pick_id).execute()
            return data
        except Exception as e:
            col_faltante = _extraer_columna_faltante(str(e))
            if col_faltante and col_faltante in data:
                logger.warning(f"Columna '{col_faltante}' no existe en picks, actualizando sin ella")
                del data[col_faltante]
                continue
            raise


def _extraer_columna_faltante(msg):
    """Extrae el nombre de la columna de un mensaje PGRST204 de PostgREST."""
    if 'PGRST204' in msg or 'no se pudo encontrar la columna' in msg.lower() or 'could not find the column' in msg.lower():
        match = re.search(r"'([^']+)'", msg)
        return match.group(1) if match else None
    return None


def _btn_pred(col, key, label, value, active, on_click, highlight=False, accent="#00d4ff"):
    """Boton-tarjeta clickeable: muestra la prediccion y sirve de seleccion."""
    icon = "✅" if active else "◯"
    if active:
        border = "#22c55e"
        bg = "rgba(34,197,94,0.20)"
    elif highlight:
        border = accent
        bg = f"rgba(255,255,255,0.10)"
    else:
        border = "rgba(255,255,255,0.20)"
        bg = "rgba(255,255,255,0.06)"
    help_txt = "Seleccionado" if active else "Clic para seleccionar"
    col.markdown(
        f'<style>button[kind="secondary"][key="{key}"] {{'
        f'background:{bg} !important;border:1.5px solid {border} !important;'
        f'border-radius:12px !important;font-size:0.78rem !important;'
        f'padding:16px 8px !important;color:#fff !important;'
        f'text-align:center !important;line-height:1.6 !important;'
        f'white-space:pre-line !important;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.3) !important;'
        f'transition:all 0.2s !important;margin-bottom:6px !important;}}'
        f'button[kind="secondary"][key="{key}"]:hover {{'
        f'border-color:{accent} !important;'
        f'background:rgba(255,255,255,0.12) !important;}}'
        f'</style>', unsafe_allow_html=True)
    col.button(f"{icon} {label}\n{value}", key=key, use_container_width=True,
               on_click=on_click, help=help_txt)


def _group_title(text, emoji, accent="#00d4ff"):
    """Titulo de grupo para seccionar apuestas."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;'
        f'margin:22px 0 10px 0;padding:8px 12px;'
        f'border-left:3px solid {accent};'
        f'background:rgba(255,255,255,0.03);border-radius:0 8px 8px 0;">'
        f'<span style="font-size:1.1rem;">{emoji}</span>'
        f'<span style="color:{accent};font-weight:700;font-size:0.85rem;'
        f'letter-spacing:0.5px;text-transform:uppercase;">{text}</span>'
        f'</div>', unsafe_allow_html=True)


def render_analizador_page():
    st.markdown("## 🎯 Analizador de Partidos")

    client = get_client()

    # Verificar si viene de Partidos con equipos seleccionados
    tiene_match = bool(st.session_state.get('selected_match_data'))
    tiene_equipos = bool(st.session_state.get('selected_local') and st.session_state.get('selected_away'))

    # SI NO hay equipos seleccionados, mostrar selector
    if not tiene_match and not tiene_equipos:
        equipos_lista = []
        try:
            resp = client.table('equipos_stats').select('equipo').limit(500).execute()
            if resp.data:
                for eq in resp.data:
                    nombre = eq.get('equipo', '')
                    if nombre and nombre not in equipos_lista:
                        equipos_lista.append(nombre)
        except Exception as e:
            logger.warning(f"Error en linea 1827: {e}")

        st.markdown("### 📊 Seleccionar Equipos")
        col1, col2 = st.columns(2)
        with col1:
            equipo_local = st.selectbox("🏠 Equipo Local", options=equipos_lista, key="local1")
        with col2:
            equipo_visitante = st.selectbox("✈️ Equipo Visitante", options=equipos_lista, key="visit1")

        if st.button("🔍 ANALIZAR", type="primary", use_container_width=True):
            if equipo_local and equipo_visitante:
                st.session_state.selected_local = equipo_local
                st.session_state.selected_away = equipo_visitante
                st.session_state.home = equipo_local
                st.session_state.away = equipo_visitante
            else:
                st.warning("Selecciona ambos equipos")
                st.stop()

    # SI hay equipos seleccionados, hacer el análisis
    # Si hay un partido seleccionado, hacer análisis automático
    if st.session_state.selected_match_data:
        p = st.session_state.selected_match_data
        local_nombre = p.get('equipo_local', '')
        visitante_nombre = p.get('equipo_visitante', '')

    # Si viene de la página Partidos con equipos en session_state
    elif 'selected_local' in st.session_state and 'selected_away' in st.session_state:
        local_nombre = st.session_state.selected_local
        visitante_nombre = st.session_state.selected_away
        tid_local = st.session_state.get('selected_team_id_local')
        tid_visitante = st.session_state.get('selected_team_id_visitante')

        st.markdown("---")
        st.markdown(f"### 🎯 Analizando: **{local_nombre}** VS **{visitante_nombre}**")

        # Buscar stats de los equipos en Supabase
        stats_local = None
        stats_visitante = None
        lambda_dinamico_local = None
        lambda_dinamico_visit = None
        promedios_dinamicos_local = None
        promedios_dinamicos_visitante = None
        lambda_historico_local = None
        lambda_historico_visit = None
        lambda_local_final = None
        lambda_visit_final = None

        try:
            resp_local = client.table('equipos_stats').select('*').ilike('equipo', f'%{local_nombre}%').execute()
            if resp_local.data:
                stats_local = resp_local.data[0]
        except Exception as e:
            logger.warning(f"Error en linea 1880: {e}")

        try:
            resp_visitante = client.table('equipos_stats').select('*').ilike('equipo', f'%{visitante_nombre}%').execute()
            if resp_visitante.data:
                stats_visitante = resp_visitante.data[0]
        except Exception as e:
            logger.warning(f"Error en linea 1887: {e}")

        # Buscar promedios_dinamicos por team_id directo
        if tid_local:
            promedios_dinamicos_local = calcular_promedios_equipo(client, tid_local)
        if tid_visitante:
            promedios_dinamicos_visitante = calcular_promedios_equipo(client, tid_visitante)

        # NO limpiar session_state aquí - se limpian después de guardar

        if stats_local and stats_visitante:
            lambda_local = stats_local.get('lambda_local', 0)
            # Usar lambda_visitante del visitante (goles como visitante)
            # Fallback a lambda_local solo si lambda_visitante es nulo/0/corrupto
            lambda_visitante = stats_visitante.get('lambda_visitante') or stats_visitante.get('lambda_local', 0)

            # Usar promedios_dinamicos si existen
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

            # Aplicar calibración
            lambda_local_adj = get_lambda_ajustada(local_nombre, lambda_local, como_local=True)
            lambda_visitante_adj = get_lambda_ajustada(visitante_nombre, lambda_visitante, como_local=False)
            lambda_local_cal = lambda_local_adj['lambda_ajustada']
            lambda_visitante_cal = lambda_visitante_adj['lambda_ajustada']

            # Factores de calibración para Over/Under y BTTS (promedio de ambos equipos)
            factores_local = obtener_factores_completos(local_nombre, como_local=True)
            factores_visitante = obtener_factores_completos(visitante_nombre, como_local=False)
            factor_over_prom = (factores_local['factor_over'] + factores_visitante['factor_over']) / 2
            factor_btts_prom = (factores_local['factor_btts'] + factores_visitante['factor_btts']) / 2

            # ★ OBTENER ÚLTIMOS 5 PARTIDOS de promedios_dinamicos
            ultimos_5_local = []
            ultimos_5_visitante = []
            if promedios_dinamicos_local:
                ultimos_5_local = promedios_dinamicos_local.get('partidos', [])[:5]
            if promedios_dinamicos_visitante:
                ultimos_5_visitante = promedios_dinamicos_visitante.get('partidos', [])[:5]

            with st.spinner("Analizando..."):
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

                # Guardar promedios_dinamicos en session_state
                st.session_state.promedios_dinamicos_local = promedios_dinamicos_local
                st.session_state.promedios_dinamicos_visitante = promedios_dinamicos_visitante

                # Aplicar calibración de Over/Under y BTTS a las probabilidades
                # factor_over > 1: el modelo subestima los goles → subir Over, bajar Under
                # factor_btts > 1: el modelo subestima BTTS → subir Yes, bajar No
                ou = result.get('over_under', {})
                if ou and factor_over_prom != 1.0:
                    nuevas = {}
                    for k, v in ou.items():
                        if 'over' in k:
                            nuevas[k] = round(min(99.9, v * factor_over_prom), 1)
                        else:
                            nuevas[k] = round(max(0.1, v * (2 - factor_over_prom)), 1)
                    result['over_under'] = nuevas
                    # Recalcular pick y prob
                    if nuevas.get('over_25', 0) >= nuevas.get('under_25', 0):
                        result['pick_over_under'] = 'Over 2.5'
                        result['prob_over_under'] = nuevas.get('over_25', 50)
                    else:
                        result['pick_over_under'] = 'Under 2.5'
                        result['prob_over_under'] = nuevas.get('under_25', 50)

                if factor_btts_prom != 1.0:
                    result['btts_yes'] = round(min(99.9, result.get('btts_yes', 50) * factor_btts_prom), 1)
                    result['btts_no'] = round(max(0.1, 100 - result['btts_yes']), 1)
                    result['pick_btts'] = 'Sí' if result['btts_yes'] >= 50 else 'No'

                # Guardar fixture_id en result para render_cuotas_mercado
                result['fixture_id'] = st.session_state.get('selected_fixture_id')

                st.session_state.analysis_result = result
                st.session_state.home = local_nombre
                st.session_state.away = visitante_nombre
                st.session_state.stats_local = stats_local
                st.session_state.stats_visitante = stats_visitante
        else:
            st.stop()  # No continuar si no hay stats

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
        # Obtener equipos disponibles de Supabase
        try:
            resp_equipos = client.table('equipos_stats').select('equipo,lambda_local').execute()
            equipos_disponibles = sorted(list(set([e.get('equipo', '') for e in resp_equipos.data if e.get('equipo')])))
            # Debug: mostrar equipos con lambda válido
            equipos_con_lambda = [e for e in resp_equipos.data if e.get('lambda_local', 0) >= 0]
            st.caption(f"📊 {len(equipos_disponibles)} equipos | {len(equipos_con_lambda)} con stats")
        except Exception as ex:
            equipos_disponibles = []
            st.error(f"Error conectando a Supabase: {ex}")

        col_space, col1, col2, col_space2 = st.columns([2, 1, 1, 2])
        with col1:
            home_team = st.selectbox("📊 Local", [""] + equipos_disponibles, key="home_select")
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
    team_id_local = None
    team_id_visitante = None
    promedios_dinamicos_local = None
    promedios_dinamicos_visitante = None
    lambda_historico_local = None
    lambda_historico_visit = None
    lambda_local_final = None
    lambda_visit_final = None

    # FUNCIÓN AUXILIAR: Buscar promedios dinámicos (por team_id directamente)
    # USAR team_id DIRECTO del partido para buscar en equipo_partidos_stats
    tid_local = st.session_state.get('selected_team_id_local')
    tid_visitante = st.session_state.get('selected_team_id_visitante')

    if tid_local:
        promedios_dinamicos_local = calcular_promedios_equipo(client, tid_local)
        equipo_local_ok = True

    if tid_visitante:
        promedios_dinamicos_visitante = calcular_promedios_equipo(client, tid_visitante)
        equipo_visitante_ok = True

    # Limpiar session_state DESPUÉS de usar
    if tid_local or tid_visitante:
        st.session_state.pop('selected_team_id_local', None)
        st.session_state.pop('selected_team_id_visitante', None)

    # Mostrar info de equipos disponibles
    if not equipos_disponibles:
        st.warning("⚠️ No hay equipos en la base de datos. Ejecuta Sincronizar primero.")

    # Mostrar error si faltan equipos
    if equipos_faltantes and not error_conexion:
        st.error(f"⚠️ Equipos sin datos completos: {', '.join(set(equipos_faltantes))}")
        st.info("💡 Ejecuta Sincronizar para obtener estadísticas de estos equipos.")

    # Botón analizar - solo si ambos equipos existen
    analizar_disabled = not (equipo_local_ok and equipo_visitante_ok)

    # ★ ANÁLISIS AUTOMÁTICO SI VIENE DE LA LISTA
    vino_de_lista = 'selected_local' in st.session_state and 'selected_away' in st.session_state

    # Si viene de lista y tiene stats, análisis automático
    if vino_de_lista and equipo_local_ok and equipo_visitante_ok:
        debe_analizar = True
    elif st.button("🎯 ANALIZAR", type="primary", use_container_width=True, disabled=analizar_disabled):
        debe_analizar = True
    else:
        debe_analizar = False

    if debe_analizar:
        try:
            if home_team and away_team and stats_local and stats_visitante:
                # LAMBDA HISTÓRICO desde equipos_stats
                lambda_historico_local = stats_local.get('lambda_local', 1.3)
                lambda_historico_visit = stats_visitante.get('lambda_visitante', 1.1)

                if lambda_historico_local <= 0 or lambda_historico_visit <= 0:
                    st.error("ERROR: Lambda invalido. Sincroniza los equipos primero.")
                    st.stop()

                with st.spinner("Analizando..."):
                    # LAMBDA DINÁMICO desde promedios ponderados
                    lambda_dinamico_local = promedios_dinamicos_local.get('lambda_ponderado') if promedios_dinamicos_local else None
                    lambda_dinamico_visit = promedios_dinamicos_visitante.get('lambda_ponderado') if promedios_dinamicos_visitante else None

                    # λ FINAL = 60% Dinámico + 40% Histórico
                    if lambda_dinamico_local and lambda_dinamico_visit:
                        lambda_local_final = lambda_dinamico_local * 0.6 + lambda_historico_local * 0.4
                        lambda_visit_final = lambda_dinamico_visit * 0.6 + lambda_historico_visit * 0.4
                    else:
                        # Si no hay datos dinámicos, usar solo histórico
                        lambda_local_final = lambda_historico_local
                        lambda_visit_final = lambda_historico_visit

                    # Usar λ FINAL para los modelos
                    lambda_local_cal = lambda_local_final
                    lambda_visitante_cal = lambda_visit_final

                    # ★ USAR PROMEDIOS DINÁMICOS si están disponibles
                    if promedios_dinamicos_local:
                        corners_l = promedios_dinamicos_local.get('promedio_corners', 5.5)
                        tiros_l = promedios_dinamicos_local.get('promedio_tiros', 13.0)
                        tiros_arco_l = promedios_dinamicos_local.get('promedio_tiros_arco', 4.5)
                        amarillas_l = promedios_dinamicos_local.get('promedio_amarillas', 2.5)
                        partidos_total_l = promedios_dinamicos_local.get('partidos_total', 0)
                    else:
                        # Estimar basado en lambda (si no hay datos en Supabase)
                        corners_l = None
                        tiros_l = None
                        tiros_arco_l = round(lambda_local_cal * 1.5, 1)
                        amarillas_l = 2.5
                        partidos_total_l = 0

                    if promedios_dinamicos_visitante:
                        corners_v = promedios_dinamicos_visitante.get('promedio_corners', 5.5)
                        tiros_v = promedios_dinamicos_visitante.get('promedio_tiros', 13.0)
                        tiros_arco_v = promedios_dinamicos_visitante.get('promedio_tiros_arco', 4.5)
                        amarillas_v = promedios_dinamicos_visitante.get('promedio_amarillas', 2.5)
                        partidos_total_v = promedios_dinamicos_visitante.get('partidos_total', 0)
                    else:
                        # Estimar basado en lambda (si no hay datos en Supabase)
                        corners_v = None
                        tiros_v = None
                        tiros_arco_v = round(lambda_visitante_cal * 1.5, 1)
                        amarillas_v = 2.5
                        partidos_total_v = 0

                    # ★ OBTENER ÚLTIMOS 5 PARTIDOS de equipo_partidos_stats
                    ultimos_5_local = []
                    ultimos_5_visitante = []

                    if promedios_dinamicos_local:
                        ultimos_5_local = promedios_dinamicos_local.get('partidos', [])[:5]
                    if promedios_dinamicos_visitante:
                        ultimos_5_visitante = promedios_dinamicos_visitante.get('partidos', [])[:5]

                    # GUARDAR promedios_dinamicos en session_state para usarlos después
                    st.session_state.promedios_dinamicos_local = promedios_dinamicos_local
                    st.session_state.promedios_dinamicos_visitante = promedios_dinamicos_visitante

                    # Llamar al modelo con TODOS los datos
                    result = calcular(
                        lambda_local=lambda_local_cal,
                        lambda_visitante=lambda_visitante_cal,
                        corners_local=corners_l,
                        corners_visitante=corners_v,
                        tarjetas_local=amarillas_l,
                        tarjetas_visitante=amarillas_v,
                        tiros_local=tiros_l,
                        tiros_visitante=tiros_v,
                        tiros_arco_local=tiros_arco_l,
                        tiros_arco_visitante=tiros_arco_v,
                        ultimos_5_local=ultimos_5_local,
                        ultimos_5_visitante=ultimos_5_visitante,
                    )

                    # Guardar info de partidos dinámicos en result
                    result['partidos_acumulados_local'] = partidos_total_l
                    result['partidos_acumulados_visitante'] = partidos_total_v
                    # Guardar fixture_id en result para render_cuotas_mercado
                    result['fixture_id'] = st.session_state.get('selected_fixture_id')

                    st.session_state.analysis_result = result
                    st.session_state.home = home_team
                    st.session_state.away = away_team
                    st.session_state.stats_local = stats_local
                    st.session_state.stats_visitante = stats_visitante

                    # Guardar TODAS las predicciones en session_state (NO en Supabase aun)
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
                            'pick': result.get('pick_tiros', ''),
                            'total': float(result.get('tiros', {}).get('total_estimado', 0)),
                            'local': float(result.get('tiros', {}).get('tiros_local_estimado', 0)),
                            'visitante': float(result.get('tiros', {}).get('tiros_visitante_estimado', 0)),
                            'over_prob': float(result.get('prob_tiros', 0)),
                            'under_prob': float(result.get('tiros', {}).get('under_24', 0))
                        },
                        'tarjetas': {
                            'pick': result.get('pick_tarjetas', ''),
                            'total': float(result.get('tarjetas', {}).get('total_estimado', 0)),
                            'over_prob': float(result.get('prob_tarjetas', 0)),
                            'under_prob': float(result.get('tarjetas', {}).get('under_6', 0))
                        }
                    }

            else:
                st.error("⚠️ Ambos equipos deben tener estadísticas. Ejecuta el robot primero.")
        except Exception as e:
            st.error(f"❌ Error en análisis: {str(e)[:100]}")
            st.info("🔻 Intenta de nuevo o verifica que los equipos existan.")

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

        # VALORES POR DEFECTO PARA EVITAR ERRORES NONE
        pj_l_display = pj_v_display = 0
        vic_l = emp_l = der_l = vic_v = emp_v = der_v = 0
        gf_l = gc_l = gf_v = gc_v = 0.0
        prom_tiros_l = prom_tiros_v = 13.0
        prom_tiros_arco_l = prom_tiros_arco_v = 4.5
        prom_amarillas_l = prom_amarillas_v = 2.5
        prom_corners_l = prom_corners_v = 5.5
        puntos = puntos_v = 0
        gf_forma = gc_forma = gf_v_forma = gc_v_forma = 0
        badges_local = badges_visitante = ''
        lambda_din_l = lambda_din_v = '0.00'
        lambda_historico_local = lambda_historico_visit = 0.0
        lambda_local_final = lambda_visit_final = 0.0

        # OBTENER promedios_dinamicos del session_state
        promedios_dinamicos_local = st.session_state.get('promedios_dinamicos_local')
        promedios_dinamicos_visitante = st.session_state.get('promedios_dinamicos_visitante')

        if stats_local and stats_visitante:
            # Fuente de datos
            source_local = stats_local.get('source', 'Supabase')
            source_visitante = stats_visitante.get('source', 'Supabase')

            st.markdown("##### 📥 Estadísticas Avanzadas")

            # Fuentes de datos en una línea
            st.markdown(f"📊 **Fuente:** Local `{source_local}` | Visitante `{source_visitante}`")

            st.caption("⚡ Lambda: 60% dinámico (últimos partidos) + 40% histórico")

            # ★ USAR PROMEDIOS DINÁMICOS si están disponibles (ponderación exponencial)
            if promedios_dinamicos_local:
                prom_corners_l = promedios_dinamicos_local.get('promedio_corners', 5.5)
                prom_amarillas_l = promedios_dinamicos_local.get('promedio_amarillas', 3.0)
                prom_tiros_l = promedios_dinamicos_local.get('promedio_tiros', 13.0)
                prom_tiros_arco_l = promedios_dinamicos_local.get('promedio_tiros_arco', 4.5)
            else:
                prom_corners_l = stats_local.get('promedio_corners', 10) or 10
                prom_amarillas_l = stats_local.get('promedio_amarillas', 2.5) or 0
                prom_tiros_l = stats_local.get('promedio_tiros', 13.0) or 0
                prom_tiros_arco_l = stats_local.get('promedio_tiros_arco', 4.5) or 0

            if promedios_dinamicos_visitante:
                prom_corners_v = promedios_dinamicos_visitante.get('promedio_corners', 5.5)
                prom_amarillas_v = promedios_dinamicos_visitante.get('promedio_amarillas', 3.0)
                prom_tiros_v = promedios_dinamicos_visitante.get('promedio_tiros', 13.0)
                prom_tiros_arco_v = promedios_dinamicos_visitante.get('promedio_tiros_arco', 4.5)
            else:
                prom_corners_v = stats_visitante.get('promedio_corners', 10) or 10
                prom_amarillas_v = stats_visitante.get('promedio_amarillas', 2.5) or 0
                prom_tiros_v = stats_visitante.get('promedio_tiros', 13.0) or 0
                prom_tiros_arco_v = stats_visitante.get('promedio_tiros_arco', 4.5) or 0

            # Calcular promedios LOCAL (para PJ, victorias, etc - de equipos_stats)
            pj_l = stats_local.get('partidos_jugados', 1) or 1
            gf_l = float(stats_local.get('goles_favor') or 0)
            gc_l = float(stats_local.get('goles_contra') or 0)
            vic_l = int(stats_local.get('victorias') or 0)
            emp_l = int(stats_local.get('empates') or 0)
            der_l = int(stats_local.get('derrotas') or 0)

            # Calcular promedios VISITANTE
            pj_v = stats_visitante.get('partidos_jugados', 1) or 1
            gf_v = float(stats_visitante.get('goles_favor') or 0)
            gc_v = float(stats_visitante.get('goles_contra') or 0)
            vic_v = int(stats_visitante.get('victorias') or 0)
            emp_v = int(stats_visitante.get('empates') or 0)
            der_v = int(stats_visitante.get('derrotas') or 0)

            # Calcular lambda_historico (basado en goles/pj)
            lambda_historico_local = gf_l / pj_l if pj_l > 0 else 1.3
            lambda_historico_visit = gf_v / pj_v if pj_v > 0 else 1.1

            # Calcular lambda_dinamico desde promedios_dinamicos
            lambda_dinamico_local_calc = promedios_dinamicos_local.get('lambda_ponderado') if promedios_dinamicos_local else None
            lambda_dinamico_visit_calc = promedios_dinamicos_visitante.get('lambda_ponderado') if promedios_dinamicos_visitante else None

            # Lambda FINAL = 60% dinamico + 40% historico
            if lambda_dinamico_local_calc is not None:
                lambda_local_final = lambda_dinamico_local_calc * 0.6 + lambda_historico_local * 0.4
                lambda_dinamico_local = lambda_dinamico_local_calc
            else:
                lambda_local_final = lambda_historico_local
                lambda_dinamico_local = None

            if lambda_dinamico_visit_calc is not None:
                lambda_visit_final = lambda_dinamico_visit_calc * 0.6 + lambda_historico_visit * 0.4
                lambda_dinamico_visit = lambda_dinamico_visit_calc
            else:
                lambda_visit_final = lambda_historico_visit
                lambda_dinamico_visit = None

            # ★ INFO DINÁMICA: Obtener datos de partidos acumulados
            partidos_acum_l = r.get('partidos_acumulados_local', 0)
            partidos_acum_v = r.get('partidos_acumulados_visitante', 0)
            pj_l_display = partidos_acum_l if partidos_acum_l > 0 else pj_l
            pj_v_display = partidos_acum_v if partidos_acum_v > 0 else pj_v

            # Lambda dinámico con fallback
            lambda_din_l = f"{lambda_dinamico_local:.2f}" if lambda_dinamico_local is not None else "?"
            lambda_din_v = f"{lambda_dinamico_visit:.2f}" if lambda_dinamico_visit is not None else "?"

            # FORMA RECIENTE - Obtener datos de forma
            forma_l_data = r.get('forma_local', {})
            forma_v_data = r.get('forma_visitante', {})
            letras = forma_l_data.get('forma_letras', [])
            puntos = forma_l_data.get('forma_puntos', 0)
            gf_forma = forma_l_data.get('goles_favor_5', 0)
            gc_forma = forma_l_data.get('goles_contra_5', 0)
            letras_v = forma_v_data.get('forma_letras', [])
            puntos_v = forma_v_data.get('forma_puntos', 0)
            gf_v_forma = forma_v_data.get('goles_favor_5', 0)
            gc_v_forma = forma_v_data.get('goles_contra_5', 0)

            # Crear badges de forma
            badges_local = crear_badges(letras)
            badges_visitante = crear_badges(letras_v)

            # Función auxiliar para crear fila de datos
            # Calcular valores seguros para lambda antes del f-string
            lambda_hist_l_val = f'{lambda_historico_local:.2f}' if lambda_historico_local is not None else '?'
            lambda_hist_v_val = f'{lambda_historico_visit:.2f}' if lambda_historico_visit is not None else '?'
            lambda_final_l_val = f'{lambda_local_final:.2f}' if lambda_local_final is not None else '?'

            # FUNCIÓN AUXILIAR PARA CONVERTIR VALORES A STRING SIN ERRORES DE FORMATO
            # CONVERTIR TODAS LAS VARIABLES A STRINGS PARA EL F-STRING
            pj_l_str = safe_fmt_int(pj_l_display)
            pj_v_str = safe_fmt_int(pj_v_display)
            vic_l_str = safe_fmt_int(vic_l)
            emp_l_str = safe_fmt_int(emp_l)
            der_l_str = safe_fmt_int(der_l)
            vic_v_str = safe_fmt_int(vic_v)
            emp_v_str = safe_fmt_int(emp_v)
            der_v_str = safe_fmt_int(der_v)
            gf_l_str = safe_fmt(gf_l)
            gc_l_str = safe_fmt(gc_l)
            gf_v_str = safe_fmt(gf_v)
            gc_v_str = safe_fmt(gc_v)
            prom_tiros_l_str = safe_fmt(prom_tiros_l)
            prom_tiros_v_str = safe_fmt(prom_tiros_v)
            prom_tiros_arco_l_str = safe_fmt(prom_tiros_arco_l)
            prom_tiros_arco_v_str = safe_fmt(prom_tiros_arco_v)
            prom_amarillas_l_str = safe_fmt(prom_amarillas_l)
            prom_amarillas_v_str = safe_fmt(prom_amarillas_v)
            prom_corners_l_str = safe_fmt(prom_corners_l)
            prom_corners_v_str = safe_fmt(prom_corners_v)
            puntos_str = safe_fmt(puntos)
            puntos_v_str = safe_fmt(puntos_v)
            gf_forma_str = safe_fmt_int(gf_forma)
            gc_forma_str = safe_fmt_int(gc_forma)
            gf_v_forma_str = safe_fmt_int(gf_v_forma)
            gc_v_forma_str = safe_fmt_int(gc_v_forma)

            lambda_final_v_val = f'{lambda_visit_final:.2f}' if lambda_visit_final is not None else '?'

            # Inicializar calibración ANTES del html_content
            calib_l = st.session_state.get('calibracion_local', {})
            calib_v = st.session_state.get('calibracion_visitante', {})
            factor_l = calib_l.get('factor', 1.0)
            factor_v = calib_v.get('factor', 1.0)
            ajuste_l = calib_l.get('ajuste', 'sin_cambio')
            ajuste_v = calib_v.get('ajuste', 'sin_cambio')

            if factor_l != 1.0:
                badge_l = "🔧" if ajuste_l == 'sube' else "📉"
                calib_l_str = f"{badge_l} {factor_l:.2f}x"
            else:
                calib_l_str = "⚪ 1.00x"

            if factor_v != 1.0:
                badge_v = "🔧" if ajuste_v == 'sube' else "📉"
                calib_v_str = f"{badge_v} {factor_v:.2f}x"
            else:
                calib_v_str = "⚪ 1.00x" 

            # Contenedor principal usando st.html()
            html_content = f"""
            <div style='background:#0a0a0a;border-radius:12px;padding:10px;margin:10px 0;'>
                <div style='background:linear-gradient(135deg,#111111,#0d0d0d);padding:15px;border-radius:10px;margin-bottom:10px;text-align:center;'>
                    <h3 style='color:#fff;margin:0;font-size:18px;'>📊 {html.escape(str(home))} <span style='color:#fff;'>vs</span> {html.escape(str(away))}</h3>
                    <p style='color:#00d4ff;font-size:11px;margin:5px 0 0;'>({pj_l_str} PJ) vs ({pj_v_str} PJ)</p>
                </div>
                <div style='display:flex;background:#111111;padding:10px;border-radius:8px;margin-bottom:5px;'>
                    <div style='width:33%;text-align:center;color:#fff;font-weight:bold;font-size:13px;'>{html.escape(str(home))}</div>
                    <div style='width:34%;text-align:center;color:#00d4ff;font-weight:bold;font-size:13px;'>📊 COMPARATIVA</div>
                    <div style='width:33%;text-align:center;color:#fff;font-weight:bold;font-size:13px;'>{html.escape(str(away))}</div>
                </div>
                {fila_dato(f'{vic_l_str}-{emp_l_str}-{der_l_str}', 'Récord (V-E-D)', f'{vic_v_str}-{emp_v_str}-{der_v_str}')}
                {fila_dato(gf_l, 'Goles Favor', gf_v, bg_par=True)}
                {fila_dato(gc_l, 'Goles Contra', gc_v)}
                {fila_dato(lambda_din_l, 'λ Dinámico', lambda_din_v, '#fff', bg_par=True)}
                {fila_dato(lambda_hist_l_val, 'λ Histórico', lambda_hist_v_val, '#00d4ff')}
                <div style='background:#111111;padding:10px 5px;border-radius:4px;margin:2px 0;display:flex;'><div style='width:33%;text-align:center;color:#fff;font-weight:bold;font-size:15px;'>🔥 {lambda_final_l_val}</div><div style='width:34%;text-align:center;color:#00d4ff;font-weight:bold;font-size:13px;'>λ FINAL</div><div style='width:33%;text-align:center;color:#fff;font-weight:bold;font-size:15px;'>🔥 {lambda_final_v_val}</div></div>
                {fila_dato(calib_l_str, '🔧 CALIBRACIÓN', calib_v_str, bg_par=True)}
                <div style='background:#0a0a0a;padding:10px;border-radius:8px;margin-top:15px;margin-bottom:5px;text-align:center;'><span style='color:#00d4ff;font-weight:bold;'>📈 PROMEDIOS POR PARTIDO</span></div>
                {fila_dato(f'{prom_tiros_l_str}', 'Tiros Total', f'{prom_tiros_v_str}', bg_par=True)}
                {fila_dato(f'{prom_tiros_arco_l_str}', 'Tiros Arco', f'{prom_tiros_arco_v_str}')}
                {fila_dato(f'{prom_amarillas_l_str} ⚑', '🟨 Amarillas', f'{prom_amarillas_v_str} ⚑', bg_par=True)}
                {fila_dato(f'{prom_corners_l_str}', 'Esquinas', f'{prom_corners_v_str}')}
                <div style='background:#0a0a0a;padding:10px;border-radius:8px;margin-top:15px;margin-bottom:5px;text-align:center;'><span style='color:#00d4ff;font-weight:bold;'>📅 FORMA RECIENTE (Últimos 5)</span></div>
                {fila_dato(f'{puntos_str}%', 'Puntos %', f'{puntos_v_str}%', bg_par=True)}
                {fila_dato(f'{gf_forma_str}f/{gc_forma_str}c', 'Goles (5 Part)', f'{gf_v_forma_str}f/{gc_v_forma_str}c')}
                {fila_dato(badges_local, 'Resultados', badges_visitante, bg_par=True)}
            </div>
            """
            # Centrar tabla comparativa usando columnas de Streamlit
            col_izq, col_centro, col_der = st.columns([1, 2, 1])
            with col_centro:
                st.html(html_content)
        # ========================
        # GUARDAR PARTIDO (TODAS LAS PREDICCIONES)
        # ========================
        st.markdown("---")

        # Verificar si hay resultado de análisis
        r = st.session_state.get('analysis_result', {})
        stats_local = st.session_state.get('stats_local', {})
        stats_visitante = st.session_state.get('stats_visitante', {})

        # VALORES POR DEFECTO PARA EVITAR ERRORES NONE
        pj_l_display = pj_v_display = 0
        vic_l = emp_l = der_l = vic_v = emp_v = der_v = 0
        gf_l = gc_l = gf_v = gc_v = 0.0
        prom_tiros_l = prom_tiros_v = 13.0
        prom_tiros_arco_l = prom_tiros_arco_v = 4.5
        prom_amarillas_l = prom_amarillas_v = 2.5
        prom_corners_l = prom_corners_v = 5.5
        puntos = puntos_v = 0
        gf_forma = gc_forma = gf_v_forma = gc_v_forma = 0
        badges_local = badges_visitante = ''
        lambda_din_l = lambda_din_v = '0.00'
        lambda_historico_local = lambda_historico_visit = 0.0
        lambda_local_final = lambda_visit_final = 0.0
        home = st.session_state.get('home', '')
        away = st.session_state.get('away', '')
        confianza = r.get('confianza', 0)
        rango = r.get('rango', 'D')

        # ========================
        # 🏟️ FOOTBALL FIELD + SELECCIONAR APUESTAS (botones-tarjeta clickeables)
        # ========================
        p1 = r.get('p1', 0)
        px = r.get('px', 0)
        p2 = r.get('p2', 0)
        es_local_max = p1 > px and p1 > p2
        es_empate_max = px > p1 and px > p2
        es_visita_max = p2 > p1 and p2 > px
        p1_fmt = int(p1)
        px_fmt = int(px)
        p2_fmt = int(p2)

        # Predicciones adicionales (stats dinamicas)
        promedios_dinamicos_local = st.session_state.get('promedios_dinamicos_local')
        promedios_dinamicos_visitante = st.session_state.get('promedios_dinamicos_visitante')
        tiene_datos_local = promedios_dinamicos_local and promedios_dinamicos_local.get('partidos_total', 0) > 0
        tiene_datos_visitante = promedios_dinamicos_visitante and promedios_dinamicos_visitante.get('partidos_total', 0) > 0
        if not (tiene_datos_local or tiene_datos_visitante):
            st.warning("⚠️ **Sin datos históricos** - Sincroniza equipos para ver predicciones adicionales.")
        datos_local = promedios_dinamicos_local or {}
        datos_visitante = promedios_dinamicos_visitante or {}
        ta_local = datos_local.get('promedio_amarillas', 0) if tiene_datos_local else 0
        ta_visitante = datos_visitante.get('promedio_amarillas', 0) if tiene_datos_visitante else 0
        tarjetas_total = ta_local + ta_visitante
        ti_local = datos_local.get('promedio_tiros', 0) if tiene_datos_local else 0
        ti_visitante = datos_visitante.get('promedio_tiros', 0) if tiene_datos_visitante else 0
        remates_total = ti_local + ti_visitante
        arco_local = datos_local.get('promedio_tiros_arco', 0) if tiene_datos_local else 0
        arco_visitante = datos_visitante.get('promedio_tiros_arco', 0) if tiene_datos_visitante else 0
        arco_total = arco_local + arco_visitante
        tiene_stats_basicos = bool(stats_local and stats_visitante)

        if r:
            pred_tiros = r.get('tiros', {})
            pred_tarjetas = r.get('tarjetas', {})
            pred_arco = r.get('tiros_arco', {})
            pick_tiros = r.get('pick_tiros') or 'Over 24'
            prob_tiros = float(r.get('prob_tiros') or 50)
            remates_modelo = float(pred_tiros.get('total_estimado') or remates_total or 0)
            pick_tarjetas = r.get('pick_tarjetas') or 'Over 6'
            prob_tarjetas = float(r.get('prob_tarjetas') or 50)
            tarjetas_modelo = float(pred_tarjetas.get('total_estimado') or tarjetas_total or 0)
            pick_arco = r.get('pick_tiros_arco') or 'Over 8'
            prob_arco = float(r.get('prob_tiros_arco') or 50)
            arco_modelo = float(pred_arco.get('total_estimado') or arco_total or 0)
            top_scores = r.get('top_scores') or {}
            score_mas_probable = list(top_scores.keys())[0] if top_scores else "?"
            pick_ou = r.get('pick_over_under', 'Over 2.5')
            prob_ou = r.get('prob_over_under', 50)
            ou_text = "Mas" if "Over" in pick_ou else "Menos"
            pick_btts = r.get('pick_btts', 'No')
            btts_yes = r.get('btts_yes', 50)
            btts_icon = "Si" if pick_btts == "Si" else "No"
            corners = r.get('corners', {})
            total_c = corners.get('total_estimado', 10)
            pick_corners = r.get('pick_corners', '+')
            ti_icon = "Mas" if "Over" in pick_tiros else "Menos"
            arco_icon = "Mas" if "Over" in pick_arco else "Menos"
            tar_icon = "Mas" if "Over" in pick_tarjetas else "Menos"
        elif tiene_stats_basicos:
            pj_l = stats_local.get('partidos_jugados', 1) or 1
            pj_v = stats_visitante.get('partidos_jugados', 1) or 1
            gf_l = float(stats_local.get('goles_favor', 0) or 0)
            gf_v = float(stats_visitante.get('goles_favor', 0) or 0)
            lambda_l = gf_l / pj_l if pj_l > 0 else 1.3
            lambda_v = gf_v / pj_v if pj_v > 0 else 1.1
            scores = {}
            for gl in range(5):
                for gv in range(5):
                    p = pp(lambda_l, gl) * pp(lambda_v, gv)
                    if p > 0.01:
                        scores[f"{gl}-{gv}"] = p
            top_scores_calc = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            score_mas_probable = top_scores_calc[0][0] if top_scores_calc else "?"
            ou_prob = sum(p for (k), p in scores.items() if sum(map(int, k.split('-'))) > 2.5)
            pick_ou = "Over 2.5" if ou_prob > 0.5 else "Under 2.5"
            prob_ou = ou_prob * 100
            ou_text = "Mas" if "Over" in pick_ou else "Menos"
            btts_yes = (1 - pp(lambda_l, 0)) * (1 - pp(lambda_v, 0)) * 100
            pick_btts = "Si" if btts_yes > 50 else "No"
            btts_icon = pick_btts
            pick_tiros = "?"; prob_tiros = 0; remates_modelo = 0
            pick_tarjetas = "?"; prob_tarjetas = 0; tarjetas_modelo = 0
            pick_arco = "?"; prob_arco = 0; arco_modelo = 0
            corners = {}; total_c = 0; pick_corners = "?"
            ti_icon = "?"; arco_icon = "?"; tar_icon = "?"
        else:
            pick_tiros = '?'; prob_tiros = 0; remates_modelo = 0
            pick_tarjetas = '?'; prob_tarjetas = 0; tarjetas_modelo = 0
            pick_arco = '?'; prob_arco = 0; arco_modelo = 0
            score_mas_probable = "?"
            pick_ou = '?'; prob_ou = 0; ou_text = "?"
            pick_btts = '?'; btts_yes = 0; btts_icon = "?"
            corners = {}; total_c = 0; pick_corners = '?'
            ti_icon = "?"; arco_icon = "?"; tar_icon = "?"

        # --- Estado de seleccion ---
        if 'sel_apuestas' not in st.session_state:
            st.session_state.sel_apuestas = set()
        def _toggle(key):
            def _cb():
                s = st.session_state.sel_apuestas
                s.discard(key) if key in s else s.add(key)
                st.session_state.sel_apuestas = s
            return _cb
        sel = st.session_state.sel_apuestas
        # --- Header del field ---
        st.markdown(
            f'<div class="field-header-card">'
            f'<span class="field-team">{home}</span>'
            f' <span class="field-vs">VS</span> '
            f'<span class="field-team">{away}</span>'
            f'</div>', unsafe_allow_html=True)

        # Colores por grupo
        C_RES = "#00d4ff"   # Resultado (azul cyan)
        C_DOB = "#a78bfa"   # Doble Oportunidad (violeta)
        C_GOL = "#22c55e"   # Goles (verde)
        C_EQ  = "#fbbf24"   # Goles por equipo (amarillo)
        C_JUE = "#f472b6"   # Juego (rosa)

        # Calcular dobles oportunidades
        dob_1x = p1 + px
        dob_x2 = px + p2
        dob_12 = p1 + p2
        es_1x_max = dob_1x >= dob_x2 and dob_1x >= dob_12
        es_x2_max = dob_x2 >= dob_1x and dob_x2 >= dob_12
        es_12_max = dob_12 >= dob_1x and dob_12 >= dob_x2

        # Over/Under 1.5 y 3.5
        ou_data = r.get('over_under', {}) if r else {}
        over_15 = float(ou_data.get('over_15', 0)) if ou_data else 0
        under_15 = float(ou_data.get('under_15', 0)) if ou_data else 0
        over_35 = float(ou_data.get('over_35', 0)) if ou_data else 0
        under_35 = float(ou_data.get('under_35', 0)) if ou_data else 0
        pick_ou15 = 'Over' if over_15 >= 50 else 'Under'
        prob_ou15 = over_15 if pick_ou15 == 'Over' else under_15
        pick_ou35 = 'Over' if over_35 >= 50 else 'Under'
        prob_ou35 = over_35 if pick_ou35 == 'Over' else under_35

        # Goles por equipo (lambda)
        gl_val = r.get('goles_local', 0) if r else 0
        gv_val = r.get('goles_visitante', 0) if r else 0
        gl_over = gl_val >= 1.0
        gv_over = gv_val >= 1.0

        # ============================
        # GRUPO 1: RESULTADO (1X2)
        # ============================
        _group_title('Resultado', '🏆', C_RES)
        c_l, c_e, c_v = st.columns(3)
        _btn_pred(c_l, 'btn_card_local', 'Local', f"{p1_fmt}%", 'Local' in sel, _toggle('Local'), es_local_max, C_RES)
        _btn_pred(c_e, 'btn_card_empate', 'Empate', f"{px_fmt}%", 'Empate' in sel, _toggle('Empate'), es_empate_max, C_RES)
        _btn_pred(c_v, 'btn_card_visita', 'Visitante', f"{p2_fmt}%", 'Visitante' in sel, _toggle('Visitante'), es_visita_max, C_RES)

        # ============================
        # GRUPO 2: DOBLE OPORTUNIDAD
        # ============================
        _group_title('Doble Oportunidad', '🔀', C_DOB)
        d1, d2, d3 = st.columns(3)
        _btn_pred(d1, 'btn_card_1x', '1X', f"{dob_1x:.0f}%", '1X' in sel, _toggle('1X'), es_1x_max, C_DOB)
        _btn_pred(d2, 'btn_card_x2', 'X2', f"{dob_x2:.0f}%", 'X2' in sel, _toggle('X2'), es_x2_max, C_DOB)
        _btn_pred(d3, 'btn_card_12', '12', f"{dob_12:.0f}%", '12' in sel, _toggle('12'), es_12_max, C_DOB)

        # ============================
        # GRUPO 3: GOLES TOTALES
        # ============================
        _group_title('Goles Totales', '⚽', C_GOL)
        g1, g2, g3, g4 = st.columns(4)
        # Calcular total de goles estimado para mostrar
        goles_estimado = (r.get('goles_local', 0) or 0) + (r.get('goles_visitante', 0) or 0) if r else 0
        ou_val = f"{ou_text} 2.5  ·  {prob_ou:.0f}%" if pick_ou != '?' else '?'
        ou15_val = f"{'Mas' if pick_ou15=='Over' else 'Menos'} 1.5  ·  {prob_ou15:.0f}%" if r else '?'
        ou35_val = f"{'Mas' if pick_ou35=='Over' else 'Menos'} 3.5  ·  {prob_ou35:.0f}%" if r else '?'
        btts_val = f"{btts_icon}  ·  {btts_yes:.0f}%" if pick_btts != '?' else '?'
        _btn_pred(g1, 'btn_card_ou15', 'OU 1.5', ou15_val, 'OU 1.5' in sel, _toggle('OU 1.5'), accent=C_GOL)
        _btn_pred(g2, 'btn_card_ou', 'OU 2.5', ou_val, 'O/U' in sel, _toggle('O/U'), accent=C_GOL)
        _btn_pred(g3, 'btn_card_ou35', 'OU 3.5', ou35_val, 'OU 3.5' in sel, _toggle('OU 3.5'), accent=C_GOL)
        _btn_pred(g4, 'btn_card_btts', 'BTTS', btts_val, 'BTTS' in sel, _toggle('BTTS'), accent=C_GOL)

        # ============================
        # GRUPO 4: GOLES POR EQUIPO
        # ============================
        _group_title(f'Goles por Equipo  ·  Total: {goles_estimado:.1f}', '🎯', C_EQ)
        e1, e2 = st.columns(2)
        gl_str = f"{gl_val:.1f} goles  ·  {'Over 1.5' if gl_over else 'Under 1.5'}" if r else '?'
        gv_str = f"{gv_val:.1f} goles  ·  {'Over 1.5' if gv_over else 'Under 1.5'}" if r else '?'
        _btn_pred(e1, 'btn_card_glocal', f'🏠 {home[:14]}', gl_str, 'Goles Local' in sel, _toggle('Goles Local'), gl_over, C_EQ)
        _btn_pred(e2, 'btn_card_gvisit', f'✈️ {away[:14]}', gv_str, 'Goles Visitante' in sel, _toggle('Goles Visitante'), gv_over, C_EQ)

        # ============================
        # GRUPO 5: JUEGO (STATS)
        # ============================
        _group_title('Estadísticas de Juego', '🎮', C_JUE)
        j1, j2, j3, j4 = st.columns(4)
        # Probabilidad de corners: usar over_95/under_95 del modelo
        prob_ck = 50
        if r and isinstance(corners, dict):
            if 'Under' in str(pick_corners):
                prob_ck = float(corners.get('under_95', 50))
            else:
                prob_ck = float(corners.get('over_95', 50))
        ck_val = f"{int(total_c)} total  ·  {pick_corners} {int(prob_ck)}%" if pick_corners != '?' else '?'
        ti_val = f"{int(remates_modelo)} total  ·  {ti_icon} {int(prob_tiros)}%" if pick_tiros != '?' else '?'
        ar_val = f"{int(arco_modelo)} total  ·  {arco_icon} {int(prob_arco)}%" if pick_arco != '?' else '?'
        tj_val = f"{int(tarjetas_modelo)} total  ·  {tar_icon} {int(prob_tarjetas)}%" if pick_tarjetas != '?' else '?'
        _btn_pred(j1, 'btn_card_ck', '🌽 Córners', ck_val, 'Corners' in sel, _toggle('Corners'), accent=C_JUE)
        _btn_pred(j2, 'btn_card_tiros', '📍 Tiros', ti_val, 'Remates' in sel, _toggle('Remates'), accent=C_JUE)
        _btn_pred(j3, 'btn_card_arco', '🎯 T. Arco', ar_val, 'Tiros Arco' in sel, _toggle('Tiros Arco'), accent=C_JUE)
        _btn_pred(j4, 'btn_card_tarj', '🟨 Tarjetas', tj_val, 'Tarjetas' in sel, _toggle('Tarjetas'), accent=C_JUE)

        # --- Score + Goles estimados ---
        st.markdown(
            f'<div class="field-score-card">'
            f'<span style="color:rgba(255,255,255,0.6);font-size:0.75rem;">Marcador más probable</span><br>'
            f'<span style="color:#fff;font-weight:800;font-size:1.3rem;font-family:monospace;">{score_mas_probable}</span>'
            f'<br><span style="color:rgba(255,255,255,0.5);font-size:0.7rem;">Goles: {goles_estimado:.1f} esperados</span>'
            f'</div>', unsafe_allow_html=True)

        # --- Boton guardar ---
        n_sel = len(sel)
        if st.button(f"💾 Guardar y ➡️ Capital  ({n_sel})", type="primary", use_container_width=True):
            mercados_seleccionados = list(sel)
            try:
                client = get_client()
                pick_data = _construir_pick_data(r, home, away, stats_local)
                guardado = _insertar_pick_resiliente(client, pick_data)
                if mercados_seleccionados:
                    pick_id = guardado.get('id') if isinstance(guardado, dict) else None
                    pendientes = st.session_state.get('apuestas_pendientes_analizador', {})
                    pendientes[pick_id] = set(mercados_seleccionados)
                    st.session_state.apuestas_pendientes_analizador = pendientes
                    st.success(f"✅ {len(mercados_seleccionados)} apuesta(s) enviada(s) a Capital")
                else:
                    st.success(f"✅ Pick guardado: {home} vs {away}")
                st.session_state.sel_apuestas = set()
            except Exception as e:
                st.error(f"❌ Error: {e}")
        # ========================
        # ⚽ GOLES ESTIMADOS - integrados en botones de arriba (sin duplicar)
        # ========================

        render_cuotas_mercado(r)
# Página: Estadísticas

def render_claves_page():
    st.markdown("### 👑 Gestión de Contraseñas")

    # Tabs
    tab_crear, tab_gestionar = st.tabs(["➕ Crear Contraseña", "📋 Ver Contraseñas"])

    # ========== TAB: CREAR ==========
    with tab_crear:
        st.markdown("#### ➕ Crear Nueva Contraseña de Acceso")

        with st.form("form_crear_clave", clear_on_submit=True):
            col_nom, col_plan = st.columns(2)
            with col_nom:
                nombre = st.text_input("Nombre / Cliente", placeholder="Ej: Juan, Carlos VIP").strip()
            with col_plan:
                plan = st.selectbox("🦂 Plan", ["semana", "mes", "elite", "vip"])

            nueva_clave = st.text_input("🔑 Nueva Contraseña", placeholder="Escribe la contraseña única").strip()

            dias_opciones = {"semana": 7, "mes": 30, "elite": 90, "vip": 90}
            dias = dias_opciones.get(plan, 30)

            col_info, col_btn = st.columns([2, 1])
            with col_info:
                plan_icon = {"semana": "📦", "mes": "👑", "elite": "📘", "vip": "⭐"}
                st.info(f"{plan_icon.get(plan, '🦂')} Plan: {plan.upper()} - {dias} días")

            submitted = st.form_submit_button("✅ Crear Contraseña", use_container_width=True, type="primary")

            if submitted:
                if not nombre.strip():
                    st.error("⚠️ Ingresa un nombre")
                elif not nueva_clave.strip():
                    st.error("⚠️ Ingresa una contraseña")
                elif len(nueva_clave) < 4:
                    st.error("⚠️ La contraseña debe tener al menos 4 caracteres")
                else:
                    # Asignar el plan seleccionado por el usuario
                    plan_asignar = plan
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
            st.markdown("**⭐ GRATIS** - Sin VIP")
        with col2:
            st.markdown("**📦 SEMANA** - 7 días VIP")

    # ========== TAB: GESTIONAR ==========
    with tab_gestionar:
        st.markdown("#### 📋 Contraseñas Creadas")

        # Botón recargar (el clic del botón ya causa rerun automático en Streamlit)
        st.button("🔄 Recargar Lista")
        usuarios = db_todos()

        if not usuarios:
            st.info("⚽ No hay contraseñas creadas. Crea una en la pestaña de arriba.")
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
                    icono = "⚡️"
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
                                nueva_pass = st.text_input("Nueva contraseña", placeholder="Nueva...", key=f"pass_{clave_id}", type="password")
                                if st.button("🔑 Cambiar", key=f"btn_pass_{clave_id}"):
                                    if nueva_pass and len(nueva_pass) >= 4:
                                        if db_cambiar_password(clave_id, nueva_pass):
                                            st.success("✅ Contraseña cambiada")
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
                                    else:
                                        st.error("❌ Error")
                            with col_c:
                                st.write("")  # Espacio
                                if st.button("🗑️ Eliminar", key=f"btn_del_{clave_id}", type="primary"):
                                    if db_eliminar_usuario(clave_id):
                                        st.success("✅ Eliminada")
                                    else:
                                        st.error("❌ No se pudo eliminar")
                        else:
                            st.info("⚡️ Cuenta del administrador")
                    st.markdown("---")

# ══════════════════════════════════════════════════════════
# PÁGINA VIP DASHBOARD - Solo para usuarios Elite/Premium
# ══════════════════════════════════════════════════════════

def render_vip_value_bets(client, usuario_id):
    """Tab Value Bets: detector de apuestas con value."""
    st.markdown("### 🎯 Detector de Value Bets")
    st.markdown("_Encuentra apuestas donde la probabilidad del modelo es MAYOR que la cuota del mercado_")

    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        prob_modelo = st.slider("📥 Probabilidad del Modelo (%)", 10, 99, 60)
    with col_v2:
        cuota_mercado = st.number_input("🏆 Cuota del Mercado", value=2.0, min_value=1.01, max_value=20.0, step=0.05)
    with col_v3:
        tipo_apuesta = st.selectbox("📋 Tipo de Apuesta", ["1X2", "Over/Under", "BTTS", "Corners", "Tarjetas"])

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

    if value >= 10:
        st.success("📘📘 **APUESTA FUERTE** - Value muy alto, alta confianza")
    elif value >= 5:
        st.success("✅ **APUESTA** - Value positivo, buena oportunidad")
    elif value >= 0:
        st.info("📥 **CAUTELA** - Value marginal, depende de otros factores")
    else:
        st.error("❌ **EVITAR** - La cuota está por encima de lo que el modelo sugiere")

    st.markdown("---")
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
        logger.warning(f"render_vip_value_bets falló: {e}")
        st.info("⚽ Conecta a Supabase para ver value bets guardados.")


def render_vip_alertas(client, usuario_id):
    """Tab Alertas: centro de notificaciones VIP."""
    st.markdown("### 🔔 Centro de Alertas VIP")

    st.markdown("#### 🔊 Crear Nueva Alerta")
    col_al1, col_al2, col_al3 = st.columns(3)
    with col_al1:
        tipo_alerta = st.selectbox("Tipo", ["alta_confianza", "value_bet", "streak", "resultado", "custom"])
    with col_al2:
        prioridad = st.selectbox("Prioridad", ["alta", "media", "baja"])
    with col_al3:
        st.write("")

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
    st.markdown("#### 🎯 Alertas Recientes")

    try:
        alertas_response = client.table('alertas').select('*').eq('usuario_id', usuario_id).order('creado_en', desc=True).limit(20).execute()
        alertas = alertas_response.data if alertas_response.data else []

        if alertas:
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
                    if st.button("✅ Marcar leída", key=f"leer_{alerta.get('id')}"):
                        try:
                            client.table('alertas').update({'leida': True}).eq('id', alerta.get('id')).execute()
                            st.success("Marcada como leída")
                        except Exception as e:
                            st.warning(f"⚠️ No se pudo marcar como leída: {e}")
        else:
            st.info("⚽ No hay alertas.")
    except Exception as e:
        logger.warning(f"render_vip_alertas falló: {e}")
        st.info("⚽ Conecta a Supabase para ver alertas.")


def render_vip_ranking(client, usuario_id, picks=None):
    """Tab Ranking: ranking mensual de pickers + badges."""
    st.markdown("### 🏆 Ranking Mensual VIP")

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
            st.info("⚽ No hay ranking aún. ¡Sé el primero!")

            if picks:
                st.markdown("##### 📥 Generar Ranking")
                if st.button("🔄 Calcular Ranking"):
                    st.info("Ranking calculado (funcionalidad completa con más usuarios)")
    except Exception as e:
        logger.warning(f"render_vip_ranking falló: {e}")
        st.info("⚽ Ranking no disponible. Conecta a Supabase.")

    st.markdown("---")
    st.markdown("#### … Mis Badges y Logros")

    num_picks = len(picks) if picks else 0
    badges_disponibles = {
        "🎯 Primer Pick": num_picks >= 1,
        "📥 10 Picks": num_picks >= 10,
        "📘 50 Picks": num_picks >= 50,
        "👑 100 Picks": num_picks >= 100,
        "🏆 ROI 10%": True,
        "🎯 Racha 5": True,
        "📘 Racha 10": True,
        "⭐ Valoración 5★": False,
    }

    cols_badge = st.columns(4)
    for i, (badge, unlocked) in enumerate(badges_disponibles.items()):
        with cols_badge[i % 4]:
            if unlocked:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a3a2a 0%, #0f2518 100%); 
                            border: 2px solid #22c55e; border-radius: 10px; padding: 12px; 
                            text-align: center; margin: 4px 0;">
                    <div style="color: #4ade80; font-weight: 700; font-size: 0.95rem;">{badge}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #1e293b; border: 2px solid #334155; border-radius: 10px; 
                            padding: 12px; text-align: center; margin: 4px 0; opacity: 0.6;">
                    <div style="color: #64748b; font-weight: 600; font-size: 0.95rem;">🔒 {badge}</div>
                </div>
                """, unsafe_allow_html=True)


def render_vip_export(client, usuario_id, picks=None):
    """Tab Exportar: descarga de reportes en CSV/Excel/JSON."""
    st.markdown("### 🔄 Exportar Reportes")

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

    col_per1, col_per2 = st.columns(2)
    with col_per1:
        fecha_inicio = st.date_input("Desde", value=pd.Timestamp.now() - pd.Timedelta(days=30))
    with col_per2:
        fecha_fin = st.date_input("Hasta", value=pd.Timestamp.now())

    if picks:
        picks_filtrados = [
            p for p in picks
            if p.get('fecha') and pd.Timestamp(fecha_inicio) <= pd.to_datetime(p.get('fecha')) <= pd.Timestamp(fecha_fin)
        ]

        st.markdown(f"📥 **{len(picks_filtrados)} pick** en el período seleccionado")

        if st.button("📘 Descargar Reporte", type="primary"):
            if tipo_reporte == "Picks Completos":
                df_export = pd.DataFrame(picks_filtrados)
            elif tipo_reporte == "Solo Resueltos":
                df_export = pd.DataFrame([p for p in picks_filtrados if p.get('acertado_1x2') is not None])
            elif tipo_reporte == "ROI por Tipo":
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
                except Exception as e:
                    logger.warning(f"export bankroll_history falló: {e}")
                    df_export = pd.DataFrame()
            else:  # Value Bets
                try:
                    vb_response = client.table('value_bets').select('*').eq('usuario_id', usuario_id).execute()
                    vb = vb_response.data if vb_response.data else []
                    df_export = pd.DataFrame(vb)
                except Exception as e:
                    logger.warning(f"export value_bets falló: {e}")
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


def render_vip_page():

    # Verificar si el usuario es VIP/Elite
    user_plan = st.session_state.user_data.get('plan', 'vip') if st.session_state.user_data else 'vip'
    is_admin = st.session_state.user_data.get('es_admin', 0) == 1 if st.session_state.user_data else False
    # Admin siempre tiene acceso VIP
    es_vip = is_admin or user_plan.lower() in ['vip', 'elite', 'admin', 'mes', 'premium']

    if not es_vip:
        # Mostrar pantalla de upgrade
        st.markdown("""
        <div style="text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 16px; margin: 20px 0; border: 1px solid #334155;">
            <h1 style="color: #f8fafc; margin-bottom: 20px;">👑 Contenido Exclusivo para Miembros VIP</h1>
            <p style="font-size: 1.2em; color: #cbd5e1; margin: 30px 0;">
                El Dashboard VIP está disponible solo para miembros con plan <strong style="color: #00d4aa;">Elite VIP</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Plan card
        st.markdown("""
        <div class="plan-card plan-vip" style="max-width: 400px; margin: 0 auto; text-align: center; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 2px solid #00d4aa; border-radius: 12px; padding: 25px;">
            <h3 style="color: #f8fafc;">👑 Plan Elite VIP</h3>
            <p class="plan-price" style="color: #00d4aa; font-size: 2rem; font-weight: 800;">$29.99 <span style="color: #94a3b8; font-size: 1rem;">/mes</span></p>
            <ul style="text-align: left; color: #e2e8f0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">✅ Dashboard VIP completo</li>
                <li style="margin-bottom: 8px;">✅ ROI por modelo y tipo de pick</li>
                <li style="margin-bottom: 8px;">✅ Simulador de Bankroll</li>
                <li style="margin-bottom: 8px;">✅ Detector de Value Bets</li>
                <li style="margin-bottom: 8px;">✅ Alertas y notificaciones</li>
                <li style="margin-bottom: 8px;">✅ Ranking mensual</li>
                <li style="margin-bottom: 8px;">✅ Reportes exportables</li>
            </ul>
            <p style="margin-top: 20px; color: #f8fafc;"><strong style="color: #00d4aa;"> 7 días GRATIS - Sin tarjeta</strong></p>
        </div>
        """, unsafe_allow_html=True)

        # Mostrar plan actual
        st.markdown("---")
        st.info(f"💰 Tu plan actual: **{user_plan.upper()}**")
        st.markdown("¿Quieres hacer upgrade? Contacta al administrador.")

        st.stop()

    # Usuario VIP - mostrar dashboard
    st.markdown("### 👑 Dashboard VIP - Gestión Inteligente de Apuestas")

    # CSS global para todo el VIP - Contraste mejorado
    st.markdown("""
    <style>
    /* Tabs del VIP */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        color: #cbd5e1;
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
        font-weight: 600;
        border: 1px solid #334155;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #00d4aa 0%, #00a88a 100%);
        color: #ffffff;
        border-color: #00d4aa;
    }
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background: #334155;
        color: #f8fafc;
    }

    /* Tabla de datos */
    .stDataFrame, .stTable {
        color: #f8fafc;
    }
    .stDataFrame table, .stTable table {
        color: #f8fafc;
    }
    .stDataFrame th, .stTable th {
        color: #00d4aa !important;
        background: #1e293b !important;
        font-weight: 700;
    }
    .stDataFrame td, .stTable td {
        color: #e2e8f0 !important;
    }

    /* Expanders */
    .stExpander {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    .stExpander summary, .stExpander [data-testid="stExpander"] summary {
        color: #f8fafc !important;
        font-weight: 600;
    }

    /* Texto markdown dentro del VIP */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        color: #e2e8f0;
    }
    .stMarkdown strong {
        color: #f8fafc;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
        color: #f8fafc;
    }

    /* Info/Warning/Success/Error boxes */
    .stAlert, [data-testid="stAlert"] {
        color: #f8fafc;
    }

    /* Radio buttons */
    .stRadio label {
        color: #e2e8f0 !important;
    }

    /* Text input */
    .stTextInput input {
        color: #f8fafc !important;
        background: #1e293b !important;
    }
    .stTextInput label {
        color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

                picks_corners = [p for p in picks_resueltos if p.get('acertado_corners') is not None]
                acertados_corners = len([p for p in picks_corners if p.get('acertado_corners')])
                pct_corners = (acertados_corners / len(picks_corners) * 100) if picks_corners else 0

                picks_tarjetas = [p for p in picks_resueltos if p.get('acertado_tarjetas') is not None]
                acertados_tarjetas = len([p for p in picks_tarjetas if p.get('acertado_tarjetas')])
                pct_tarjetas = (acertados_tarjetas / len(picks_tarjetas) * 100) if picks_tarjetas else 0

                picks_remates = [p for p in picks_resueltos if p.get('acertado_remates') is not None]
                acertados_remates = len([p for p in picks_remates if p.get('acertado_remates')])
                pct_remates = (acertados_remates / len(picks_remates) * 100) if picks_remates else 0

                picks_arco = [p for p in picks_resueltos if p.get('acertado_arco') is not None]
                acertados_arco = len([p for p in picks_arco if p.get('acertado_arco')])
                pct_arco = (acertados_arco / len(picks_arco) * 100) if picks_arco else 0

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
                with col3:
                    st.metric("⚽ BTTS", f"{acertados_btts}/{len(picks_btts)}", f"{pct_btts:.1f}% acierto")
                    if pct_btts > 55: st.success("✅ Rentable")
                    elif pct_btts < 45: st.error("❌ Perjudicial")
                    else: st.info("📥 Neutral")

                col4, col5, col6, col7 = st.columns(4)
                with col4:
                    st.metric("🔑 Corners", f"{acertados_corners}/{len(picks_corners)}", f"{pct_corners:.1f}% acierto")
                    if pct_corners > 55: st.success("✅ Rentable")
                    elif pct_corners < 45: st.error("❌ Perjudicial")
                    else: st.info("📥 Neutral")
                with col5:
                    st.metric("🟨 Tarjetas", f"{acertados_tarjetas}/{len(picks_tarjetas)}", f"{pct_tarjetas:.1f}% acierto")
                    if pct_tarjetas > 55: st.success("✅ Rentable")
                    elif pct_tarjetas < 45: st.error("❌ Perjudicial")
                    else: st.info("📥 Neutral")
                with col6:
                    st.metric("🔫 Remates", f"{acertados_remates}/{len(picks_remates)}", f"{pct_remates:.1f}% acierto")
                    if pct_remates > 55: st.success("✅ Rentable")
                    elif pct_remates < 45: st.error("❌ Perjudicial")
                    else: st.info("📥 Neutral")
                with col7:
                    st.metric("🎯 T. Arco", f"{acertados_arco}/{len(picks_arco)}", f"{pct_arco:.1f}% acierto")
                    if pct_arco > 55: st.success("✅ Rentable")
                    elif pct_arco < 45: st.error("❌ Perjudicial")
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
                        st.info(f"📘 Los picks de ALTA CONFIANZA (95%+) tienen {pct_95:.1f}% de aciertos. ¡Sigue así!")
                    elif pct_95 < 60:
                        st.warning(f"⚠️ Los picks de alta confianza solo acertaron {pct_95:.1f}%. Revisar calibración.")
            else:
                st.info("⚽ No hay picks resueltos aún. Completa algunos análisis y registra los resultados.")
        else:
            st.info("⚽ No hay picks guardados aún. Ve al Analizador para crear picks.")

    # ========== TAB 2: RESULTADOS (AUTO) ==========
    with tab_resultados:
        st.markdown("### 📊 Resultados Automáticos")
        st.info("🤖 Los resultados se actualizan automáticamente cuando sincronizas partidos desde la página 📊 Partidos. No necesitas ingresar nada manualmente.")

        # Obtener picks con resultado
        try:
            response = client.table('picks').select('*').order('fecha', desc=True).execute()
            picks_res = response.data if response.data else []
        except Exception as e:
            logger.warning(f"carga de picks falló: {e}")
            picks_res = []

        picks_con_resultado = [p for p in picks_res if p.get('resultado_1x2') is not None]
        picks_pendientes = [p for p in picks_res if p.get('resultado_1x2') is None]

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("✅ Resueltos", len(picks_con_resultado))
        with col_r2:
            st.metric("⏳ Pendientes", len(picks_pendientes))

        if picks_pendientes:
            with st.expander(f"📋 {len(picks_pendientes)} picks esperando resultados"):
                for p in picks_pendientes[:10]:
                    st.write(f"⚽ **{p.get('equipo_local', '?')} vs {p.get('equipo_visitante', '?')}** ({p.get('fecha', '')[:10]})")

        if picks_con_resultado:
            with st.expander(f"✅ {len(picks_con_resultado)} picks ya resueltos"):
                for p in picks_con_resultado[:10]:
                    acertado = p.get('acertado_1x2')
                    icon = "✅" if acertado else "❌"
                    st.write(f"{icon} **{p.get('equipo_local', '?')} vs {p.get('equipo_visitante', '?')}** → Real: {p.get('resultado_1x2', '?')} | Marcador: {p.get('marcador', '?')}")

        st.markdown("---")
        st.markdown("#### 🔄 Cómo funciona")
        st.markdown("""
        1. **Analiza** un partido en el Analizador y guarda el pick
        2. **Aposta** desde el Bankroll
        3. Cuando el partido termine, ve a **📊 Partidos → 🔄 Sincronizar**
        4. El sistema obtiene resultados reales y actualiza TODO automáticamente:
           - ✅ Resultados 1X2, O/U, BTTS
           - ✅ Córners, Tarjetas, Remates, Tiros Arco
           - ✅ Bankroll (ganancias/pérdidas)
           - ✅ Calibración de lambdas
        """)

    # ========== TAB 3: BANKROLL ==========
    with tab_bankroll:
        # CSS específico para bankroll - Contraste mejorado
        st.markdown("""
        <style>
        /* Checkbox verde */
        [data-testid="stCheckbox"] {
            background: #0d2818 !important;
            border: 2px solid #22c55e !important;
            border-radius: 6px !important;
            padding: 6px 8px !important;
        }

        [data-testid="stCheckbox"] input[type="checkbox"] {
            width: 22px !important;
            height: 22px !important;
            accent-color: #22c55e !important;
            cursor: pointer;
        }

        [data-testid="stCheckbox"] label {
            color: #f1f5f9 !important;
            font-size: 14px !important;
            font-weight: 500 !important;
        }

        /* Inputs de número (cuota) */
        div[data-testid="stNumberInput"] {
            max-width: 80px !important;
            min-height: 32px !important;
        }

        div[data-testid="stNumberInput"] label {
            color: #e2e8f0 !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        div[data-testid="stNumberInput"] input {
            color: #000000 !important;
            font-size: 14px !important;
            font-weight: bold !important;
            background: #ffffff !important;
            padding: 2px 6px !important;
            min-height: 32px !important;
        }

        /* Selectbox - IGUAL a los number inputs */
        div[data-testid="stSelectbox"] {
            max-width: 80px !important;
            min-height: 32px !important;
            background: #ffffff !important;
            border: 2px solid #22c55e !important;
            border-radius: 8px !important;
        }

        div[data-testid="stSelectbox"] label {
            color: #e2e8f0 !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        div[data-testid="stSelectbox"],
        div[data-testid="stSelectbox"] *,
        div[data-testid="stSelectbox"] input,
        div[data-testid="stSelectbox"] span,
        div[data-testid="stSelectbox"] p,
        div[data-testid="stSelectbox"] div {
            color: #000000 !important;
            font-size: 14px !important;
            font-weight: bold !important;
            background: #ffffff !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: none !important;
            min-height: 32px !important;
            padding: 2px 6px !important;
        }

        /* Filas de selección de picks - COMPACTAS */
        div[data-testid="stHorizontalBlock"] {
            gap: 4px !important;
            align-items: center !important;
        }
        [data-testid="stCheckbox"] {
            padding: 0 !important;
            margin: 0 !important;
            min-height: 24px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [data-testid="stCheckbox"] > div {
            min-height: 24px !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        [data-testid="stCheckbox"] label {
            font-size: 0px !important;
            padding: 0 !important;
            margin: 0 !important;
            line-height: 0 !important;
            display: flex !important;
            align-items: center !important;
        }
        [data-testid="stCheckbox"] label span {
            display: none !important;
        }
        [data-testid="stCheckbox"] label p {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 0px !important;
            line-height: 0 !important;
        }
        [data-testid="stCheckbox"] input[type="checkbox"] {
            width: 20px !important;
            height: 20px !important;
            margin: 0 !important;
            cursor: pointer;
        }

        /* Texto de captions */
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #94a3b8 !important;
        }

        /* Métricas */
        [data-testid="stMetric"] label {
            color: #cbd5e1 !important;
            font-weight: 600 !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #f8fafc !important;
        }
        [data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: #94a3b8 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("### 🏆 Mi Bankroll")
        usuario_id = st.session_state.user_data.get('nombre', 'default') if st.session_state.user_data else 'default'

        MONEDAS = {
            "USD": {"simbolo": "$", "nombre": "Dólar"},
            "EUR": {"simbolo": "€", "nombre": "Euro"},
            "MXN": {"simbolo": "$", "nombre": "Peso MX"},
            "COP": {"simbolo": "$", "nombre": "Peso CO"},
            "PEN": {"simbolo": "S/", "nombre": "Sol PE"},
            "CLP": {"simbolo": "$", "nombre": "Peso CL"},
            "ARS": {"simbolo": "$", "nombre": "Peso AR"},
            "BRL": {"simbolo": "R$", "nombre": "Real"},
        }

        # Obtener picks del usuario
        try:
            response_picks = client.table('picks').select('*').eq('usuario', usuario_id).execute()
            picks_disponibles = response_picks.data if response_picks.data else []
        except Exception as e:
            logger.error(f"Error obteniendo picks: {e}")
            picks_disponibles = []

        # Obtener apuestas
        try:
            response_apuestas = client.table('bankroll_apuestas').select('*').eq('usuario', usuario_id).order('fecha', desc=True).execute()
            apuestas = response_apuestas.data if response_apuestas.data else []
        except Exception as e:
            logger.error(f"Error obteniendo apuestas: {e}")
            apuestas = []

        # ==================== SUBTABS ====================

        sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs(["📥 Dashboard", "➕ Agregar", "📋 Historial", "⚙️ Config"])

        # ========== SUBTAB 1: DASHBOARD ==========
        with sub_tab1:
            # Cargar bankroll guardado de user_stats
            try:
                resp_stats = client.table('user_stats').select('bankroll_inicial,total_retirado').eq('usuario', usuario_id).execute()
                if resp_stats.data:
                    bankroll_guardado = resp_stats.data[0].get('bankroll_inicial', 1000.0)
                    total_retirado_guardado = resp_stats.data[0].get('total_retirado', 0.0) or 0.0
                else:
                    bankroll_guardado = 1000.0
                    total_retirado_guardado = 0.0
            except Exception as e:
                bankroll_guardado = 1000.0
                total_retirado_guardado = 0.0

            # Cargar historial de retiros
            try:
                resp_retiros = client.table('bankroll_retiros').select('*').eq('usuario', usuario_id).order('fecha', desc=True).execute()
                retiros = resp_retiros.data if resp_retiros.data else []
            except Exception as e:
                retiros = []

            # Info de bankroll (moneda por defecto)
            simbolo = "$"
            st.markdown(f"""
            📊 **Bankroll Inicial:** {format_money(bankroll_guardado, simbolo)} 
            | 💸 **Total Retirado:** {format_money(total_retirado_guardado, simbolo)}
            """)
            st.markdown("_💡 Para cambiar moneda o hacer retiros, ve a **⚙️ Config**_")

            if apuestas:
                total_apostado = sum(a.get('cantidad', 0) for a in apuestas)
                ganancias = sum(a.get('ganancia', 0) for a in apuestas)
                # Bankroll real = Inicial + Ganancias - Retirado
                bankroll_actual = bankroll_guardado + ganancias - total_retirado_guardado
                roi = ((bankroll_actual - bankroll_guardado) / bankroll_guardado * 100) if bankroll_guardado > 0 else 0
                apuestas_ganadas = len([a for a in apuestas if a.get('ganancia', 0) > 0])
                total_apuestas = len(apuestas)
                tasa_acierto = (apuestas_ganadas / total_apuestas * 100) if total_apuestas > 0 else 0

                # Bankroll grande
                color_ganancia = "#4ade80" if ganancias >= 0 else "#f87171"
                color_label = "#cbd5e1"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1a3a2a 0%, #0f2518 100%); 
                            border-radius: 16px; padding: 30px; text-align: center; 
                            border: 2px solid {color_ganancia}; margin: 20px 0;
                            box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
                    <div style="color: {color_label}; font-size: 0.9rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;">Bankroll Actual</div>
                    <div style="font-size: 3rem; font-weight: 800; color: {color_ganancia}; margin: 10px 0; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{format_money(bankroll_actual, simbolo)}</div>
                    <div style="color: {color_ganancia}; font-size: 1.2rem; font-weight: 600;">{'+' if ganancias >= 0 else ''}{format_money(ganancias, simbolo)} ({'+' if roi >= 0 else ''}{roi:.1f}%)</div>
                </div>
                """, unsafe_allow_html=True)

                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("📈 ROI", f"{'+' if roi >= 0 else ''}{roi:.1f}%")
                with col_m2:
                    st.metric("🎯 Aciertos", f"{tasa_acierto:.0f}%", delta=f"{apuestas_ganadas}/{total_apuestas}")
                with col_m3:
                    st.metric("💰 Apostado", format_money(total_apostado, simbolo))
                with col_m4:
                    st.metric("🏆 Ganancia", format_money(ganancias, simbolo))

                if bankroll_actual >= bankroll_guardado * 1.1:
                    st.success(f"✅ Excelente: +{((bankroll_actual/bankroll_guardado)-1)*100:.1f}%")
                elif bankroll_actual >= bankroll_guardado:
                    st.info(f"📊 Estable")
                else:
                    st.warning(f"⚠️ En pérdida")

                if len(apuestas) > 1:
                    evolucion = []
                    b = bankroll_guardado
                    for a in sorted(apuestas, key=lambda x: x.get('fecha', '')):
                        b += a.get('ganancia', 0)
                        evolucion.append({'Fecha': str(a.get('fecha', ''))[:10], 'Bankroll': b})
                    st.markdown("#### 📈 Evolución")
                    st.line_chart(pd.DataFrame(evolucion).set_index('Fecha'))
            else:
                st.info("⚽ No tienes apuestas aún. Ve a 'Agregar' para empezar.")

        # ========== SUBTAB 2: AGREGAR ==========
        with sub_tab2:
            picks_sin = [p for p in picks_disponibles if p.get('acertado_1x2') is None]

            # Apuestas pendientes enviadas desde el Analizador
            pendientes_analizador = st.session_state.get('apuestas_pendientes_analizador', {})
            if pendientes_analizador:
                num_pend = sum(len(v) for v in pendientes_analizador.values())
                st.success(f"📥 Tienes {num_pend} apuesta(s) preseleccionada(s) desde el Analizador. Revisa las casillas marcadas abajo.")

            if not picks_sin:
                st.info("📋 No tienes picks. Ve al Analizador y guarda partidos.")
            else:
                modo = st.radio("🎲 Tipo", ["📋 Individual", "🔥 Combinada"], horizontal=True, index=0, key="modo_apuesta")
                es_combinada = modo == "🔥 Combinada"
                st.markdown("---")

                # Sección de borrado de picks (colapsable, no interfiere con apostar)
                with st.expander("🗑️ Borrar Picks"):
                    if picks_sin:
                        opciones_borrar = {}
                        for p in picks_sin:
                            label = f"{p.get('equipo_local', '?')} vs {p.get('equipo_visitante', '?')}"
                            if label not in opciones_borrar:
                                opciones_borrar[label] = p.get('id')
                        seleccion_borrar = st.multiselect(
                            "Selecciona los partidos a borrar",
                            list(opciones_borrar.keys()),
                            key="borrar_picks_sel"
                        )
                        if seleccion_borrar:
                            if st.button("🗑️ Borrar seleccionados", type="secondary", key="btn_borrar_picks"):
                                try:
                                    ids_borrar = [opciones_borrar[s] for s in seleccion_borrar]
                                    client.table('picks').delete().in_('id', ids_borrar).execute()
                                    st.success(f"✅ {len(ids_borrar)} pick(s) borrado(s)")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al borrar: {e}")
                    else:
                        st.info("No hay picks para borrar")

                # Recopilar opciones
                opciones = []
                for p in picks_sin:
                    local = p.get('equipo_local', '?')
                    visitante = p.get('equipo_visitante', '?')
                    match_key = f"{local} vs {visitante}"

                    if p.get('prediccion_1x2'):
                        opciones.append({'pick': p, 'display': f"{match_key} - 1X2: {p.get('prediccion_1x2')}", 'tipo': '1X2', 'cuota': float(p.get('cuota_1x2') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_1x2', 50)})
                    if p.get('prediccion_ou'):
                        opciones.append({'pick': p, 'display': f"{match_key} - O/U: {p.get('prediccion_ou')}", 'tipo': 'O/U', 'cuota': float(p.get('cuota_ou') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_ou', 50)})
                    if p.get('prediccion_btts'):
                        opciones.append({'pick': p, 'display': f"{match_key} - BTTS", 'tipo': 'BTTS', 'cuota': float(p.get('cuota_btts') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_btts', 50)})
                    if p.get('prediccion_corners'):
                        opciones.append({'pick': p, 'display': f"{match_key} - Corners", 'tipo': 'Corners', 'cuota': float(p.get('cuota_corners') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_corners', 50)})
                    if p.get('prediccion_tarjetas'):
                        opciones.append({'pick': p, 'display': f"{match_key} - Tarjetas", 'tipo': 'Tarjetas', 'cuota': float(p.get('cuota_tarjetas') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_tarjetas', 50)})
                    if p.get('prediccion_remates'):
                        opciones.append({'pick': p, 'display': f"{match_key} - Remates: {p.get('prediccion_remates')}", 'tipo': 'Remates', 'cuota': float(p.get('cuota_remates') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_remates', 50)})
                    if p.get('prediccion_arco'):
                        opciones.append({'pick': p, 'display': f"{match_key} - Tiros Arco: {p.get('prediccion_arco')}", 'tipo': 'Tiros Arco', 'cuota': float(p.get('cuota_arco') or 2.0), 'conf': p.get('confianza', 70), 'prob': p.get('prob_arco', 50)})

                st.markdown("#### 📋 Selecciona Picks (ingresa cuota)")
                seleccionados = []
                cantidades_dict = {}
                for i, opt in enumerate(opciones):
                    pick_id_opt = opt['pick'].get('id')
                    tipo_opt = opt.get('tipo')
                    # Pre-marcar si viene del Analizador (match por pick_id + tipo)
                    pre_sel = False
                    if pick_id_opt in pendientes_analizador:
                        tipos_pend = pendientes_analizador[pick_id_opt]
                        if tipo_opt in tipos_pend:
                            pre_sel = True
                    cols = st.columns([1, 4, 2])
                    with cols[0]:
                        sel = st.checkbox("", value=pre_sel, key=f"sel_pick_{i}")
                        if sel:
                            seleccionados.append(i)
                    with cols[1]:
                        st.markdown(f"**{opt['display']}** <span style='color:#94a3b8;font-size:0.8rem'> | {opt['tipo']} | {(opt.get('prob') or 0):.0f}%</span>", unsafe_allow_html=True)
                    with cols[2]:
                        cantidad_input = st.number_input("Cuota", value=float(opt['cuota']), min_value=1.01, max_value=100.0, step=0.05, key=f"cuota_{i}", label_visibility="collapsed")
                        cantidades_dict[i] = cantidad_input

                st.markdown("---")

                if seleccionados:
                    st.markdown("#### 💰 Configurar")

                    if es_combinada and len(seleccionados) < 2:
                        st.warning("⚠️ Para combinada selecciona al menos 2 picks")
                    else:
                        if es_combinada:
                            cuota_total = 1.0
                            for i in seleccionados:
                                cuota_total *= cantidades_dict.get(i, opciones[i]['cuota'])

                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #2a1a3a 0%, #1a0f25 100%); 
                                        border-radius: 12px; padding: 20px; border: 2px solid #8b5cf6; margin: 15px 0;
                                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 700; font-size: 1.1rem; color: #f8fafc;">🔥 COMBINADA {len(seleccionados)} LEGS</span>
                                    <span style="background: #8b5cf6; padding: 5px 15px; border-radius: 10px; font-weight: 700; color: #ffffff;">@ {cuota_total:.2f}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            for i in seleccionados:
                                opt = opciones[i]
                                st.markdown(f"- **{opt['pick'].get('equipo_local', '?')} vs {opt['pick'].get('equipo_visitante', '?')}** → {opt['tipo']}: {opt.get('prediccion', opt.get('display', '').split(' - ')[-1])} @ {opt['cuota']:.2f}")

                            cantidad = st.number_input(f"💵 Cantidad ({simbolo})", value=25.0, min_value=1.0, step=5.0, key="cant_combinada")
                            ganancia = cantidad * (cuota_total - 1)
                            retorno = cantidad * cuota_total

                            col_g1, col_g2, col_g3 = st.columns(3)
                            with col_g1:
                                st.metric("📈 Ganancia", f"+{format_money(ganancia, simbolo)}")
                            with col_g2:
                                st.metric("💰 Retorno", format_money(retorno, simbolo))
                            with col_g3:
                                st.metric("📊 Cuota", f"@{cuota_total:.2f}")

                            if st.button("🔥 CREAR COMBINADA", type="primary", use_container_width=True):
                                fecha_hoy = str(datetime.now(timezone(timedelta(hours=-5))).date())
                                equipos = " + ".join([f"{opciones[i]['pick'].get('equipo_local', '')} vs {opciones[i]['pick'].get('equipo_visitante', '')}" for i in seleccionados])
                                try:
                                    client.table('bankroll_apuestas').insert({
                                        'usuario': usuario_id,
                                        'fecha': fecha_hoy,
                                        'equipo': f"[COMB] {equipos}",
                                        'cuota': float(cuota_total),
                                        'cantidad': float(cantidad),
                                        'mercado': f"Combinada_{len(seleccionados)}",
                                        'ganancia': 0,
                                        'resultado': None
                                    }).execute()
                                    st.success(f"✅ Combinada creada: {len(seleccionados)} legs @ {cuota_total:.2f}")
                                    st.session_state.pop('apuestas_pendientes_analizador', None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        else:
                            cantidades = {}
                            for i in seleccionados:
                                opt = opciones[i]
                                cols = st.columns([3, 1, 1])
                                with cols[0]:
                                    st.markdown(f"**{opt['pick'].get('equipo_local', '?')} vs {opt['pick'].get('equipo_visitante', '?')}** - {opt['tipo']}")
                                with cols[1]:
                                    cantidades[i] = st.number_input(f"@{opt['cuota']:.2f}", value=25.0, min_value=1.0, step=5.0, key=f"cant_{i}")
                                with cols[2]:
                                    gan = cantidades[i] * (cantidades_dict.get(i, opt['cuota']) - 1)
                                    st.success(f"+{format_money(gan, simbolo)}")

                            total_ap = sum(cantidades.values())
                            st.markdown(f"**Total: {format_money(total_ap, simbolo)}**")

                            if st.button("➕ APOSTAR", type="primary", use_container_width=True):
                                fecha_hoy = str(datetime.now(timezone(timedelta(hours=-5))).date())
                                try:
                                    for i in seleccionados:
                                        opt = opciones[i]
                                        client.table('bankroll_apuestas').insert({
                                            'usuario': usuario_id,
                                            'fecha': fecha_hoy,
                                            'fixture_id': opt['pick'].get('fixture_id', 0),  # Para auto-actualizar
                                            'equipo': f"{opt['pick'].get('equipo_local', '')} vs {opt['pick'].get('equipo_visitante', '')}",
                                            'cuota': float(cantidades_dict.get(i, opt['cuota'])),
                                            'cantidad': float(cantidades[i]),
                                            'mercado': opt['tipo'],
                                            'pick_id': opt['pick'].get('id'),
                                            'ganancia': 0,
                                            'resultado': None
                                        }).execute()
                                    st.success(f"✅ {len(seleccionados)} apuesta(s) creada(s)")
                                    st.session_state.pop('apuestas_pendientes_analizador', None)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                else:
                    st.info("👆 Selecciona los picks")

        with sub_tab3:
            st.markdown("#### 📋 Historial de Apuestas")

            # Botón para limpiar bankroll
            col_clean, col_count = st.columns([1, 3])
            with col_clean:
                if st.button("🗑️ Limpiar Todo", help="Eliminar todas las apuestas guardadas"):
                    try:
                        resp_b = client.table('bankroll_apuestas').select('id', count='exact').eq('usuario', usuario_id).execute()
                        num_b = resp_b.count if hasattr(resp_b, 'count') else len(resp_b.data) if resp_b.data else 0

                        if num_b > 0:
                            client.table('bankroll_apuestas').delete().eq('usuario', usuario_id).execute()
                            st.success(f"✅ Eliminadas: {num_b} apuestas")
                            st.rerun()
                        else:
                            st.info("No hay apuestas para limpiar")
                    except Exception as e:
                        st.error(f"Error: {e}")
            with col_count:
                st.write(f"**Total: {len(apuestas)} apuestas**")

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
                st.write(f"**Mostrando: {len(apuestas_filtradas)} apuestas**")
                st.caption("_💡 Los resultados se actualizan automáticamente al sincronizar partidos_")

                for i, a in enumerate(apuestas_filtradas):
                    estado_icon = "✅" if a.get('resultado') == True else ("❌" if a.get('resultado') == False else "⏳")
                    ganancia = a.get('ganancia', 0)
                    ganancia_fmt = format_money(ganancia, simbolo)
                    cantidad_fmt = format_money(a.get('cantidad', 0), simbolo)

                    # Color según resultado
                    if a.get('resultado') == True:
                        border_color = "#22c55e"
                        bg_color = "rgba(34, 197, 94, 0.1)"
                    elif a.get('resultado') == False:
                        border_color = "#ef4444"
                        bg_color = "rgba(239, 68, 68, 0.1)"
                    else:
                        border_color = "#64748b"
                        bg_color = "rgba(100, 116, 139, 0.1)"

                    st.markdown(f"""
                    <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                                border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #f8fafc; font-weight: 600; font-size: 1rem;">
                                {estado_icon} {a.get('equipo', 'N/A')}
                            </span>
                            <span style="color: {'#4ade80' if ganancia > 0 else '#f87171' if ganancia < 0 else '#94a3b8'}; 
                                        font-weight: 700; font-size: 1.1rem;">
                                {'+' if ganancia > 0 else ''}{ganancia_fmt}
                            </span>
                        </div>
                        <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px;">
                            📅 {a.get('fecha', 'N/A')} | 🏆 {cantidad_fmt} @ {a.get('cuota', 'N/A')} | 📋 {a.get('mercado', 'N/A')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No tienes apuestas registradas")

    # ========== SUBTAB 4: CONFIGURACIÓN ==========
    with sub_tab4:
        st.markdown("### ⚙️ Configuración")

        # Cargar datos actuales
        try:
            resp_stats = client.table('user_stats').select('*').eq('usuario', usuario_id).execute()
            if resp_stats.data:
                stats_data = resp_stats.data[0]
                bankroll_actual_db = stats_data.get('bankroll_inicial', 1000.0)
            else:
                bankroll_actual_db = 1000.0
        except Exception as e:
            bankroll_actual_db = 1000.0

        # TODO en una sola línea compacta
        col1, col2, col3, col4 = st.columns([2.5, 1, 1, 1])

        with col1:
            st.markdown("""
            <style>
            /* Selector de moneda mas grande (Streamlit 1.61 usa react-aria, no baseweb).
               Se apunta por aria-label del input para afectar SOLO a este selectbox.
               Hay que tocar el contenedor y el ComboBox, no solo el input, para que crezca. */
            div[data-testid="stSelectbox"]:has(input[aria-label="💰 Moneda"]) > div {
                min-height: 4.5rem !important;
            }
            div[data-testid="stSelectbox"]:has(input[aria-label="💰 Moneda"]) .react-aria-ComboBox {
                min-height: 4.5rem !important;
            }
            div[data-testid="stSelectbox"]:has(input[aria-label="💰 Moneda"]) .react-aria-ComboBox [role="combobox"] {
                font-size: 1.6rem !important;
                min-height: 4rem !important;
                padding: 0.8rem 1rem !important;
                line-height: 1.6rem !important;
            }
            div[data-testid="stSelectbox"]:has(input[aria-label="💰 Moneda"]) .react-aria-ComboBox button[aria-label="Open"] {
                min-height: 4rem !important;
                height: 4rem !important;
                width: 3rem !important;
            }
            div[data-testid="stSelectbox"]:has(input[aria-label="💰 Moneda"]) [data-testid="stWidgetLabel"] p {
                font-size: 1.05rem !important;
                font-weight: 700 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            moneda_select = st.selectbox(
                "💰 Moneda",
                options=list(MONEDAS.keys()),
                format_func=lambda x: f"{MONEDAS[x]['simbolo']} {MONEDAS[x]['nombre']} ({x})",
                index=0,
                key="moneda_config"
            )
            simbolo = MONEDAS[moneda_select]["simbolo"]

        with col2:
            nuevo_bankroll = st.number_input(
                "📊 Inicial", 
                value=float(bankroll_actual_db), 
                min_value=100.0, 
                step=100.0,
                key="nuevo_bankroll_input"
            )

        with col3:
            monto_retiro = st.number_input(
                "💸 Retiro", 
                min_value=0.0, 
                step=10.0,
                key="monto_retiro_input"
            )

        with col4:
            st.markdown("&nbsp;")
            if st.button("💾 Guardar", type="primary", use_container_width=True):
                try:
                    # Siempre guardar bankroll inicial
                    client.table('user_stats').upsert({
                        'usuario': usuario_id,
                        'bankroll_inicial': float(nuevo_bankroll),
                    }, on_conflict='usuario').execute()

                    # Si hay retiro, registrarlo
                    if monto_retiro > 0:
                        fecha_hoy = str(datetime.now(timezone(timedelta(hours=-5))).date())
                        client.table('bankroll_retiros').insert({
                            'usuario': usuario_id,
                            'fecha': fecha_hoy,
                            'cantidad': float(monto_retiro),
                            'nota': 'Retiro'
                        }).execute()
                        resp_upd = client.table('user_stats').select('total_retirado').eq('usuario', usuario_id).execute()
                        if resp_upd.data:
                            total_actual = resp_upd.data[0].get('total_retirado', 0) or 0
                            client.table('user_stats').update({
                                'total_retirado': float(total_actual) + float(monto_retiro)
                            }).eq('usuario', usuario_id).execute()
                        st.success(f"✅ Guardado + Retiro: {format_money(monto_retiro, simbolo)}")
                    else:
                        st.success(f"✅ Bankroll guardado")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        st.markdown("---")

        # Historial de retiros
        st.markdown("**📜 Retiros**")

        try:
            resp_hist = client.table('bankroll_retiros').select('*').eq('usuario', usuario_id).order('fecha', desc=True).execute()
            retiros_list = resp_hist.data if resp_hist.data else []
        except Exception as e:
            retiros_list = []

        if retiros_list:
            total_retiros = sum(r.get('cantidad', 0) for r in retiros_list)
            st.caption(f"Total: **{format_money(total_retiros, simbolo)}** | {len(retiros_list)} retiros")

            # Mostrar en tabla compacta
            datos_retiros = []
            for r in retiros_list[:10]:  # Solo últimos 10
                datos_retiros.append({
                    "Fecha": str(r.get('fecha', ''))[:10],
                    "Cantidad": format_money(r.get('cantidad', 0), simbolo),
                    "Nota": r.get('nota', '')[:20]
                })
            st.dataframe(pd.DataFrame(datos_retiros), hide_index=True, use_container_width=True)
        else:
            st.caption("Sin retiros aún")

    # ========== TAB 4: VALUE BETS ==========
    with tab_value:
        render_vip_value_bets(client, usuario_id)

    # ========== TAB 5: ALERTAS ==========
    with tab_alertas:
        render_vip_alertas(client, usuario_id)

    # ========== TAB 6: RANKING ==========
    with tab_ranking:
        render_vip_ranking(client, usuario_id, picks)

    # ========== TAB 7: EXPORTAR ==========
    with tab_export:
        render_vip_export(client, usuario_id, picks)

        # Mostrar Consensus Meter
    st.markdown("---")
    st.markdown("### 🎲 Consensus de Modelos")
    st.markdown("_¿Cuántos modelos están de acuerdo en el último pick?_" )

    # Obtener resultado del análisis actual
    r = st.session_state.get('analysis_result', {})
    modelos_data = r.get('modelos', {})

    if modelos_data:
        # Extraer p1 de cada modelo
        poisson_p1 = modelos_data.get('poisson', {}).get('p1', 0)
        dixon_p1 = modelos_data.get('dixon_coles', {}).get('p1', 0)
        montecarlo_p1 = modelos_data.get('monte_carlo', {}).get('p1', 0)
        forma_p1 = modelos_data.get('forma', {}).get('p1', 0)

        # Nombres y valores
        modelos_info = [
            ("Poisson", poisson_p1),
            ("Dixon-Coles", dixon_p1),
            ("Monte Carlo", montecarlo_p1),
            ("Forma", forma_p1),
        ]

        # Mostrar tabla con cada modelo
        col_modelos = st.columns(4)
        p1_values = []
        for i, (nombre, p1) in enumerate(modelos_info):
            with col_modelos[i]:
                st.metric(f"📊 {nombre}", f"{p1:.1f}%")
            p1_values.append(p1)

        # Calcular discrepancia
        promedio = sum(p1_values) / len(p1_values)
        discrepancia = max(p1_values) - min(p1_values)

        # Mostrar resumen
        st.markdown(f"""
        <div style="background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin: 10px 0;">
            <span style="color: #cbd5e1; font-weight: 600;">Promedio:</span> 
            <span style="color: #f8fafc; font-weight: 700;">{promedio:.1f}%</span> | 
            <span style="color: #cbd5e1; font-weight: 600;">Rango:</span> 
            <span style="color: #f8fafc; font-weight: 700;">{discrepancia:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

        if discrepancia < 8:
            st.success("📌 **ALTO CONSENSO** - Los modelos están muy alineados")
        elif discrepancia < 15:
            st.info("📥 **CONSENSO MODERADO** - Buena señal")
        else:
            st.warning("🙏 **BAJO CONSENSO** - Los modelos discrepan, mayor riesgo")
    else:
        st.info("No hay datos de modelos disponibles (analiza un partido primero)")

# ═══════════════════════════════════════════════════════════════════════════════
# EJECUTAR EL SISTEMA DE LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
render_login_form()
