import subprocess
import json

LEAGUES = [239, 240, 241, 128, 129, 24, 72, 281, 265, 242, 252, 299, 268, 244, 13, 11, 39, 40, 140, 141, 135, 78, 61, 88, 94, 144, 203, 2, 3, 848, 262, 253, 16, 307, 98, 292]

API_KEY = "e3926f829cd848f4b2b54d722ca29701"

for liga_id in LEAGUES:
    cmd = f'curl -s "https://v3.football.api-sports.io/fixtures?league={liga_id}&season=2026&from=2026-08-01&to=2026-08-07" -H "x-apisports-key: {API_KEY}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        count = len(data.get('response', []))
        if count > 0:
            print(f"OK Liga {liga_id}: {count} partidos")
        else:
            print(f"-- Liga {liga_id}: 0 partidos")
    except:
        print(f"ERR Liga {liga_id}: Error")
