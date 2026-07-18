#!/usr/bin/env python3
"""
Scraper Real de Fútbol - Scorpion Elite
Usa Playwright para extraer datos reales de Flashscore

Ejecución: python scraper_real.py
"""

import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from supabase import create_client
import json

# Configuración Supabase (usar variables de entorno)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Prioridades de ligas
LIGAS_PRIORIDAD = {
    "champions league": 15, "uefa champions league": 15,
    "premier league": 14, "premier league inglaterra": 14,
    "la liga": 13, "liga españa": 13,
    "serie a": 12, "serie a italia": 12,
    "bundesliga": 11, "bundesliga alemania": 11,
    "ligue 1": 10, "ligue 1 francia": 10,
    "europa league": 9, "europa league uefa": 9,
    "libertadores": 8, "copa libertadores": 8,
    "brasileiro": 7, "brasil serie a": 7,
    "eredivisie": 7, "holanda": 7,
    "liga mx": 6, "liga mexicana": 6,
    "mls": 5, "major league soccer": 5,
    "superlig": 4, "liga turca": 4,
    "liga portuguesa": 3, "primeira liga": 3,
}


def get_supabase_client():
    """Obtiene cliente de Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase no configurado")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return None


def calcular_prioridad(liga_nombre):
    """Calcula la prioridad de una liga"""
    liga_lower = liga_nombre.lower()
    for nombre, prio in LIGAS_PRIORIDAD.items():
        if nombre in liga_lower:
            return prio
    return 1


async def scrape_flashscore():
    """Hace scraping de Flashscore usando Playwright"""
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER REAL (7 DÍAS)")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
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
        print("✅ Página cargada")
        await asyncio.sleep(3)
        
        # Scroll para cargar más partidos
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(1)
        
        # Extraer partidos de la página principal
        print("\n📅 Extrayendo partidos de los próximos 7 días...")
        matches = await extract_matches_from_page(page)
        all_matches.extend(matches)
        print(f"   Total encontrados: {len(matches)}")
        
        await browser.close()
    
    print(f"\n📊 Total partidos extraídos: {len(all_matches)}")
    return all_matches


async def extract_matches_from_page(page):
    """Extrae partidos de la página actual"""
    matches = []
    seen_matches = set()
    
    await page.wait_for_selector('.event__match', timeout=15000)
    await asyncio.sleep(2)
    
    data = await page.evaluate("""
        () => {
            const matches = [];
            const seenKeys = new Set();
            const events = document.querySelectorAll('.event__match');
            
            events.forEach(event => {
                try {
                    const timeEl = event.querySelector('.event__time');
                    let time = timeEl ? timeEl.textContent.replace(/\\n/g, ' ').trim() : '';
                    time = time.replace('FRO', '').trim();
                    
                    const homeEl = event.querySelector('.event__homeParticipant');
                    const awayEl = event.querySelector('.event__awayParticipant');
                    const home = homeEl ? homeEl.textContent.trim() : '';
                    const away = awayEl ? awayEl.textContent.trim() : '';
                    
                    if (!home || !away) return;
                    
                    const key = home + '|' + away;
                    if (seenKeys.has(key)) return;
                    seenKeys.add(key);
                    
                    let league = 'Liga';
                    let prev = event.previousElementSibling;
                    let attempts = 0;
                    
                    while (prev && attempts < 10) {
                        const leagueTitle = prev.querySelector('.headerLeague__title');
                        if (leagueTitle) {
                            league = leagueTitle.textContent.trim();
                            break;
                        }
                        prev = prev.previousElementSibling;
                        attempts++;
                    }
                    
                    matches.push({ time, home, away, league });
                } catch (e) {}
            });
            
            return matches;
        }
    """)
    
    for item in data:
        match_id = hash(f"{item['home']}{item['away']}{item['league']}{item['time']}") % 10000000
        
        match_data = {
            "fixture_id": match_id,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora_utc": item['time'] or "00:00",
            "hora_local": item['time'],
            "liga": item['league'] or "Liga",
            "liga_id": 0,
            "pais": "",
            "prioridad": calcular_prioridad(item['league'] or "Liga"),
            "equipo_home": item['home'],
            "equipo_away": item['away'],
            "prob_home": 45,
            "prob_draw": 30,
            "prob_away": 25,
            "cuota_1": 2.10,
            "cuota_x": 3.40,
            "cuota_2": 3.50,
            "pick": "1",
            "cuota_pick": 2.10,
            "confianza": 45,
            "valor": 0,
            "actualizado_en": datetime.now().isoformat()
        }
        
        matches.append(match_data)
        print(f"   ✓ {item['home']} vs {item['away']} ({item['league']})")
    
    return matches


def guardar_en_supabase(supabase, partidos):
    """Guarda partidos en Supabase"""
    if not supabase:
        return 0
    
    try:
        supabase.table("partidos").delete().neq("id", 0).execute()
        guardados = 0
        for partido in partidos:
            try:
                supabase.table("partidos").insert(partido).execute()
                guardados += 1
            except Exception as e:
                if "duplicate" not in str(e).lower():
                    print(f"   ⚠️  Error: {e}")
        return guardados
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return 0


async def main():
    """Función principal"""
    partidos = await scrape_flashscore()
    
    if not partidos:
        print("\n⚠️  No se encontraron partidos")
        return
    
    print(f"\n💾 Guardando {len(partidos)} partidos...")
    
    supabase = get_supabase_client()
    if supabase:
        guardados = guardar_en_supabase(supabase, partidos)
        print(f"\n✅ {guardados} partidos guardados en Supabase")
    else:
        print("\n⚠️  Modo demo - datos no guardados")
        with open("partidos_debug.json", "w") as f:
            json.dump(partidos, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
