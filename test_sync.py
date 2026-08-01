"""Script para probar sincronización - ejecutar localmente"""
import requests
from supabase import create_client

# CONFIGURACIÓN - pon tu SUPABASE_ANON_KEY aquí
SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "TU_ANON_KEY_AQUI"  # Cambiar por tu anon key de Supabase

API_URL = "https://v3.football.api-sports.io"
API_KEY = "e3926f829cd848f4b2b54d722ca29701"
headers = {'x-apisports-key': API_KEY}

def test_sync():
    print("🔄 Probando sincronización...\n")
    
    # 1. Conectar a Supabase
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión a Supabase: OK")
    except Exception as e:
        print(f"❌ Error conexión Supabase: {e}")
        return
    
    # 2. Verificar tablas
    resp_partidos = client.table('partidos').select('*').execute()
    resp_equipos = client.table('equipos_stats').select('*').execute()
    print(f"📊 Partidos en BD: {len(resp_partidos.data)}")
    print(f"📊 Equipos en BD: {len(resp_equipos.data)}")
    
    # 3. Descargar UN partido de prueba (La Liga)
    print("\n📡 Descargando partido de prueba (La Liga)...")
    params = {'league': 140, 'season': 2026, 'from': '2026-07-31', 'to': '2026-08-01'}
    resp = requests.get(f"{API_URL}/fixtures", headers=headers, params=params, timeout=15)
    
    if resp.status_code == 200:
        fixtures = resp.json().get('response', [])
        if fixtures:
            f = fixtures[0]
            fix = f.get('fixture', {})
            teams = f.get('teams', {})
            league = f.get('league', {})
            
            print(f"✅ Fixture: {teams.get('home', {}).get('name')} vs {teams.get('away', {}).get('name')}")
            
            # 4. Guardar partido
            partido_data = {
                'fixture_id': fix.get('id'),
                'fecha': fix.get('date', '')[:10],
                'hora': fix.get('date', '')[11:16],
                'liga': league.get('name', ''),
                'equipo_local': teams.get('home', {}).get('name', ''),
                'equipo_visitante': teams.get('away', {}).get('name', ''),
            }
            client.table('partidos').upsert(partido_data, on_conflict='fixture_id').execute()
            print(f"✅ Partido guardado")
            
            # 5. Guardar stats de equipos
            for tipo in ['home', 'away']:
                team = teams.get(tipo, {})
                team_name = team.get('name', '')
                team_id_api = team.get('id', 0)
                
                if team_name and team_id_api:
                    resp_t = requests.get(f"{API_URL}/teams/statistics", 
                        headers=headers, 
                        params={'team': team_id_api, 'league': 140, 'season': 2026}, 
                        timeout=10)
                    if resp_t.status_code == 200:
                        stats = resp_t.json().get('response', {})
                        if stats:
                            gf = stats.get('goals', {}).get('for', {}).get('total', 0) or 0
                            gc = stats.get('goals', {}).get('against', {}).get('total', 0) or 0
                            wins = stats.get('fixtures', {}).get('wins', {}).get('total', 0) or 0
                            draws = stats.get('fixtures', {}).get('draws', {}).get('total', 0) or 0
                            loses = stats.get('fixtures', {}).get('loses', {}).get('total', 0) or 0
                            pj = stats.get('fixtures', {}).get('played', {}).get('total', 1) or 1
                            
                            eq_data = {
                                'equipo': team_name,
                                'liga': league.get('name', ''),
                                'temporada': '2026-2027',
                                'partidos_jugados': pj,
                                'victorias': wins,
                                'empates': draws,
                                'derrotas': loses,
                                'goles_favor': gf,
                                'goles_contra': gc,
                                'lambda_local': 1.5,
                                'lambda_visitante': 1.2,
                                'ultimos_5_partidos': ['W', 'D', 'L', 'W', 'W'],
                            }
                            client.table('equipos_stats').upsert(eq_data, ignore_duplicates=True).execute()
                            print(f"✅ Stats guardadas: {team_name} (V={wins}, E={draws}, D={loses}, GF={gf}, GC={gc})")
    
    # 6. Resultado final
    print("\n📊 RESULTADO FINAL:")
    resp_equipos = client.table('equipos_stats').select('*').execute()
    print(f"   Total equipos en BD: {len(resp_equipos.data)}")
    
    if resp_equipos.data:
        print("\n📋 Muestra:")
        for e in resp_equipos.data[:3]:
            print(f"   - {e['equipo']}: V={e['victorias']}, E={e['empates']}, D={e['derrotas']}")

if __name__ == "__main__":
    test_sync()
