"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Scraping de ultimos 5 partidos por equipo
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from supabase import create_client
from typing import Dict, List, Optional


# Configuracion
SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

BASE_URL_FLASHSCORE = "https://www.flashscore.com.ar"
BASE_URL_SOCCERWAY = "https://pt.soccerway.com"


def search_team_flashscore(team_name: str) -> Optional[str]:
    """Busca un equipo en Flashscore y retorna su URL."""
    try:
        search_url = f"{BASE_URL_FLASHSCORE}/buscar/?q={requests.utils.quote(team_name)}"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = str(link.get('href', ''))
                if '/equipo/' in href:
                    return href
    except Exception as e:
        print(f"Error Flashscore: {e}")
    return None


def search_team_soccerway(team_name: str) -> Optional[str]:
    """Busca un equipo en Soccerway y retorna su URL."""
    try:
        search_url = f"{BASE_URL_SOCCERWAY}/search/?q={requests.utils.quote(team_name)}"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = str(link.get('href', ''))
                if '/teams/' in href:
                    return href
    except Exception as e:
        print(f"Error Soccerway: {e}")
    return None


def get_last_5_matches_soccerway(team_url: str) -> List[Dict]:
    """Obtiene los ultimos 5 partidos desde Soccerway."""
    matches = []
    try:
        url = BASE_URL_SOCCERWAY + team_url if team_url.startswith('/') else team_url
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar tabla de partidos recientes
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Buscar fecha, equipos y marcador
                        date_text = cells[0].get_text(strip=True) if cells else ""
                        team1 = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        team2 = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        
                        # Buscar marcador
                        score_text = ""
                        for cell in cells:
                            text = cell.get_text(strip=True)
                            if re.search(r'\d+-\d+', text):
                                score_text = text
                                break
                        
                        if team1 and team2:
                            score_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', score_text)
                            if score_match:
                                matches.append({
                                    'local': team1,
                                    'visitante': team2,
                                    'goles_local': int(score_match.group(1)),
                                    'goles_visitante': int(score_match.group(2))
                                })
                
                if len(matches) >= 5:
                    break
                    
    except Exception as e:
        print(f"Error obteniendo partidos: {e}")
    
    return matches[:5]


def calculate_averages(matches: List[Dict], is_local: bool) -> Optional[Dict]:
    """Calcula promedios de los ultimos 5 partidos. Retorna None si no hay datos."""
    if not matches:
        return None
    
    valid_matches = [m for m in matches if isinstance(m, dict) and 'goles_local' in m]
    if not valid_matches:
        return None
    
    total = len(valid_matches)
    
    if is_local:
        goles_favor = sum(m.get('goles_local', 0) for m in valid_matches)
        goles_contra = sum(m.get('goles_visitante', 0) for m in valid_matches)
    else:
        goles_favor = sum(m.get('goles_visitante', 0) for m in valid_matches)
        goles_contra = sum(m.get('goles_local', 0) for m in valid_matches)
    
    return {
        'prom_goles_favor': round(goles_favor / total, 2),
        'prom_goles_contra': round(goles_contra / total, 2)
    }


def update_team_in_supabase(team_name: str, stats_local: Dict, stats_away: Dict):
    """Actualiza las estadisticas del equipo en Supabase."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    lambda_local = round(stats_local.get('prom_goles_favor', 1.3) * 1.1, 2)
    lambda_visitante = round(stats_away.get('prom_goles_favor', 1.1) * 0.85, 2)
    
    data = {
        'equipo': team_name,
        'partidos_jugados': 5,
        'goles_favor': int(stats_local.get('prom_goles_favor', 0) * 5),
        'goles_contra': int(stats_local.get('prom_goles_contra', 0) * 5),
        'lambda_local': lambda_local,
        'lambda_visitante': lambda_visitante,
    }
    
    try:
        client.table('estadisticas_equipos').upsert(data, on_conflict='equipo').execute()
        return True
    except Exception as e:
        print(f"Error guardando {team_name}: {e}")
        return False


def run_robot_for_team(team_name: str) -> Dict:
    """Ejecuta el robot para un equipo."""
    print(f"Procesando: {team_name}")
    
    result = {
        'equipo': team_name,
        'encontrado': False,
        'partidos': 0,
        'exito': False
    }
    
    # Intentar buscar en Soccerway primero (mas estable)
    team_url = search_team_soccerway(team_name)
    
    if not team_url:
        # Intentar Flashscore
        team_url = search_team_flashscore(team_name)
    
    if not team_url:
        print(f"  ❌ Equipo no encontrado: {team_name}")
        return result
    
    result['encontrado'] = True
    print(f"  ✓ URL encontrada: {team_url}")
    
    # Obtener partidos
    matches = get_last_5_matches_soccerway(team_url)
    result['partidos'] = len(matches)
    
    # Calcular promedios
    stats_local = calculate_averages(matches, is_local=True)
    stats_away = calculate_averages(matches, is_local=False)
    
    # Solo guardar si tiene DATOS REALES
    if stats_local is None or stats_away is None:
        print(f"  ⚠️ Sin datos reales - NO se guarda")
        return result
    
    print(f"  📊 Lambda local: {stats_local['prom_goles_favor']:.2f}")
    
    # Guardar
    if update_team_in_supabase(team_name, stats_local, stats_away):
        result['exito'] = True
        print(f"  ✅ Guardado en Supabase")
    else:
        print(f"  ❌ Error guardando")
    
    return result


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """Ejecuta el robot para una lista de equipos."""
    results = []
    
    for i, team in enumerate(team_names):
        print(f"\n[{i+1}/{len(team_names)}] {team}")
        result = run_robot_for_team(team)
        results.append(result)
        
        if i < len(team_names) - 1:
            time.sleep(2)
    
    return results
