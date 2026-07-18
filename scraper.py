#!/usr/bin/env python3
"""
Scraper de partidos de fútbol - Scorpion Elite
Guarda datos en Supabase para consumo por la app de Streamlit

Ejecución: python scraper.py
"""

import requests
import os
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# API Keys de API-Football
API_KEYS = [
    "e3926f829cd848f4b2b54d722ca29701",
    "124c9519df145caf883cd82f0b2a4671",
]

# Configuración Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Prioridades de ligas
LIGAS_POR_ID = {
    71: 7,   # Serie A Brasil
    39: 14,  # Premier League
    140: 13, # La Liga
    135: 12, # Serie A Italia
    78: 11,  # Bundesliga
    61: 10,  # Ligue 1
    253: 5,  # MLS
    262: 6,  # Liga MX
}

LIGAS_PRIORIDAD = {
    "champions league": 15,
    "premier league": 14,
    "la liga": 13,
    "serie a": 12,
    "bundesliga": 11,
    "ligue 1": 10,
    "europa league": 9,
    "libertadores": 8,
    "brasileiro": 7,
    "brasil": 7,
    "eredivisie": 7,
    "liga mx": 6,
    "major league soccer": 5,
}


def get_supabase_client():
    """Obtiene cliente de Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase no configurado, usando modo demo")
        return None
    
    try:
        from supabase import create_client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        print("⚠️  supabase-py no instalado, usando modo demo")
        return None


def obtener_partidos_de_apis(fecha_str):
    """Obtiene partidos de todas las APIs disponibles"""
    all_partidos = []
    
    # API-Football
    for api_key in API_KEYS:
        try:
            url = f"https://v3.football.api-sports.io/fixtures?date={fecha_str}"
            headers = {"x-apisports-key": api_key}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("response"):
                    all_partidos.extend(data["response"])
                    print(f"  ✅ API-Football: {len(data['response'])} partidos")
        except Exception as e:
            print(f"  ❌ Error API-Football: {e}")
    
    # TheSportsDB (fallback)
    if not all_partidos:
        try:
            url = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"
            params = {"d": fecha_str}
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", []) or []
                
                for event in events:
                    if event.get("strSport") != "Soccer":
                        continue
                    
                    all_partidos.append({
                        "fixture": {
                            "id": event.get("idEvent", 0),
                            "date": event.get("dateEvent", "") + "T" + event.get("strTime", "00:00"),
                        },
                        "league": {
                            "id": 0,
                            "name": event.get("strLeague", "Liga"),
                            "country": ""
                        },
                        "teams": {
                            "home": {"id": 0, "name": event.get("strHomeTeam", "Local")},
                            "away": {"id": 0, "name": event.get("strAwayTeam", "Visita")}
                        }
                    })
                print(f"  ✅ TheSportsDB: {len(all_partidos)} partidos")
        except Exception as e:
            print(f"  ❌ Error TheSportsDB: {e}")
    
    # Flashscore (último fallback)
    if not all_partidos:
        try:
            url = "https://www.flashscore.com/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                events = soup.find_all('div', class_='event__match')
                
                for event in events[:10]:
                    try:
                        home = event.find('div', class_='event__homeParticipant')
                        away = event.find('div', class_='event__awayParticipant')
                        time = event.find('div', class_='event__time')
                        league = event.find_previous('div', class_='event__league')
                        
                        if home and away:
                            all_partidos.append({
                                "fixture": {
                                    "id": hash(home.text + away.text),
                                    "date": fecha_str + "T" + (time.text if time else "00:00"),
                                },
                                "league": {
                                    "id": 0,
                                    "name": league.text if league else "Liga",
                                    "country": ""
                                },
                                "teams": {
                                    "home": {"id": 0, "name": home.text.strip()},
                                    "away": {"id": 0, "name": away.text.strip()}
                                }
                            })
                print(f"  ✅ Flashscore: {len(all_partidos)} partidos")
        except Exception as e:
            print(f"  ❌ Error Flashscore: {e}")
    
    # Eliminar duplicados
    seen_ids = set()
    unique_partidos = []
    for p in all_partidos:
        fixture_id = p["fixture"]["id"]
        if fixture_id not in seen_ids:
            seen_ids.add(fixture_id)
            unique_partidos.append(p)
    
    return unique_partidos


def obtener_predicciones_y_cuotas(fixture_id, api_key):
    """Obtiene predicciones y cuotas de un partido"""
    predictions = {"prob_home": 50, "prob_draw": 30, "prob_away": 20}
    odds = {"cuota_1": 1.90, "cuota_x": 3.50, "cuota_2": 4.00}
    
    # Predictions
    try:
        url = f"https://v3.football.api-sports.io/predictions?fixture={fixture_id}"
        response = requests.get(url, headers={"x-apisports-key": api_key}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            pred_response = data.get("response", [])
            if pred_response:
                percent = pred_response[0].get("predictions", {}).get("percent", {})
                if percent:
                    predictions["prob_home"] = int(percent.get("home", "50%").replace("%", "") or 50)
                    predictions["prob_draw"] = int(percent.get("draw", "30%").replace("%", "") or 30)
                    predictions["prob_away"] = int(percent.get("away", "20%").replace("%", "") or 20)
    except:
        pass
    
    # Odds
    try:
        url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
        response = requests.get(url, headers={"x-apisports-key": api_key}, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            odds_response = data.get("response", [])
            if odds_response:
                bets = odds_response[0].get("bookmakers", [{}])[0].get("bets", [])
                
                for bet in bets:
                    if bet.get("name") == "Match Winner":
                        for v in bet.get("values", []):
                            if v.get("value") == "Home":
                                odds["cuota_1"] = float(v.get("odd", 1.90))
                            elif v.get("value") == "Draw":
                                odds["cuota_x"] = float(v.get("odd", 3.50))
                            elif v.get("value") == "Away":
                                odds["cuota_2"] = float(v.get("odd", 4.00))
    except:
        pass
    
    return predictions, odds


def calcular_pick(prob_home, prob_draw, prob_away, cuota_1, cuota_x, cuota_2):
    """Calcula el mejor pick basado en probabilidades y cuotas"""
    if prob_home >= prob_draw and prob_home >= prob_away:
        pick = "1"
        cuota = cuota_1
        prob = prob_home
    elif prob_away >= prob_draw and prob_away >= prob_home:
        pick = "2"
        cuota = cuota_2
        prob = prob_away
    else:
        pick = "X"
        cuota = cuota_x
        prob = prob_draw
    
    prob_implicita = round(100 / cuota, 1) if cuota > 0 else 50
    valor = round(prob - prob_implicita, 1)
    confianza = round((max(prob_home, prob_draw, prob_away) / (prob_home + prob_draw + prob_away)) * 100, 0)
    
    return {
        "pick": pick,
        "cuota": cuota,
        "probabilidad": prob,
        "confianza": confianza,
        "valor": valor
    }


def guardar_en_supabase(supabase, partidos_data):
    """Guarda partidos en Supabase"""
    if not supabase:
        return 0
    
    try:
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Eliminar partidos del día
        supabase.table("partidos").delete().eq("fecha", fecha_hoy).execute()
        
        # Insertar nuevos partidos
        for partido in partidos_data:
            supabase.table("partidos").insert(partido).execute()
        
        return len(partidos_data)
    except Exception as e:
        print(f"  ❌ Error guardando en Supabase: {e}")
        return 0


def run_scraper():
    """Ejecuta el scraping para 7 días"""
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER (7 DÍAS)")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Obtener cliente Supabase
    supabase = get_supabase_client()
    
    # Obtener fechas: hoy + 6 días siguientes
    dias_a_buscar = []
    for i in range(7):
        fecha = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        dias_a_buscar.append(fecha)
    
    print(f"📅 Fechas a procesar: {', '.join(dias_a_buscar)}")
    print()
    
    total_partidos = 0
    
    for fecha_str in dias_a_buscar:
        print(f"📡 {fecha_str}:")
        
        # Verificar si ya hay partidos para esta fecha
        if supabase:
            try:
                existing = supabase.table("partidos").select("id").eq("fecha", fecha_str).execute()
                if existing.data:
                    print(f"  ⏭️  Ya hay {len(existing.data)} partidos, saltando...")
                    continue
            except:
                pass
        
        # Obtener partidos de la API
        fixtures = obtener_partidos_de_apis(fecha_str)
        print(f"  Encontrados: {len(fixtures)} partidos")
        
        if not fixtures:
            print(f"  ⚠️  Sin partidos para {fecha_str}")
            continue
        
        # Procesar partidos
        partidos_para_guardar = []
        
        for fixture in fixtures:
            try:
                fixture_id = fixture["fixture"]["id"]
                home_name = fixture["teams"]["home"]["name"]
                away_name = fixture["teams"]["away"]["name"]
                league_name = fixture["league"]["name"]
                hora_utc = fixture["fixture"]["date"][11:16]
                
                # Calcular hora local (UTC-3)
                try:
                    dt = datetime.strptime(hora_utc, "%H:%M")
                    dt = dt + timedelta(hours=-3)
                    hora_local = dt.strftime("%H:%M")
                except:
                    hora_local = hora_utc
                
                partido_data = {
                    "fixture_id": fixture_id,
                    "fecha": fecha_str,
                    "hora": hora_local,
                    "liga": league_name,
                    "equipo_local": home_name,
                    "equipo_visitante": away_name,
                }
                
                partidos_para_guardar.append(partido_data)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        # Guardar en Supabase
        if supabase and partidos_para_guardar:
            try:
                for partido in partidos_para_guardar:
                    supabase.table("partidos").insert(partido).execute()
                print(f"  ✅ {len(partidos_para_guardar)} partidos guardados")
                total_partidos += len(partidos_para_guardar)
            except Exception as e:
                print(f"  ❌ Error guardando: {e}")
        
        print()
    
    print("=" * 60)
    print(f"✅ SCRAPER COMPLETADO - {total_partidos} partidos totales")
    print("=" * 60)


if __name__ == "__main__":
    run_scraper()
