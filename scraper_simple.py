#!/usr/bin/env python3
"""
Scraper Simple - Scorpion Elite
Extrae partidos de HOY de la página principal
Solo los partidos visibles inicialmente (los de hoy)
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright
from supabase import create_client
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KE = os.environ.get("SUPABASE_KE", "")

# LAS 28 LIGAS
LIGAS_DESEADAS = [
    "champions league", "copa libertadores", "europa league", "premier league", 
    "laliga", "la liga", "serie a", "bundesliga", "ligue 1", "liga mx", 
    "mls", "brasileirao", "championship", "segunda division", "serie b",
    "2. bundesliga", "ligue 2", "liga aguila", "primera b", "primera division",
    "primera nacional", "j league", "eredivisie", "jupiler", "primeira"
]


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


def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER")
    print("=" * 60)
    
    fecha_hoy = get_fecha_colombia()
    print(f"\n📅 Fecha Colombia: {fecha_hoy}\n")
    
    all_partidos = []
    seen = set()
    
    async def scrape():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            print("📡 Conectando a Flashscore...")
            await page.goto("https://www.flashscore.com/football/", timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Solo hacer scroll inicial - NO cargar todo
            print("📜 Cargando partidos...")
            await asyncio.sleep(3)
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1)
            
            # Extraer partidos - los primeros que aparecen son los de HOY
            print("🔍 Extrayendo partidos de HOY...")
            
            data = await page.evaluate("""
                () => {
                    const matches = [];
                    const sections = document.querySelectorAll('.event__match');
                    
                    sections.forEach(section => {
                        try {
                            // Hora
                            const timeEl = section.querySelector('.event__time');
                            let hora = timeEl ? timeEl.textContent.replace(/\\n/g, '').trim() : '00:00';
                            hora = hora.replace('FRO', '').trim();
                            
                            // Equipos
                            const homeEl = section.querySelector('.event__homeParticipant');
                            const awayEl = section.querySelector('.event__awayParticipant');
                            const home = homeEl ? homeEl.textContent.trim() : '';
                            const away = awayEl ? awayEl.textContent.trim() : '';
                            
                            // Liga - buscar en headers cercanos
                            let liga = '';
                            let prev = section.previousElementSibling;
                            for (let i = 0; i < 10 && prev; i++) {
                                const titleEl = prev.querySelector('.event__title');
                                if (titleEl) {
                                    liga = titleEl.textContent.trim();
                                    break;
                                }
                                prev = prev.previousElementSibling;
                            }
                            
                            if (home && away && home !== away && liga) {
                                matches.push({ hora, home, away, liga });
                            }
                        } catch(e) {}
                    });
                    
                    return matches;
                }
            """)
            
            await browser.close()
            return data
    
    matches = asyncio.run(scrape())
    print(f"\n📊 Partidos encontrados: {len(matches)}")
    
    # Filtrar solo las ligas deseadas
    for item in matches:
        liga_lower = item['liga'].lower()
        
        # Verificar si es liga deseada
        es_deseada = any(l in liga_lower for l in LIGAS_DESEADAS)
        
        if not es_deseada:
            continue
        
        # Limpiar nombre de liga
        liga_nombre = item['liga']
        if 'champions' in liga_lower:
            liga_nombre = "Champions League"
        elif 'libertadores' in liga_lower:
            liga_nombre = "Copa Libertadores"
        elif 'europa' in liga_lower:
            liga_nombre = "UEFA Europa League"
        elif 'premier' in liga_lower:
            liga_nombre = "Premier League"
        elif 'laliga' in liga_lower or ('la' in liga_lower and 'liga' in liga_lower):
            liga_nombre = "LaLiga"
        elif 'serie a' in liga_lower:
            liga_nombre = "Serie A"
        elif 'bundesliga' in liga_lower:
            if '2.' in liga_lower:
                liga_nombre = "2. Bundesliga"
            else:
                liga_nombre = "Bundesliga"
        elif 'ligue 1' in liga_lower or ('ligue' in liga_lower and '1' in item['liga']):
            liga_nombre = "Ligue 1"
        elif 'ligue 2' in liga_lower:
            liga_nombre = "Ligue 2"
        elif 'liga mx' in liga_lower or 'mx' in liga_lower:
            liga_nombre = "Liga MX"
        elif 'mls' in liga_lower or 'major' in liga_lower:
            liga_nombre = "MLS"
        elif 'brasileirao' in liga_lower:
            if 'b' in liga_lower and 'serie' in liga_lower:
                liga_nombre = "Brasileirão Série B"
            else:
                liga_nombre = "Brasileirão Série A"
        elif 'championship' in liga_lower:
            liga_nombre = "EFL Championship"
        elif 'segunda' in liga_lower:
            liga_nombre = "LaLiga 2"
        elif 'serie b' in liga_lower:
            liga_nombre = "Serie B"
        elif 'liga aguila' in liga_lower:
            liga_nombre = "Liga BetPlay Dimayor"
        elif 'primera b' in liga_lower:
            liga_nombre = "Torneo BetPlay Dimayor"
        elif 'primera nacional' in liga_lower:
            liga_nombre = "Primera Nacional"
        elif 'primera division' in liga_lower:
            liga_nombre = "Liga Profesional Argentina"
        elif 'j league' in liga_lower:
            liga_nombre = "J1 League"
        elif 'eredivisie' in liga_lower:
            liga_nombre = "Eredivisie"
        elif 'jupiler' in liga_lower:
            liga_nombre = "Jupiler Pro League"
        elif 'primeira' in liga_lower:
            liga_nombre = "Primeira Liga"
        
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
    
    print(f"\n📊 Total partidos de HOY: {len(all_partidos)}")
    
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
    main()
