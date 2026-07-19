"""
Scorpion Elite - FBref Scraper
==============================
Scraping ultra-ligero de FBref para los últimos 5 partidos de cada equipo.
Usa tablas HTML simples sin JavaScript - consume mínima memoria.
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# ═══════════════════════════════════════════════════════════════════════════════
# URLs DE FBBREF POR EQUIPO
# ═══════════════════════════════════════════════════════════════════════════════

FBREF_SQUADS = {
    # Premier League
    'Manchester City': '361ca564/Manchester-City-Stats',
    'Arsenal': 'b8b03df0/Arsenal-Stats',
    'Liverpool': '822bd0ba/Liverpool-Stats',
    'Chelsea': 'cff44d04/Chelsea-Stats',
    'Manchester United': '19538871/Manchester-United-Stats',
    'Tottenham': '361ca564/Tottenham-Hotspur-Stats',
    'Newcastle': 'b2b47a98/Newcastle-United-Stats',
    'Brighton': '0335a503/Brighton-and-Hove-Albion-Stats',
    'Aston Villa': '9600892f/Aston-Villa-Stats',
    'West Ham': '8eccca6e/West-Ham-United-Stats',
    'Crystal Palace': 'a2da8f83/Crystal-Palace-Stats',
    'Fulham': 'fd7b415d/Fulham-Stats',
    'Wolves': 'f7c6d7b0/Wolverhampton-Wanderers-Stats',
    'Brentford': 'cd05481d/Brentford-Stats',
    'Bournemouth': '4ba9d3a3/Bournemouth-Stats',
    'Nottingham Forest': 'e3a1d1fb/Nottingham-Forest-Stats',
    'Everton': 'd3fd31cc/Everton-Stats',
    'Leicester': 'a2d74b07/Leicester-City-Stats',
    'Ipswich': '5ae01eb8/Ipswich-Town-Stats',
    'Southampton': 'cff44d04/Southampton-Stats',
    
    # La Liga
    'Real Madrid': '53a2f82b/Real-Madrid-Stats',
    'Barcelona': '361ca564/FC-Barcelona-Stats',
    'Atletico Madrid': 'f7fab33c/Atletico-Madrid-Stats',
    'Real Sociedad': 'ee2d5bce/Real-Sociedad-Stats',
    'Athletic Bilbao': 'fbf6a8ae/Athletic-Club-Stats',
    'Sevilla': 'ad0bae88/Sevilla-Stats',
    'Villarreal': 'f8d357d5/Villarreal-Stats',
    'Real Betis': 'cd3fb8ef/Real-Betis-Stats',
    'Valencia': 'dcc91a7b/Valencia-Stats',
    'Getafe': '5e42e779/CE-Getafe-Stats',
    'Osasuna': 'd1fa625c/CA-Osasuna-Stats',
    'Celta Vigo': 'f9d8c7e1/Celta-Vigo-Stats',
    'Mallorca': 'c4e92e9c/RCD-Mallorca-Stats',
    'Las Palmas': 'e67a39d7/UD-Las-Palmas-Stats',
    'Rayo Vallecano': 'c6a3c0e5/Rayo-Vallecano-Stats',
    'Real Valladolid': '7e7e52a5/Real-Valladolid-Stats',
    'Espanyol': 'a4943555/RCD-Espanyol-Stats',
    'Alaves': '1e71c7c8/Deportivo-Alaves-Stats',
    'Girona': '98e8c0e8/Girona-FC-Stats',
    'Leganes': '6e6c53b2/CD-Leganes-Stats',
    
    # Bundesliga
    'Bayern Munich': 'fc65c9f2/FC-Bayern-Munich-Stats',
    'Borussia Dortmund': 'addf9828/Borussia-Dortmund-Stats',
    'RB Leipzig': 'c18905e9/RB-Leipzig-Stats',
    'Bayer Leverkusen': 'b6967de9/Bayer-04-Leverkusen-Stats',
    'Eintracht Frankfurt': 'b5f85301/Eintracht-Frankfurt-Stats',
    'Wolfsburg': 'cd89f64e/VfL-Wolfsburg-Stats',
    'Freiburg': '2a6c2ca2/SC-Freiburg-Stats',
    'Mainz': 'cf5a4e36/1-FSV-Mainz-05-Stats',
    'Monchengladbach': 'c09ddc04/Borussia-Mgladbach-Stats',
    'Union Berlin': '7e12e6e9/1-FC-Union-Berlin-Stats',
    'Dortmund': 'addf9828/Borussia-Dortmund-Stats',
    'Hoffenheim': '2bb56f32/TSG-1899-Hoffenheim-Stats',
    'Werder Bremen': '4e82d8d8/SV-Werder-Bremen-Stats',
    'Bochum': '95b65df5/VfL-Bochum-Stats',
    'Heidenheim': 'a9e26af1/1-FC-Heidenheim-Stats',
    'Stuttgart': 'deb5c1a9/VfB-Stuttgart-Stats',
    'Augsburg': 'fc80169f/FC-Augsburg-Stats',
    'Holstein Kiel': 'a68b4e9e/Holstein-Kiel-Stats',
    'Eintracht Braunschweig': 'bcd7f59a/Eintracht-Braunschweig-Stats',
    
    # Serie A
    'Inter Milan': 'd6f4e60c/Inter-Milan-Stats',
    'AC Milan': 'c8e86ee2/AC-Milan-Stats',
    'Juventus': '907a5e38/Juventus-Stats',
    'Napoli': 'a4f5a882/SSC-Napoli-Stats',
    'Roma': 'cf5a4e36/AS-Roma-Stats',
    'Lazio': 'a54f3f3d/Lazio-Stats',
    'Atalanta': 'bf5a23a5/Atalanta-Stats',
    'Fiorentina': '3e74e5c6/Fiorentina-Stats',
    'Bologna': '8c65c9e2/Bologna-Stats',
    'Torino': 'c1c7a6e7/Torino-Stats',
    'Monza': 'b6e85b0c/AC-Monza-Stats',
    'Genoa': 'dbce207c/Genoa-Stats',
    'Lecce': '9d3c65a5/US-Lecce-Stats',
    'Udinese': '1c52f8d7/Udinese-Stats',
    'Cagliari': '73c8e4fd/Cagliari-Stats',
    'Parma': '9dc30e5a/Parma-Stats',
    'Como': 'b54e4c2e/Como-Stats',
    'Empoli': '2b16f176/Empoli-Stats',
    'Verona': 'e25e85da/Hellas-Verona-Stats',
    'Venezia': 'fe79b92c/Venezia-Stats',
    
    # Ligue 1
    'PSG': 'e2d889f8/Paris-Saint-Germain-Stats',
    'Monaco': 'c1a2c7c5/AS-Monaco-Stats',
    'Marseille': '2abb4c5e/Olympique-Marseille-Stats',
    'Lyon': '8d70d3f8/Olympique-Lyon-Stats',
    'Lille': '176f3dc5/LOSC-Lille-Stats',
    'Nice': 'f98e0d8b/OGC-Nice-Stats',
    'Lens': 'a427c8b0/RC-Lens-Stats',
    'Rennes': 'a25b6e2c/Stade-Rennais-Stats',
    'Toulouse': '76f2c2a1/Toulouse-Stats',
    'Brest': 'd53c1f3a/Stade-Brestois-Stats',
    'Strasbourg': '4c80c70e/RC-Strasbourg-Stats',
    'Nantes': '6eff7cc4/FC-Nantes-Stats',
    'Reims': 'b1e84b0d/Stade-de-Reims-Stats',
    'Le Havre': 'c6d8e4e0/Le-Havre-Stats',
    'Montpellier': '7c5d7f0e/Montpellier-HSC-Stats',
    'Auxerre': '4f9a0f4f/AJ-Auxerre-Stats',
    'Saint Etienne': 'd3e84f60/AS-Saint-Etienne-Stats',
    'Angers': 'b9c5a5f0/Angers-SCO-Stats',
    'Metz': '9b3c5e82/FC-Metz-Stats',
    
    # Eredivisie
    'Ajax': '0a26a56a/Amsterdam-Ajax-Stats',
    'PSV': '5e42e779/PSV-Eindhoven-Stats',
    'PSV Eindhoven': '5e42e779/PSV-Eindhoven-Stats',
    'Feyenoord': 'e67a39d7/Feyenoord-Stats',
    'AZ': 'c7f10f1d/AZ-Alkmaar-Stats',
    'AZ Alkmaar': 'c7f10f1d/AZ-Alkmaar-Stats',
    'Twente': '9d1a7790/FC-Twente-Stats',
    'Utrecht': '8e74aee6/FC-Utrecht-Stats',
    'Groningen': '3f60ea0a/FC-Groningen-Stats',
    'Vitesse': '8a30e4e1/Vitesse-Stats',
    'Sparta Rotterdam': '5c5c8a8e/Sparta-Rotterdam-Stats',
    'Heerenveen': '2b20a90b/SC-Heerenveen-Stats',
    'NEC Nijmegen': '7c6a0e3f/NEC-Nijmegen-Stats',
    'Almere City': '9f8e0f6d/Almere-City-Stats',
    'Waalwijk': 'c8e86ee2/RKC-Waalwijk-Stats',
    
    # Liga MX
    'Club America': 'ce3c7e4d/Club-America-Stats',
    'Chivas': 'a1f1c6b2/Guadalajara-Stats',
    'Chivas Guadalajara': 'a1f1c6b2/Guadalajara-Stats',
    'Tigres': '2f22dc85/Tigres-Stats',
    'Tigres UANL': '2f22dc85/Tigres-Stats',
    'Monterrey': '1c7053a0/Monterrey-Stats',
    'Pumas': 'f1fda0b5/Pumas-Stats',
    'Pumas UNAM': 'f1fda0b5/Pumas-Stats',
    'Cruz Azul': '7ab4c0e3/Cruz-Azul-Stats',
    'Leon': '1e71c7c8/Leon-Stats',
    'Santos': '7c7a9c0e/Santos-Laguna-Stats',
    'Santos Laguna': '7c7a9c0e/Santos-Laguna-Stats',
    'Necaxa': 'c1b5a7d2/Necaxa-Stats',
    'Puebla': '5c5d8f3e/Puebla-Stats',
    'Tijuana': '4c66e2f7/Xolos-de-Tijuana-Stats',
    'Queretaro': '5e42e779/Queretaro-Stats',
    'Mazatlan': '7f3d6e9a/Mazatlan-Stats',
    'San Luis': '1e71c7c8/San-Luis-Stats',
    'Atlas': 'c1a2c7c5/Atlas-Stats',
    'Juarez': '7c7a9c0e/Juarez-Stats',
    
    # Argentina
    'River Plate': 'a4f5a882/River-Plate-Stats',
    'Boca Juniors': 'c3b5a7d2/Boca-Juniors-Stats',
    'Racing Club': '7c7a9c0e/Racing-Club-Stats',
    'Estudiantes': '5e42e779/Estudiantes-Stats',
    'Defensa y Justicia': '3f60ea0a/Defensa-y-Justicia-Stats',
    'San Lorenzo': '1c7053a0/San-Lorenzo-Stats',
    'Velez Sarsfield': '8e74aee6/Velez-Sarsfield-Stats',
    'Huracan': '5c5c8a8e/Huracan-Stats',
    'Argentinos Juniors': '7ab4c0e3/Argentinos-JuniStats',
    'Talleres': 'c1b5a7d2/Talleres-Stats',
    'Belgrano': '5e42e779/Belgrano-Stats',
    'Instituto': '7c7a9c0e/Instituto-Stats',
    'Godoy Cruz': '1e71c7c8/Godoy-Cruz-Stats',
    
    # Brasil
    'Flamengo': 'c11e6d8e/Flamengo-Stats',
    'Palmeiras': 'b4ba92a2/Palmeiras-Stats',
    'Corinthians': 'f39b7b2d/Corinthians-Stats',
    'Sao Paulo': 'c8e86ee2/Sao-Paulo-Stats',
    'Santos': '7c7a9c0e/Santos-Stats',
    'Internacional': '1c7053a0/Internacional-Stats',
    'Gremio': '5e42e779/Gremio-Stats',
    'Atletico Mineiro': 'c1a2c7c5/Atletico-Mineiro-Stats',
    'Fluminense': '7ab4c0e3/Fluminense-Stats',
    'Botafogo': '8e74aee6/Botafogo-Stats',
    'Vasco': '1e71c7c8/Vasco-da-Gama-Stats',
    'Cruzeiro': 'c1b5a7d2/Cruzeiro-Stats',
    'Athletico Paranaense': '5e42e779/Athletico-PR-Stats',
    'Bahia': '7c7a9c0e/Bahia-Stats',
    'Fortaleza': '8a30e4e1/Fortaleza-Stats',
    
    # Colombia
    'Atletico Nacional': 'c1a2c7c5/Atletico-Nacional-Stats',
    'Millonarios': '7ab4c0e3/Millonarios-Stats',
    'Santa Fe': '1e71c7c8/Santa-Fe-Stats',
    'Junior': '5e42e779/Junior-Stats',
    'America de Cali': 'c1b5a7d2/America-de-Cali-Stats',
    'Once Caldas': '7c7a9c0e/Once-Caldas-Stats',
    'Independiente Medellin': '8e74aee6/Independiente-Medellin-Stats',
    'Alianza Petrolera': '5e42e779/Alianza-Petrolera-Stats',
    'Patriotas': '1c7053a0/Patriotas-Stats',
    'Deportivo Pasto': '7ab4c0e3/Deportivo-Pasto-Stats',
    
    # Chile
    'Colo Colo': 'c1a2c7c5/Colo-Colo-Stats',
    'Universidad de Chile': '7ab4c0e3/Universidad-de-Chile-Stats',
    'U de Chile': '7ab4c0e3/Universidad-de-Chile-Stats',
    'Catolica': '1e71c7c8/Catolica-Stats',
    'Union Española': '5e42e779/Union-Espanola-Stats',
    'Audax Italiano': '7c7a9c0e/Audax-Italiano-Stats',
    'Palestino': '8e74aee6/Palestino-Stats',
    'Huachipato': '1c7053a0/Huachipato-Stats',
    'Cobreloa': 'c1b5a7d2/Cobreloa-Stats',
    'Magallanes': '7ab4c0e3/Magallanes-Stats',
    
    # Peru
    'Universitario': '7ab4c0e3/Universitario-Stats',
    'Alianza Lima': '1e71c7c8/Alianza-Lima-Stats',
    'Sporting Cristal': '5e42e779/Sporting-Cristal-Stats',
    'Melgar': '7c7a9c0e/Melgar-Stats',
    'Universitario de Deportes': '7ab4c0e3/Universitario-Stats',
    
    # Ecuador
    'LDU Quito': '7ab4c0e3/LDU-Quito-Stats',
    'Barcelona SC': 'c1a2c7c5/Barcelona-SC-Stats',
    'Emelec': '1e71c7c8/Emelec-Stats',
    'Independiente del Valle': '5e42e779/Independiente-del-Valle-Stats',
    'Liga Quito': '7ab4c0e3/Liga-de-Quito-Stats',
    
    # Paraguay
    'Olimpia': 'c1a2c7c5/Olimpia-Stats',
    'Cerro Porteno': '7ab4c0e3/Cerro-Porteno-Stats',
    'Libertad': '1e71c7c8/Libertad-Stats',
    'Guarani': '5e42e779/Club-Guarani-Stats',
    'Nacional': '7c7a9c0e/Nacional-Stats',
    
    # Uruguay
    'Penarol': 'c1a2c7c5/Club-Athletic-Pe%C3%B1arol-Stats',
    'Nacional': '7ab4c0e3/Club-Nacional-de-Football-Stats',
    'Liverpool Montevideo': '1e71c7c8/Liverpool-Stats',
    'Defensor Sporting': '5e42e779/Defensor-Sporting-Stats',
    'Wanderers': '7c7a9c0e/Montevideo-Wanderers-Stats',
    
    # Venezuela
    'Caracas': 'c1a2c7c5/Caracas-FC-Stats',
    'Deportivo Tachira': '7ab4c0e3/Deportivo-Tachira-Stats',
    'Estudiantes Merida': '1e71c7c8/Estudiantes-de-Merida-Stats',
    'Zulia': '5e42e779/Zulia-FC-Stats',
    'Mineros': '7c7a9c0e/Mineros-de-Guayana-Stats',
}


class FBrefScraper:
    """Scraper ultra-ligero de FBref."""
    
    BASE_URL = "https://fbref.com/en/squads"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def get_squad_url(self, team_name: str) -> Optional[str]:
        """Obtiene la URL del equipo."""
        # Buscar en diccionario
        for name, path in FBREF_SQUADS.items():
            if name.lower() == team_name.lower():
                return f"{self.BASE_URL}/{path}"
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                return f"{self.BASE_URL}/{path}"
        return None
    
    def scrape_last_matches(self, team_url: str, num_matches: int = 5) -> List[Dict]:
        """Extrae los últimos N partidos del equipo."""
        matches = []
        
        try:
            response = self.session.get(team_url, timeout=10)
            if response.status_code != 200:
                return matches
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar tabla de partidos recientes
            # FBref usa table con id que contiene "matchlogs"
            tables = soup.find_all('table')
            
            for table in tables:
                # Buscar la tabla de partidos (puede tener id con "matchlogs" o "recent")
                table_id = table.get('id', '')
                if 'matchlogs' in table_id.lower() or 'recent' in table_id.lower():
                    rows = table.find_all('tr')
                    
                    for i, row in enumerate(rows):
                        if i >= num_matches + 1:  # +1 porque la primera fila es header
                            break
                        
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 5:
                            continue
                        
                        # Extraer datos básicos
                        match_data = {}
                        
                        # Fecha (primer celda)
                        date_cell = cells[0].get_text(strip=True)
                        match_data['fecha'] = date_cell
                        
                        # Competición
                        if len(cells) > 1:
                            match_data['competencia'] = cells[1].get_text(strip=True)
                        
                        # Rival (usualmente columna 4 o 5)
                        for j, cell in enumerate(cells):
                            text = cell.get_text(strip=True)
                            if text and not text.isdigit() and 'vs' not in text.lower():
                                if j > 2 and j < 7:
                                    match_data['rival'] = text
                                    break
                        
                        # Resultado - buscar patrón "2 - 1"
                        row_text = row.get_text()
                        score_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', row_text)
                        if score_match:
                            match_data['goles_local'] = int(score_match.group(1))
                            match_data['goles_visitante'] = int(score_match.group(2))
                        
                        # Remates (tiros)
                        for cell in cells:
                            header = cell.get('data-stat', '')
                            if header == 'shots' or 'shot' in header.lower():
                                match_data['remates'] = int(cell.get_text(strip=True) or 0)
                            if header == 'shots_on_target' or 'on target' in header.lower():
                                match_data['remates_arco'] = int(cell.get_text(strip=True) or 0)
                            if header == 'yellow_cards':
                                match_data['amarillas'] = int(cell.get_text(strip=True) or 0)
                            if header == 'red_cards':
                                match_data['rojas'] = int(cell.get_text(strip=True) or 0)
                            if header == 'corners' or 'corner' in header.lower():
                                match_data['corners'] = int(cell.get_text(strip=True) or 0)
                            if header == 'possession':
                                match_data['posesion'] = cell.get_text(strip=True)
                        
                        if match_data.get('fecha'):
                            matches.append(match_data)
            
            return matches[:num_matches]
            
        except Exception as e:
            logger.error(f"Error scrapeando {team_url}: {e}")
            return []
    
    def calculate_stats_from_matches(self, matches: List[Dict]) -> Dict:
        """Calcula estadísticas promediadas de los partidos."""
        if not matches:
            return {}
        
        total_remates = 0
        total_remates_arco = 0
        total_amarillas = 0
        total_rojas = 0
        total_corners = 0
        total_posesion = 0
        posesion_count = 0
        goles_favor = 0
        goles_contra = 0
        
        for m in matches:
            total_remates += m.get('remates', 0)
            total_remates_arco += m.get('remates_arco', 0)
            total_amarillas += m.get('amarillas', 0)
            total_rojas += m.get('rojas', 0)
            total_corners += m.get('corners', 0)
            
            # Procesar posesión
            posesion = m.get('posesion', '')
            if posesion and '%' in posesion:
                try:
                    total_posesion += float(posesion.replace('%', ''))
                    posesion_count += 1
                except:
                    pass
            
            # Goles
            if m.get('goles_local') is not None:
                # Asumimos que somos locales en estos datos
                goles_favor += m.get('goles_local', 0)
                goles_contra += m.get('goles_visitante', 0)
        
        n = len(matches)
        
        return {
            'partidos': n,
            'promedio_remates': round(total_remates / n, 1),
            'promedio_remates_arco': round(total_remates_arco / n, 1),
            'promedio_amarillas': round(total_amarillas / n, 1),
            'promedio_rojas': round(total_rojas / n, 1),
            'promedio_corners': round(total_corners / n, 1),
            'promedio_posesion': round(total_posesion / posesion_count, 1) if posesion_count > 0 else 50,
            'goles_favor_total': goles_favor,
            'goles_contra_total': goles_contra,
            'lambda_local': round(goles_favor / n, 2),
            'lambda_visitante': round((goles_contra / n) * 0.85, 2),  # Ajuste para visitante
        }


def scrape_team_fbref(team_name: str, num_matches: int = 5) -> Dict:
    """
    Función principal para raspar un equipo de FBref.
    Retorna estadísticas de los últimos N partidos.
    """
    scraper = FBrefScraper()
    
    # Obtener URL
    url = scraper.get_squad_url(team_name)
    if not url:
        # Intentar búsqueda difusa
        for name, path in FBREF_SQUADS.items():
            if team_name.lower() in name.lower() or name.lower() in team_name.lower():
                url = f"{scraper.BASE_URL}/{path}"
                team_name = name
                break
    
    if not url:
        return {
            'equipo': team_name,
            'encontrado': False,
            'source': 'fbref',
            'matches': [],
            'stats': {}
        }
    
    # Obtener partidos
    matches = scraper.scrape_last_matches(url, num_matches)
    
    # Calcular estadísticas
    stats = scraper.calculate_stats_from_matches(matches)
    
    return {
        'equipo': team_name,
        'encontrado': len(matches) > 0,
        'source': 'fbref',
        'url': url,
        'matches': matches,
        'stats': stats
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    test_teams = ['Barcelona', 'Real Madrid', 'PSG', 'Manchester City', 'River Plate']
    
    print("=" * 60)
    print("PRUEBA: FBref Scraper")
    print("=" * 60)
    
    for team in test_teams:
        print(f"\n🔍 {team}...")
        result = scrape_team_fbref(team, num_matches=5)
        
        if result['encontrado']:
            print(f"   ✅ Encontrado: {result['equipo']}")
            print(f"   📊 Partidos analizados: {len(result['matches'])}")
            
            stats = result['stats']
            print(f"   📈 Promedio remates: {stats.get('promedio_remates', 'N/A')}")
            print(f"   🎯 Promedio remates arco: {stats.get('promedio_remates_arco', 'N/A')}")
            print(f"   🟨 Promedio amarillas: {stats.get('promedio_amarillas', 'N/A')}")
            print(f"   📐 Promedio corners: {stats.get('promedio_corners', 'N/A')}")
            print(f"   ⚽ Goles favor: {stats.get('goles_favor_total', 'N/A')}")
            print(f"   🏠 λ Local: {stats.get('lambda_local', 'N/A')}")
        else:
            print(f"   ❌ No encontrado")
