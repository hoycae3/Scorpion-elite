"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Scraping desde FBref
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from supabase import create_client
from typing import Dict, List, Optional


# Configuracion
SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

BASE_URL = "https://fbref.com"


def search_team_fbref(team_name: str) -> Optional[str]:
    """Busca un equipo en FBref y retorna su URL."""
    try:
        search_url = f"{BASE_URL}/en/search/search/?q={requests.utils.quote(team_name)}"
        response = requests.get(search_url, headers=HEADERS, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar en resultados de busqueda
            results = soup.find_all('a', href=re.compile(r'/en/squads/'))
            
            for result in results[:3]:  # Probar los primeros 3
                href = result.get('href', '')
                name = result.get_text(strip=True)
                
                if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                    return href
            
            # Retornar el primero si hay resultados
            if results:
                return results[0].get('href')
                
    except Exception as e:
        print(f"Error FBref: {e}")
    
    return None


def get_team_stats_fbref(team_url: str) -> Optional[Dict]:
    """Obtiene estadisticas del equipo desde FBref."""
    try:
        url = BASE_URL + team_url if team_url.startswith('/') else team_url
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        stats = {}
        
        # Buscar la tabla de estadisticas generales (Resumen)
        tables = soup.find_all('table', id=re.compile(r'stats|shooting|passing|defensive'))
        
        for table in tables:
            # Intentar encontrar filas con datos
            rows = table.find_all('tr')
            
            for row in rows:
                # Skip header rows
                if 'thead' in str(row) or row.find('th'):
                    continue
                
                cells = row.find_all('td')
                if not cells:
                    continue
                
                # Primera celda es el nombre del equipo
                if cells and len(cells) > 1:
                    # Buscar estadisticas de goles/disparo
                    for i, cell in enumerate(cells[:20]):
                        text = cell.get_text(strip=True)
                        
                        # Goles
                        if text.isdigit() and 'goles' not in stats:
                            stats['goles'] = int(text)
                        
                        # Disparos
                        if 'Sh' in cell.get('data-stat', ''):
                            try:
                                stats['disparos'] = float(text)
                            except:
                                pass
                        
                        # Disparos a puerta
                        if 'SoT' in cell.get('data-stat', ''):
                            try:
                                stats['disparos_puerta'] = float(text)
                            except:
                                pass
                        
                        # xG (expected goals)
                        if 'xg' in cell.get('data-stat', '').lower():
                            try:
                                stats['xg'] = float(text)
                            except:
                                pass
                
                break  # Solo primera fila de datos
        
        # Alternativa: buscar en el texto de la pagina
        if not stats:
            page_text = soup.get_text()
            
            # Buscar patrones numericos para estadisticas
            # GF = Goals For, GA = Goals Against
            gf_match = re.search(r'GF\s+(\d+)', page_text)
            ga_match = re.search(r'GA\s+(\d+)', page_text)
            
            if gf_match:
                stats['goles'] = int(gf_match.group(1))
            if ga_match:
                stats['goles_contra'] = int(ga_match.group(1))
        
        return stats if stats else None
        
    except Exception as e:
        print(f"Error obteniendo stats: {e}")
        return None


def calculate_lambda_from_stats(stats: Dict, is_local: bool = True) -> float:
    """Calcula lambda desde estadisticas de FBref."""
    if not stats:
        return None
    
    # Usar xG si esta disponible, sino goles
    xg = stats.get('xg')
    goles = stats.get('goles')
    
    if xg and xg > 0:
        value = xg
    elif goles and goles > 0:
        value = goles
    else:
        return None
    
    # Ajustar por local/visitante
    if is_local:
        return round(value * 1.1, 2)
    else:
        return round(value * 0.85, 2)


def run_robot_for_team(team_name: str) -> Dict:
    """Ejecuta el robot para un equipo."""
    print(f"Procesando: {team_name}")
    
    result = {
        'equipo': team_name,
        'encontrado': False,
        'exito': False,
        'lambda_local': None,
        'lambda_visitante': None
    }
    
    # 1. Buscar equipo
    team_url = search_team_fbref(team_name)
    
    if not team_url:
        print(f"  ❌ Equipo no encontrado: {team_name}")
        return result
    
    result['encontrado'] = True
    print(f"  ✓ URL: {team_url[:50]}...")
    
    # 2. Obtener estadisticas
    stats = get_team_stats_fbref(team_url)
    
    if not stats:
        print(f"  ⚠️ Sin estadisticas disponibles")
        return result
    
    print(f"  📊 Stats: {stats}")
    
    # 3. Calcular lambdas
    lambda_local = calculate_lambda_from_stats(stats, is_local=True)
    lambda_visitante = calculate_lambda_from_stats(stats, is_local=False)
    
    if not lambda_local or not lambda_visitante:
        print(f"  ⚠️ No se pudo calcular lambda")
        return result
    
    result['lambda_local'] = lambda_local
    result['lambda_visitante'] = lambda_visitante
    
    # 4. Guardar en Supabase
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    data = {
        'equipo': team_name,
        'lambda_local': lambda_local,
        'lambda_visitante': lambda_visitante,
        'partidos_jugados': 10
    }
    
    try:
        client.table('estadisticas_equipos').upsert(data, on_conflict='equipo').execute()
        result['exito'] = True
        print(f"  ✅ Guardado - λ_local={lambda_local}, λ_away={lambda_visitante}")
    except Exception as e:
        print(f"  ❌ Error guardando: {e}")
    
    return result


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """Ejecuta el robot para una lista de equipos."""
    results = []
    
    for i, team in enumerate(team_names):
        print(f"\n[{i+1}/{len(team_names)}] {team}")
        result = run_robot_for_team(team)
        results.append(result)
        
        if i < len(team_names) - 1:
            time.sleep(1.5)  # Pausa para no saturar
    
    return results


# Prueba rapida
if __name__ == "__main__":
    result = run_robot_for_team("Barcelona")
    print(result)
