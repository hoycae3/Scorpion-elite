"""
Configuración centralizada del proyecto Scorpion Elite.
Todas las constantes y configuraciones se managanean desde aquí.
"""
import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class Config:
    """Configuración global de la aplicación."""
    
    # API Keys
    API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "124c9519df145caf883cd82f0b2a4671")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "scorpion_admin_2025")
    
    # Rutas
    DB_PATH: str = os.getenv("DB_PATH", "/tmp/scorpion_v4.db")
    
    # Configuración de modelos matemáticos
    MONTE_CARLO_SIMULATIONS: int = 3000
    DC_RHO_CORRELATION: float = -0.1
    HOME_ADVANTAGE: int = 50  # Ventaja local en ELO
    
    # Pesos de modelos (suman 1.0)
    WEIGHT_POISSON: float = 0.35
    WEIGHT_DIXON_COLES: float = 0.30
    WEIGHT_MONTE_CARLO: float = 0.20
    WEIGHT_ELO: float = 0.15
    
    # Factores de ajuste
    HOME_GOALS_FACTOR: float = 1.08
    AWAY_GOALS_FACTOR: float = 0.78
    ELO_ADJUSTMENT_FACTOR: float = 4000
    ELO_MIN_FACTOR: float = 0.7
    ELO_MAX_FACTOR: float = 1.4
    
    # Límites
    MAX_GOALS_CALC: int = 9
    MAX_PARTIDOS_GRATIS: int = 5
    
    # Timeouts (segundos)
    TIMEOUT_API: int = 15
    TIMEOUT_SHORT: int = 8


# Diccionario de ligas con sus IDs en API-Football
LIGAS: Dict[str, int] = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39,
    "🇪🇸 La Liga": 140,
    "🇩🇪 Bundesliga": 78,
    "🇮🇹 Serie A": 135,
    "🇫🇷 Ligue 1": 61,
    "🇳🇱 Eredivisie": 88,
    "🇵🇹 Primeira Liga": 94,
    "🌍 Champions League": 2,
    "🌍 Europa League": 3,
    "🌍 Conference League": 848,
    "🌎 Libertadores": 13,
    "🌎 Sudamericana": 11,
    "🌎 Copa America": 9,
    "🌍 Mundial FIFA 2026": 1,
    "🇺🇸 MLS": 253,
    "🇲🇽 Liga MX": 262,
    "🇨🇴 Liga BetPlay": 239,
    "🇦🇷 Primera Division": 128,
    "🇧🇷 Brasileirao": 71,
    "🇹🇷 Super Lig": 203,
    "🇸🇦 Saudi Pro League": 307,
}

# Promedios de estadísticas por liga
LIGAS_PROMEDIOS: Dict[str, Dict[str, float]] = {
    "premier": {"gm": 1.54, "gc": 1.11, "tiros": 14.2, "corners": 5.2, "tarj": 1.8},
    "la liga": {"gm": 1.62, "gc": 1.08, "tiros": 13.8, "corners": 5.5, "tarj": 2.2},
    "bundesliga": {"gm": 1.82, "gc": 1.28, "tiros": 15.1, "corners": 5.8, "tarj": 1.6},
    "serie a": {"gm": 1.48, "gc": 1.07, "tiros": 13.2, "corners": 5.0, "tarj": 2.4},
    "ligue": {"gm": 1.51, "gc": 1.07, "tiros": 13.5, "corners": 5.1, "tarj": 2.0},
    "libertadores": {"gm": 1.32, "gc": 1.08, "tiros": 12.0, "corners": 4.8, "tarj": 2.8},
    "sudamericana": {"gm": 1.28, "gc": 1.07, "tiros": 11.8, "corners": 4.7, "tarj": 2.9},
    "eredivisie": {"gm": 1.88, "gc": 1.32, "tiros": 15.5, "corners": 5.9, "tarj": 1.5},
    "mls": {"gm": 1.45, "gc": 1.20, "tiros": 13.0, "corners": 5.0, "tarj": 1.9},
    "colombia": {"gm": 1.25, "gc": 1.10, "tiros": 11.5, "corners": 4.6, "tarj": 2.6},
    "mundial": {"gm": 1.35, "gc": 1.05, "tiros": 13.0, "corners": 4.8, "tarj": 1.8},
    "copa america": {"gm": 1.28, "gc": 1.08, "tiros": 12.2, "corners": 4.7, "tarj": 2.2},
    "champions": {"gm": 1.45, "gc": 1.05, "tiros": 14.0, "corners": 5.2, "tarj": 1.7},
    "europa": {"gm": 1.42, "gc": 1.08, "tiros": 13.5, "corners": 5.0, "tarj": 1.9},
    "default": {"gm": 1.40, "gc": 1.15, "tiros": 12.8, "corners": 4.9, "tarj": 2.0},
}

# Ligas consideradas "top"
LIGAS_TOP: list = [
    "premier", "la liga", "bundesliga", "serie a", "ligue",
    "champions", "europa", "libertadores", "mundial", "copa america", "eredivisie"
]

# Mapa deUnderstat
UNDERSTAT_MAP: Dict[str, str] = {
    "premier": "EPL",
    "premier league": "EPL",
    "la liga": "La_liga",
    "bundesliga": "Bundesliga",
    "serie a": "Serie_A",
    "ligue 1": "Ligue_1",
    "ligue": "Ligue_1",
}

# Torneos FIFA
TORNEOS_FIFA: list = [
    "mundial", "world cup", "fifa", "copa del mundo", "nations league",
    "eurocopa", "euro 20", "copa america", "gold cup", "afcon"
]

# Selecciones disponibles
SELECCIONES: set = {
    "argentina", "brasil", "brazil", "francia", "france", "alemania", "germany",
    "espana", "spain", "portugal", "inglaterra", "england", "italia", "italy",
    "belgica", "belgium", "croacia", "croatia", "holanda", "netherlands", "uruguay",
    "colombia", "chile", "mexico", "estados unidos", "usa", "japon", "japan",
    "marruecos", "morocco", "senegal", "australia", "corea", "korea", "suiza",
    "switzerland", "dinamarca", "denmark", "polonia", "poland", "austria",
    "turquia", "turkey", "serbia", "ecuador", "peru", "ghana", "nigeria", "camerun",
    "sudafrica", "south africa", "arabia", "saudi", "iran", "qatar", "canada",
    "gales", "wales", "escocia", "scotland", "hungria", "georgia", "eslovenia",
}

# Configuración global
config = Config()
