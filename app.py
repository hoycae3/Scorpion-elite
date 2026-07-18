import streamlit as st
import os

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Scorpion Elite",
    page_icon="🦂",
    layout="wide"
)

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ══════════════════════════════════════════════════════════
# INICIALIZAR SESIÓN
# ══════════════════════════════════════════════════════════
if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False
if "page" not in st.session_state:
    st.session_state.page = "Inicio"

# ══════════════════════════════════════════════════════════
# FUNCIONES DE SUPABASE
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def obtener_partidos(fecha=None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        if fecha:
            response = supabase.table("partidos").select("*").eq("fecha", str(fecha)).execute()
        else:
            response = supabase.table("partidos").select("*").execute()
        
        return response.data if response.data else []
    except Exception as e:
        return []

def formatear_partido(p):
    """Formatea un partido para mostrar"""
    return {
        "Hora": p.get("hora_local", "00:00"),
        "Liga": p.get("liga", "N/A"),
        "Local": p.get("equipo_home", "N/A"),
        "Visitante": p.get("equipo_away", "N/A"),
        "Pick": p.get("pick", "-"),
        "Cuota": p.get("cuota_pick", "-"),
        "Confianza": f"{p.get('confianza', 0)}%"
    }

# ══════════════════════════════════════════════════════════
# ESTILOS CSS
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Fondo oscuro */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%);
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #ffd700 !important;
        font-family: 'Arial Black', sans-serif;
    }
    
    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-radius: 15px;
        padding: 25px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    
    /* Feature icons */
    .feature-icon {
        font-size: 50px;
        margin-bottom: 15px;
    }
    
    /* Stats */
    .stat-number {
        font-size: 48px;
        font-weight: bold;
        color: #ffd700;
    }
    
    .stat-label {
        color: #aaa;
        font-size: 14px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# HEADER CON TÍTULO Y LOGIN
# ══════════════════════════════════════════════════════════
col_header_left, col_header_right = st.columns([3, 1])

with col_header_left:
    st.markdown("<h1 style='font-size: 24px; margin: 0;'>🦂 SCORPION ELITE</h1>", unsafe_allow_html=True)

with col_header_right:
    if st.session_state.admin_logged:
        if st.button("🔒 Cerrar Sesión", use_container_width=True):
            st.session_state.admin_logged = False
            st.session_state.page = "Inicio"
            st.rerun()
    else:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.page = "Login"
            st.rerun()

# ══════════════════════════════════════════════════════════
# NAVEGACIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════
st.markdown("<hr style='border-color: rgba(255,215,0,0.3); margin: 5px 0;'>", unsafe_allow_html=True)

# Menú según estado de login
selection = "🏠"
if st.session_state.admin_logged:
    menu_options = ["🏠", "📊 Predicciones", "📈 Estadísticas", "⚙️ Configuración"]
    selection = st.radio("", menu_options, horizontal=True, label_visibility="collapsed")
else:
    st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# PÁGINA: LOGIN
# ══════════════════════════════════════════════════════════
if st.session_state.page == "Login":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("<h2 style='text-align: center;'>🔐 Login</h2>", unsafe_allow_html=True)
        
        password = st.text_input("Contraseña", type="password")
        
        col_1, col_2, col_3 = st.columns([1, 1, 1])
        with col_2:
            if st.button("🔓 Ingresar", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_logged = True
                    st.session_state.page = "Inicio"
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
        
        if st.button("← Volver al Inicio"):
            st.session_state.page = "Inicio"
            st.rerun()

# ══════════════════════════════════════════════════════════
# PÁGINA: INICIO
# ══════════════════════════════════════════════════════════
elif selection == "🏠":
    st.markdown("<h2>📅 Partidos</h2>", unsafe_allow_html=True)
    
    # Debug info
    st.write(f"URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ Sin URL")
    st.write(f"KEY: {'✅ Configurada' if SUPABASE_KEY else '❌ Sin KEY'}")
    
    # Obtener partidos
    partidos = obtener_partidos()
    
    if partidos:
        st.success(f"✅ {len(partidos)} partidos encontrados")
        
        # Mostrar partidos en tabla
        datos_partidos = [formatear_partido(p) for p in partidos]
        st.dataframe(datos_partidos, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No hay partidos - Revisa las secrets")

# ══════════════════════════════════════════════════════════
# PÁGINA: PREDICCIONES
# ══════════════════════════════════════════════════════════
elif selection == "📊 Predicciones":
    st.markdown("<h2>📊 Predicciones de Partidos</h2>", unsafe_allow_html=True)
    
    # Selector de fecha
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fecha = st.date_input("Selecciona la fecha", value=None)
    
    with col2:
        liga = st.selectbox("Liga", ["Todas", "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Placeholder para predicciones
    st.info("👆 Selecciona una fecha para ver las predicciones")
    
    st.markdown("""
    <div class="card" style='text-align: center; padding: 50px;'>
        <h3 style='color: #ffd700;'>🔮 Área de Predicciones</h3>
        <p style='color: #aaa;'>Los partidos aparecerán aquí cuando se seleccione una fecha.</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# PÁGINA: ESTADÍSTICAS
# ══════════════════════════════════════════════════════════
elif selection == "📈 Estadísticas":
    st.markdown("<h2>📈 Estadísticas y Análisis</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3 style='color: #ffd700;'>📊 Modelos de Análisis</h3>
        <br>
        <h4>🎯 Modelo Poisson</h4>
        <p style='color: #ccc;'>Distribución de probabilidad de goles basados en promedio histórico de equipos.</p>
        
        <h4>📉 Dixon-Coles</h4>
        <p style='color: #ccc;'>Modelo especial para marcadores correctos, considera el factor de agresividad.</p>
        
        <h4>🎲 Monte Carlo</h4>
        <p style='color: #ccc;'>Simulación de miles de escenarios para calcular probabilidades precisas.</p>
        
        <h4>⚡ Sistema Elo</h4>
        <p style='color: #ccc;'>Clasificación dinámica basada en rendimiento actual de los equipos.</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# PÁGINA: CONFIGURACIÓN
# ══════════════════════════════════════════════════════════
elif selection == "⚙️ Configuración":
    st.markdown("<h2>⚙️ Configuración</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3 style='color: #ffd700;'>🔑 API Keys</h3>
        <p style='color: #ccc;'>Configura tus claves de API en Streamlit Cloud (secrets).</p>
        <ul style='color: #ccc;'>
            <li><strong>API_FOOTBALL_KEY</strong> - Key de API-Football</li>
            <li><strong>ADMIN_PASSWORD</strong> - Contraseña de administrador</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h3 style='color: #ffd700;'>📋 Información</h3>
        <p style='color: #ccc;'><strong>Versión:</strong> V4 Pro</p>
        <p style='color: #ccc;'><strong>Última actualización:</strong> Julio 2026</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════
st.markdown("<br><br><hr style='border-color: rgba(255,215,0,0.3);'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>🦂 Scorpion Elite © 2026</p>", unsafe_allow_html=True)
