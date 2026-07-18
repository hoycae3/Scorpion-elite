#!/usr/bin/env python3
"""
Scorpion Elite - Scraper
Usa Playwright para hacer scraping de Flashscore
"""

import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KE = os.environ.get("SUPABASE_KE", "")

# LAS 28 LIGAS
LIGAS = {
    "Premier League": "https://www.flashscore.com/football/england/premier-league/",
    "LaLiga": "https://www.flashscore.com/football/spain/laliga/",
    "Serie A": "https://www.flashscore.com/football/italy/serie-a/",
    "Bundesliga": "https://www.flashscore.com/football/germany/bundesliga/",
    "Ligue 1": "https://www.flashscore.com/football/france/ligue-1/",
    "Liga MX": "https://www.flashscore.com/football/mexico/liga-mx/",
    "MLS": "https://www.flashscore.com/football/usa/mls/",
    "Champions League": "https://www.flashscore.com/football/uefa-champions-league/",
    "Copa Libertadores": "https://www.flashscore.com/football/south-america/copa-libertadores/",
    "Brasileirão Série A": "https://www.flashscore.com/football/brazil/serie-a/",
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


async def scrape_league(page, liga_nombre, url):
    """Scrapea partidos de una liga"""
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await asyncio.sleep(8)  # Esperar que carguen los eventos
        
        # Extraer partidos
        data = await page.evaluate("""
            () => {
                const matches = [];
                const events = document.querySelectorAll('.event__match');
                
                events.forEach(event => {
                    try {
                        const timeEl = event.querySelector('.event__time');
                        let time = timeEl ? timeEl.textContent.replace(/\\n/g, '').trim() : '00:00';
                        time = time.replace('FRO', '').trim();
                        
                        const homeEl = event.querySelector('.event__homeParticipant');
                        const awayEl = event.querySelector('.event__awayParticipant');
                        const home = homeEl ? homeEl.textContent.trim() : '';
                        const away = awayEl ? awayEl.textContent.trim() : '';
                        
                        if (home && away && home !== away) {
                            matches.push({ time, home, away });
                        }
                    } catch(e) {}
                });
                
                return matches;
            }
        """)
        
        return data
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


async def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER")
    print("=" * 60)
    
    fecha_hoy = get_fecha_colombia()
    print(f"\n📅 Fecha Colombia: {fecha_hoy}\n")
    
    all_partidos = []
    seen = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Bloquear scripts que pueden causar problemas
        await context.route("**/*analytics*", lambda route: route.abort())
        await context.route("**/*ads*", lambda route: route.abort())
        
        for liga_nombre, url in LIGAS.items():
            print(f"🔍 {liga_nombre}...")
            matches = await scrape_league(page, liga_nombre, url)
            
            count = 0
            for item in matches:
                key = f"{item['home']}{item['away']}{liga_nombre}{fecha_hoy}"
                
                if key not in seen:
                    seen.add(key)
                    match_id = hash(key) % 10000000
                    
                    partido = {
                        "fixture_id": match_id,
                        "fecha": fecha_hoy,
                        "hora": item['time'] or '00:00',
                        "liga": liga_nombre,
                        "equipo_local": item['home'],
                        "equipo_visitante": item['away'],
                    }
                    
                    all_partidos.append(partido)
                    print(f"   ⚽ {item['home']} vs {item['away']}")
                    count += 1
            
            print(f"   ✅ {count} partidos\n")
        
        await browser.close()
    
    print(f"📊 Total partidos: {len(all_partidos)}")
    
    # Guardar
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
    asyncio.run(main())
