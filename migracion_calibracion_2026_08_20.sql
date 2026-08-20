-- Migración: activar calibración automática por equipo (sesión 2026-08-19/20)
-- Ejecutar UNA VEZ en el SQL Editor de Supabase. Sin estas columnas,
-- _insertar_pick_resiliente las omite y la calibración nunca arranca.

ALTER TABLE picks ADD COLUMN IF NOT EXISTS lambda_local_predicha DECIMAL(5,3);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS lambda_visitante_predicha DECIMAL(5,3);

-- A partir de aquí: cada pick nuevo guarda los lambdas predichos y cada
-- liquidación (FT en sync) alimenta calibracion_equipos + calibracion_historico.
