"""
Tests para APIs de football.
"""
import pytest
from unittest.mock import Mock, patch

from scorpion.api.football import FootballAPI, APIError


class TestFootballAPI:
    """Tests para FootballAPI."""

    def setup_method(self):
        """Setup antes de cada test."""
        self.api = FootballAPI(api_key="test_key")

    def test_limpiar_nombre(self):
        """Debe limpiar nombres de equipos."""
        assert self.api._limpiar_nombre("Botafogo-RJ") == "Botafogo"
        assert self.api._limpiar_nombre("Atletico (MG)") == "Atletico"
        assert self.api._limpiar_nombre("C.D. Guadalajara") == "C.D. Guadalajara"

    def test_cache_temporadas(self):
        """Debe usar caché para temporadas."""
        self.api._cache_temporadas[39] = 2025
        assert self.api.get_temporada(39) == 2025

    def test_cache_elo(self):
        """Debe usar caché para ELO."""
        self.api._cache_elo["Arsenal"] = 1850.5
        assert self.api.get_elo("Arsenal") == 1850.5

    @patch('requests.Session.get')
    def test_request_timeout(self, mock_get):
        """Debe manejar timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        result = self.api._request("http://test.com", {})
        assert result is None

    @patch('requests.Session.get')
    def test_request_error(self, mock_get):
        """Debe manejar errores de request."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Error")
        result = self.api._request("http://test.com", {})
        assert result is None

    def test_parse_fixture(self):
        """Debe parsear fixture correctamente."""
        fixture = {
            "fixture": {"date": "2025-01-15T20:00:00Z"},
            "league": {"name": "Premier League", "id": 39},
            "teams": {
                "home": {"name": "Arsenal", "id": 1},
                "away": {"name": "Chelsea", "id": 2}
            }
        }
        partido = self.api.parse_fixture(fixture)
        assert partido.dia == "2025-01-15"
        assert partido.hora == "20:00"
        assert partido.hora_sort == 1200
        assert partido.local == "Arsenal"
        assert partido.visitante == "Chelsea"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
