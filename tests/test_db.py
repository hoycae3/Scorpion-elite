"""
Tests para el módulo de base de datos.
"""
import pytest
import tempfile
import os
from datetime import date

from scorpion.db.database import Database, DatabaseError, ValidationError


class TestDatabase:
    """Tests para Database."""

    def setup_method(self):
        """Crea base de datos temporal."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.db = Database(self.temp_db.name)

    def teardown_method(self):
        """Limpia archivo temporal."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass

    def test_creacion_usuario(self):
        """Debe crear usuario correctamente."""
        self.db.guardar_usuario("12345", "Test User", "gratis", 30)
        usuario = self.db.get_usuario("12345")
        assert usuario is not None
        assert usuario["nombre"] == "Test User"
        assert usuario["plan"] == "gratis"

    def test_usuario_no_existe(self):
        """Debe retornar None para usuario inexistente."""
        usuario = self.db.get_usuario("nonexistent")
        assert usuario is None

    def test_validacion_cedula_vacia(self):
        """Debe rechazar cédula vacía."""
        with pytest.raises(ValidationError):
            self.db.guardar_usuario("", "Test", "gratis", 30)

    def test_validacion_plan_invalido(self):
        """Debe rechazar plan inválido."""
        with pytest.raises(ValidationError):
            self.db.guardar_usuario("12345", "Test", "invalid_plan", 30)

    def test_validacion_dias_invalidos(self):
        """Debe rechazar días inválidos."""
        with pytest.raises(ValidationError):
            self.db.guardar_usuario("12345", "Test", "gratis", 0)
        with pytest.raises(ValidationError):
            self.db.guardar_usuario("12345", "Test", "gratis", 50000)

    def test_login_admin_correcto(self):
        """Debe verificar contraseña admin correcta."""
        assert self.db.login_admin("scorpion_admin_2025") is True

    def test_login_admin_incorrecto(self):
        """Debe rechazar contraseña incorrecta."""
        assert self.db.login_admin("wrong_password") is False

    def test_verificar_acceso_usuario_activo(self):
        """Usuario activo debe tener acceso."""
        ok, plan, dr = self.db.verificar_acceso("admin")
        assert ok is True
        assert plan == "admin"

    def test_verificar_acceso_usuario_inactivo(self):
        """Usuario inexistente no debe tener acceso."""
        ok, plan, dr = self.db.verificar_acceso("nonexistent999")
        assert ok is False

    def test_guardar_pick(self):
        """Debe guardar pick correctamente."""
        self.db.guardar_pick(
            fecha="2025-01-15",
            liga="Premier League",
            local="Arsenal",
            visitante="Chelsea",
            hora="20:00",
            mercado="Over 2.5",
            detalle="xG alto",
            cuota=1.85,
            edge=3.2,
            confianza=72.5,
            rango="A+"
        )
        picks = self.db.get_picks("2025-01-15")
        assert len(picks) == 1
        assert picks[0]["local"] == "Arsenal"
        assert picks[0]["mercado"] == "Over 2.5"

    def test_incrementar_consultas(self):
        """Debe incrementar contador de consultas."""
        self.db.guardar_usuario("test123", "Test", "gratis", 30)
        count1 = self.db.incrementar_consultas("test123")
        assert count1 == 1
        count2 = self.db.incrementar_consultas("test123")
        assert count2 == 2

    def test_estadisticas(self):
        """Debe retornar estadísticas."""
        stats = self.db.get_estadisticas()
        assert "usuarios" in stats
        assert "activos" in stats
        assert "picks" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
