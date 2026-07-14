"""
API de Football con type hints y validación robusta.
Maneja API-Football, Understat, TheSportsDB y ClubElo.
"""
import re
import json
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

from scorpion.config import config, UNDERSTAT_MAP, SELECCIONES, LIGAS, TORNEOS_FIFA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Error en API."""
    pass


class RateLimitError(APIError):
    """Error por límite de requests."""
    pass


@dataclass
class StatsEquipo:
    """Estadísticas de un equipo."""
    nombre: str
    liga: str
    gm: Optional[float] = None  # Goles marcados
    gc: Optional[float] = None  # Goles recibidos
    elo: Optional[float] = None  # Rating Elo
    xg: Optional[float] = None  # xG
    xga: Optional[float] = None  # xG contra
    tiros_pg: Optional[float] = None
    fuente: str = "Sin datos"
    ok: bool = False
    fuentes_usadas: List[str] = None

    def __post_init__(self):
        if self.fuentes_usadas is None:
            self.fuentes_usadas = []


@dataclass
class Partido:
    """Representa un partido."""
    dia: str
    hora: str
    hora_sort: int
    liga: str
    liga_id: int
    local: str
    visitante: str
    tid_l: Optional[int] = None
    tid_v: Optional[int] = None


class FootballAPI:
    """Cliente para APIs de fútbol."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Inicializa el cliente de API.
        
        Args:
            api_key: Clave de API-Football (opcional).
        """
        self.api_key = api_key or config.API_FOOTBALL_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; ScorpionElite/4.0)",
            "Accept": "application/json,text/html,*/*"
        })
        # Cachés
        self._cache_temporadas: Dict[int, int] = {}
        self._cache_stats: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
        self._cache_understat: Dict[str, Dict] = {}
        self._cache_elo: Dict[str, Optional[float]] = {}

    def _request(self, url: str, params: Dict[str, Any], timeout: int = 15) -> Optional[Dict]:
        """Hace request con manejo de errores."""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout en request a {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en request: {e}")
            return None

    def get_temporada(self, liga_id: int) -> int:
        """Obtiene la temporada actual de una liga."""
        if liga_id in self._cache_temporadas:
            return self._cache_temporadas[liga_id]
        
        fallback = {1: 2026, 253: 2025, 262: 2025, 239: 2025, 71: 2025}
        try:
            data = self._request(
                "https://v3.football.api-sports.io/leagues",
                {"id": liga_id, "current": "true"},
                timeout=10
            )
            if data:
                seasons = data.get("response", [{}])[0].get("seasons", [])
                activa = [s for s in seasons if s.get("current")]
                if activa:
                    t = activa[0]["year"]
                    self._cache_temporadas[liga_id] = t
                    return t
                if seasons:
                    t = seasons[-1]["year"]
                    self._cache_temporadas[liga_id] = t
                    return t
        except Exception as e:
            logger.error(f"Error obteniendo temporada: {e}")
        
        t = fallback.get(liga_id, 2024)
        self._cache_temporadas[liga_id] = t
        return t

    def get_fixtures(self, liga_id: int, fecha: Optional[str] = None, desde: Optional[str] = None, hasta: Optional[str] = None) -> List[Dict]:
        """Obtiene fixtures de una liga."""
        temporada = self.get_temporada(liga_id)
        headers = {"x-apisports-key": self.api_key}
        
        # Intentar con parámetros de temporada primero
        if fecha:
            params = {"league": liga_id, "season": temporada, "date": fecha}
            data = self._request("https://v3.football.api-sports.io/fixtures", params, headers=headers)
            if data and data.get("response"):
                return data["response"]
        
        if desde and hasta:
            params = {"league": liga_id, "season": temporada, "from": desde, "to": hasta}
            data = self._request("https://v3.football.api-sports.io/fixtures", params, headers=headers)
            if data and data.get("response"):
                return data["response"]
        
        return []

    def parse_fixture(self, f: Dict) -> Partido:
        """Convierte fixture de API a objeto Partido."""
        dt = f["fixture"]["date"]
        return Partido(
            dia=dt[:10],
            hora=dt[11:16],
            hora_sort=int(dt[11:13]) * 60 + int(dt[14:16]),
            liga=f["league"]["name"],
            liga_id=f["league"]["id"],
            local=f["teams"]["home"]["name"],
            visitante=f["teams"]["away"]["name"],
            tid_l=f["teams"]["home"]["id"],
            tid_v=f["teams"]["away"]["id"],
        )

    def get_stats_equipo(self, team_id: int, liga_id: int) -> Tuple[Optional[float], Optional[float]]:
        """Obtiene estadísticas de un equipo desde API-Football."""
        key = f"{team_id}_{liga_id}"
        if key in self._cache_stats:
            return self._cache_stats[key]
        
        temporada = self.get_temporada(liga_id)
        try:
            data = self._request(
                "https://v3.football.api-sports.io/teams/statistics",
                {"team": team_id, "season": temporada, "league": liga_id},
                headers={"x-apisports-key": self.api_key},
                timeout=12
            )
            if data:
                d = data.get("response", {})
                gf = d.get("goals", {}).get("for", {}).get("average", {}).get("total")
                ga = d.get("goals", {}).get("against", {}).get("average", {}).get("total")
                result = (float(gf) if gf else None, float(ga) if ga else None)
                self._cache_stats[key] = result
                return result
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
        
        self._cache_stats[key] = (None, None)
        return (None, None)

    def buscar_equipo(self, nombre: str, liga_id: Optional[int] = None) -> Tuple[Optional[int], Optional[str]]:
        """Busca ID de equipo por nombre."""
        headers = {"x-apisports-key": self.api_key}
        nombre_clean = self._limpiar_nombre(nombre)
        
        for buscar in [nombre_clean, nombre]:
            try:
                params = {"name": buscar}
                if liga_id:
                    params["league"] = liga_id
                data = self._request("https://v3.football.api-sports.io/teams", params, headers=headers, timeout=10)
                if data and data.get("response"):
                    team = data["response"][0]["team"]
                    return team["id"], team["name"]
            except Exception:
                pass
        return None, None

    @staticmethod
    def _limpiar_nombre(nombre: str) -> str:
        """Limpia sufijos de ciudad/país."""
        nombre = re.sub(r"-\s*[A-Z]{2,3}$", "", nombre.strip())
        nombre = re.sub(r"\s*\([^)]+\)", "", nombre)
        return nombre.strip(" .-")

    def get_understat(self, equipo: str, liga: str, temporada: int = 2024) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Obtiene xG desde Understat."""
        league_understat = next((v for k, v in UNDERSTAT_MAP.items() if k in liga.lower()), None)
        if not league_understat:
            return None, None, None, None
        
        cache_key = f"{league_understat}_{temporada}"
        if cache_key not in self._cache_understat:
            try:
                response = self.session.get(f"https://understat.com/league/{league_understat}/{temporada}", timeout=15)
                soup = BeautifulSoup(response.text, "lxml")
                for script in soup.find_all("script"):
                    if "teamsData" in str(script):
                        match = re.search(r"JSON\.parse\(.(.*?)\.replace", str(script))
                        if match:
                            self._cache_understat[cache_key] = json.loads(match.group(1).encode().decode("unicode_escape"))
                        break
            except Exception as e:
                logger.error(f"Error Understat: {e}")
                self._cache_understat[cache_key] = {}
        
        data = self._cache_understat.get(cache_key, {})
        equipo_lower = equipo.lower()
        for team_name, stats in data.items():
            if any(p in team_name.lower() for p in equipo_lower.split()[:2]):
                history = stats.get("history", [])[-10:]
                if history:
                    return (
                        round(sum(x.get("xG", 0) for x in history) / len(history), 2),
                        round(sum(x.get("xGA", 0) for x in history) / len(history), 2),
                        round(sum(x.get("scored", 0) for x in history) / len(history), 2),
                        round(sum(x.get("missed", 0) for x in history) / len(history), 2),
                    )
        return None, None, None, None

    def get_thesportsdb(self, nombre: str) -> Optional[Dict]:
        """Busca equipo en TheSportsDB."""
        nombre_clean = self._limpiar_nombre(nombre)
        for buscar in [nombre_clean, nombre]:
            try:
                response = self.session.get(
                    f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={requests.utils.quote(buscar)}",
                    timeout=8
                )
                data = response.json()
                if data and data.get("teams"):
                    return data["teams"][0]
            except Exception:
                pass
        return None

    def get_elo(self, equipo: str) -> Optional[float]:
        """Obtiene rating Elo desde ClubElo."""
        if equipo in self._cache_elo:
            return self._cache_elo[equipo]
        
        try:
            nombre_url = equipo.replace(" ", "-").replace(".", "")
            response = self.session.get(f"http://api.clubelo.com/{nombre_url}", timeout=8)
            if response.status_code == 200 and len(response.text) > 50:
                linea = response.text.strip().split("\n")[-1].split(",")
                if len(linea) >= 4:
                    elo = float(linea[3])
                    self._cache_elo[equipo] = elo
                    return elo
        except Exception as e:
            logger.error(f"Error ELO: {e}")
        
        self._cache_elo[equipo] = None
        return None

    def obtener_stats_completo(
        self,
        nombre: str,
        liga: str,
        team_id: Optional[int] = None,
        liga_id: Optional[int] = None,
    ) -> StatsEquipo:
        """
        Obtiene estadísticas desde múltiples fuentes en cascada.
        
        Fuentes (en orden de prioridad):
        1. API-Football (requiere API key)
        2. Understat (xG para ligas europeas)
        3. TheSportsDB (cualquier liga)
        4. ClubElo (ratings ELO)
        """
        stats = StatsEquipo(nombre=nombre, liga=liga)
        es_torneo = any(k in liga.lower() for k in TORNEOS_FIFA)
        es_seleccion = any(k in nombre.lower() for k in SELECCIONES)

        # Fuente 1: API-Football
        if team_id and liga_id:
            try:
                if not team_id:
                    team_id, _ = self.buscar_equipo(nombre, liga_id)
                if team_id:
                    gm, gc = self.get_stats_equipo(team_id, liga_id)
                    if gm is not None:
                        stats.gm = round(gm, 2)
                        stats.gc = round(gc, 2) if gc else None
                        stats.fuente = "API-Football"
                        stats.ok = True
                        stats.fuentes_usadas.append("API-Football")
            except Exception as e:
                logger.error(f"Error API-Football: {e}")

        # Fuente 2: Understat
        if not stats.ok and not es_torneo:
            try:
                xg, xga, gm_u, gc_u = self.get_understat(nombre, liga)
                if xg is not None:
                    stats.xg = xg
                    stats.xga = xga
                    if not stats.ok:
                        stats.gm = gm_u
                        stats.gc = gc_u
                        stats.fuente = "Understat"
                        stats.ok = True
                    stats.fuentes_usadas.append("Understat")
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Error Understat: {e}")

        # Fuente 3: TheSportsDB
        try:
            td = self.get_thesportsdb(nombre)
            if td:
                team_id_tdb = td.get("idTeam", "")
                if not stats.ok:
                    gm2, gc2 = self._get_thesportsdb_stats(team_id_tdb)
                    if gm2:
                        stats.gm = gm2
                        stats.gc = gc2
                        stats.fuente = "TheSportsDB"
                        stats.ok = True
                stats.fuentes_usadas.append("TheSportsDB")
            time.sleep(0.2)
        except Exception as e:
            logger.error(f"Error TheSportsDB: {e}")

        # Fuente 4: ClubElo
        try:
            elo = self.get_elo(nombre)
            if elo:
                stats.elo = elo
                stats.fuentes_usadas.append("ClubElo")
        except Exception as e:
            logger.error(f"Error ClubElo: {e}")

        return stats

    def _get_thesportsdb_stats(self, team_id: str) -> Tuple[Optional[float], Optional[float]]:
        """Obtiene últimos partidos de TheSportsDB."""
        try:
            response = self.session.get(
                f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={team_id}",
                timeout=10
            )
            data = response.json()
            if data and data.get("results"):
                raw = [x for x in data["results"] if x.get("intHomeScore") is not None][-10:]
                gml, gcl = [], []
                for x in raw:
                    try:
                        sh = int(x.get("intHomeScore") or 0)
                        sa = int(x.get("intAwayScore") or 0)
                        if str(x.get("idHomeTeam", "")) == str(team_id):
                            gml.append(sh)
                            gcl.append(sa)
                        else:
                            gml.append(sa)
                            gcl.append(sh)
                    except:
                        pass
                if gml:
                    return round(sum(gml) / len(gml), 2), round(sum(gcl) / len(gcl), 2)
        except:
            pass
        return None, None
