#!/usr/bin/env python3
"""
Scraper Simple - Scorpion Elite
Extrae partidos de las 10 ligas principales
Rápido (~2-3 minutos)
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
from supabase import create_client
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KE = os.environ.get("SUPABASE_KE", "")

# LAS 10 LIGAS PRINCIPALES
LIGAS_POR_PAIS = {
    "Champions League": "https://www.flashscore.com/football/uefa-champions-league/",
    "Premier League": "https://www.flashscore.com/football/england/premier-league/",
    "LaLiga": "https://www.flashscore.com/football/spain/laliga/",
    "Serie A": "https://www.flashscore.com/football/italy/serie-a/",
    "Bundesliga": "https://www.flashscore.com/football/germany/bundesliga/",
    "Ligue 1": "https://www.flashscore.com/football/france/ligue-1/",
    "Liga MX": "https://www.flashscore.com/football/mexico/liga-mx/",
    "MLS": "https://www.flashscore.com/football/usa/mls/",
    "Copa Libertadores": "https://www.flashscore.com/football/south-america/copa-libertadores/",
    "Brasileirão Série A": "https://www.flashscore.com/football/brazil/serie-a/",
}


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KE:
        print("⚠️  Supabase no configurado - Modo demo")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KE)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return None


async def scrape_liga(page, liga_nombre, url, fecha):
    """Extrae partidos de una liga específica"""
    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=15000)
        await asyncio.sleep(1)
        
        # Scroll rápido
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(0.3)
        
        # Extraer partidos
        data = await page.evaluate("""
            () => {
                const matches = [];
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
                        
                        if (home && away) {
                            matches.push({ time: time || '00:00', home, away });
                        }
                    } catch(e) {}
                });
                
                return matches;
            }
        """)
        
        return data
        
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return []


async def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER RÁPIDO")
    print("=" * 60)
    
    # Zona horaria de Colombia (UTC-5)
    COLOMBIA_TZ = timezone(timedelta(hours=-5))
    now_colombia = datetime.now(COLOMBIA_TZ)
    today = now_colombia.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha = today.strftime("%Y-%m-%d")
    
    print(f"\n📅 Fecha Colombia: {fecha}")
    print(f"⏰ Hora: {now_colombia.strftime('%H:%M')} Colombia\n")
    
    all_partidos = []
    seen = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        for liga_nombre, url in LIGAS_POR_PAIS.items():
            print(f"🔍 {liga_nombre}...")
            matches = await scrape_liga(page, liga_nombre, url, fecha)
            
            count = 0
            for item in matches:
                key = f"{item['home']}{item['away']}{liga_nombre}{fecha}"
                
                if key not in seen:
                    seen.add(key)
                    match_id = hash(key) % 10000000
                    
                    partido = {
                        "fixture_id": match_id,
                        "fecha": fecha,
                        "hora": item['time'],
                        "liga": liga_nombre,
                        "equipo_local": item['home'],
                        "equipo_visitante": item['away'],
                    }
                    
                    all_partidos.append(partido)
                    print(f"   ⚽ {item['home']} vs {item['away']}")
                    count += 1
            
            print(f"   ✅ {count} partidos\n")
        
        await browser.close()
    
    print(f"📊 Total: {len(all_partidos)} partidos de {len(LIGAS_POR_PAIS)} ligas")
    
    # Guardar en Supabase
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
        print("\n⚠️  Modo demo")
        with open("partidos_debug.json", "w", encoding="utf-8") as f:
            json.dump(all_partidos, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
