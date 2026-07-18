#!/usr/bin/env python3
"""
Scraper Simple - Scorpion Elite
Solo extrae las 28 ligas principales
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
from supabase import create_client
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KE = os.environ.get("SUPABASE_KE", "")

# LAS 28 LIGAS QUE QUEREMOS
LIGAS_DESEADAS = [
    # Torneos Internacionales
    ("UEFA Champions League", ["champions league", "uefa champions"]),
    ("Copa Libertadores", ["copa libertadores", "libertadores"]),
    ("UEFA Europa League", ["europa league", "uefa europa"]),
    ("Copa Mundial FIFA", ["copa mundial", "world cup"]),
    ("Copa América", ["copa america"]),
    ("Eurocopa", ["eurocopa", "euro"]),
    
    # Inglaterra
    ("Premier League", ["premier league"]),
    ("EFL Championship", ["championship", "efl championship"]),
    
    # España
    ("LaLiga", ["laliga", "la liga", "liga española"]),
    ("LaLiga 2", ["laliga 2", "segunda division", "laliga hypermotion"]),
    
    # Italia
    ("Serie A", ["serie a"]),
    ("Serie B", ["serie b"]),
    
    # Alemania
    ("Bundesliga", ["bundesliga"]),
    ("2. Bundesliga", ["2. bundesliga", "bundesliga 2"]),
    
    # Francia
    ("Ligue 1", ["ligue 1", "liga 1 francia"]),
    ("Ligue 2", ["ligue 2"]),
    
    # Colombia
    ("Liga BetPlay Dimayor", ["liga colombia", "dimayor", "liga col"]),
    ("Torneo BetPlay Dimayor", ["categoria primera b", "primera b colombia"]),
    
    # Brasil
    ("Brasileirão Série A", ["brasileirao", "brasileirão"]),
    ("Brasileirão Série B", ["serie b brasil", "brasil serie b"]),
    
    # Argentina
    ("Liga Profesional Argentina", ["liga profesional", "liga argentina"]),
    ("Primera Nacional", ["primera nacional", "nacional argentina"]),
    
    # México
    ("Liga MX", ["liga mx", "liga mexicana", "liga mx apertura", "liga mx clausura"]),
    
    # USA
    ("MLS", ["major league", "mls soccer", "liga mayor"]),
    
    # Japón
    ("J1 League", ["j1 league", "j1 japón", "j league"]),
    
    # Holanda
    ("Eredivisie", ["eredivisie", "holanda primera"]),
    
    # Bélgica
    ("Jupiler Pro League", ["belgian pro", "jupiler", "belgica"]),
    
    # Portugal
    ("Primeira Liga", ["primeira liga", "liga portuguesa"]),
]


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KE:
        print("⚠️  Supabase no configurado - Modo demo")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KE)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return None


def get_liga_limpia(nombre_liga):
    """Retorna el nombre limpio de la liga si está en nuestra lista"""
    if not nombre_liga:
        return None
    
    nombre_lower = nombre_liga.lower()
    
    for nombre_limpio, keywords in LIGAS_DESEADAS:
        for keyword in keywords:
            if keyword in nombre_lower:
                return nombre_limpio
    return None


async def scrape_flashscore():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER (Solo 28 ligas)")
    print("=" * 60)
    
    all_matches = []
    Mexico_TZ = timezone(timedelta(hours=-6))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Obtener los próximos 7 días en hora de México
        now_mexico = datetime.now(Mexico_TZ)
        today = now_mexico.replace(hour=0, minute=0, second=0, microsecond=0)
        dates_to_scrape = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        
        print(f"📅 Buscando partidos para 7 días...\n")
        
        await page.goto("https://www.flashscore.com/football/", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        print("✅ Conectado a Flashscore")
        await asyncio.sleep(3)
        
        for date_str in dates_to_scrape:
            print(f"\n📅 {date_str}")
            try:
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, 2000)")
                    await asyncio.sleep(1)
                
                matches = await extract_matches(page, date_str)
                all_matches.extend(matches)
                print(f"   ✅ {len(matches)} partidos de las 28 ligas")
                
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
        
        await browser.close()
    
    return all_matches


async def extract_matches(page, date_str):
    """Extrae partidos de las ligas deseadas"""
    matches = []
    
    await page.wait_for_selector('.event__match', timeout=15000)
    await asyncio.sleep(2)
    
    data = await page.evaluate("""
        () => {
            const events = document.querySelectorAll('.event__match');
            const results = [];
            
            events.forEach(event => {
                try {
                    const timeEl = event.querySelector('.event__time');
                    let time = timeEl ? timeEl.textContent.replace(/\\n/g, ' ').trim() : '';
                    time = time.replace('FRO', '').trim();
                    
                    const homeEl = event.querySelector('.event__homeParticipant');
                    const awayEl = event.querySelector('.event__awayParticipant');
                    
                    let home = homeEl ? homeEl.textContent.trim() : '';
                    let away = awayEl ? awayEl.textContent.trim() : '';
                    
                    if (!home || !away) return;
                    
                    let league = '';
                    let prev = event.previousElementSibling;
                    for (let i = 0; i < 5 && prev; i++) {
                        const title = prev.querySelector('.headerLeague__title');
                        if (title) {
                            league = title.textContent.trim();
                            break;
                        }
                        prev = prev.previousElementSibling;
                    }
                    
                    results.push({ time, home, away, league });
                } catch(e) {}
            });
            
            return results;
        }
    """)
    
    for item in data:
        liga_limpia = get_liga_limpia(item['league'])
        
        if liga_limpia:
            match_id = hash(f"{item['home']}{item['away']}{liga_limpia}{date_str}") % 10000000
            
            partido = {
                "fixture_id": match_id,
                "fecha": date_str,
                "hora": item['time'] or "00:00",
                "liga": liga_limpia,
                "equipo_local": item['home'],
                "equipo_visitante": item['away'],
            }
            
            matches.append(partido)
            print(f"   ⚽ {item['home']} vs {item['away']} ({liga_limpia})")
    
    return matches


def guardar_en_supabase(supabase, partidos):
    if not supabase:
        return 0
    
    try:
        # Limpiar tabla
        print("🗑️ Limpiando tabla...")
        supabase.table("partidos").delete().neq("id", 0).execute()
        
        guardados = 0
        for partido in partidos:
            try:
                supabase.table("partidos").upsert(partido, on_conflict="fixture_id").execute()
                guardados += 1
            except:
                pass
        
        return guardados
    except Exception as e:
        print(f"❌ Error: {e}")
        return 0


async def main():
    partidos = await scrape_flashscore()
    
    if not partidos:
        print("\n⚠️  No se encontraron partidos")
        return
    
    print(f"\n📊 Total: {len(partidos)} partidos de las 28 ligas")
    
    supabase = get_supabase_client()
    if supabase:
        guardados = guardar_en_supabase(supabase, partidos)
        print(f"\n✅ {guardados} partidos guardados en Supabase")
    else:
        print("\n⚠️  Modo demo - Guardando en archivo")
        with open("partidos_debug.json", "w", encoding="utf-8") as f:
            json.dump(partidos, f, indent=2, ensure_ascii=False)
        print("📁 Guardado en partidos_debug.json")
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
