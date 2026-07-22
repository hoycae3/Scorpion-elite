import streamlit as st
import pandas as pd
import os
import sqlite3
import hashlib
import logging
from datetime import date, timedelta

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
# CONFIGURACION
# ══════════════════════════════════════════════════════════
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jjtifureeygvygxtpuku.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA")
DB_PATH = "/tmp/scorpion_users.db"

# ══════════════════════════════════════════════════════════
# SISTEMA DE USUARIOS (SQLite local)
# ══════════════════════════════════════════════════════════
def get_hoy():
    return str(date.today())

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    c = get_conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password TEXT UNIQUE NOT NULL,
        nombre TEXT,
        plan TEXT DEFAULT 'gratis',
        fecha_inicio TEXT,
        dias INTEGER DEFAULT 36500,
        activo INTEGER DEFAULT 1,
        es_admin INTEGER DEFAULT 0,
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, liga TEXT, local TEXT, visitante TEXT, hora TEXT,
        mercado TEXT, detalle TEXT, cuota REAL, edge REAL,
        confianza REAL, rango TEXT, notas TEXT, plan_min TEXT DEFAULT 'gratis'
    );
    """)
    # Crear admin si no existe
    h = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (password,nombre,plan,fecha_inicio,dias,activo,es_admin) VALUES (?,?,?,?,?,?,?)",
              (h,"Administrador","admin",get_hoy(),36500,1,1))
    c.commit(); c.close()

def db_get_by_password(pwd_hash):
    try:
        c = get_conn()
        c.row_factory = sqlite3.Row
        # Verificar que la tabla existe
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not c.fetchone():
            return None
        r = c.execute("SELECT * FROM usuarios WHERE password=?", (pwd_hash,)).fetchone()
        c.close()
        return dict(r) if r else None
    except Exception as e:
        return None

def db_get_by_id(user_id):
    try:
        c = get_conn()
        c.row_factory = sqlite3.Row
        r = c.execute("SELECT * FROM usuarios WHERE id=?", (user_id,)).fetchone()
        c.close()
        return dict(r) if r else None
    except Exception as e:
        return None

def db_todos():
    c = get_conn()
    r = c.execute("SELECT * FROM usuarios ORDER BY id ASC").fetchall()
    c.close()
    return [dict(x) for x in r]

def db_crear_usuario(password, nombre, plan, dias):
    """Crea un nuevo usuario con password"""
    c = get_conn()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("""INSERT INTO usuarios (password, nombre, plan, fecha_inicio, dias, activo)
                      VALUES (?, ?, ?, ?, ?, 1)""",
                  (pwd_hash, nombre, plan, get_hoy(), dias))
        c.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    c.close()
    return success

def db_eliminar_usuario(user_id):
    """Elimina un usuario por ID"""
    c = get_conn()
    c.execute("DELETE FROM usuarios WHERE id=? AND es_admin=0", (user_id,))
    c.commit()
    affected = c.total_changes
    c.close()
    return affected > 0

def db_actualizar_plan(user_id, plan, dias):
    c = get_conn()
    c.execute("UPDATE usuarios SET plan=?, dias=?, fecha_inicio=? WHERE id=?", 
               (plan, dias, get_hoy(), user_id))
    c.commit(); c.close()

def db_login(password):
    """Verifica password y retorna usuario"""
    # Asegurar que la DB existe
    init_db()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    result = db_get_by_password(pwd_hash)
    if result:
        return result
    # Fallback: crear admin si no existe
    if password == ADMIN_PASSWORD:
        h = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
        c = get_conn()
        c.execute("INSERT OR IGNORE INTO usuarios (password,nombre,plan,fecha_inicio,dias,activo,es_admin) VALUES (?,?,?,?,?,?,?)",
                  (h,"Administrador","admin",get_hoy(),36500,1,1))
        c.commit()
        c.close()
        return db_get_by_password(pwd_hash)
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

# CSS
st.markdown("""
<style>
.stApp { background: #0a0a0a; }
.title { color: #ffd700; font-size: 48px; font-weight: bold; margin: 0; line-height: 48px; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 3px 0; border-bottom: 2px solid #333; }
.stDataFrame { background: #1a1a1a; }
.section-title { margin-top: 5px; margin-bottom: 0; }
div.block-container { padding-top: 1rem; }
div[data-testid="stHorizontalBlock"] { align-items: center; }
</style>
""", unsafe_allow_html=True)

# Login
if not st.session_state.logged:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown("<br>" * 2, unsafe_allow_html=True)
    # Login simple con password
    password = st.text_input("Password", type="password", placeholder="Ingresa la clave de acceso")
    
    if st.button("Entrar", use_container_width=True):
        if not password.strip():
            st.error("Ingresa la password")
        else:
            # Debug
            st.write(f"Debug: password={password.strip()}, admin={ADMIN_PASSWORD}")
            if password.strip() == ADMIN_PASSWORD:
                st.session_state.logged = True
                st.session_state.is_admin = True
                st.session_state.user_data = {"nombre": "Admin", "plan": "admin", "es_admin": 1}
                st.rerun()
            else:
                st.error("Password incorrecta")

    
    st.stop()

# Dashboard
else:
    # Sidebar con información del usuario
    with st.sidebar:
        st.markdown("## 🦂 Scorpion Elite")
        st.markdown(f"**Usuario:** {st.session_state.user_data.get('nombre', 'Admin') if st.session_state.user_data else 'Admin'}")
        st.markdown(f"**Plan:** {st.session_state.user_data.get('plan', 'admin') if st.session_state.user_data else 'admin'}")
        st.markdown("---")
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged = False
            st.session_state.user_data = None
            st.session_state.is_admin = False
            st.rerun()
    
    # Menú horizontal arriba
    st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    
    col_menu1, col_menu2, col_menu3, col_menu4, col_menu5 = st.columns(5)
    
    with col_menu1:
        if st.button("📂 Carga", use_container_width=True, type="primary" if st.session_state.page == "Carga" else "secondary"):
            st.session_state.page = "Carga"
            st.rerun()
    
    with col_menu2:
        if st.button("📊 Analizador", use_container_width=True, type="primary" if st.session_state.page == "Analizador" else "secondary"):
            st.session_state.page = "Analizador"
            st.rerun()
    
    with col_menu3:
        if st.button("📈 Estadísticas", use_container_width=True, type="primary" if st.session_state.page == "Estadisticas" else "secondary"):
            st.session_state.page = "Estadisticas"
            st.rerun()
    
    with col_menu4:
        if st.button("📉 Dashboard", use_container_width=True, type="primary" if st.session_state.page == "Dashboard" else "secondary"):
            st.session_state.page = "Dashboard"
            st.rerun()
    
    with col_menu5:
        if st.button("🔑 Claves", use_container_width=True, type="primary" if st.session_state.page == "Claves" else "secondary"):
            st.session_state.page = "Claves"
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
                                    client = create_client(SUPABASE_URL, SUPABASE_KEY)
                                    
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
                            client = create_client(SUPABASE_URL, SUPABASE_KEY)
                            client.table('partidos').delete().neq('id', 0).execute()
                            st.success("✅ Partidos eliminados")
                            st.rerun()
                else:
                    st.warning("No se encontraron partidos en el archivo")
                    
            except Exception as e:
                st.error(f"Error al leer archivo: {str(e)}")
    
    # Página: Analizador
    elif st.session_state.page == "Analizador":
        st.markdown("### 📊 Analizador")
        
        # Obtener lista de equipos disponibles
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            response_equipos = client.table('equipos_stats').select('equipo, liga').execute()
            equipos_disponibles = [e['equipo'].title() for e in response_equipos.data] if response_equipos.data else []
            equipos_disponibles = sorted(set(equipos_disponibles))
        except:
            equipos_disponibles = []
        
        # Mostrar equipos disponibles
        if not equipos_disponibles:
            st.warning("⚠️ No hay equipos guardados. Ve a 'Estadísticas' para agregar equipos.")
        
        # Selector de equipos - CSS para hacerlo compacto
        st.markdown("""
        <style>
        /* Selectbox más pequeños */
        [data-testid="stSelectbox"] [data-baseweb="select"] {
            min-height: 28px !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            min-height: 28px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔍 Seleccionar Partido")
        
        col1, col2 = st.columns(2)
        with col1:
            home_team = st.selectbox("🏠", [""] + equipos_disponibles, key="home_select")
        with col2:
            away_team = st.selectbox("✈️", [""] + equipos_disponibles, key="away_select")
        
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
                client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
                client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
                                'pick': f"Over {remates_total:.0f}" if remates_over_prob > 50 else f"Under {remates_total:.0f}",
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
                
                # Badge de fuente de datos
                col_src1, col_src2, col_src3 = st.columns([1, 1, 2])
                with col_src1:
                    st.markdown(f"**🏦 Fuente Local:** `{source_local}`")
                with col_src2:
                    st.markdown(f"**🏦 Fuente Visitante:** `{source_visitante}`")
                
                # Obtener lambdas ajustadas
                lambda_local_adj = get_lambda_ajustada(home, stats_local.get('lambda_local', 0), como_local=True)
                lambda_visitante_adj = get_lambda_ajustada(away, stats_visitante.get('lambda_visitante', 0), como_local=False)
                
                col_est1, col_est2 = st.columns(2)
                
                with col_est1:
                    icono_ajuste_local = "🔼" if lambda_local_adj['factor'] > 1 else ("🔽" if lambda_local_adj['factor'] < 1 else "➖")
                    color_ajuste_local = "#00ff88" if lambda_local_adj['factor'] > 1 else ("#ff6b6b" if lambda_local_adj['factor'] < 1 else "#00d4ff")
                    
                    # Calcular promedios
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
                    
                    st.markdown(f"""
                    <div class="simple-card simple-card-green" style="padding: 15px;">
                        <h4 style="color: #00ff88; margin: 0 0 12px 0; font-size: 16px;">🏠 {home}</h4>
                        <div style="font-size: 12px; line-height: 1.6;">
                            <p style="margin: 2px 0;">📅 PJ: <span style="color: #fff;">{pj_l}</span> | V: <span style="color: #00ff88;">{vic_l}</span> | E: <span style="color: #ffd700;">{emp_l}</span> | D: <span style="color: #ff6b6b;">{der_l}</span></p>
                            <p style="margin: 2px 0;">⚽ GF: <span style="color: #fff;">{gf_l}</span> | GC: <span style="color: #ff6b6b;">{gc_l}</span> | Diff: <span style="color: #00d4ff;">{gf_l - gc_l:+.0f}</span></p>
                            <hr style="margin: 8px 0; border-color: #333;">
                            <p style="margin: 2px 0;">📊 λ Local: <span style="color: #00d4ff;">{stats_local.get('lambda_local', 0):.2f}</span> → <span style="color: {color_ajuste_local};">{lambda_local_adj['lambda_ajustada']:.2f}</span> {icono_ajuste_local}</p>
                            <p style="margin: 2px 0;">⚡ Factor: <span style="color: {color_ajuste_local};">{lambda_local_adj['factor']:.3f}</span></p>
                            <hr style="margin: 8px 0; border-color: #333;">
                            <p style="margin: 2px 0;">🌽 Córners: <span style="color: #00d2d3;">{prom_corners_l:.1f}</span> avg</p>
                            <p style="margin: 2px 0;">🟨 Amarillas: <span style="color: #ffd700;">{prom_amarillas_l:.1f}</span> avg</p>
                            <p style="margin: 2px 0;">🔫 Tiros: <span style="color: #fff;">{prom_tiros_l:.1f}</span> | Arco: <span style="color: #fff;">{prom_tiros_arco_l:.1f}</span></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_est2:
                    icono_ajuste_vis = "🔼" if lambda_visitante_adj['factor'] > 1 else ("🔽" if lambda_visitante_adj['factor'] < 1 else "➖")
                    color_ajuste_vis = "#00ff88" if lambda_visitante_adj['factor'] > 1 else ("#ff6b6b" if lambda_visitante_adj['factor'] < 1 else "#00d4ff")
                    
                    # Calcular promedios
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
                    
                    st.markdown(f"""
                    <div class="simple-card simple-card-red" style="padding: 15px;">
                        <h4 style="color: #ff6b6b; margin: 0 0 12px 0; font-size: 16px;">✈️ {away}</h4>
                        <div style="font-size: 12px; line-height: 1.6;">
                            <p style="margin: 2px 0;">📅 PJ: <span style="color: #fff;">{pj_v}</span> | V: <span style="color: #00ff88;">{vic_v}</span> | E: <span style="color: #ffd700;">{emp_v}</span> | D: <span style="color: #ff6b6b;">{der_v}</span></p>
                            <p style="margin: 2px 0;">⚽ GF: <span style="color: #fff;">{gf_v}</span> | GC: <span style="color: #ff6b6b;">{gc_v}</span> | Diff: <span style="color: #00d4ff;">{gf_v - gc_v:+.0f}</span></p>
                            <hr style="margin: 8px 0; border-color: #333;">
                            <p style="margin: 2px 0;">📊 λ Visitante: <span style="color: #00d4ff;">{stats_visitante.get('lambda_visitante', 0):.2f}</span> → <span style="color: {color_ajuste_vis};">{lambda_visitante_adj['lambda_ajustada']:.2f}</span> {icono_ajuste_vis}</p>
                            <p style="margin: 2px 0;">⚡ Factor: <span style="color: {color_ajuste_vis};">{lambda_visitante_adj['factor']:.3f}</span></p>
                            <hr style="margin: 8px 0; border-color: #333;">
                            <p style="margin: 2px 0;">🌽 Córners: <span style="color: #00d2d3;">{prom_corners_v:.1f}</span> avg</p>
                            <p style="margin: 2px 0;">🟨 Amarillas: <span style="color: #ffd700;">{prom_amarillas_v:.1f}</span> avg</p>
                            <p style="margin: 2px 0;">🔫 Tiros: <span style="color: #fff;">{prom_tiros_v:.1f}</span> | Arco: <span style="color: #fff;">{prom_tiros_arco_v:.1f}</span></p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
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
            # RECUADRO PRINCIPAL
            # ========================
            pick = r.get('pick_1x2', 'X')
            confianza = r.get('confianza', 0)
            rango = r.get('rango', 'D')
            marcador = r.get('marcador_predicho', f"{r.get('lambda_local', 0):.1f}-{r.get('lambda_visitante', 0):.1f}")
            
            pick_icon = {"1": "🏠", "X": "🤝", "2": "✈️"}
            rango_color = {"A+": "🟢", "A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
            
            st.markdown(f"""
            <div style="background: #1a1a2e; border: 1px solid #00d4ff; border-radius: 8px; padding: 12px 20px; text-align: center; margin: 10px auto; max-width: 500px;">
                <p style="color: #00d4ff; margin: 0; font-size: 10px; font-weight: 600; letter-spacing: 1px;">⚡ ANÁLISIS</p>
                <p style="color: white; margin: 5px 0; font-size: 18px;">⚽ {home} vs {away}</p>
                <p style="color: #00d4ff; margin: 3px 0; font-size: 14px;">Expected Score: {marcador}</p>
                <p style="color: #00d4ff; margin: 8px 0; font-size: 28px; font-weight: bold;">
                    {pick_icon.get(pick, '🎯')} {pick}
                </p>
                <span style="background: rgba(0, 212, 255, 0.1); border: 1px solid #00d4ff; padding: 3px 10px; border-radius: 10px; font-size: 11px;">
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
                            client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
            # PROBABILIDADES 1X2
            # ========================
            st.markdown("##### 🎯 Probabilidades (1X2)")
            
            p1 = r.get('p1', 0)
            px = r.get('px', 0)
            p2 = r.get('p2', 0)
            
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            with col1:
                border = '2px solid #00ff88' if p1 > px and p1 > p2 else '1px solid rgba(255,255,255,0.1)'
                st.markdown(f"""
                <div class="simple-card" style="border: {border}; text-align: center;">
                    <p style="color: #00ff88; margin: 0; font-size: 13px;">🏠 {home}</p>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 28px;">{p1:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                border = '2px solid #ffd700' if px > p1 and px > p2 else '1px solid rgba(255,255,255,0.1)'
                st.markdown(f"""
                <div class="simple-card" style="border: {border}; text-align: center;">
                    <p style="color: #ffd700; margin: 0; font-size: 13px;">🤝 Empate</p>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 28px;">{px:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                border = '2px solid #ff6b6b' if p2 > p1 and p2 > px else '1px solid rgba(255,255,255,0.1)'
                st.markdown(f"""
                <div class="simple-card" style="border: {border}; text-align: center;">
                    <p style="color: #ff6b6b; margin: 0; font-size: 13px;">✈️ {away}</p>
                    <p style="color: white; margin: 10px 0 0 0; font-size: 28px;">{p2:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # PREDICCIONES ADICIONALES
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
            pick_remates = "Over" if remates_over_prob > 50 else "Under"
            
            # Probabilidades para tarjetas
            tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))
            pick_tarjetas = "Over" if tarjetas_over_prob > 50 else "Under"
            
            modelos = r.get('modelos', {})
            mc = modelos.get('monte_carlo', {})
            top_scores = mc.get('top_scores', {})
            score_mas_probable = list(top_scores.keys())[0] if top_scores else "2-1"
            
            col_space, col_ou, col_btts, col_corners, col_remates, col_tarjetas, col_score, col_space2 = st.columns([0.5, 1, 1, 1, 1, 1, 1, 0.5])
            
            with col_ou:
                pick_ou = r.get('pick_over_under', 'Over 2.5')
                prob_ou = r.get('prob_over_under', 50)
                ou_icon = "📈" if "Over" in pick_ou else "📉"
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px; text-align: center; height: 100%;">
                    <p style="color: #888; margin: 0; font-size: 10px;">O/U 2.5</p>
                    <p style="color: #ff9f43; margin: 5px 0; font-size: 14px; font-weight: bold;">{ou_icon} {pick_ou}</p>
                    <p style="color: #fff; margin: 0; font-size: 13px; font-weight: bold;">{prob_ou:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btts:
                pick_btts = r.get('pick_btts', 'No')
                btts_yes = r.get('btts_yes', 50)
                btts_icon = "✅" if pick_btts == "Sí" else "❌"
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px; text-align: center; height: 100%;">
                    <p style="color: #888; margin: 0; font-size: 10px;">Ambos Marcan</p>
                    <p style="color: #a55eea; margin: 5px 0; font-size: 14px; font-weight: bold;">{btts_icon} {pick_btts}</p>
                    <p style="color: #fff; margin: 0; font-size: 13px; font-weight: bold;">{btts_yes:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_corners:
                corners = r.get('corners', {})
                total_c = corners.get('total_estimado', 10)
                pick_corners = r.get('pick_corners', 'Over')
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px; text-align: center; height: 100%;">
                    <p style="color: #888; margin: 0; font-size: 10px;">Córners</p>
                    <p style="color: #00d2d3; margin: 5px 0; font-size: 14px; font-weight: bold;">{total_c:.0f}</p>
                    <p style="color: #fff; margin: 0; font-size: 12px;">{pick_corners}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_remates:
                remates_icon = "📈" if pick_remates == "Over" else "📉"
                remates_color = "#00ff88" if pick_remates == "Over" else "#ff6b6b"
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px; text-align: center; height: 100%;">
                    <p style="color: #888; margin: 0; font-size: 10px;">Remates</p>
                    <p style="color: #00ff88; margin: 5px 0; font-size: 16px; font-weight: bold;">{remates_total:.0f}</p>
                    <p style="color: {remates_color}; margin: 5px 0; font-size: 12px; font-weight: bold;">{remates_icon} {pick_remates}</p>
                    <p style="color: #fff; margin: 0; font-size: 12px;">{remates_over_prob:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_tarjetas:
                tarjetas_icon = "📈" if pick_tarjetas == "Over" else "📉"
                tarjetas_color = "#00ff88" if pick_tarjetas == "Over" else "#ff6b6b"
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 12px; text-align: center; height: 100%;">
                    <p style="color: #888; margin: 0; font-size: 10px;">🟨 Tarjetas</p>
                    <p style="color: #ffd700; margin: 5px 0; font-size: 16px; font-weight: bold;">{tarjetas_total:.1f}</p>
                    <p style="color: {tarjetas_color}; margin: 5px 0; font-size: 12px; font-weight: bold;">{tarjetas_icon} {pick_tarjetas}</p>
                    <p style="color: #fff; margin: 0; font-size: 12px;">{tarjetas_over_prob:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_score:
                st.markdown(f"""
                <div style="background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 15px; text-align: center; height: 100%;">
                    <p style="color: #888; margin: 0; font-size: 11px;">🎯 Marcador</p>
                    <p style="color: #ff6b6b; margin: 8px 0; font-size: 16px; font-weight: bold;">{score_mas_probable}</p>
                    <p style="color: #fff; margin: 0; font-size: 12px;">Probable</p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # FORMA RECIENTE
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
                
                forma_html = "".join([
                    f"<span class='forma-g'>{c}</span> " if c=='G' else (
                    f"<span class='forma-e'>{c}</span> " if c=='E' else (
                    f"<span class='forma-p'>{c}</span> " if c=='P' else c + " "
                    )) for c in letras
                ])
                
                st.markdown(f"""
                <div class="simple-card simple-card-green">
                    <h4 style="color: #00ff88; margin: 0 0 8px 0; font-size: 13px;">🏠 {home}</h4>
                    <p style="margin: 0 0 5px 0; font-size: 14px;">{forma_html}</p>
                    <p style="color: #888; margin: 0; font-size: 11px;">
                        Puntos: <span style="color: #fff;">{puntos:.0f}%</span> | 
                        Goles: <span style="color: #fff;">{gf}f/{gc}c</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_forma_away:
                letras_v = forma_v.get('forma_letras', '-----')
                puntos_v = forma_v.get('forma_puntos', 0)
                gf_v = forma_v.get('goles_favor_5', 0)
                gc_v = forma_v.get('goles_contra_5', 0)
                
                forma_html_v = "".join([
                    f"<span class='forma-g'>{c}</span> " if c=='G' else (
                    f"<span class='forma-e'>{c}</span> " if c=='E' else (
                    f"<span class='forma-p'>{c}</span> " if c=='P' else c + " "
                    )) for c in letras_v
                ])
                
                st.markdown(f"""
                <div class="simple-card simple-card-red">
                    <h4 style="color: #ff6b6b; margin: 0 0 8px 0; font-size: 13px;">✈️ {away}</h4>
                    <p style="margin: 0 0 5px 0; font-size: 14px;">{forma_html_v}</p>
                    <p style="color: #888; margin: 0; font-size: 11px;">
                        Puntos: <span style="color: #fff;">{puntos_v:.0f}%</span> | 
                        Goles: <span style="color: #fff;">{gf_v}f/{gc_v}c</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Página: Estadísticas
    elif st.session_state.page == "Estadisticas":
        st.markdown("### 📈 Estadísticas")
        
        # Sección: Robot automático
        st.markdown("### 🤖 Buscar Todos los Equipos del Excel")
        st.info("Sube tu Excel con partidos → Presiona el botón → El robot busca automáticamente TODOS los equipos en football-data y Soccerway")
        
        if st.button("🔄 Buscar Equipos del Excel", type="primary", use_container_width=True):
            with st.spinner("Buscando equipos..."):
                try:
                    # Obtener equipos de Supabase
                    client = create_client(SUPABASE_URL, SUPABASE_KEY)
                    response = client.table('partidos').select('equipo_local, equipo_visitante').execute()
                    
                    if not response.data:
                        st.warning("⚠️ No hay partidos en Supabase. Sube un Excel primero.")
                    else:
                        # Extraer equipos únicos
                        equipos = set()
                        for p in response.data:
                            if p.get('equipo_local'):
                                equipos.add(p['equipo_local'])
                            if p.get('equipo_visitante'):
                                equipos.add(p['equipo_visitante'])
                        
                        equipos = sorted(list(equipos))
                        st.info(f"📊 {len(equipos)} equipos encontrados: {', '.join(equipos)}")
                        
                        # Buscar todos con el robot
                        with st.spinner("🤖 Buscando en football-data y API-Football..."):
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
                                fuente_nombre = {
                                    'football-data.co.uk': '🌐 football-data',
                                    'api-football.com': '🔷 API-Football'
                                }.get(fuente, fuente)
                                st.markdown(f"- **{r.get('equipo_real', r['equipo'])}** ({r.get('liga', 'N/A')})")
                                st.markdown(f"  `λL={r['lambda_local']} | λV={r['lambda_visitante']} | Partidos={r['partidos_jugados']} | Fuente: {fuente_nombre}`")
                        
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
                                        # Nuevos stats
                                        'promedio_tiros': float(r.get('tiros_promedio', 12)) or 12,
                                        'promedio_tiros_arco': float(r.get('tiros_arco_promedio', 4)) or 4,
                                        'promedio_corners_total': float(r.get('corners_promedio', 10)) or 10,
                                        'promedio_amarillas': float(r.get('tarjetas_promedio', 3)) or 3,
                                        # Fuente de datos
                                        'source': r.get('source', 'football-data.co.uk'),
                                        # Guardar últimos 5 partidos como JSON
                                        'ultimos_5_partidos': r.get('ultimos_5_partidos', []),
                                    }
                                    
                                    # Intentar upsert (actualizar si existe)
                                    try:
                                        client.table('equipos_stats').upsert(data).execute()
                                    except:
                                        # Si falla upsert, intentar insert directo
                                        try:
                                            client.table('equipos_stats').insert(data).execute()
                                        except Exception as insert_error:
                                            # Crear sin los campos nuevos
                                            data_basic = {k: v for k, v in data.items() if k != 'ultimos_5_partidos'}
                                            client.table('equipos_stats').insert(data_basic).execute()
                                    
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
        
        # Formulario para agregar equipo
        with st.form("form_equipo", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                equipo = st.text_input("Nombre del Equipo", placeholder="Ej: Barcelona")
            with col2:
                liga = st.text_input("Liga", placeholder="Ej: La Liga")
            with col3:
                temporada = st.text_input("Temporada", value="2025")
            
            st.markdown("** Estadísticas de Temporada**")
            col_pj, col_vic, col_emp, col_der = st.columns(4)
            with col_pj:
                partidos = st.number_input("Partidos Jugados", min_value=0, value=0)
            with col_vic:
                victorias = st.number_input("Victorias", min_value=0, value=0)
            with col_emp:
                empates = st.number_input("Empates", min_value=0, value=0)
            with col_der:
                derrotas = st.number_input("Derrotas", min_value=0, value=0)
            
            col_gf, col_gc = st.columns(2)
            with col_gf:
                goles_favor = st.number_input("Goles a Favor", min_value=0, value=0)
            with col_gc:
                goles_contra = st.number_input("Goles en Contra", min_value=0, value=0)
            
            st.markdown("**📊 Estadísticas Avanzadas (Opcional)**")
            col_corners, col_tarjetas = st.columns(2)
            with col_corners:
                promedio_corners = st.number_input("Promedio Córners/partido", min_value=0.0, value=10.0, step=0.5, format="%.1f")
            with col_tarjetas:
                promedio_tarjetas = st.number_input("Promedio Tarjetas/partido", min_value=0.0, value=3.0, step=0.5, format="%.1f")
            
            col_tiros, col_tiros_arco = st.columns(2)
            with col_tiros:
                promedio_tiros = st.number_input("Promedio Tiros/partido", min_value=0.0, value=12.0, step=0.5, format="%.1f")
            with col_tiros_arco:
                promedio_tiros_arco = st.number_input("Promedio Tiros al Arco/partido", min_value=0.0, value=4.0, step=0.5, format="%.1f")
            
            st.markdown("**📅 Últimos 5 Partidos (Opcional - G=Ganó, E=Empate, P=Perdió)**")
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                u1 = st.selectbox("Partido 1", ["", "G", "E", "P"], index=0, key="u1")
                u2 = st.selectbox("Partido 2", ["", "G", "E", "P"], index=0, key="u2")
            with col_u2:
                u3 = st.selectbox("Partido 3", ["", "G", "E", "P"], index=0, key="u3")
                u4 = st.selectbox("Partido 4", ["", "G", "E", "P"], index=0, key="u4")
            with col_u3:
                u5 = st.selectbox("Partido 5", ["", "G", "E", "P"], index=0, key="u5")
            
            submitted = st.form_submit_button("💾 Guardar Equipo", use_container_width=True)
            
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
                client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
        
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
                                st.success("✅ Datos actualizados")
                                st.rerun()
                            
                            if deleted:
                                client.table('equipos_stats').delete().eq('id', eq.get('id')).execute()
                                st.success("✅ Equipo eliminado")
                                st.rerun()
            else:
                st.info("📭 No hay equipos guardados. Agrega uno con el formulario de arriba.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:100]}")

    # Página: Gestión de Claves
    elif st.session_state.page == "Claves":
        st.markdown("### 🔑 Gestión de Claves")
        
        # Crear nueva clave
        st.markdown("### ➕ Crear Nueva Clave de Acceso")
        
        with st.form("form_clave", clear_on_submit=True):
            col_nom, col_plan = st.columns(2)
            with col_nom:
                nombre = st.text_input("Nombre / Cliente", placeholder="Ej: Juan, Carlos, Cliente1")
            with col_plan:
                plan = st.selectbox("Plan", ["gratis", "dia", "semana", "mes"])
            
            dias_opciones = {"gratis": 36500, "dia": 1, "semana": 7, "mes": 30}
            dias = dias_opciones.get(plan, 30)
            
            nueva_clave = st.text_input("Nueva Clave", placeholder="Escribe la clave que quieres dar")
            
            if st.form_submit_button("🔑 Crear Clave", use_container_width=True):
                if not nombre.strip():
                    st.error("Ingresa un nombre")
                elif not nueva_clave.strip():
                    st.error("Ingresa una clave")
                else:
                    if db_crear_usuario(nueva_clave.strip(), nombre.strip(), plan, dias):
                        st.success(f"✅ Clave '{nueva_clave}' creada para {nombre}")
                        st.rerun()
                    else:
                        st.error("❌ Esta clave ya existe. Usa otra.")
        
        st.markdown("---")
        st.markdown("### 📋 Claves Existentes")
        
        usuarios = db_todos()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Claves", len(usuarios))
        with col2:
            st.metric("Admins", sum(1 for u in usuarios if u.get('es_admin') == 1))
        
        if usuarios:
            for u in usuarios:
                es_admin = u.get('es_admin') == 1
                plan_icon = {"gratis": "🆓", "dia": "📅", "semana": "📆", "mes": "👑"}.get(u.get('plan', 'gratis'), "❓")
                
                if es_admin:
                    with st.expander(f"⚙️ {u.get('nombre', 'Admin')} - {plan_icon} {u.get('plan', 'admin')} **(Admin)**"):
                        st.info("Esta es la cuenta de administrador principal")
                else:
                    with st.expander(f"👤 {u.get('nombre', 'Sin nombre')} - {plan_icon} {u.get('plan', 'gratis')}"):
                        st.write(f"**Nombre:** {u.get('nombre', '')}")
                        st.write(f"**Plan:** {u.get('plan', 'gratis')}")
                        st.write(f"**Dias:** {u.get('dias', 0)}")
                        st.write(f"**Creado:** {u.get('creado', '')}")
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if st.button(f"👑 Mes", key=f"mes_{u['id']}"):
                                db_actualizar_plan(u['id'], "mes", 30)
                                st.success("Plan actualizado a Mes")
                                st.rerun()
                        with col_b:
                            if st.button(f"📆 Semana", key=f"sem_{u['id']}"):
                                db_actualizar_plan(u['id'], "semana", 7)
                                st.success("Plan actualizado a Semana")
                                st.rerun()
                        with col_c:
                            if st.button(f"🗑️ Eliminar", key=f"del_{u['id']}"):
                                if db_eliminar_usuario(u['id']):
                                    st.success("✅ Eliminado")
                                    st.rerun()
                                else:
                                    st.error("No se pudo eliminar")


    # ==================== PÁGINA: DASHBOARD ====================
    elif st.session_state.page == "Dashboard":
        st.markdown("### 📉 Dashboard de Picks")
        
        # Obtener picks de Supabase
        try:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
                                st.success("✅ Eliminado")
                                st.rerun()
                        
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
