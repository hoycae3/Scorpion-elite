"""
Scorpion Elite - Robot Extractor de Estadísticas
================================================
Scraping de últimos 5 partidos por equipo desde Flashscore
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from supabase import create_client
from typing import Dict, List, Optional


# Configuración
SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

BASE_URL = "https://www.flashscore.com.ar"


def search_team(team_name: str) -> Optional[str]:
    """
    Busca un equipo en Flashscore y retorna su URL.
    """
    try:
        search_url = f"{BASE_URL}/search/?q={requests.utils.quote(team_name)}"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Buscar resultado en la tabla de búsqueda
            links = soup.find_all('a', href=re.compile(r'/equipo/.*/'))
            for link in links:
                href = link.get('href', '')
                if team_name.lower() in link.get_text().lower():
                    return href
            # Si no encontró match exacto, retornar el primero
            if links:
                return links[0].get('href')
    except Exception as e:
        print(f"Error buscando equipo {team_name}: {e}")
    return None


def get_last_5_matches(team_url: str) -> List[Dict]:
    """
    Obtiene los últimos 5 partidos de un equipo.
    """
    matches = []
    try:
        url = BASE_URL + team_url if team_url.startswith('/') else team_url
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la sección de últimos partidos
            sections = soup.find_all('div', class_=re.compile(r'section|matches'))
            
            for section in sections:
                # Buscar filas de partidos
                rows = section.find_all('div', class_=re.compile(r'event|match'))
                
                for row in rows[:5]:  # Solo últimos 5
                    match_data = parse_match_row(row)
                    if match_data:
                        matches.append(match_data)
                
                if len(matches) >= 5:
                    break
                    
    except Exception as e:
        print(f"Error obteniendo partidos: {e}")
    
    return matches[:5]


def parse_match_row(row) -> Optional[Dict]:
    """
    Parsea una fila de partido para extraer datos.
    """
    try:
        data = {}
        
        # Extraer hora/fecha
        time_elem = row.find('span', class_=re.compile(r'time'))
        if time_elem:
            data['hora'] = time_elem.get_text(strip=True)
        
        # Extraer nombres de equipos
        teams = row.find_all('a', class_=re.compile(r'team|name'))
        if len(teams) >= 2:
            data['local'] = teams[0].get_text(strip=True)
            data['visitante'] = teams[1].get_text(strip=True)
        
        # Extraer marcador (si existe)
        score = row.find_all('span', class_=re.compile(r'score|FT|current'))
        if len(score) >= 2:
            try:
                data['goles_local'] = int(score[0].get_text(strip=True))
                data['goles_visitante'] = int(score[1].get_text(strip=True))
            except:
                pass
        
        # Extraer estadísticas del partido
        stats = row.find_all('div', class_=re.compile(r'stats|statistic'))
        for stat in stats:
            stat_text = stat.get_text(strip=True).lower()
            
            if 'corner' in stat_text or 'córner' in stat_text:
                nums = re.findall(r'\d+', stat_text)
                if len(nums) >= 2:
                    data['corners_local'] = int(nums[0])
                    data['corners_visitante'] = int(nums[1])
            
            elif 'yellow' in stat_text or 'amarilla' in stat_text:
                nums = re.findall(r'\d+', stat_text)
                if len(nums) >= 2:
                    data['tarjetas_amarillas_local'] = int(nums[0])
                    data['tarjetas_amarillas_visitante'] = int(nums[1])
            
            elif 'red' in stat_text or 'roja' in stat_text:
                nums = re.findall(r'\d+', stat_text)
                if len(nums) >= 2:
                    data['tarjetas_rojas_local'] = int(nums[0])
                    data['tarjetas_rojas_visitante'] = int(nums[1])
            
            elif 'shots' in stat_text or 'remate' in stat_text:
                nums = re.findall(r'\d+', stat_text)
                if len(nums) >= 2:
                    data['remates_local'] = int(nums[0])
                    data['remates_visitante'] = int(nums[1])
            
            elif 'saved' in stat_text or 'atajada' in stat_text:
                nums = re.findall(r'\d+', stat_text)
                if len(nums) >= 2:
                    data['atajadas_local'] = int(nums[0])
                    data['atajadas_visitante'] = int(nums[1])
        
        return data if 'local' in data else None
        
    except Exception as e:
        return None


def calculate_averages(matches: List[Dict], is_local: bool) -> Dict:
    """
    Calcula promedios de los últimos 5 partidos.
    """
    if not matches:
        return {
            'prom_goles_favor': 0,
            'prom_goles_contra': 0,
            'prom_corners': 0,
            'prom_tarjetas_amarillas': 0,
            'prom_tarjetas_rojas': 0,
            'prom_remates': 0,
            'prom_atajadas': 0
        }
    
    suffix_local = '_local' if is_local else '_visitante'
    suffix_away = '_visitante' if is_local else '_local'
    
    total_matches = len(matches)
    
    # Goles
    goles_favor = sum(m.get(f'goles{suffix_local}', 0) for m in matches)
    goles_contra = sum(m.get(f'goles{suffix_away}', 0) for m in matches)
    
    # Corners
    corners = sum(m.get(f'corners{suffix_local}', 0) for m in matches)
    
    # Tarjetas
    amarillas = sum(m.get(f'tarjetas_amarillas{suffix_local}', 0) for m in matches)
    rojas = sum(m.get(f'tarjetas_rojas{suffix_local}', 0) for m in matches)
    
    # Remates
    remates = sum(m.get(f'remates{suffix_local}', 0) for m in matches)
    
    # Atajadas
    atajadas = sum(m.get(f'atajadas{suffix_local}', 0) for m in matches)
    
    return {
        'prom_goles_favor': round(goles_favor / total_matches, 2),
        'prom_goles_contra': round(goles_contra / total_matches, 2),
        'prom_corners': round(corners / total_matches, 2),
        'prom_tarjetas_amarillas': round(amarillas / total_matches, 2),
        'prom_tarjetas_rojas': round(rojas / total_matches, 2),
        'prom_remates': round(remates / total_matches, 2),
        'prom_atajadas': round(atajadas / total_matches, 2)
    }


def update_team_in_supabase(team_name: str, stats_local: Dict, stats_away: Dict):
    """
    Actualiza las estadísticas del equipo en Supabase.
    """
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Calcular lambda desde promedios
    lambda_local = round(stats_local.get('prom_goles_favor', 1.3) * 1.1, 2)
    lambda_visitante = round(stats_away.get('prom_goles_favor', 1.1) * 0.85, 2)
    
    data = {
        'equipo': team_name,
        'partidos_jugados': 5,
        'goles_favor': int(stats_local.get('prom_goles_favor', 0) * 5),
        'goles_contra': int(stats_local.get('prom_goles_contra', 0) * 5),
        'lambda_local': lambda_local,
        'lambda_visitante': lambda_visitante,
        'stats_json': {
            'local': stats_local,
            'visitante': stats_away
        }
    }
    
    try:
        # Intentar actualizar o insertar
        client.table('estadisticas_equipos').upsert(data, on_conflict='equipo').execute()
        return True
    except Exception as e:
        print(f"Error guardando {team_name}: {e}")
        return False


def run_robot_for_team(team_name: str) -> Dict:
    """
    Ejecuta el robot completo para un equipo.
    """
    print(f"Procesando: {team_name}")
    
    result = {
        'equipo': team_name,
        'encontrado': False,
        'partidos': 0,
        'stats_local': None,
        'stats_away': None,
        'exito': False
    }
    
    # 1. Buscar equipo
    team_url = search_team(team_name)
    if not team_url:
        print(f"  ❌ Equipo no encontrado: {team_name}")
        return result
    
    result['encontrado'] = True
    print(f"  ✓ URL encontrada: {team_url}")
    
    # 2. Obtener últimos 5 partidos
    matches = get_last_5_matches(team_url)
    result['partidos'] = len(matches)
    
    if not matches:
        print(f"  ⚠️ Sin partidos encontrados")
        return result
    
    print(f"  ✓ {len(matches)} partidos encontrados")
    
    # 3. Calcular promedios
    stats_local = calculate_averages(matches, is_local=True)
    stats_away = calculate_averages(matches, is_local=False)
    
    result['stats_local'] = stats_local
    result['stats_away'] = stats_away
    
    # 4. Guardar en Supabase
    if update_team_in_supabase(team_name, stats_local, stats_away):
        result['exito'] = True
        print(f"  ✅ Guardado en Supabase")
    else:
        print(f"  ❌ Error guardando")
    
    return result


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """
    Ejecuta el robot para una lista de equipos.
    """
    results = []
    
    for i, team in enumerate(team_names):
        print(f"\n[{i+1}/{len(team_names)}] {team}")
        result = run_robot_for_team(team)
        results.append(result)
        
        # Pausa entre requests para evitar bloqueos
        if i < len(team_names) - 1:
            time.sleep(2)
    
    return results


# ======================= INTERFAZ STREAMLIT =======================
def create_streamlit_button():
    """
    Retorna el código del botón para Streamlit.
    Para usar en app.py.
    """
    return '''
# En tu app.py, agrega esto donde quieras el botón:

def run_stats_robot():
    """Ejecuta el robot de estadísticas."""
    from stats_robot import run_robot_batch, run_robot_for_team
    
    st.info("🔄 Ejecutando robot de estadísticas...")
    
    # Lista de equipos a actualizar (puedes personalizarla)
    equipos = [
        "Barcelona",
        "Real Madrid", 
        "Manchester United",
        "Liverpool",
        "Bayern Munich",
        "PSG",
        "Juventus",
        "AC Milan",
        "Borussia Dortmund",
        "Atletico Madrid"
    ]
    
    with st.spinner("Extrayendo estadísticas de equipos..."):
        results = run_robot_batch(equipos)
        
        exitos = sum(1 for r in results if r['exito'])
        encontrados = sum(1 for r in results if r['encontrado'])
        
        st.success(f"✅ Proceso completado: {exitos}/{len(equipos)} equipos actualizados")
        
        # Mostrar resumen
        for r in results:
            if r['exito']:
                st.markdown(f"✅ **{r['equipo']}** - {r['partidos']} partidos")
            elif r['encontrado']:
                st.markdown(f"⚠️ **{r['equipo']}** - Encontrado pero sin datos")
            else:
                st.markdown(f"❌ **{r['equipo']}** - No encontrado")


# Botón en la interfaz:
if st.button("🔄 Actualizar Estadísticas de la Semana", type="primary"):
    run_stats_robot()
'''
