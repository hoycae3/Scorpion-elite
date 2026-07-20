import streamlit as st
import pandas as pd
import os
from supabase import create_client
from data_loader import parse_flashscore_excel, validate_matches
from analysis_models import calcular
from stats_extractor import calculate_team_lambda
from stats_robot import run_robot_batch
from scrapers_fallback import scrape_team_fallback

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
        
        if st.button("📈 Estadísticas", use_container_width=True, type="secondary" if st.session_state.page != "Estadisticas" else "primary"):
            st.session_state.page = "Estadisticas"
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
                                            result = client.table('partido').upsert(data, on_conflict='fixture_id').execute()
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
                            client.table('partido').delete().neq('id', 0).execute()
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
        
        with col2:
            away_team = st.text_input("✈️ Equipo Visitante", placeholder="Ej: Real Madrid")
        
        # Validar que ambos equipos tengan DATOS REALES en Supabase
        lambda_local = None
        lambda_visitante = None
        equipo_local_ok = False
        equipo_visitante_ok = False
        equipos_faltantes = []
        
        if home_team:
            try:
                client = create_client(SUPABASE_URL, SUPABASE_KEY)
                resp = client.table('equipos_stas').select('lambda_local').ilike('equipo', f'%{home_team}%').execute()
                if resp.data and resp.data[0].get('lambda_local', 0) > 0:
                    lambda_local = resp.data[0].get('lambda_local')
                    equipo_local_ok = True
                    st.success(f"✅ {home_team} - λ={lambda_local}")
                else:
                    equipos_faltantes.append(home_team)
            except:
                equipos_faltantes.append(home_team)
        
        if away_team:
            try:
                client = create_client(SUPABASE_URL, SUPABASE_KEY)
                resp = client.table('equipos_stas').select('lambda_visitante').ilike('equipo', f'%{away_team}%').execute()
                if resp.data and resp.data[0].get('lambda_visitante', 0) > 0:
                    lambda_visitante = resp.data[0].get('lambda_visitante')
                    equipo_visitante_ok = True
                    st.success(f"✅ {away_team} - λ={lambda_visitante}")
                else:
                    equipos_faltantes.append(away_team)
            except:
                equipos_faltantes.append(away_team)
        
        # Mostrar error si faltan equipos
        if equipos_faltantes:
            st.error(f"⚠️ Equipos sin estadísticas: {', '.join(set(equipos_faltantes))}")
            st.info("📝 Ve a la pestaña 'Estadísticas' y ejecuta 'Actualizar Estadísticas de la Semana' para agregarlos.")
        
        # Botón analizar - solo si ambos equipos existen
        analizar_disabled = not (equipo_local_ok and equipo_visitante_ok)
        
        if st.button("🎯 ANALIZAR", type="primary", use_container_width=True, disabled=analizar_disabled):
            if home_team and away_team and lambda_local and lambda_visitante:
                with st.spinner("Analizando..."):
                    result = calcular(lambda_local, lambda_visitante)
                    st.session_state.analysis_result = result
                    st.session_state.home = home_team
                    st.session_state.away = away_team
            else:
                st.error("⚠️ Ambos equipos deben tener estadísticas. Ejecuta el robot primero.")
        
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
                    response = client.table('partido').select('equipo_local, equipo_visitante').execute()
                    
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
                        st.info(f"📊 {len(equipos)} equipos encontrados. Buscando...")
                        
                        # Buscar todos
                        results = run_robot_batch(equipos)
                        
                        # Intentar fallback para equipos no encontrados
                        no_encontrados = [r for r in results if not r['encontrado']]
                        fallback_results = []
                        
                        if no_encontrados:
                            st.info(f"🔄 Buscando {len(no_encontrados)} equipos en base de datos local...")
                            for r in no_encontrados:
                                fb_result = scrape_team_fallback(r['equipo'])
                                if fb_result['encontrado']:
                                    # Convertir formato
                                    new_result = {
                                        'equipo': r['equipo'],
                                        'encontrado': True,
                                        'exito': True,
                                        'sin_estadisticas': False,
                                        'equipo_real': fb_result['equipo'],
                                        'liga': fb_result['liga'],
                                        'lambda_local': fb_result['stats'].get('lambda_local', 1.3),
                                        'lambda_visitante': fb_result['stats'].get('lambda_visitante', 1.1),
                                        'goles_favor': fb_result['stats'].get('goles_favor', 0),
                                        'goles_contra': fb_result['stats'].get('goles_contra', 0),
                                        'partidos_jugados': fb_result['stats'].get('partidos', 0),
                                        'fuentes_probadas': ['LOCAL_DB'],
                                    }
                                    # Actualizar resultado original
                                    idx = results.index(r)
                                    results[idx] = new_result
                                    fallback_results.append(fb_result['equipo'])
                        
                        # Resumen
                        exitos = [r for r in results if r['exito']]
                        sin_stats = [r for r in exitos if r.get('sin_estadisticas')]
                        con_stats = [r for r in exitos if not r.get('sin_estadisticas')]
                        no_encontrados_final = [r for r in results if not r['encontrado']]
                        
                        # Estadisticas reales vs estimados
                        st.success(f"✅ **{len(exitos)} equipos encontrados** de {len(equipos)}")
                        
                        if fallback_results:
                            st.success(f"🔗 **{len(fallback_results)} encontrados en base de datos local**")
                        if con_stats:
                            st.markdown(f"📊 **{len(con_stats)} con estadísticas reales**")
                        if sin_stats:
                            st.markdown(f"📋 **{len(sin_stats)} con datos estimados** (sin estadísticas disponibles)")
                        if no_encontrados_final:
                            st.warning(f"❌ **{len(no_encontrados_final)} NO encontrados**")
                            with st.expander("Ver equipos no encontrados"):
                                for r in no_encontrados_final:
                                    st.markdown(f"- {r['equipo']}")
                        
                        # Mostrar equipos con stats
                        if con_stats:
                            with st.expander(f"📊 Ver {len(con_stats)} equipos con estadísticas"):
                                for r in con_stats:
                                    src = r.get('fuentes_probadas', ['?'])[-1]
                                    src_emoji = {"FD": "📊", "SW": "🌐", "LOCAL_DB": "💾"}.get(src, "❓")
                                    st.markdown(f"{src_emoji} **{r.get('equipo_real', r['equipo'])}** ({r.get('liga', 'N/A')}) - λL:{r['lambda_local']} λV:{r['lambda_visitante']}")
                        
                        # Mostrar equipos sin stats (estimados)
                        if sin_stats:
                            with st.expander(f"📋 Ver {len(sin_stats)} equipos con datos estimados"):
                                for r in sin_stats:
                                    st.markdown(f"⚠️ **{r.get('equipo_real', r['equipo'])}** ({r.get('liga', 'N/A')}) - λL:{r['lambda_local']} λV:{r['lambda_visitante']} *(estimado)*")
                        
                        # Guardar estadísticas en Supabase
                        equipos_con_stats = con_stats + sin_stats
                        if equipos_con_stats:
                            st.info("💾 Guardando estadísticas en Supabase...")
                            guardados = 0
                            errores = 0
                            for r in equipos_con_stats:
                                try:
                                    equipo_nombre = r.get('equipo_real', r['equipo'])
                                    data = {
                                        'equipo': equipo_nombre,
                                        'liga': r.get('liga', 'Desconocida'),
                                        'temporada': '2024-25',
                                        'partidos_jugados': r.get('partidos_jugados', 0) or 0,
                                        'goles_favor': r.get('goles_favor', 0) or 0,
                                        'goles_contra': r.get('goles_contra', 0) or 0,
                                        'lambda_local': float(r.get('lambda_local', 1.3)) or 1.3,
                                        'lambda_visitante': float(r.get('lambda_visitante', 1.1)) or 1.1,
                                    }
                                    
                                    # Intentar upsert (actualizar si existe)
                                    try:
                                        client.table('equipos_stas').upsert(data).execute()
                                    except:
                                        # Si falla upsert, intentar insert directo
                                        client.table('equipos_stas').insert(data).execute()
                                    
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
            
            submitted = st.form_submit_button("💾 Guardar Equipo", use_container_width=True)
            
            if submitted and equipo:
                # Calcular lambdas
                lambda_local = calculate_team_lambda(goles_favor, goles_contra, partidos, is_home=True)
                lambda_visitante = calculate_team_lambda(goles_favor, goles_contra, partidos, is_home=False)
                
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
                    'lambda_visitante': lambda_visitante
                }
                
                try:
                    client.table('equipos_stas').upsert(data, on_conflict='equipo,temporada').execute()
                    st.success(f"✅ {equipo} guardado exitosamente")
                except Exception as e:
                    st.error(f"Error: {str(e)[:50]}")
        
        st.markdown("---")
        st.markdown("### 📋 Equipos con Estadísticas")
        
        # Mostrar tabla directamente
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        try:
            response = client.table('equipos_stas').select('equipo,liga,partidos_jugados,lambda_local,lambda_visitante,goles_favor,goles_contra').execute()
            
            if response.data and len(response.data) > 0:
                st.success(f"✅ {len(response.data)} equipos con estadísticas guardadas")
                
                # Crear DataFrame
                df = pd.DataFrame(response.data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("📭 No hay equipos guardados. Sube un Excel y busca equipos primero.")
        except Exception as e:
            st.error(f"❌ Error al conectar: {str(e)}")
        
        st.markdown("---")
        st.markdown("### 🔍 Buscar Equipo Específico")
        
        # Buscar equipo
        equipo_buscar = st.text_input("Buscar equipo...", placeholder="Escribe el nombre del equipo")
        
        if equipo_buscar:
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            try:
                # Buscar por nombre
                response = client.table('equipos_stas').select('*').ilike('equipo', f'%{equipo_buscar}%').execute()
                
                if response.data:
                    st.markdown(f"**{len(response.data)} resultado(s) encontrado(s)**")
                    
                    for eq in response.data:
                        with st.expander(f"⚽ {eq['equipo']} - {eq.get('liga', 'N/A')}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Temporada:** {eq.get('temporada', 'N/A')}")
                                st.markdown(f"**Partidos:** {eq.get('partidos_jugados', 0)}")
                                st.markdown(f"**Victorias:** {eq.get('victorias', 0)}")
                                st.markdown(f"**Empates:** {eq.get('empates', 0)}")
                                st.markdown(f"**Derrotas:** {eq.get('derrotas', 0)}")
                            with col2:
                                st.markdown(f"**Goles a Favor:** {eq.get('goles_favor', 0)}")
                                st.markdown(f"**Goles en Contra:** {eq.get('goles_contra', 0)}")
                                st.markdown(f"**Lambda Local:** {eq.get('lambda_local', 0):.2f}")
                                st.markdown(f"**Lambda Visitante:** {eq.get('lambda_visitante', 0):.2f}")
                            
                            # Botón eliminar
                            if st.button(f"🗑️ Eliminar {eq['equipo']}", key=f"del_{eq['id']}"):
                                client.table('equipos_stas').delete().eq('id', eq['id']).execute()
                                st.success("✅ Eliminado")
                                st.rerun()
                else:
                    st.info("No se encontraron equipos")
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")
