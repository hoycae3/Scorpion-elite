"""
Scorpion Elite - Modelos de Análisis Matemático
==============================================
4 modelos combinados para predecir resultados de fútbol:
- Poisson (35%): Distribución de probabilidad para goles
- Dixon-Coles (30%): Corrige dependencia entre goles marcados/recibidos
- Monte Carlo (20%): Simulación de 1000 partidos
- Elo (15%): Rating histórico de equipos
"""

import numpy as np
import pandas as pd
from scipy.stats import poisson
from typing import Tuple, Dict
import random


class FootballAnalyzer:
    """Analizador de partidos con 4 modelos matemáticos."""
    
    def __init__(self):
        self.elo_ratings = {}  # Cache de ratings Elo por equipo
        self.default_elo = 1500  # Elo inicial para equipos nuevos
        self.elo_k_factor = 32  # Factor K para actualizaciones Elo
    
    def analyze_match(
        self, 
        home_team: str, 
        away_team: str,
        home_goals_avg: float = 1.5,
        away_goals_avg: float = 1.2,
        home_attack: float = 1.0,
        home_defense: float = 1.0,
        away_attack: float = 1.0,
        away_defense: float = 1.0,
        liga_promedio_goles: float = 2.7,
        dc_tau: float = 0.1  # Parámetro de correlación Dixon-Coles
    ) -> Dict:
        """
        Analiza un partido usando los 4 modelos.
        
        Args:
            home_team: Nombre equipo local
            away_team: Nombre equipo visitante
            home_goals_avg: Promedio histórico de goles del local
            away_goals_avg: Promedio histórico de goles del visitante
            home_attack: Factor de ataque del local (1.0 = promedio)
            home_defense: Factor de defensa del local (1.0 = promedio)
            away_attack: Factor de ataque del visitante
            away_defense: Factor de defensa del visitante
            liga_promedio_goles: Promedio de goles de la liga
            dc_tau: Parámetro de correlación Dixon-Coles (-0.25 a 0.25)
        
        Returns:
            Dict con resultados de cada modelo y combinada
        """
        # Calcular lambda (media de goles esperados) ajustado
        lambda_home = self._calculate_lambda(
            home_goals_avg, away_goals_avg,
            home_attack, home_defense, away_attack, away_defense,
            liga_promedio_goles, is_home=True
        )
        lambda_away = self._calculate_lambda(
            home_goals_avg, away_goals_avg,
            home_attack, home_defense, away_attack, away_defense,
            liga_promedio_goles, is_home=False
        )
        
        # Ejecutar los 4 modelos
        poisson_result = self._poisson_model(lambda_home, lambda_away, dc_tau)
        dc_result = self._dixon_coles_model(lambda_home, lambda_away, dc_tau)
        mc_result = self._monte_carlo_model(lambda_home, lambda_away, simulations=1000)
        elo_result = self._elo_model(home_team, away_team)
        
        # Combinar resultados con pesos
        combined = self._combine_models(poisson_result, dc_result, mc_result, elo_result)
        
        return {
            'equipo_local': home_team,
            'equipo_visitante': away_team,
            'lambda_local': lambda_home,
            'lambda_visitante': lambda_away,
            'poisson': poisson_result,
            'dixon_coles': dc_result,
            'monte_carlo': mc_result,
            'elo': elo_result,
            'combined': combined
        }
    
    def _calculate_lambda(
        self, home_avg: float, away_avg: float,
        home_attack: float, home_defense: float,
        away_attack: float, away_defense: float,
        liga_avg: float, is_home: bool
    ) -> float:
        """Calcula el lambda (goles esperados) ajustado."""
        if is_home:
            # Lambda local: ataque propio × defensa rival / promedio de liga × factor casa
            lam = home_avg * home_attack * away_defense / liga_avg
            lam *= 1.12  # Factor de ventaja local (~12%)
        else:
            # Lambda visitante
            lam = away_avg * away_attack * home_defense / liga_avg
            lam *= 0.88  # Factor desventaja visitante
        
        return max(lam, 0.1)  # Mínimo 0.1 goles
    
    def _poisson_model(self, lambda_home: float, lambda_away: float, tau: float) -> Dict:
        """Modelo Poisson básico con corrección Dixon-Coles."""
        results = {
            'prob_home': 0, 'prob_draw': 0, 'prob_away': 0,
            'prob_under_15': 0, 'prob_over_15': 0,
            'prob_btts_yes': 0, 'prob_btts_no': 0,
            'score_probs': {}
        }
        
        max_goals = 7  # Máximos goles a considerar
        
        # Distribución Poisson corregida
        for home_goals in range(max_goals):
            for away_goals in range(max_goals):
                # Probabilidad Poisson base
                p_home = poisson.pmf(home_goals, lambda_home)
                p_away = poisson.pmf(away_goals, lambda_away)
                
                # Corrección Dixon-Coles (dependencia entre goles)
                dc_correction = 1 + tau * min(home_goals, away_goals) * (1 - home_goals/(max_goals-1)) * (1 - away_goals/(max_goals-1))
                p_joint = p_home * p_away * dc_correction
                
                # Guardar probabilidad del score
                results['score_probs'][f"{home_goals}-{away_goals}"] = p_joint
                
                # 1X2
                if home_goals > away_goals:
                    results['prob_home'] += p_joint
                elif home_goals == away_goals:
                    results['prob_draw'] += p_joint
                else:
                    results['prob_away'] += p_joint
                
                # Over/Under 1.5
                if home_goals + away_goals > 1.5:
                    results['prob_over_15'] += p_joint
                else:
                    results['prob_under_15'] += p_joint
                
                # BTTS
                if home_goals > 0 and away_goals > 0:
                    results['prob_btts_yes'] += p_joint
                else:
                    results['prob_btts_no'] += p_joint
        
        # Normalizar
        total = results['prob_home'] + results['prob_draw'] + results['prob_away']
        if total > 0:
            results['prob_home'] /= total
            results['prob_draw'] /= total
            results['prob_away'] /= total
        
        results['peso'] = 0.35
        results['nombre'] = 'Poisson'
        
        return results
    
    def _dixon_coles_model(self, lambda_home: float, lambda_away: float, tau: float) -> Dict:
        """Modelo Dixon-Coles mejorado con correlación de pequeños scores."""
        results = {
            'prob_home': 0, 'prob_draw': 0, 'prob_away': 0,
            'prob_under_15': 0, 'prob_over_15': 0,
            'prob_btts_yes': 0, 'prob_btts_no': 0,
            'score_probs': {}
        }
        
        max_goals = 6
        
        for home_goals in range(max_goals):
            for away_goals in range(max_goals):
                # Modelo DC con correlación rho
                rho = tau  # Parámetro de correlación
                
                # Poisson inflado/deflacionado para 0-0, 0-1, 1-0
                if home_goals <= 1 and away_goals <= 1:
                    if home_goals == 0 and away_goals == 0:
                        correction = 1 + rho
                    elif home_goals == away_goals:
                        correction = 1
                    else:
                        correction = 1 + rho * 0.5
                else:
                    correction = 1 - rho * (home_goals + away_goals) / (2 * max_goals)
                
                p_home = poisson.pmf(home_goals, lambda_home)
                p_away = poisson.pmf(away_goals, lambda_away)
                p_joint = p_home * p_away * correction
                
                results['score_probs'][f"{home_goals}-{away_goals}"] = p_joint
                
                # 1X2
                if home_goals > away_goals:
                    results['prob_home'] += p_joint
                elif home_goals == away_goals:
                    results['prob_draw'] += p_joint
                else:
                    results['prob_away'] += p_joint
                
                # Over/Under 1.5
                if home_goals + away_goals > 1.5:
                    results['prob_over_15'] += p_joint
                else:
                    results['prob_under_15'] += p_joint
                
                # BTTS
                if home_goals > 0 and away_goals > 0:
                    results['prob_btts_yes'] += p_joint
                else:
                    results['prob_btts_no'] += p_joint
        
        # Normalizar
        total = results['prob_home'] + results['prob_draw'] + results['prob_away']
        if total > 0:
            results['prob_home'] /= total
            results['prob_draw'] /= total
            results['prob_away'] /= total
        
        results['peso'] = 0.30
        results['nombre'] = 'Dixon-Coles'
        
        return results
    
    def _monte_carlo_model(self, lambda_home: float, lambda_away: float, simulations: int = 1000) -> Dict:
        """Simulación Monte Carlo."""
        results = {
            'prob_home': 0, 'prob_draw': 0, 'prob_away': 0,
            'prob_under_15': 0, 'prob_over_15': 0,
            'prob_btts_yes': 0, 'prob_btts_no': 0,
            'score_probs': {},
            'simulations': simulations
        }
        
        # Contadores
        home_wins, draws, away_wins = 0, 0, 0
        under_15, over_15 = 0, 0
        btts_yes, btts_no = 0, 0
        score_count = {}
        
        # Semilla para reproducibilidad (opcional)
        random.seed(42)
        np.random.seed(42)
        
        for _ in range(simulations):
            # Simular goles con Poisson
            home_goals = min(int(np.random.poisson(lambda_home)), 8)
            away_goals = min(int(np.random.poisson(lambda_away)), 8)
            
            # Contar resultados
            if home_goals > away_goals:
                home_wins += 1
            elif home_goals == away_goals:
                draws += 1
            else:
                away_wins += 1
            
            # Over/Under 1.5
            if home_goals + away_goals > 1.5:
                over_15 += 1
            else:
                under_15 += 1
            
            # BTTS
            if home_goals > 0 and away_goals > 0:
                btts_yes += 1
            else:
                btts_no += 1
            
            # Score
            score = f"{home_goals}-{away_goals}"
            score_count[score] = score_count.get(score, 0) + 1
        
        # Convertir a probabilidades
        results['prob_home'] = home_wins / simulations
        results['prob_draw'] = draws / simulations
        results['prob_away'] = away_wins / simulations
        results['prob_over_15'] = over_15 / simulations
        results['prob_under_15'] = under_15 / simulations
        results['prob_btts_yes'] = btts_yes / simulations
        results['prob_btts_no'] = btts_no / simulations
        results['score_probs'] = {k: v/simulations for k, v in score_count.items()}
        
        results['peso'] = 0.20
        results['nombre'] = 'Monte Carlo'
        
        return results
    
    def _elo_model(self, home_team: str, away_team: str) -> Dict:
        """Modelo Elo simple."""
        # Obtener o inicializar ratings
        home_elo = self.elo_ratings.get(home_team, self.default_elo)
        away_elo = self.elo_ratings.get(away_team, self.default_elo)
        
        # Calcular expectativa de victoria (Elo)
        elo_diff = home_elo - away_elo
        expected_home = 1 / (1 + 10 ** (-elo_diff / 400))
        expected_away = 1 - expected_home
        
        # Convertir a probabilidades 1X2 (asumiendo ~27% de empates base)
        draw_base = 0.27
        home_adj = expected_home * (1 - draw_base)
        away_adj = expected_away * (1 - draw_base)
        total = home_adj + away_adj + draw_base
        
        results = {
            'prob_home': home_adj / total,
            'prob_draw': draw_base / total,
            'prob_away': away_adj / total,
            'elo_local': home_elo,
            'elo_visitante': away_elo,
            'elo_diff': elo_diff
        }
        
        # Para mercados adicionales, estimar basándose en diferencia Elo
        goal_diff_factor = abs(elo_diff) / 400
        
        if elo_diff > 0:
            results['prob_over_15'] = 0.45 + min(goal_diff_factor * 0.2, 0.15)
            results['prob_btts_yes'] = 0.50 + min(goal_diff_factor * 0.1, 0.10)
        else:
            results['prob_over_15'] = 0.45 - min(goal_diff_factor * 0.1, 0.10)
            results['prob_btts_yes'] = 0.50 - min(goal_diff_factor * 0.05, 0.05)
        
        results['prob_under_15'] = 1 - results['prob_over_15']
        results['prob_btts_no'] = 1 - results['prob_btts_yes']
        
        results['peso'] = 0.15
        results['nombre'] = 'Elo'
        
        return results
    
    def _combine_models(self, poisson: Dict, dc: Dict, mc: Dict, elo: Dict) -> Dict:
        """Combina los 4 modelos con sus pesos."""
        combined = {}
        
        mercados = ['prob_home', 'prob_draw', 'prob_away', 'prob_over_15', 'prob_under_15', 'prob_btts_yes', 'prob_btts_no']
        
        for mercado in mercados:
            p_val = poisson.get(mercado, 0) * 0.35
            dc_val = dc.get(mercado, 0) * 0.30
            mc_val = mc.get(mercado, 0) * 0.20
            elo_val = elo.get(mercado, 0) * 0.15
            combined[mercado] = p_val + dc_val + mc_val + elo_val
        
        # Determinar pick recomendado
        if combined['prob_home'] > combined['prob_draw'] and combined['prob_home'] > combined['prob_away']:
            combined['pick'] = '1'
            combined['prob_pick'] = combined['prob_home']
        elif combined['prob_away'] > combined['prob_draw'] and combined['prob_away'] > combined['prob_home']:
            combined['pick'] = '2'
            combined['prob_pick'] = combined['prob_away']
        else:
            combined['pick'] = 'X'
            combined['prob_pick'] = combined['prob_draw']
        
        # Calcular confianza (0-100%)
        confianza = int(combined['prob_pick'] * 100)
        combined['confianza'] = confianza
        
        # Clasificación A+, B, C, D
        if confianza >= 75:
            combined['rating'] = 'A+'
        elif confianza >= 55:
            combined['rating'] = 'B'
        elif confianza >= 40:
            combined['rating'] = 'C'
        else:
            combined['rating'] = 'D'
        
        return combined
    
    def update_elo(self, home_team: str, away_team: str, home_goals: int, away_goals: int):
        """Actualiza ratings Elo después de un partido."""
        home_elo = self.elo_ratings.get(home_team, self.default_elo)
        away_elo = self.elo_ratings.get(away_team, self.default_elo)
        
        # Calcular esperado
        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        expected_away = 1 - expected_home
        
        # Resultado real
        if home_goals > away_goals:
            actual_home, actual_away = 1, 0
        elif home_goals < away_goals:
            actual_home, actual_away = 0, 1
        else:
            actual_home, actual_away = 0.5, 0.5
        
        # Actualizar
        new_home_elo = home_elo + self.elo_k_factor * (actual_home - expected_home)
        new_away_elo = away_elo + self.elo_k_factor * (actual_away - expected_away)
        
        self.elo_ratings[home_team] = new_home_elo
        self.elo_ratings[away_team] = new_away_elo


# Función helper para usar directamente
def analyze(home: str, away: str, **kwargs) -> Dict:
    """Función simple para analizar un partido."""
    analyzer = FootballAnalyzer()
    return analyzer.analyze_match(home, away, **kwargs)
