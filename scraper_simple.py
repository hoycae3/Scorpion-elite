#!/usr/bin/env python3
"""
Scraper Simple - Scorpion Elite
Extrae partidos de la página principal de Flashscore
Rapido y eficiente
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
    "champions league", "copa libertadores", "europa league", "copa mundial", "copa america",
    "premier league", "championship", "laliga", "laliga 2", "serie a", "serie b",
    "bundesliga", "2. bundesliga", "ligue 1", "ligue 2", "liga aguila", "primera b",
    "brasileirao", "serie b brasil", "liga profesional", "primera nacional",
    "liga mx", "major league", "j league", "eredivisie", "belgian", "primeira liga"
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


async def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER RÁPIDO")
    print("=" * 60)
    
    # Zona horaria de Colombia (UTC-5)
    COLOMBIA_TZ = timezone(timedelta(hours=-5))
    now_colombia = datetime.now(COLOMBIA_TZ)
    today = now_colombia.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"\n📅 Fecha Colombia: {today.strftime('%Y-%m-%d')}")
    print(f"⏰ Hora actual: {now_colombia.strftime('%H:%M')} Colombia\n")
    
    all_partidos = []
    seen = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("📡 Conectando a Flashscore...")
        await page.goto("https://www.flashscore.com/football/", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        print("✅ Página cargada\n")
        
        # Scroll para cargar todos los partidos
        for i in range(10):
            await page.evaluate("window.scrollBy(0, 3000)")
            await asyncio.sleep(0.5)
        
        # Extraer todos los partidos de una vez
        print("🔍 Extrayendo partidos...")
        
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
                        
                        // Buscar nombre de liga
                        let league = '';
                        let prev = event.previousElementSibling;
                        for (let i = 0; i < 5 && prev; i++) {
                            const title = prev.querySelector('.headerLeague__title');
                            if (title) {
                                league = title.textContent.trim().toLowerCase();
                                break;
                            }
                            prev = prev.previousElementSibling;
                        }
                        
                        if (home && away) {
                            matches.push({ time: time || '00:00', home, away, league });
                        }
                    } catch(e) {}
                });
                
                return matches;
            }
        """)
        
        print(f"📊 Partidos encontrados: {len(data)}\n")
        
        # Filtrar solo las ligas que queremos
        for item in data:
            liga_lower = item['league'].lower()
            
            # Verificar si es una liga deseada
            es_deseada = any(l in liga_lower for l in LIGAS_DESEADAS)
            
            if es_deseada:
                # Determinar nombre limpio de la liga
                liga_nombre = item['league']
                if 'champions' in liga_lower:
                    liga_nombre = "Champions League"
                elif 'libertadores' in liga_lower:
                    liga_nombre = "Copa Libertadores"
                elif 'europa' in liga_lower:
                    liga_nombre = "UEFA Europa League"
                elif 'premier' in liga_lower:
                    liga_nombre = "Premier League"
                elif 'championship' in liga_lower:
                    liga_nombre = "EFL Championship"
                elif 'laliga' in liga_lower or 'liga' in liga_lower and 'españa' in liga_lower:
                    liga_nombre = "LaLiga"
                elif 'laliga 2' in liga_lower or 'segunda' in liga_lower:
                    liga_nombre = "LaLiga 2"
                elif 'serie a' in liga_lower:
                    liga_nombre = "Serie A"
                elif 'serie b' in liga_lower:
                    liga_nombre = "Serie B"
                elif 'bundesliga' in liga_lower:
                    if '2.' in liga_lower or '2a' in liga_lower:
                        liga_nombre = "2. Bundesliga"
                    else:
                        liga_nombre = "Bundesliga"
                elif 'ligue 1' in liga_lower or 'liga 1' in liga_lower:
                    liga_nombre = "Ligue 1"
                elif 'ligue 2' in liga_lower:
                    liga_nombre = "Ligue 2"
                elif 'liga aguila' in liga_lower:
                    liga_nombre = "Liga BetPlay Dimayor"
                elif 'primera b' in liga_lower:
                    liga_nombre = "Torneo BetPlay Dimayor"
                elif 'brasileirao' in liga_lower or 'brasil' in liga_lower:
                    if 'serie b' in liga_lower:
                        liga_nombre = "Brasileirão Série B"
                    else:
                        liga_nombre = "Brasileirão Série A"
                elif 'liga profesional' in liga_lower:
                    liga_nombre = "Liga Profesional Argentina"
                elif 'primera nacional' in liga_lower:
                    liga_nombre = "Primera Nacional"
                elif 'liga mx' in liga_lower:
                    liga_nombre = "Liga MX"
                elif 'major league' in liga_lower:
                    liga_nombre = "MLS"
                elif 'j league' in liga_lower:
                    liga_nombre = "J1 League"
                elif 'eredivisie' in liga_lower:
                    liga_nombre = "Eredivisie"
                elif 'belgian' in liga_lower or 'jupiler' in liga_lower:
                    liga_nombre = "Jupiler Pro League"
                elif 'primeira' in liga_lower:
                    liga_nombre = "Primeira Liga"
                
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
                    print(f"   ⚽ {item['home']} vs {item['away']} ({liga_nombre})")
        
        await browser.close()
    
    print(f"\n📊 Total partidos de las 28 ligas: {len(all_partidos)}")
    
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
        print("\n⚠️  Modo demo - Guardando en archivo")
        with open("partidos_debug.json", "w", encoding="utf-8") as f:
            json.dump(all_partidos, f, indent=2, ensure_ascii=False)
        print("📁 Guardado en partidos_debug.json")
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
