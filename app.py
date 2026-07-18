import streamlit as st
import pandas as pd
import os
from supabase import create_client
from data_loader import parse_flashscore_excel, validate_matches
from analysis_models import calcular

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

# Configuración
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jjtifureeygvygxtpuku.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA")

# Session state
if "logged" not in st.session_state:
    st.session_state.logged = False
if "df_partidos" not in st.session_state:
    st.session_state.df_partidos = None
if "page" not in st.session_state:
    st.session_state.page = "Carga"

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
        col_pass, col_btn = st.columns([2, 1])
        with col_pass:
            password = st.text_input("", type="password", placeholder="Password", label_visibility="collapsed", key="login_password")
        with col_btn:
            if st.button("🔓 Entrar", type="primary", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.rerun()
                else:
                    st.error("❌ Incorrecta")
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
        st.markdown("---")
        
        if st.button("📂 Carga", use_container_width=True, type="secondary" if st.session_state.page != "Carga" else "primary"):
            st.session_state.page = "Carga"
            st.rerun()
        
        if st.button("📊 Analizador", use_container_width=True, type="secondary" if st.session_state.page != "Analizador" else "primary"):
            st.session_state.page = "Analizador"
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"**Usuario:** Admin")
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged = False
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
                                        data = {
                                            'fixture_id': abs(hash(f"{row['equipo_local']}{row['equipo_visitante']}")) % (10**10),
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
        
        # Formulario simple
        st.markdown("### 🔍 Analizar Partido")
        
        col1, col2 = st.columns(2)
        with col1:
            home_team = st.text_input("🏠 Equipo Local", placeholder="Ej: Barcelona")
            lambda_local = st.number_input("Lambda Local (goles esperados)", min_value=0.1, max_value=5.0, value=1.5, step=0.1)
        
        with col2:
            away_team = st.text_input("✈️ Equipo Visitante", placeholder="Ej: Real Madrid")
            lambda_visitante = st.number_input("Lambda Visitante (goles esperados)", min_value=0.1, max_value=5.0, value=1.2, step=0.1)
        
        # Botón analizar
        if st.button("🎯 ANALIZAR", type="primary", use_container_width=True):
            if home_team and away_team:
                with st.spinner("Analizando..."):
                    result = calcular(lambda_local, lambda_visitante)
                    st.session_state.analysis_result = result
                    st.session_state.home = home_team
                    st.session_state.away = away_team
            else:
                st.error("⚠️ Ingresa ambos equipos")
        
        # Mostrar resultados
        if 'analysis_result' in st.session_state:
            r = st.session_state.analysis_result
            home = st.session_state.home
            away = st.session_state.away
            
            st.markdown("---")
            st.markdown(f"## 📊 {home} vs {away}")
            
            # Pick y confianza
            col_pick, col_conf = st.columns(2)
            with col_pick:
                rating_emoji = {"A+": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}
                st.metric("Pick", f"{r['pick']} {rating_emoji.get(r['rango'], '')}")
            with col_conf:
                st.metric("Confianza", f"{r['confianza']}% ({r['rango']})")
            
            # Probabilidades 1X2
            st.markdown("### 🎯 1X2")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**1 (Local)**")
                st.markdown(f"# {r['p1']:.1f}%")
                st.progress(r['p1']/100, color="green")
            with col2:
                st.markdown("**X (Empate)**")
                st.markdown(f"# {r['px']:.1f}%")
                st.progress(r['px']/100, color="gray")
            with col3:
                st.markdown("**2 (Visitante)**")
                st.markdown(f"# {r['p2']:.1f}%")
                st.progress(r['p2']/100, color="blue")
            
            # Detalle por modelo
            with st.expander("📋 Detalle por Modelo"):
                modelos = [
                    ("Poisson (35%)", r['poisson']),
                    ("Dixon-Coles (30%)", r['dixon_coles']),
                    ("Monte Carlo (20%)", r['monte_carlo']),
                    ("Elo (15%)", r['elo'])
                ]
                for nombre, m in modelos:
                    col_h, col_d, col_a = st.columns(3)
                    with col_h:
                        st.metric(nombre, f"1: {m['p1']}%")
                    with col_d:
                        st.metric("", f"X: {m['px']}%")
                    with col_a:
                        st.metric("", f"2: {m['p2']}%")
