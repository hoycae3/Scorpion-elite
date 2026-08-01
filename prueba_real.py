import requests
from datetime import datetime, timedelta, timezone

API_URL = "https://v3.football.api-sports.io"
API_KEY = "e3926f829cd848f4b2b54d722ca29701"
headers = {'x-apisports-key': API_KEY}

TARGET_LEAGUES = [
    239, 240, 241, 128, 129, 24, 72, 281, 265, 242, 252, 299, 268, 244, 13, 11,
    39, 40, 140, 141, 135, 78, 61, 88, 94, 144, 203, 2, 3, 848,
    262, 253, 16, 307, 98, 292
]

season = 2026
hoy = datetime.now(timezone(timedelta(hours=-5))).date()
hoy_str = hoy.strftime('%Y-%m-%d')
fecha_hasta_7 = (hoy + timedelta(days=6)).strftime('%Y-%m-%d')

print(f"=== PRUEBA ===")
print(f"Season: {season}")
print(f"Desde: {hoy_str}")
print(f"Hasta: {fecha_hasta_7}")
print()

total = 0
for liga_id in TARGET_LEAGUES:
    params = {'league': liga_id, 'season': season, 'from': hoy_str, 'to': fecha_hasta_7}
    resp = requests.get(f"{API_URL}/fixtures", headers=headers, params=params, timeout=15)
    
    if resp.status_code == 200:
        count = len(resp.json().get('response', []))
        if count > 0:
            print(f"✅ Liga {liga_id}: {count} partidos")
            total += count
        else:
            print(f"⚪ Liga {liga_id}: 0")
    else:
        print(f"❌ Liga {liga_id}: Error {resp.status_code}")

print(f"\n=== TOTAL: {total} partidos ===")
