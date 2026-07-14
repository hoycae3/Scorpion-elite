"""
Tests para el motor de análisis matemático.
"""
import pytest
from scorpion.models.math import MotorAnalisis, MercadoPick, CalculoResultado


class TestPoisson:
    """Tests para distribución de Poisson."""

    def setup_method(self):
        """Setup antes de cada test."""
        self.motor = MotorAnalisis()

    def test_poisson_lambda_cero(self):
        """Test Poisson con lambda=0."""
        # P(X=0) = 1 cuando lambda = 0
        assert self.motor.poisson_probabilidad(0, 0) == 1.0
        # P(X>0) = 0 cuando lambda = 0
        assert self.motor.poisson_probabilidad(0, 1) == 0.0
        assert self.motor.poisson_probabilidad(0, 5) == 0.0

    def test_poisson_probabilidad_negativa(self):
        """Test Poisson con valores negativos de k."""
        assert self.motor.poisson_probabilidad(1, -1) == 0.0

    def test_poisson_lambda_1(self):
        """Test Poisson con lambda=1."""
        # P(X=0) = e^-1 ≈ 0.368
        p0 = self.motor.poisson_probabilidad(1, 0)
        assert 0.36 < p0 < 0.37

    def test_poisson_suma_probabilidades(self):
        """La suma de todas las probabilidades debe ser ~1."""
        lam = 1.5
        total = sum(self.motor.poisson_probabilidad(lam, k) for k in range(20))
        assert 0.99 < total < 1.01


class TestModelos1X2:
    """Tests para modelos de probabilidad 1X2."""

    def setup_method(self):
        self.motor = MotorAnalisis()

    def test_poisson_probabilidades_suman_100(self):
        """Las probabilidades deben sumar 100%."""
        p1, px, p2 = self.motor.modelo_poisson_1x2(1.5, 1.2)
        total = p1 + px + p2
        assert 99 < total < 101

    def test_monte_carlo_probabilidades_suman_100(self):
        """Las probabilidades Monte Carlo deben sumar ~100%."""
        p1, px, p2, _, _ = self.motor.modelo_monte_carlo_1x2(1.5, 1.2, n=1000)
        total = p1 + px + p2
        assert 99 < total < 101

    def test_elo_equipo_mas_fuerte(self):
        """Un equipo con mayor ELO debe tener mayor probabilidad."""
        # ELO alto local
        p1, px, p2 = self.motor.modelo_elo_1x2(1800, 1500)
        assert p1 > p2

    def test_elo_equipos_iguales(self):
        """Equipos con mismo ELO deben tener probabilidades similares."""
        p1, px, p2 = self.motor.modelo_elo_1x2(1500, 1500)
        # Con ventaja local, local debería ser favorito
        assert p1 > p2


class TestOverUnder:
    """Tests para mercados Over/Under."""

    def setup_method(self):
        self.motor = MotorAnalisis()

    def test_over_05_probabilidad(self):
        """Over 0.5 con xG=1.0 debe ser aproximadamente 63%."""
        over05, _, _, _ = self.motor.calcular_over_under(1.0)
        # P(X>=1) = 1 - P(X=0) = 1 - e^-1 ≈ 63.2%
        assert 60 < over05 < 70

    def test_over_35_poco_probable(self):
        """Over 3.5 debe ser bajo para partidos pocos goleadores."""
        _, _, _, over35 = self.motor.calcular_over_under(1.0)
        assert over35 < 20

    def test_mas_goles_mas_over(self):
        """Con más xG, Over 2.5 debe ser mayor."""
        over25_low, _, _, _ = self.motor.calcular_over_under(1.0)
        over25_high, _, _, _ = self.motor.calcular_over_under(3.0)
        assert over25_high > over25_low


class TestBTTS:
    """Tests para BTTS."""

    def setup_method(self):
        self.motor = MotorAnalisis()

    def test_btts_symmetry(self):
        """BTTS Si + BTTS No debe ser 100%."""
        btts_si, btts_no = self.motor.calcular_btts(1.5, 1.2)
        assert 99 < btts_si + btts_no < 101

    def test_equipos_solidos_no_marcan(self):
        """Equipos con xG bajo deben tener BTTS bajo."""
        btts_si, _ = self.motor.calcular_btts(0.5, 0.5)
        assert btts_si < 30


class TestCalculoCompleto:
    """Tests para análisis completo."""

    def setup_method(self):
        self.motor = MotorAnalisis()

    def test_analisis_sin_datos(self):
        """Análisis sin datos reales debe funcionar."""
        resultado = self.motor.analizar(liga="Premier League")
        assert isinstance(resultado, CalculoResultado)
        assert resultado.p1 + resultado.px + resultado.p2 > 99
        assert resultado.rango in ["C", "D"]

    def test_analisis_con_datos_reales(self):
        """Análisis con datos reales debe tener mejor confianza."""
        resultado = self.motor.analizar(
            gm_local=1.8, gc_local=1.0,
            gm_visitante=1.2, gc_visitante=1.3,
            liga="Premier League",
            usar_datos_reales=True
        )
        assert resultado.datos_reales is True
        assert resultado.rango in ["A+", "B", "C"]

    def test_analisis_con_elo(self):
        """Análisis con ELO debe ajustar probabilidades."""
        sin_elo = self.motor.analizar(gm_local=1.5, gm_visitante=1.5, liga="Premier League")
        con_elo = self.motor.analizar(
            gm_local=1.5, gm_visitante=1.5,
            elo_local=1800, elo_visitante=1500,
            liga="Premier League"
        )
        # El equipo con mayor ELO debe tener más probabilidad de ganar
        assert con_elo.p1 > sin_elo.p1 or con_elo.p2 < sin_elo.p2

    def test_mercados_generados(self):
        """Debe generar mercados con probabilidades válidas."""
        resultado = self.motor.analizar(gm_local=1.5, gm_visitante=1.2, liga="Premier League")
        assert len(resultado.mercados) > 0
        for m in resultado.mercados:
            assert isinstance(m, MercadoPick)
            assert 0 <= m.probabilidad <= 100
            assert m.cuota_referencia >= 1.0


class TestMercadoPick:
    """Tests para MercadoPick."""

    def test_validacion_probabilidad(self):
        """MercadoPick permite valores fuera de rango (validación informativa)."""
        # La validación actual es informativa, no levanta excepciones
        m = MercadoPick("Test", -10, 2.0)
        assert m.probabilidad == -10  # Se acepta el valor

    def test_validacion_cuota(self):
        """MercadoPick permite cuota < 1.0."""
        m = MercadoPick("Test", 50, 0.9)
        assert m.cuota_referencia == 0.9

    def test_creacion_correcta(self):
        """Creación con valores válidos."""
        m = MercadoPick("Victoria Local", 55, 1.82, edge=2.5, es_recomendado=True)
        assert m.nombre == "Victoria Local"
        assert m.probabilidad == 55
        assert m.edge == 2.5
        assert m.es_recomendado is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
