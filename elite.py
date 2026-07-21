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
    # Sidebar con navegación
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { background: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("## 🦂 Menú")
        st.markdown(f"**Usuario:** {st.session_state.user_data.get('nombre', 'Admin') if st.session_state.user_data else 'Admin'}")
        st.markdown(f"**Plan:** {st.session_state.user_data.get('plan', 'admin') if st.session_state.user_data else 'admin'}")
        st.markdown("---")
        
        if st.button("📂 Carga", use_container_width=True, type="secondary" if st.session_state.page != "Carga" else "primary"):
            st.session_state.page = "Carga"
            st.rerun()
        
        if st.button("📊 Analizador", use_container_width=True, type="secondary" if st.session_state.page != "Analizador" else "primary"):
            st.session_state.page = "Analizador"
            st.rerun()
        
        if st.button("📈 Estadísticas", use_container_width=True, type="secondary" if st.session_state.page != "Estadisticas" else "primary"):
            st.session_state.page = "Estadisticas"
            st.rerun()
        
        if st.button("🔑 Claves", use_container_width=True, type="secondary" if st.session_state.page != "Claves" else "primary"):
            st.session_state.page = "Claves"
            st.rerun()
        
        st.markdown("---")
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged = False
            st.session_state.user_data = None
            st.session_state.is_admin = False
            st.rerun()
    
    # Página: Carga
    if st.session_state.page == "Carga":
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
        
        # Sección de carga
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
        st.markdown('<h1 class="title">📊 Analizador</h1>', unsafe_allow_html=True)
        
        # Obtener lista de equipos disponibles
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            response_equipos = client.table('equipos_stats').select('equipo, liga').execute()
            equipos_disponibles = [e['equipo'].title() for e in response_equipos.data] if response_equipos.data else []
            equipos_disponibles = sorted(set(equipos_disponibles))
        except:
            equipos_disponibles = []
        
        # Mostrar equipos disponibles
        if equipos_disponibles:
            st.markdown("### 📋 Equipos Disponibles")
            st.info(f"Tienes **{len(equipos_disponibles)}** equipos guardados: {', '.join(equipos_disponibles[:10])}{'...' if len(equipos_disponibles) > 10 else ''}")
        else:
            st.warning("⚠️ No hay equipos guardados. Ve a 'Estadísticas' para agregar equipos.")
        
        # Selector de equipos
        st.markdown("### 🔍 Seleccionar Partido")
        
        # Opción para escribir manualmente o seleccionar
        modo_entrada = st.radio("¿Cómo quieres elegir los equipos?", ["📋 Seleccionar de lista", "✏️ Escribir manualmente"], horizontal=True)
        
        if modo_entrada == "📋 Seleccionar de lista" and equipos_disponibles:
            col1, col2 = st.columns(2)
            with col1:
                home_team = st.selectbox("🏠 Equipo Local", [""] + equipos_disponibles, key="home_select")
            with col2:
                away_team = st.selectbox("✈️ Equipo Visitante", [""] + equipos_disponibles, key="away_select")
        else:
            col1, col2 = st.columns(2)
            with col1:
                home_team = st.text_input("🏠 Equipo Local", placeholder="Escribe el nombre...")
            with col2:
                away_team = st.text_input("✈️ Equipo Visitante", placeholder="Escribe el nombre...")
        
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
                        
                        # GUARDAR AUTOMÁTICAMENTE EN HISTORIAL (opcional)
                        try:
                            client = create_client(SUPABASE_URL, SUPABASE_KEY)
                            modelos = result.get('modelos', {})
                            
                            historial_data = {
                                'fecha': str(date.today()),
                                'liga': stats_local.get('liga', 'Desconocida'),
                                'equipo_local': home_team,
                                'equipo_visitante': away_team,
                                'prediccion_final': result.get('pick_1x2', ''),
                                'probabilidad_final': float(result.get('prob_1x2', 0)),
                                'confianza': int(result.get('confianza', 0)),
                                'rango': result.get('rango', 'D'),
                                'forma_local_pct': float(result.get('forma_local', {}).get('forma_puntos', 0)),
                                'forma_visitante_pct': float(result.get('forma_visitante', {}).get('forma_puntos', 0)),
                            }
                            client.table('historial_predicciones').insert(historial_data).execute()
                        except Exception as e:
                            pass  # No mostrar error, el análisis principal funciona
                            
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
            # RECUADRO PRINCIPAL
            # ========================
            pick = r.get('pick_1x2', 'X')
            confianza = r.get('confianza', 0)
            rango = r.get('rango', 'D')
            
            pick_icon = {"1": "🏠", "X": "🤝", "2": "✈️"}
            rango_color = {"A+": "🟢", "A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
            
            # Pick principal
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                        padding: 20px; border-radius: 15px; text-align: center; margin: 10px 0;">
                <h2 style="color: white; margin: 0;">⚽ {home} vs {away}</h2>
                <h1 style="color: #00d4ff; margin: 15px 0 5px 0;">
                    {pick_icon.get(pick, '🎯')} {pick}
                </h1>
                <p style="color: #aaa; margin: 0;">
                    {rango_color.get(rango, '⚪')} Confianza: {confianza}% ({rango})
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # ========================
            # PROBABILIDADES 1X2
            # ========================
            st.markdown("### 🎯 Probabilidades (1X2)")
            
            p1 = r.get('p1', 0)
            px = r.get('px', 0)
            p2 = r.get('p2', 0)
            
            col1, col2, col3 = st.columns([1.5, 1, 1.5])
            with col1:
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 15px; border-radius: 10px; text-align: center; 
                            border: 2px solid {'#00ff88' if p1 > px and p1 > p2 else '#333'};">
                    <h3 style="color: #00ff88; margin: 0;">🏠 {home}</h3>
                    <h1 style="color: white; margin: 10px 0;">{p1:.1f}%</h1>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 15px; border-radius: 10px; text-align: center;
                            border: 2px solid {'#ffd700' if px > p1 and px > p2 else '#333'};">
                    <h3 style="color: #ffd700; margin: 0;">🤝 Empate</h3>
                    <h1 style="color: white; margin: 10px 0;">{px:.1f}%</h1>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 15px; border-radius: 10px; text-align: center;
                            border: 2px solid {'#ff6b6b' if p2 > p1 and p2 > px else '#333'};">
                    <h3 style="color: #ff6b6b; margin: 0;">✈️ {away}</h3>
                    <h1 style="color: white; margin: 10px 0;">{p2:.1f}%</h1>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # PREDICCIONES ADICIONALES
            # ========================
            st.markdown("### 📊 Predicciones Adicionales")
            
            col_ou, col_btts, col_corners = st.columns(3)
            
            with col_ou:
                pick_ou = r.get('pick_over_under', 'Over 2.5')
                prob_ou = r.get('prob_over_under', 50)
                ou_icon = "📈" if "Over" in pick_ou else "📉"
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 12px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0;">Over/Under 2.5</p>
                    <h2 style="color: #ff9f43; margin: 5px 0;">{ou_icon} {pick_ou}</h2>
                    <p style="color: #fff; margin: 0;">{prob_ou:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btts:
                pick_btts = r.get('pick_btts', 'No')
                btts_yes = r.get('btts_yes', 50)
                btts_icon = "✅" if pick_btts == "Sí" else "❌"
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 12px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0;">Ambos Marcan</p>
                    <h2 style="color: #a55eea; margin: 5px 0;">{btts_icon} {pick_btts}</h2>
                    <p style="color: #fff; margin: 0;">{btts_yes:.0f}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_corners:
                corners = r.get('corners', {})
                total_c = corners.get('total_estimado', 10)
                pick_c = r.get('pick_corners', 'Over 10')
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 12px; border-radius: 10px; text-align: center;">
                    <p style="color: #888; margin: 0;">Córners Totales</p>
                    <h2 style="color: #00d2d3; margin: 5px 0;">⚽ ~{total_c:.0f}</h2>
                    <p style="color: #fff; margin: 0;">{pick_c}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # FORMA RECIENTE
            # ========================
            st.markdown("### 📅 Forma Reciente (Últimos 5)")
            
            forma_l = r.get('forma_local', {})
            forma_v = r.get('forma_visitante', {})
            
            col_forma_local, col_forma_away = st.columns(2)
            
            with col_forma_local:
                letras = forma_l.get('forma_letras', '-----')
                puntos = forma_l.get('forma_puntos', 0)
                gf = forma_l.get('goles_favor_5', 0)
                gc = forma_l.get('goles_contra_5', 0)
                
                # Colores para cada resultado
                emoji_forma = {"L": "🟢", "E": "🟡", "V": "🔴"}
                forma_html = "".join([f"<span style='color: {'#00ff88' if c=='L' else '#ffd700' if c=='E' else '#ff6b6b'}'>{c}</span>" for c in letras])
                
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 15px; border-radius: 10px;">
                    <h4 style="color: #00ff88; margin: 0 0 10px 0;">🏠 {home}</h4>
                    <p style="color: #fff; font-size: 24px; margin: 0;">{forma_html}</p>
                    <p style="color: #888; margin: 5px 0;">Puntos: <span style="color: #fff;">{puntos:.0f}%</span></p>
                    <p style="color: #888; margin: 5px 0;">Goles: <span style="color: #fff;">{gf}f / {gc}c</span></p>
                </div>
                """, unsafe_allow_html=True)
            
            with col_forma_away:
                letras_v = forma_v.get('forma_letras', '-----')
                puntos_v = forma_v.get('forma_puntos', 0)
                gf_v = forma_v.get('goles_favor_5', 0)
                gc_v = forma_v.get('goles_contra_5', 0)
                
                forma_html_v = "".join([f"<span style='color: {'#00ff88' if c=='L' else '#ffd700' if c=='E' else '#ff6b6b'}'>{c}</span>" for c in letras_v])
                
                st.markdown(f"""
                <div style="background: #0d1b2a; padding: 15px; border-radius: 10px;">
                    <h4 style="color: #ff6b6b; margin: 0 0 10px 0;">✈️ {away}</h4>
                    <p style="color: #fff; font-size: 24px; margin: 0;">{forma_html_v}</p>
                    <p style="color: #888; margin: 5px 0;">Puntos: <span style="color: #fff;">{puntos_v:.0f}%</span></p>
                    <p style="color: #888; margin: 5px 0;">Goles: <span style="color: #fff;">{gf_v}f / {gc_v}c</span></p>
                </div>
                """, unsafe_allow_html=True)
            
            # ========================
            # ESTADÍSTICAS DE EQUIPOS
            # ========================
            stats_local = st.session_state.get('stats_local', {})
            stats_visitante = st.session_state.get('stats_visitante', {})
            
            if stats_local and stats_visitante:
                st.markdown("### 📈 Estadísticas del Robot")
                
                col_est1, col_est2 = st.columns(2)
                
                with col_est1:
                    st.markdown(f"""
                    <div style="background: #0d1b2a; padding: 15px; border-radius: 10px;">
                        <h4 style="color: #00ff88; margin: 0 0 10px 0;">🏠 {home}</h4>
                        <p style="color: #888; margin: 3px 0;">λ Local: <span style="color: #fff;">{stats_local.get('lambda_local', 0):.2f}</span></p>
                        <p style="color: #888; margin: 3px 0;">Partidos: <span style="color: #fff;">{stats_local.get('partidos_jugados', 0)}</span></p>
                        <p style="color: #888; margin: 3px 0;">Córners: <span style="color: #fff;">{stats_local.get('promedio_corners_total', 0):.1f}/part</span></p>
                        <p style="color: #888; margin: 3px 0;">Tarjetas: <span style="color: #fff;">{stats_local.get('promedio_amarillas', 0):.1f}/part</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_est2:
                    st.markdown(f"""
                    <div style="background: #0d1b2a; padding: 15px; border-radius: 10px;">
                        <h4 style="color: #ff6b6b; margin: 0 0 10px 0;">✈️ {away}</h4>
                        <p style="color: #888; margin: 3px 0;">λ Visitante: <span style="color: #fff;">{stats_visitante.get('lambda_visitante', 0):.2f}</span></p>
                        <p style="color: #888; margin: 3px 0;">Partidos: <span style="color: #fff;">{stats_visitante.get('partidos_jugados', 0)}</span></p>
                        <p style="color: #888; margin: 3px 0;">Córners: <span style="color: #fff;">{stats_visitante.get('promedio_corners_total', 0):.1f}/part</span></p>
                        <p style="color: #888; margin: 3px 0;">Tarjetas: <span style="color: #fff;">{stats_visitante.get('promedio_amarillas', 0):.1f}/part</span></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Página: Estadísticas
    elif st.session_state.page == "Estadisticas":
        st.markdown('<h1 class="title">📈 Estadísticas</h1>', unsafe_allow_html=True)
        
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
                        if equipos_a_guardar:
                            st.info("💾 Guardando estadísticas en Supabase...")
                            guardados = 0
                            errores = 0
                            for r in equipos_a_guardar:
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
            
            st.markdown("**📅 Últimos 5 Partidos (Opcional - Formato: L/E/V)**")
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                u1 = st.selectbox("Partido 1", ["", "L", "E", "V"], index=0, key="u1")
                u2 = st.selectbox("Partido 2", ["", "L", "E", "V"], index=0, key="u2")
            with col_u2:
                u3 = st.selectbox("Partido 3", ["", "L", "E", "V"], index=0, key="u3")
                u4 = st.selectbox("Partido 4", ["", "L", "E", "V"], index=0, key="u4")
            with col_u3:
                u5 = st.selectbox("Partido 5", ["", "L", "E", "V"], index=0, key="u5")
            
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
        st.markdown('<h1 class="title">🔑 Gestión de Claves</h1>', unsafe_allow_html=True)
        
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
