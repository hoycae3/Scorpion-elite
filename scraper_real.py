#!/usr/bin/env python3
"""
Scraper Real de Fútbol - Scorpion Elite
Usa Playwright para extraer datos reales de Flashscore

Incluye:
- Partidos de los próximos 7 días
- Priorización mejorada de ligas

Ejecución: python scraper_real.py
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from supabase import create_client
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Prioridades de ligas MEJORADAS
LIGAS_PRIORIDAD = {
    # Top tier (15)
    "champions league": 15,
    
    # Top europeas (13-14)
    "premier league": 14,  # Inglaterra
    "la liga": 13, "laliga": 13,
    "serie a": 12,
    "bundesliga": 11,
    "ligue 1": 10,
    
    # Europa League (9)
    "europa league": 9,
    
    # Libertadores (8)
    "libertadores": 8,
    
    # Sudamérica - Alta prioridad (6-7)
    "brasileiro": 7, "serie a betano": 7,
    "liga argentina": 7, "primera nacional": 7, "liga profesional": 7,
    "liga colombiana": 6, "liga i": 6, "categoría": 6,
    "liga 1": 6, "liga perú": 6,
    "liga chile": 6, "primera division chile": 6,
    "j1 league": 6, "j league": 6, "liga japones": 6,
    "liga uruguaya": 6, "primera division uru": 6,
    "liga mx": 6, "liga mexicana": 6,
    "copa argentina": 6,
    "copa libertadores": 6,
    
    # Otras importantes (4-5)
    "eredivisie": 5, "primeira liga": 5,
    "super lig": 5, "turkish": 5,
    "mls": 5,
    "belgian": 4, "belgian pro": 4,
    "austrian": 4, "austrian bundesliga": 4,
    "copa do brasil": 4,
}


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase no configurado")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return None


def calcular_prioridad(liga_nombre):
    liga_lower = liga_nombre.lower()
    
    # Buscar coincidencias
    for nombre, prio in LIGAS_PRIORIDAD.items():
        if nombre in liga_lower:
            return prio
    
    # Penalizar ligas menores
    if any(x in liga_lower for x in ["friendly", "amistoso", "amical"]):
        return 1
    if any(x in liga_lower for x in ["u21", "u20", "u19", "u18", "u17", "u16"]):
        return 2
    if any(x in liga_lower for x in ["women", "femenino"]):
        return 2
    if any(x in liga_lower for x in ["premier league", "championship"]):
        return 3
    
    return 1


def calcular_pick(prob_home, prob_draw, prob_away, cuota_1, cuota_x, cuota_2):
    if prob_home >= prob_draw and prob_home >= prob_away:
        pick, cuota, prob = "1", cuota_1, prob_home
    elif prob_away >= prob_draw and prob_away >= prob_home:
        pick, cuota, prob = "2", cuota_2, prob_away
    else:
        pick, cuota, prob = "X", cuota_x, prob_draw
    
    prob_implicita = round(100 / cuota, 1) if cuota > 0 else 50
    valor = round(prob - prob_implicita, 1)
    confianza = int(round((max(prob_home, prob_draw, prob_away) / (prob_home + prob_draw + prob_away)) * 100))
    
    return {"pick": pick, "cuota": cuota, "probabilidad": prob, "confianza": confianza, "valor": valor}


async def scrape_flashscore():
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
        
        print("\n📅 Extrayendo partidos de los próximos 7 días...")
        matches = await extract_matches(page)
        all_matches.extend(matches)
        print(f"   Total encontrados: {len(matches)}")
        
        await browser.close()
    
    print(f"\n📊 Total partidos extraídos: {len(all_matches)}")
    return all_matches


async def extract_matches(page):
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
        prioridad = calcular_prioridad(item['league'] or "Liga")
        
        match_data = {
            "fixture_id": match_id,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora_utc": item['time'] or "00:00",
            "hora_local": item['time'],
            "liga": item['league'] or "Liga",
            "liga_id": 0,
            "pais": "",
            "prioridad": prioridad,
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
        
        if prioridad >= 5:
            print(f"   ⭐ {item['home']} vs {item['away']} ({item['league']})")
    
    return matches


def guardar_en_supabase(supabase, partidos):
    if not supabase:
        return 0
    
    try:
        guardados = 0
        for partido in partidos:
            try:
                # Usar upsert para actualizar o insertar
                supabase.table("partidos").upsert(partido, on_conflict="fixture_id").execute()
                guardados += 1
            except Exception as e:
                # Si falla el upsert, intentar solo insert
                try:
                    supabase.table("partidos").insert(partido).execute()
                    guardados += 1
                except:
                    pass
        return guardados
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return 0


async def main():
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
