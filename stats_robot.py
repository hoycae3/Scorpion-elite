"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Scraping con Playwright - Navegador real para evadir bloqueos
"""

import asyncio
from playwright.async_api import async_playwright
import re
import time
from supabase import create_client
from typing import Dict, List, Optional


# Configuracion
SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"


async def search_team_fbref(page, team_name: str) -> Optional[str]:
    """Busca un equipo en FBref usando Playwright."""
    try:
        search_url = f"https://fbref.com/en/search/search/?q={team_name.replace(' ', '+')}"
        
        await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(2000)  # Esperar carga
        
        # Buscar link del equipo
        links = await page.query_selector_all('a[href*="/squads/"]')
        
        for link in links:
            href = await link.get_attribute('href')
            text = await link.text_content()
            
            if text and team_name.lower() in text.lower():
                return href
        
        # Retornar primero si hay
        if links:
            return await links[0].get_attribute('href')
            
    except Exception as e:
        print(f"Error buscando: {e}")
    
    return None


async def get_team_stats_fbref(page, team_url: str) -> Optional[Dict]:
    """Obtiene estadisticas del equipo desde FBref."""
    try:
        if not team_url.startswith('http'):
            url = "https://fbref.com" + team_url
        else:
            url = team_url
        
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)  # Esperar JavaScript
        
        stats = {}
        
        # Buscar estadisticas en la pagina
        page_text = await page.content()
        
        # Buscar patrones como "GF" (Goals For), "GA" (Goals Against)
        gf_match = re.search(r'GF\s*</t[dc][^>]*>\s*<t[dc][^>]*>\s*(\d+)', page_text)
        ga_match = re.search(r'GA\s*</t[dc][^>]*>\s*<t[dc][^>]*>\s*(\d+)', page_text)
        xg_match = re.search(r'xG\s*</t[dc][^>]*>\s*<t[dc][^>]*>\s*([\d.]+)', page_text)
        
        if gf_match:
            stats['goles'] = float(gf_match.group(1))
        if ga_match:
            stats['goles_contra'] = float(ga_match.group(1))
        if xg_match:
            stats['xg'] = float(xg_match.group(1))
        
        # Alternativa: buscar en texto visible
        if not stats:
            text = await page.inner_text('body')
            
            # Patrones para estadisticas
            patterns = [
                r'Goals For\s*(\d+)',
                r'GF\s*(\d+)',
                r'xG\s*([\d.]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    if 'goles' not in stats:
                        stats['goles'] = value
                    elif 'xg' not in stats and '.' in match.group(1):
                        stats['xg'] = value
        
        return stats if stats else None
        
    except Exception as e:
        print(f"Error obteniendo stats: {e}")
        return None


async def run_robot_async(team_name: str) -> Dict:
    """Ejecuta el robot para un equipo con Playwright."""
    print(f"Procesando: {team_name}")
    
    result = {
        'equipo': team_name,
        'encontrado': False,
        'exito': False,
        'lambda_local': None,
        'lambda_visitante': None
    }
    
    async with async_playwright() as p:
        # Lanzar navegador
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. Buscar equipo
            team_url = await search_team_fbref(page, team_name)
            
            if not team_url:
                print(f"  ❌ Equipo no encontrado")
                return result
            
            result['encontrado'] = True
            print(f"  ✓ Encontrado")
            
            # 2. Obtener estadisticas
            stats = await get_team_stats_fbref(page, team_url)
            
            if not stats:
                print(f"  ⚠️ Sin estadisticas")
                return result
            
            print(f"  📊 Stats: {stats}")
            
            # 3. Calcular lambda
            if stats.get('xg'):
                value = stats['xg']
            elif stats.get('goles'):
                value = stats['goles']
            else:
                print(f"  ⚠️ Sin datos de goles/xG")
                return result
            
            lambda_local = round(value * 1.1, 2)
            lambda_visitante = round(value * 0.85, 2)
            
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
            
            client.table('estadisticas_equipos').upsert(data, on_conflict='equipo').execute()
            result['exito'] = True
            print(f"  ✅ Guardado - λL:{lambda_local} λV:{lambda_visitante}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        finally:
            await browser.close()
    
    return result


def run_robot_for_team(team_name: str) -> Dict:
    """Funcion wrapper sincrona."""
    return asyncio.run(run_robot_async(team_name))


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """Ejecuta el robot para una lista de equipos."""
    results = []
    
    for i, team in enumerate(team_names):
        print(f"\n[{i+1}/{len(team_names)}] {team}")
        result = run_robot_for_team(team)
        results.append(result)
        time.sleep(1)  # Pausa entre equipos
    
    return results


# Prueba
if __name__ == "__main__":
    result = run_robot_for_team("Barcelona")
    print(result)
