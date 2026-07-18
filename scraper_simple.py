#!/usr/bin/env python3
"""
Scorpion Elite - Scraper
Usa API-Football como fuente principal, con fallback a scraping
"""

import os
import json
from datetime import datetime, timedelta, timezone
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KE = os.environ.get("SUPABASE_KE", "")

# APIs disponibles
API_FOOTBALL_KEYS = [
    os.environ.get("API_FOOTBALL_KEY", ""),
    "e3926f829cd848f4b2b54d722ca29701",
    "124c9519df145caf883cd82f0b2a4671"
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


def get_partidos_api_football(api_key, fecha):
    """Obtiene partidos de API-Football"""
    import requests
    
    url = "https://v3.football.api-sports.io/fixtures"
    
    headers = {
        'x-apisports-key': api_key
    }
    
    params = {
        'date': fecha,
        'league': '1,2,3,4,5,10,11,12,13,14,15,16,17,18,20,21,22,23,24,30,31,32,33,34,39,40,41,42,43,44,45,46,47,48,61,62,71,72,81,82,88,89,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250',
        'season': '2024'
    }
    
    print(f"📡 Consultando API-Football para {fecha}...")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        
        if data.get('results', 0) > 0:
            return data['response']
        return []
    except Exception as e:
        print(f"❌ Error API: {e}")
        return []


def main():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER")
    print("=" * 60)
    
    fecha_hoy = get_fecha_colombia()
    print(f"\n📅 Fecha Colombia: {fecha_hoy}\n")
    
    all_partidos = []
    seen = set()
    
    # Intentar con API-Football
    for api_key in API_FOOTBALL_KEYS:
        if not api_key:
            continue
            
        fixtures = get_partidos_api_football(api_key, fecha_hoy)
        
        if fixtures:
            print(f"📊 Partidos de API: {len(fixtures)}")
            
            for fixture in fixtures:
                try:
                    league = fixture.get('league', {})
                    teams = fixture.get('teams', {})
                    goals = fixture.get('goals', {})
                    fixture_info = fixture.get('fixture', {})
                    
                    liga_nombre = league.get('name', 'Unknown')
                    home_name = teams.get('home', {}).get('name', '')
                    away_name = teams.get('away', {}).get('name', '')
                    time_str = fixture_info.get('timestamp', 0)
                    
                    if time_str:
                        hora = datetime.fromtimestamp(time_str).strftime('%H:%M')
                    else:
                        hora = '00:00'
                    
                    # Filtrar solo ligas principales
                    ligas_deseadas = [
                        'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
                        'Liga MX', 'MLS', 'Champions League', 'Libertadores', 'Copa',
                        'Serie B', '2. Bundesliga', 'Championship', 'BetPlay', 'Brasileirão',
                        'Primera Division', 'Jupiler', 'Primeira Liga', 'Eredivisie', 'J1 League'
                    ]
                    
                    es_deseada = any(l.lower() in liga_nombre.lower() for l in ligas_deseadas)
                    
                    if not es_deseada:
                        continue
                    
                    # Limpiar nombre de liga
                    if 'Premier' in liga_nombre:
                        liga_nombre = "Premier League"
                    elif 'La Liga' in liga_nombre or 'LALIGA' in liga_nombre.upper():
                        liga_nombre = "LaLiga"
                    elif 'Serie A' in liga_nombre:
                        liga_nombre = "Serie A"
                    elif 'Bundesliga' in liga_nombre:
                        liga_nombre = "Bundesliga"
                    elif 'Ligue 1' in liga_nombre:
                        liga_nombre = "Ligue 1"
                    elif 'Liga MX' in liga_nombre or 'MX' in liga_nombre:
                        liga_nombre = "Liga MX"
                    elif 'MLS' in liga_nombre:
                        liga_nombre = "MLS"
                    elif 'Champions League' in liga_nombre:
                        liga_nombre = "Champions League"
                    elif 'Libertadores' in liga_nombre:
                        liga_nombre = "Copa Libertadores"
                    elif 'Serie B' in liga_nombre:
                        liga_nombre = "Serie B"
                    elif '2. Bundesliga' in liga_nombre:
                        liga_nombre = "2. Bundesliga"
                    elif 'Championship' in liga_nombre:
                        liga_nombre = "EFL Championship"
                    elif 'BetPlay' in liga_nombre:
                        liga_nombre = "Liga BetPlay Dimayor"
                    elif 'Brasileirão' in liga_nombre:
                        if 'Série B' in liga_nombre:
                            liga_nombre = "Brasileirão Série B"
                        else:
                            liga_nombre = "Brasileirão Série A"
                    elif 'Primera' in liga_nombre and 'Division' in liga_nombre:
                        liga_nombre = "Liga Profesional Argentina"
                    elif 'Jupiler' in liga_nombre:
                        liga_nombre = "Jupiler Pro League"
                    elif 'Primeira' in liga_nombre:
                        liga_nombre = "Primeira Liga"
                    elif 'Eredivisie' in liga_nombre:
                        liga_nombre = "Eredivisie"
                    elif 'J1' in liga_nombre:
                        liga_nombre = "J1 League"
                    
                    key = f"{home_name}{away_name}{liga_nombre}{fecha_hoy}"
                    
                    if key not in seen and home_name and away_name:
                        seen.add(key)
                        match_id = hash(key) % 10000000
                        
                        partido = {
                            "fixture_id": match_id,
                            "fecha": fecha_hoy,
                            "hora": hora,
                            "liga": liga_nombre,
                            "equipo_local": home_name,
                            "equipo_visitante": away_name,
                        }
                        
                        all_partidos.append(partido)
                        print(f"   ⚽ {home_name} vs {away_name} ({liga_nombre})")
                        
                except Exception as e:
                    continue
            
            if all_partidos:
                break  # Si tenemos datos, paramos
    
    print(f"\n📊 Total partidos: {len(all_partidos)}")
    
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
    else:
        print("\n⚠️  No se encontraron partidos")
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
