-- ================================================================================
-- SCRIPT: Recalcular lambda_local y lambda_visitante desde historial
-- ================================================================================
-- Este script recalcula los lambdas basándose en equipo_partidos_stats
-- para que reflejen el rendimiento real del equipo como LOCAL y VISITANTE
-- ================================================================================

-- PASO 1: Crear tabla temporal con cálculos
DROP TABLE IF EXISTS temp_lambdas;

CREATE TEMP TABLE temp_lambdas AS
SELECT 
    team_id,
    CASE 
        WHEN COUNT(CASE WHEN es_local = true THEN 1 END) > 0 
        THEN ROUND(
            SUM(CASE WHEN es_local = true THEN COALESCE(goles_favor, 0) ELSE 0 END)::NUMERIC / 
            COUNT(CASE WHEN es_local = true THEN 1 END), 
            2
        )
        ELSE 1.3 
    END AS nuevo_lambda_local,
    CASE 
        WHEN COUNT(CASE WHEN es_local = false THEN 1 END) > 0 
        THEN ROUND(
            SUM(CASE WHEN es_local = false THEN COALESCE(goles_favor, 0) ELSE 0 END)::NUMERIC / 
            COUNT(CASE WHEN es_local = false THEN 1 END), 
            2
        )
        ELSE 1.1 
    END AS nuevo_lambda_visitante,
    COUNT(CASE WHEN es_local = true THEN 1 END) AS pj_local,
    COUNT(CASE WHEN es_local = false THEN 1 END) AS pj_visitante
FROM equipo_partidos_stats
WHERE team_id IS NOT NULL
GROUP BY team_id;

-- PASO 2: Actualizar equipos_stats con los nuevos valores
UPDATE equipos_stats e
SET 
    lambda_local = t.nuevo_lambda_local,
    lambda_visitante = t.nuevo_lambda_visitante
FROM temp_lambdas t
WHERE e.team_id = t.team_id;

-- PASO 3: Mostrar algunos ejemplos
SELECT 
    equipo,
    lambda_local,
    lambda_visitante,
    lambda_local - lambda_visitante AS diferencia
FROM equipos_stats
WHERE lambda_local IS NOT NULL
ORDER BY lambda_local DESC
LIMIT 20;

-- Confirmar
SELECT COUNT(*) as equipos_actualizados FROM temp_lambdas;
