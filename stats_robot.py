"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Usa Wikipedia para extraer estadisticas de equipos
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


def get_team_stats_wikipedia(team_name: str) -> Optional[Dict]:
    """Busca el equipo en Wikipedia y extrae estadisticas."""
    
    # Limpiar nombre del equipo
    clean_name = team_name.replace(' ', '_')
    
    # URLs posibles
    urls = [
        f"https://en.wikipedia.org/wiki/{clean_name}",
        f"https://en.wikipedia.org/wiki/{clean_name}_({int(time.time()) % 1000})",  # Evitar cache
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                stats = {}
                
                # Metodo 1: Buscar en tablas de la pagina
                tables = soup.find_all('table', class_='wikitable')
                
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            cell_text = cells[0].get_text(strip=True).lower()
                            
                            # Detectar si es una fila de equipo
                            if 'league' in cell_text or 'season' in cell_text or 'division' in cell_text:
                                # Extraer numeros
                                numbers = re.findall(r'\d+', row.get_text())
                                if len(numbers) >= 2:
                                    stats['gf'] = int(numbers[0])  # Goals For
                                    stats['ga'] = int(numbers[1])  # Goals Against
                                    break
                
                # Metodo 2: Buscar en infobox
                infobox = soup.find('table', class_='infobox')
                if infobox:
                    infobox_text = infobox.get_text()
                    
                    # Buscar patrones de estadisticas
                    gf_match = re.search(r'Goals\s*for[;:]\s*(\d+)', infobox_text, re.IGNORECASE)
                    ga_match = re.search(r'Goals\s*against[;:]\s*(\d+)', infobox_text, re.IGNORECASE)
                    
                    if gf_match:
                        stats['gf'] = int(gf_match.group(1))
                    if ga_match:
                        stats['ga'] = int(ga_match.group(1))
                
                # Metodo 3: Buscar estadisticas de temporada actual
                if not stats:
                    # Buscar en el texto
                    page_text = soup.get_text()
                    
                    # Patrones comunes
                    patterns = [
                        r'(\d+)\s*\(GF\)',
                        r'Goals\s*For\s*:\s*(\d+)',
                        r'GF\s*=\s*(\d+)',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            stats['gf'] = int(match.group(1))
                            break
                
                if stats:
                    return stats
                    
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    return None


def search_wikipedia(team_name: str) -> Optional[str]:
    """Busca el equipo en Wikipedia y retorna la URL."""
    
    search_url = f"https://en.wikipedia.org/w/index.php?search={team_name.replace(' ', '+')}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar link al articulo
            link = soup.find('a', title=lambda x: x and team_name.lower() in x.lower())
            if link:
                href = link.get('href', '')
                if '/wiki/' in href:
                    return href
                    
    except Exception as e:
        print(f"Error buscando: {e}")
    
    return None


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
    
    # Esperar para evitar bloqueos
    time.sleep(1)
    
    # 1. Buscar en Wikipedia
    team_url = search_wikipedia(team_name)
    
    if not team_url:
        print(f"  ❌ Equipo no encontrado en Wikipedia")
        return result
    
    result['encontrado'] = True
    print(f"  ✓ Encontrado")
    
    # 2. Obtener estadisticas
    stats = get_team_stats_wikipedia(team_url)
    
    if not stats:
        print(f"  ⚠️ Sin estadisticas disponibles")
        return result
    
    print(f"  📊 GF: {stats.get('gf', 'N/A')}, GA: {stats.get('ga', 'N/A')}")
    
    # 3. Calcular lambda (aproximado por partido)
    gf = stats.get('gf', 0)
    if gf > 0:
        # Suponer ~30 partidos por temporada (varia por liga)
        lambda_season = gf / 30
        
        # Ajustar por local/visitante
        lambda_local = round(lambda_season * 1.1, 2)
        lambda_visitante = round(lambda_season * 0.85, 2)
        
        result['lambda_local'] = lambda_local
        result['lambda_visitante'] = lambda_visitante
        
        # 4. Guardar en Supabase
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        data = {
            'equipo': team_name,
            'lambda_local': lambda_local,
            'lambda_visitante': lambda_visitante,
            'partidos_jugados': 30
        }
        
        try:
            client.table('estadisticas_equipos').upsert(data, on_conflict='equipo').execute()
            result['exito'] = True
            print(f"  ✅ Guardado - λL:{lambda_local} λV:{lambda_visitante}")
        except Exception as e:
            print(f"  ❌ Error guardando: {e}")
    else:
        print(f"  ⚠️ Sin datos de goles")
    
    return result


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """Ejecuta el robot para una lista de equipos."""
    results = []
    
    for i, team in enumerate(team_names):
        print(f"\n[{i+1}/{len(team_names)}] {team}")
        result = run_robot_for_team(team)
        results.append(result)
    
    return results


# Prueba
if __name__ == "__main__":
    result = run_robot_for_team("Barcelona")
    print(result)
