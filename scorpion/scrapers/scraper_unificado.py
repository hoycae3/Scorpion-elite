"""
Scraper Unificado - Scorpion Elite
Combina datos de: Flashscore, Transfermarkt, Soccerway, WhoScored
Guarda todo en Supabase
"""
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar scrapers
from .flashscore_scraper import FlashscoreScraper
from .transfermarkt_scraper import TransfermarktScraper
from .soccerway_scraper import SoccerwayScraper
from .whoscored_scraper import WhoScoredScraper


class ScraperUnificado:
    """Scraper que combina todas las fuentes y guarda en Supabase"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        
        # Inicializar scrapers
        self.flashscore = FlashscoreScraper()
        self.transfermarkt = TransfermarktScraper()
        self.soccerway = SoccerwayScraper()
        self.whoscored = WhoScoredScraper()
        
        # Configuración
        self.ligas_principales = [
            "Premier League",
            "La Liga", 
            "Serie A",
            "Bundesliga",
            "Ligue 1",
            "Brasileiro",
            "MLS",
            "Liga MX"
        ]
    
    def _get_supabase(self):
        """Obtiene cliente de Supabase si no está inicializado"""
        if self.supabase:
            return self.supabase
        
        try:
            from supabase import create_client
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if url and key:
                self.supabase = create_client(url, key)
                return self.supabase
        except ImportError:
            logger.warning("supabase-py no instalado")
        except Exception as e:
            logger.error(f"Error conectando a Supabase: {e}")
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SCRAPING DE PARTIDOS (Flashscore)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def scrape_partidos(self, dias: int = 2) -> List[Dict]:
        """
        Scraping de partidos de Flashscore
        
        Args:
            dias: Número de días hacia adelante
            
        Returns:
            Lista de partidos
        """
        logger.info("🦂 Iniciando scraping de partidos (Flashscore)...")
        
        try:
            partidos = self.flashscore.get_today_matches(dias=dias)
            logger.info(f"✅ {len(partidos)} partidos obtenidos de Flashscore")
            return partidos
        except Exception as e:
            logger.error(f"❌ Error en scraping de partidos: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SCRAPING DE TABLAS DE POSICIONES (Transfermarkt)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def scrape_transfermarkt(self, liga: str) -> Dict:
        """
        Scraping de estadísticas de equipos (Transfermarkt)
        
        Args:
            liga: Nombre de la liga
            
        Returns:
            Diccionario con tabla de posiciones
        """
        logger.info(f"📊 Scraping Transfermarkt: {liga}")
        
        try:
            result = self.transfermarkt.get_league_standings(liga)
            logger.info(f"✅ {len(result)} equipos de {liga}")
            return result
        except Exception as e:
            logger.error(f"❌ Error scraping Transfermarkt: {e}")
            return []
    
    def scrape_all_leagues_transfermarkt(self) -> List[Dict]:
        """Scraping de todas las ligas configuradas"""
        all_teams = []
        
        for liga in self.ligas_principales:
            teams = self.scrape_transfermarkt(liga)
            for team in teams:
                team['liga'] = liga
                team['source'] = 'transfermarkt'
            all_teams.extend(teams)
        
        return all_teams
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SCRAPING DE RESULTADOS HISTÓRICOS (Soccerway)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def scrape_soccerway(self, liga: str) -> List[Dict]:
        """
        Scraping de resultados históricos (Soccerway)
        
        Args:
            liga: Nombre de la liga
            
        Returns:
            Lista de resultados
        """
        logger.info(f"📜 Scraping Soccerway: {liga}")
        
        try:
            results = self.soccerway.get_league_results(liga, limit=100)
            logger.info(f"✅ {len(results)} resultados de {liga}")
            return results
        except Exception as e:
            logger.error(f"❌ Error scraping Soccerway: {e}")
            return []
    
    def scrape_team_form(self, team_name: str) -> Dict:
        """
        Obtiene la forma actual de un equipo
        
        Args:
            team_name: Nombre del equipo
            
        Returns:
            Diccionario con score de forma
        """
        try:
            form = self.soccerway.calculate_team_form_score(team_name)
            return form
        except Exception as e:
            logger.error(f"Error obteniendo forma de {team_name}: {e}")
            return {'score': 0, 'form_string': ''}
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # SCRAPING DE ESTADÍSTICAS AVANZADAS (WhoScored)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def scrape_whoscored(self, region: str = "England") -> List[Dict]:
        """
        Scraping de estadísticas avanzadas (WhoScored)
        
        Args:
            region: Región para buscar
            
        Returns:
            Lista de partidos con estadísticas
        """
        logger.info(f"⚡ Scraping WhoScored: {region}")
        
        try:
            matches = self.whoscored.get_upcoming_matches(region)
            logger.info(f"✅ {len(matches)} partidos de WhoScored")
            return matches
        except Exception as e:
            logger.error(f"❌ Error scraping WhoScored: {e}")
            return []
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # GUARDADO EN SUPABASE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def guardar_partidos(self, partidos: List[Dict]) -> int:
        """Guarda partidos en Supabase"""
        supabase = self._get_supabase()
        if not supabase:
            logger.warning("⚠️ Supabase no disponible, guardando en memoria")
            return 0
        
        saved = 0
        for partido in partidos:
            try:
                # Verificar si ya existe
                existing = supabase.table("partidos").select("id").eq(
                    "fixture_id", partido.get("fixture_id")
                ).execute()
                
                if existing.data:
                    # Actualizar
                    supabase.table("partidos").update({
                        "source_flashscore": True,
                        "actualizado_en": datetime.now().isoformat()
                    }).eq("fixture_id", partido.get("fixture_id")).execute()
                else:
                    # Insertar
                    partido['source_flashscore'] = True
                    partido['estado'] = 'programado'
                    supabase.table("partidos").insert(partido).execute()
                
                saved += 1
            except Exception as e:
                logger.error(f"Error guardando partido: {e}")
        
        logger.info(f"💾 {saved} partidos guardados en Supabase")
        return saved
    
    def guardar_estadisticas_equipos(self, equipos: List[Dict]) -> int:
        """Guarda estadísticas de equipos en Supabase"""
        supabase = self._get_supabase()
        if not supabase:
            return 0
        
        saved = 0
        for equipo in equipos:
            try:
                equipo_data = {
                    "equipo": equipo.get("equipo"),
                    "liga": equipo.get("liga"),
                    "source": equipo.get("source", "transfermarkt"),
                    "posicion_tabla": equipo.get("posicion"),
                    "puntos": equipo.get("puntos"),
                    "partido_jugados": equipo.get("partidos_jugados"),
                    "victorias": equipo.get("victorias"),
                    "empates": equipo.get("empates"),
                    "derrotas": equipo.get("derrotas"),
                    "goles_favor": equipo.get("goles_favor"),
                    "goles_contra": equipo.get("goles_contra"),
                    "diferencia_goles": equipo.get("diferencia_goles"),
                    "ultimos_5": json.dumps([]),  # Se actualiza con Soccerway
                }
                
                supabase.table("estadisticas_equipos").upsert(
                    equipo_data,
                    on_conflict="equipo,liga,source"
                ).execute()
                
                saved += 1
            except Exception as e:
                logger.error(f"Error guardando equipo: {e}")
        
        logger.info(f"💾 {saved} equipos guardados en Supabase")
        return saved
    
    def guardar_resultados_historicos(self, resultados: List[Dict], liga: str) -> int:
        """Guarda resultados históricos en Supabase"""
        supabase = self._get_supabase()
        if not supabase:
            return 0
        
        saved = 0
        for resultado in resultados:
            try:
                # Determinar resultado para betting
                if resultado.get('goles_local', 0) > resultado.get('goles_visitante', 0):
                    bet_result = 'home'
                elif resultado.get('goles_local', 0) < resultado.get('goles_visitante', 0):
                    bet_result = 'away'
                else:
                    bet_result = 'draw'
                
                result_data = {
                    "match_id": resultado.get("match_id"),
                    "fecha": resultado.get("fecha"),
                    "liga": liga,
                    "equipo_local": resultado.get("equipo_local"),
                    "equipo_visitante": resultado.get("equipo_visitante"),
                    "goles_local": resultado.get("goles_local"),
                    "goles_visitante": resultado.get("goles_visitante"),
                    "resultado": bet_result,
                    "source": "soccerway"
                }
                
                supabase.table("resultados_historicos").upsert(
                    result_data,
                    on_conflict="match_id"
                ).execute()
                
                saved += 1
            except Exception as e:
                logger.error(f"Error guardando resultado: {e}")
        
        logger.info(f"💾 {saved} resultados históricos guardados")
        return saved
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EJECUCIÓN COMPLETA
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def run_full_scrape(self):
        """
        Ejecuta scraping completo de todas las fuentes
        """
        logger.info("=" * 60)
        logger.info("🦂 SCORPION ELITE - SCRAPING COMPLETO")
        logger.info("=" * 60)
        
        summary = {
            "partidos": 0,
            "equipos": 0,
            "resultados": 0,
            "tiempo_total": None
        }
        
        start_time = datetime.now()
        
        # 1. Scraping de partidos (Flashscore)
        logger.info("\n📅 FASE 1: Partidos de Flashscore")
        partidos = self.scrape_partidos(dias=2)
        summary["partidos"] = self.guardar_partidos(partidos)
        
        # 2. Scraping de tablas (Transfermarkt)
        logger.info("\n📊 FASE 2: Estadísticas de Transfermarkt")
        equipos = self.scrape_all_leagues_transfermarkt()
        summary["equipos"] = self.guardar_estadisticas_equipos(equipos)
        
        # 3. Scraping de resultados (Soccerway)
        logger.info("\n📜 FASE 3: Resultados de Soccerway")
        for liga in self.ligas_principales[:3]:  # Solo las 3 principales para no demorar
            resultados = self.scrape_soccerway(liga)
            summary["resultados"] += self.guardar_resultados_historicos(resultados, liga)
        
        # Resumen
        end_time = datetime.now()
        summary["tiempo_total"] = str(end_time - start_time)
        
        logger.info("\n" + "=" * 60)
        logger.info("📋 RESUMEN DE SCRAPING")
        logger.info("=" * 60)
        logger.info(f"  📅 Partidos: {summary['partidos']}")
        logger.info(f"  📊 Equipos: {summary['equipos']}")
        logger.info(f"  📜 Resultados: {summary['resultados']}")
        logger.info(f"  ⏱️  Tiempo: {summary['tiempo_total']}")
        logger.info("=" * 60)
        
        return summary


# ═══════════════════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    scraper = ScraperUnificado()
    result = scraper.run_full_scrape()
    print(f"\n✅ Scraping completado: {result}")
