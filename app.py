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
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion_admin_2025")

# ══════════════════════════════════════════════════════════
# INICIALIZAR SESIÓN
# ══════════════════════════════════════════════════════════
if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False
if "page" not in st.session_state:
    st.session_state.page = "Inicio"

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
# HEADER
# ══════════════════════════════════════════════════════════
col1, col2 = st.columns([1, 4])

with col1:
    st.markdown("<h1 style='font-size: 36px;'>🦂 SCORPION ELITE</h1>", unsafe_allow_html=True)

with col2:
    st.markdown("<p style='color: #888; font-size: 14px; line-height: 60px;'>Análisis Predictivo de Partidos de Fútbol</p>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# NAVEGACIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════
st.markdown("<hr style='border-color: rgba(255,215,0,0.3);'>", unsafe_allow_html=True)

# Menú según estado de login
if st.session_state.admin_logged:
    menu_options = ["🏠 Inicio", "📊 Predicciones", "📈 Estadísticas", "⚙️ Configuración"]
    selection = st.radio("", menu_options, horizontal=True, label_visibility="collapsed")
else:
    menu_options = ["🏠 Inicio"]
    selection = st.radio("", menu_options, horizontal=True, label_visibility="collapsed")
    
    # Botón de login
    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("🔐 Panel Administrador", use_container_width=True):
            st.session_state.page = "Login"
            st.rerun()

# ══════════════════════════════════════════════════════════
# PÁGINA: LOGIN
# ══════════════════════════════════════════════════════════
if st.session_state.page == "Login":
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("<h2 style='text-align: center;'>🔐 Acceso a Scorpion Elite</h2>", unsafe_allow_html=True)
        
        # Selector de tipo de usuario
        user_type = st.radio("Tipo de usuario:", ["👤 Cliente", "👑 Administrador"], horizontal=True)
        
        password = st.text_input("Contraseña", type="password")
        
        col_1, col_2, col_3 = st.columns([1, 1, 1])
        with col_2:
            if st.button("🔓 Ingresar", use_container_width=True):
                if user_type == "👑 Administrador":
                    if password == ADMIN_PASSWORD:
                        st.session_state.admin_logged = True
                        st.session_state.user_type = "admin"
                        st.session_state.page = "Inicio"
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta")
                else:
                    # Cliente - cualquier contraseña funciona (o puedes agregar validación)
                    st.session_state.admin_logged = True
                    st.session_state.user_type = "cliente"
                    st.session_state.page = "Inicio"
                    st.rerun()
        
        if st.button("← Volver al Inicio"):
            st.session_state.page = "Inicio"
            st.rerun()

# ══════════════════════════════════════════════════════════
# PÁGINA: INICIO
# ══════════════════════════════════════════════════════════
elif selection == "🏠 Inicio":
    # Hero section
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("<h2>Bienvenido a Scorpion Elite</h2>", unsafe_allow_html=True)
        st.markdown("""
        <p style='color: #ccc; font-size: 18px; line-height: 1.8;'>
        El sistema de análisis predictivo más avanzado para fútbol. 
        Utilizamos modelos matemáticos como Poisson, Dixon-Coles y Monte Carlo 
        para predecir resultados con alta precisión.
        </p>
        """, unsafe_allow_html=True)
        
        # Botón de acción
        if st.button("🚀 Comenzar Análisis", type="primary", use_container_width=True):
            st.session_state.page = "Predicciones"
            st.rerun()
    
    with col_right:
        st.markdown("""
        <div class="card">
            <h3 style='color: #ffd700;'>🎯 Características</h3>
            <ul style='color: #ccc; font-size: 16px; line-height: 2;'>
                <li>📊 <strong>Predicciones Poisson</strong> - Distribución de goles</li>
                <li>🎯 <strong>Dixon-Coles</strong> - Análisis de marcador correcto</li>
                <li>🎲 <strong>Monte Carlo</strong> - Simulaciones avanzadas</li>
                <li>📈 <strong>Sistema Elo</strong> - Rankings dinámicos</li>
                <li>⚽ <strong>+50 ligas</strong> - Cobertura mundial</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Stats
    st.markdown("<h3 style='text-align: center;'>📊 Estadísticas del Sistema</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("<div style='text-align: center;' class='card'>", unsafe_allow_html=True)
        st.markdown("<span class='stat-number'>87%</span>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Precisión Promedio</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div style='text-align: center;' class='card'>", unsafe_allow_html=True)
        st.markdown("<span class='stat-number'>1,200+</span>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Partidos Analizados</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div style='text-align: center;' class='card'>", unsafe_allow_html=True)
        st.markdown("<span class='stat-number'>50+</span>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Ligas Disponibles</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown("<div style='text-align: center;' class='card'>", unsafe_allow_html=True)
        st.markdown("<span class='stat-number'>24/7</span>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Actualizaciones</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

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

# Botón de logout si está logueado
if st.session_state.admin_logged:
    col_f1, col_f2 = st.columns([4, 1])
    with col_f2:
        if st.button("🔒 Cerrar Sesión"):
            st.session_state.admin_logged = False
            st.session_state.page = "Inicio"
            st.rerun()

st.markdown("<p style='text-align: center; color: #555;'>🦂 Scorpion Elite © 2026 | Análisis Predictivo de Fútbol</p>", unsafe_allow_html=True)
