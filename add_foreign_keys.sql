-- ═══════════════════════════════════════════════════════════════════════════════
-- MIGRACIÓN: Foreign Keys para integridad referencial
-- ═══════════════════════════════════════════════════════════════════════════════
-- Objetivo: Añadir foreign keys para garantizar integridad referencial a nivel DB.
--
-- ⚠️  ANTES DE EJECUTAR: revisar si hay datos huérfanos. Las FKs fallarán si
--     existen registros que referencian IDs inexistentes. Los DO blocks de
--     abajo son idempotentes (no fallan si la constraint ya existe).
--
-- Ejecutar en el SQL Editor de Supabase.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- FK 1: equipo_partidos_stats.fixture_id → partidos.fixture_id
-- VIABLE: partidos.fixture_id es UNIQUE NOT NULL.
-- ─────────────────────────────────────────────────────────────────────────────
-- Limpieza previa de registros huérfanos (segura: solo borra stats sin partido):
DELETE FROM equipo_partidos_stats
WHERE fixture_id IS NOT NULL
  AND fixture_id NOT IN (SELECT fixture_id FROM partidos);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_eps_fixture_partidos'
    ) THEN
        ALTER TABLE equipo_partidos_stats
        ADD CONSTRAINT fk_eps_fixture_partidos
        FOREIGN KEY (fixture_id) REFERENCES partidos(fixture_id)
        ON DELETE CASCADE;
        RAISE NOTICE '✔ FK fk_eps_fixture_partidos creada';
    ELSE
        RAISE NOTICE '• FK fk_eps_fixture_partidos ya existe';
    END IF;
END $$;

-- ═══════════════════════════════════════════════════════════════════════════════
-- FKs PENDIENTES (requieren migración de datos previa)
-- ═══════════════════════════════════════════════════════════════════════════════
-- Las siguientes relaciones NO se pueden crear directamente porque las columnas
-- actuales usan tipos/valores que no coinciden con la tabla referenciada.
-- Requieren una migración de datos para alinear los tipos antes de aplicar la FK.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- equipo_partidos_stats.team_id → equipos_stats.team_id
--   PROBLEMA: equipos_stats.team_id es BIGINT pero NO es UNIQUE ni NOT NULL.
--   MIGRACIÓN: hacer UNIQUE(team_id) en equipos_stats (requiere desduplicar y
--   llenar NULLs) antes de poder crear la FK.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- bankroll_apuestas.usuario_id / user_stats.usuario_id / alertas.usuario_id /
-- value_bets.usuario_id / ranking.usuario_id → usuarios.id
--   PROBLEMA: estas tablas usan usuario_id VARCHAR(100) con DEFAULT 'default',
--   mientras usuarios.id es BIGSERIAL. No hay match directo.
--   MIGRACIÓN: añadir columna usuario_db_id BIGINT a cada tabla, poblarla desde
--   el mapeo nombre→id, y luego crear las FKs sobre usuario_db_id.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- picks.fixture_id → partidos.fixture_id
--   PROBLEMA: picks.fixture_id es BIGINT pero permite NULL y puede tener
--   fixtures no presentes en partidos (picks manuales).
--   MIGRACIÓN: limpiar picks huérfanos o permitir ON DELETE NO ACTION con
--   verificación previa de integridad.
-- ═══════════════════════════════════════════════════════════════════════════════
