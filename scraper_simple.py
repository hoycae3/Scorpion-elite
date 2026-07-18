#!/usr/bin/env python3
"""
Scraper Simple - Scorpion Elite
Solo extrae las 28 ligas principales
Captura la fecha correcta de cada partido
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

# LAS 28 LIGAS CON SUS PÁGINAS EN FLASSSCORE
LIGAS_POR_PAIS = {
    "Champions League": "https://www.flashscore.com/football/uefa-champions-league/",
    "Copa Libertadores": "https://www.flashscore.com/football/south-america/copa-libertadores/",
    "UEFA Europa League": "https://www.flashscore.com/football/uefa-europa-league/",
    "Premier League": "https://www.flashscore.com/football/england/premier-league/",
    "EFL Championship": "https://www.flashscore.com/football/england/championship/",
    "LaLiga": "https://www.flashscore.com/football/spain/laliga/",
    "LaLiga 2": "https://www.flashscore.com/football/spain/laliga-2/",
    "Serie A": "https://www.flashscore.com/football/italy/serie-a/",
    "Serie B": "https://www.flashscore.com/football/italy/serie-b/",
    "Bundesliga": "https://www.flashscore.com/football/germany/bundesliga/",
    "2. Bundesliga": "https://www.flashscore.com/football/germany/2-bundesliga/",
    "Ligue 1": "https://www.flashscore.com/football/france/ligue-1/",
    "Ligue 2": "https://www.flashscore.com/football/france/ligue-2/",
    "Liga BetPlay Dimayor": "https://www.flashscore.com/football/colombia/liga-aguila/",
    "Torneo BetPlay Dimayor": "https://www.flashscore.com/football/colombia/primera-b/",
    "Brasileirão Série A": "https://www.flashscore.com/football/brazil/serie-a/",
    "Brasileirão Série B": "https://www.flashscore.com/football/brazil/serie-b/",
    "Liga Profesional Argentina": "https://www.flashscore.com/football/argentina/primera-division/",
    "Primera Nacional": "https://www.flashscore.com/football/argentina/primera-nacional/",
    "Liga MX": "https://www.flashscore.com/football/mexico/liga-mx/",
    "MLS": "https://www.flashscore.com/football/usa/mls/",
    "J1 League": "https://www.flashscore.com/football/japan/j-league/",
    "Eredivisie": "https://www.flashscore.com/football/netherlands/eredivisie/",
    "Jupiler Pro League": "https://www.flashscore.com/football/belgium/jupiler-pro-league/",
    "Primeira Liga": "https://www.flashscore.com/football/portugal/primeira-liga/",
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


async def scrape_liga(page, liga_nombre, url, fecha_base, year):
    """Extrae partidos de una liga específica capturando la fecha correcta"""
    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        await asyncio.sleep(3)
        
        # Scroll para cargar más partidos
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1500)")
            await asyncio.sleep(1)
        
        # Extraer partidos con la fecha del evento
        data = await page.evaluate(f"""
            () => {{
                const matches = [];
                const events = document.querySelectorAll('.event__match');
                
                events.forEach(event => {{
                    try {{
                        const timeEl = event.querySelector('.event__time');
                        let time = timeEl ? timeEl.textContent.replace(/\\n/g, ' ').trim() : '';
                        time = time.replace('FRO', '').trim();
                        
                        const homeEl = event.querySelector('.event__homeParticipant');
                        const awayEl = event.querySelector('.event__awayParticipant');
                        
                        const home = homeEl ? homeEl.textContent.trim() : '';
                        const away = awayEl ? awayEl.textContent.trim() : '';
                        
                        // Buscar la fecha en el header de la sección
                        let dayNum = '';
                        let prev = event.previousElementSibling;
                        for (let i = 0; i < 5 && prev; i++) {{
                            const dateEl = prev.querySelector('.event__date');
                            if (dateEl) {{
                                const text = dateEl.textContent;
                                const match = text.match(/(\\d+)/);
                                if (match) dayNum = match[1];
                                break;
                            }}
                            prev = prev.previousElementSibling;
                        }}
                        
                        if (home && away) {{
                            matches.push({{ 
                                time: time || '00:00', 
                                home, 
                                away,
                                day: dayNum
                            }});
                        }}
                    }} catch(e) {{}}
                }});
                
                return matches;
            }}
        """)
        
        return data
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def parse_fecha(flashscore_date, year=2026):
    """Convierte fecha de Flashscore (ej: '18 jul') a formato YYYY-MM-DD"""
    meses = {
        'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
    }
    
    try:
        parts = flashscore_date.lower().split()
        if len(parts) >= 2:
            dia = int(parts[0])
            mes = meses.get(parts[1][:3], 7)  # Default julio
            return f"{year}-{mes:02d}-{dia:02d}"
    except:
        pass
    return None


async def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER (28 ligas)")
    print("=" * 60)
    
    Mexico_TZ = timezone(timedelta(hours=-6))
    now_mexico = datetime.now(Mexico_TZ)
    today = now_mexico.replace(hour=0, minute=0, second=0, microsecond=0)
    year = today.year
    
    print(f"\n📅 Fecha México: {today.strftime('%Y-%m-%d')}\n")
    
    all_partidos = []
    seen = set()  # Para evitar duplicados
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        for liga_nombre, url in LIGAS_POR_PAIS.items():
            print(f"\n🔍 {liga_nombre}...")
            matches = await scrape_liga(page, liga_nombre, url, today, year)
            
            for item in matches:
                # Generar fecha real
                if item.get('day'):
                    fecha = f"{year}-{now_mexico.month:02d}-{int(item['day']):02d}"
                else:
                    fecha = today.strftime("%Y-%m-%d")
                
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
                    print(f"   ⚽ {item['home']} vs {item['away']} ({fecha} {item['time']})")
            
            print(f"   ✅ {len(matches)} partidos")
        
        await browser.close()
    
    print(f"\n📊 Total: {len(all_partidos)} partidos")
    
    # Guardar
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
        print("\n⚠️  Modo demo - Guardando en archivo")
        with open("partidos_debug.json", "w", encoding="utf-8") as f:
            json.dump(all_partidos, f, indent=2, ensure_ascii=False)
        print("📁 Guardado en partidos_debug.json")
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
