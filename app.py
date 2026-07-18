import streamlit as st
import pandas as pd
import os
from supabase import create_client
from data_loader import parse_flashscore_excel, validate_matches

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

# CSS
st.markdown("""
<style>
.stApp { background: #0a0a0a; }
.title { color: #ffd700; font-size: 48px; font-weight: bold; margin: 0; padding: 0; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 3px 0; border-bottom: 2px solid #333; }
.stDataFrame { background: #1a1a1a; }
.section-title { margin-top: 5px; margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

# Login
if not st.session_state.logged:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    with col2:
        with st.expander("🔐 Login", expanded=False):
            password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Ingresa password")
            if st.button("Entrar", type="primary"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.rerun()
                else:
                    st.error("Incorrecta")

# Dashboard
else:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🔓 Logout"):
            st.session_state.logged = False
            st.rerun()
    
    # Sección de carga
    st.markdown("---")
    st.markdown('<p class="section-title">### 📂 Cargar archivos</p>', unsafe_allow_html=True)
    
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
                
                # Botón para enviar a Supabase
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✅ Guardar en Supabase", type="primary", use_container_width=True):
                        try:
                            client = create_client(SUPABASE_URL, SUPABASE_KEY)
                            
                            guardados = 0
                            for _, row in df_partidos.iterrows():
                                data = {
                                    'fixture_id': abs(hash(f"{row['equipo_local']}{row['equipo_visitante']}")) % (10**10),
                                    'fecha': row['fecha'],
                                    'hora': row['hora'],
                                    'liga': row['liga'],
                                    'pais': row['pais'],
                                    'liga_codigo': row['liga_codigo'],
                                    'equipo_local': row['equipo_local'],
                                    'equipo_visitante': row['equipo_visitante']
                                }
                                try:
                                    client.table('partidos').upsert(data, on_conflict='fixture_id').execute()
                                    guardados += 1
                                except Exception as e:
                                    pass
                            
                            st.success(f"✅ {guardados} partidos guardados en Supabase")
                            st.session_state.df_partidos = None
                            
                        except Exception as e:
                            st.error(f"Error al guardar: {str(e)[:100]}")
            else:
                st.warning("No se encontraron partidos en el archivo")
                
        except Exception as e:
            st.error(f"Error al leer archivo: {str(e)}")
    
    # Mostrar partidos existentes en Supabase
    st.markdown("---")
    st.markdown("### 📊 Partidos en Supabase")
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = client.table('partidos').select('*').execute()
        
        if response.data:
            df_db = pd.DataFrame(response.data)
            st.dataframe(df_db, use_container_width=True, height=300)
            st.info(f"Total: {len(response.data)} partidos")
        else:
            st.info("No hay partidos en la base de datos")
    except Exception as e:
        st.error(f"Error al cargar: {str(e)[:100]}")
