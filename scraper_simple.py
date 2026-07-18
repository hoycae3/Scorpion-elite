#!/usr/bin/env python3
"""
Scraper Simple - Scorpion Elite
Extrae partidos de las 28 ligas para HOY
Captura la fecha correcta de cada partido desde Flashscore
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
from supabase import create_client
import json
import re

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KE = os.environ.get("SUPABASE_KE", "")

# LAS 28 LIGAS
LIGAS_POR_PAIS = {
    "Champions League": "https://www.flashscore.com/football/uefa-champions-league/",
    "Copa Libertadores": "https://www.flashscore.com/football/south-america/copa-libertadores/",
    "Premier League": "https://www.flashscore.com/football/england/premier-league/",
    "LaLiga": "https://www.flashscore.com/football/spain/laliga/",
    "Serie A": "https://www.flashscore.com/football/italy/serie-a/",
    "Bundesliga": "https://www.flashscore.com/football/germany/bundesliga/",
    "Ligue 1": "https://www.flashscore.com/football/france/ligue-1/",
    "Liga MX": "https://www.flashscore.com/football/mexico/liga-mx/",
    "MLS": "https://www.flashscore.com/football/usa/mls/",
    "Brasileirão Série A": "https://www.flashscore.com/football/brazil/serie-a/",
    "EFL Championship": "https://www.flashscore.com/football/england/championship/",
    "LaLiga 2": "https://www.flashscore.com/football/spain/laliga-2/",
    "Serie B": "https://www.flashscore.com/football/italy/serie-b/",
    "2. Bundesliga": "https://www.flashscore.com/football/germany/2-bundesliga/",
    "Ligue 2": "https://www.flashscore.com/football/france/ligue-2/",
    "Liga BetPlay Dimayor": "https://www.flashscore.com/football/colombia/liga-aguila/",
    "Torneo BetPlay Dimayor": "https://www.flashscore.com/football/colombia/primera-b/",
    "Brasileirão Série B": "https://www.flashscore.com/football/brazil/serie-b/",
    "Liga Profesional Argentina": "https://www.flashscore.com/football/argentina/primera-division/",
    "Primera Nacional": "https://www.flashscore.com/football/argentina/primera-nacional/",
    "J1 League": "https://www.flashscore.com/football/japan/j-league/",
    "Eredivisie": "https://www.flashscore.com/football/netherlands/eredivisie/",
    "Jupiler Pro League": "https://www.flashscore.com/football/belgium/jupiler-pro-league/",
    "Primeira Liga": "https://www.flashscore.com/football/portugal/primeira-liga/",
    "UEFA Europa League": "https://www.flashscore.com/football/uefa-europa-league/",
    "Copa Libertadores": "https://www.flashscore.com/football/south-america/copa-libertadores/",
    "Copa Sudamericana": "https://www.flashscore.com/football/south-america/copa-sudamericana/",
    "UEFA Nations League": "https://www.flashscore.com/football/uefa-nations-league/",
}


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KE:
        print("⚠️  Supabase no configurado")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KE)
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def get_fecha_colombia():
    """Obtiene la fecha actual en Colombia"""
    COLOMBIA_TZ = timezone(timedelta(hours=-5))
    return datetime.now(COLOMBIA_TZ).strftime("%Y-%m-%d")


async def scrape_pagina_principal():
    """Scrapea TODOS los partidos de la página principal de Flashscore"""
    all_matches = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("📡 Conectando a Flashscore...")
        await page.goto("https://www.flashscore.com/football/", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        # Scroll para cargar todo
        print("📜 Cargando partidos...")
        for i in range(15):
            await page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(0.3)
        
        # Extraer TODOS los partidos con su fecha
        print("🔍 Extrayendo partidos...")
        
        data = await page.evaluate("""
            () => {
                const matches = [];
                // Buscar todas las secciones de eventos
                const sections = document.querySelectorAll('[id^="g_"]');
                
                sections.forEach(section => {
                    try {
                        // Obtener la fecha de esta sección
                        const dateEl = section.closest('.sports-book')?.querySelector('.event__date') 
                                     || section.querySelector('.event__date');
                        let fecha = '';
                        if (dateEl) {
                            fecha = dateEl.textContent.trim();
                        }
                        
                        // Obtener hora
                        const timeEl = section.querySelector('.event__time');
                        let hora = timeEl ? timeEl.textContent.replace(/\\n/g, '').trim() : '00:00';
                        hora = hora.replace('FRO', '').trim();
                        
                        // Obtener equipos
                        const homeEl = section.querySelector('.event__homeParticipant');
                        const awayEl = section.querySelector('.event__awayParticipant');
                        const home = homeEl ? homeEl.textContent.trim() : '';
                        const away = awayEl ? awayEl.textContent.trim() : '';
                        
                        // Obtener liga
                        let liga = '';
                        let header = section.previousElementSibling;
                        while (header) {
                            const titleEl = header.querySelector('.headerLeague__title');
                            if (titleEl) {
                                liga = titleEl.textContent.trim();
                                break;
                            }
                            header = header.previousElementSibling;
                        }
                        
                        if (home && away && home !== away) {
                            matches.push({ fecha, hora, home, away, liga });
                        }
                    } catch(e) {}
                });
                
                return matches;
            }
        """)
        
        await browser.close()
        all_matches = data
    
    return all_matches


def parsear_fecha_flashscore(fecha_str, year=2026):
    """Convierte fecha de Flashscore a YYYY-MM-DD"""
    meses = {
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
    }
    
    fecha_str = fecha_str.lower().strip()
    
    # Buscar patrón: día + mes (ej: "18 jul" o "18 de jul")
    match = re.search(r'(\d+)\s*(?:de\s*)?(\w+)', fecha_str)
    if match:
        dia = int(match.group(1))
        mes_str = match.group(2)[:3]
        mes = meses.get(mes_str, 7)
        return f"{year}-{mes:02d}-{dia:02d}"
    
    return None


def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER")
    print("=" * 60)
    
    fecha_hoy = get_fecha_colombia()
    print(f"\n📅 Fecha Colombia: {fecha_hoy}\n")
    
    # Ejecutar el scrape
    matches = asyncio.run(scrape_pagina_principal())
    
    print(f"\n📊 Partidos encontrados en Flashscore: {len(matches)}")
    
    # Filtrar solo partidos de HOY y de las ligas deseadas
    all_partidos = []
    seen = set()
    
    ligas_deseadas = list(LIGAS_POR_PAIS.keys())
    
    print(f"\n🔍 Filtrando partidos de las 28 ligas para {fecha_hoy}...\n")
    
    for item in matches:
        fecha_parseada = parsear_fecha_flashscore(item['fecha'])
        
        # Solo partidos de hoy
        if fecha_parseada != fecha_hoy:
            continue
        
        liga = item['liga']
        
        # Verificar si es una liga deseada
        es_deseada = any(l.lower() in liga.lower() or liga.lower() in l.lower() 
                        for l in ligas_deseadas)
        
        if not es_deseada:
            continue
        
        # Determinar nombre correcto de la liga
        liga_nombre = liga
        for nombre, url in LIGAS_POR_PAIS.items():
            if nombre.lower() in liga.lower() or liga.lower() in nombre.lower():
                liga_nombre = nombre
                break
        
        key = f"{item['home']}{item['away']}{liga_nombre}{fecha_hoy}"
        
        if key not in seen:
            seen.add(key)
            match_id = hash(key) % 10000000
            
            partido = {
                "fixture_id": match_id,
                "fecha": fecha_hoy,
                "hora": item['hora'] or '00:00',
                "liga": liga_nombre,
                "equipo_local": item['home'],
                "equipo_visitante": item['away'],
            }
            
            all_partidos.append(partido)
            print(f"   ⚽ {item['home']} vs {item['away']} ({liga_nombre})")
    
    print(f"\n📊 Total partidos de HOY ({fecha_hoy}): {len(all_partidos)}")
    
    # Guardar en Supabase
    if all_partidos:
        supabase = get_supabase_client()
        if supabase:
            try:
                print("\n🗑️ Limpiando tabla...")
                supabase.table("partidos").delete().neq("id", 0).execute()
                
                guardados = 0
                for partido in all_partidos:
                    try:
                        supabase.table("partidos").upsert(partido, on_conflict="fixture_id").execute()
                        guardados += 1
                    except:
                        pass
                
                print(f"✅ {guardados} partidos guardados en Supabase")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            with open("partidos_debug.json", "w", encoding="utf-8") as f:
                json.dump(all_partidos, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
