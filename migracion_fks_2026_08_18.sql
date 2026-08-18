-- ═══════════════════════════════════════════════════════════════════════════════
-- MIGRACIÓN: Foreign Keys para integridad referencial (completa)
-- Fecha: 2026-08-18
-- 
-- Crea FKs para que al borrar un partido/equipo, los registros dependientes
-- (cuotas, stats, picks) se borren automáticamente (CASCADE).
--
-- ⚠️ Ejecutar en Supabase → SQL Editor. Es idempotente (no falla si ya existe).
-- ═══════════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- FK 1: equipo_partidos_stats.fixture_id → partidos.fixture_id
-- Borra stats huérfanas si se borra el partido.
-- ─────────────────────────────────────────────────────────────────────────────
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

-- ─────────────────────────────────────────────────────────────────────────────
-- FK 2: cuotas.fixture_id → partidos.fixture_id
-- Borra cuotas si se borra el partido.
-- ─────────────────────────────────────────────────────────────────────────────
DELETE FROM cuotas
WHERE fixture_id IS NOT NULL
  AND fixture_id NOT IN (SELECT fixture_id FROM partidos);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_cuotas_fixture_partidos'
    ) THEN
        ALTER TABLE cuotas
        ADD CONSTRAINT fk_cuotas_fixture_partidos
        FOREIGN KEY (fixture_id) REFERENCES partidos(fixture_id)
        ON DELETE CASCADE;
        RAISE NOTICE '✔ FK fk_cuotas_fixture_partidos creada';
    ELSE
        RAISE NOTICE '• FK fk_cuotas_fixture_partidos ya existe';
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- FK 3: equipo_partidos_stats.team_id → equipos_stats.team_id
-- Asegura que cada stat apunte a un equipo existente.
-- ─────────────────────────────────────────────────────────────────────────────
-- Limpiar stats de equipos que ya no existen
DELETE FROM equipo_partidos_stats
WHERE team_id IS NOT NULL
  AND team_id NOT IN (SELECT team_id FROM equipos_stats WHERE team_id IS NOT NULL);

-- Necesitamos UNIQUE en equipos_stats.team_id para poder usarlo como FK
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'equipos_stats' AND constraint_name = 'equipos_stats_team_id_key'
    ) THEN
        EXECUTE 'ALTER TABLE equipos_stats ADD CONSTRAINT equipos_stats_team_id_key UNIQUE (team_id)';
        RAISE NOTICE '✔ UNIQUE constraint en equipos_stats.team_id creado';
    ELSE
        RAISE NOTICE '• UNIQUE constraint en equipos_stats.team_id ya existe';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_eps_team_equipos'
    ) THEN
        ALTER TABLE equipo_partidos_stats
        ADD CONSTRAINT fk_eps_team_equipos
        FOREIGN KEY (team_id) REFERENCES equipos_stats(team_id)
        ON DELETE CASCADE;
        RAISE NOTICE '✔ FK fk_eps_team_equipos creada';
    ELSE
        RAISE NOTICE '• FK fk_eps_team_equipos ya existe';
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- FK 4: picks.fixture_id → partidos.fixture_id
-- ON DELETE SET NULL (no borra el pick, solo lo desvincula)
-- ─────────────────────────────────────────────────────────────────────────────
-- Limpiar picks huérfanos (fixture_id no existente en partidos)
DELETE FROM picks
WHERE fixture_id IS NOT NULL
  AND fixture_id NOT IN (SELECT fixture_id FROM partidos);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_picks_fixture_partidos'
    ) THEN
        ALTER TABLE picks
        ADD CONSTRAINT fk_picks_fixture_partidos
        FOREIGN KEY (fixture_id) REFERENCES partidos(fixture_id)
        ON DELETE SET NULL;
        RAISE NOTICE '✔ FK fk_picks_fixture_partidos creada';
    ELSE
        RAISE NOTICE '• FK fk_picks_fixture_partidos ya existe';
    END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFICACIÓN
-- ═══════════════════════════════════════════════════════════════════════════════
-- Después de ejecutar, correr esto para ver las FKs creadas:
-- SELECT constraint_name, table_name, confrelid::regclass AS references
-- FROM information_schema.table_constraints
-- WHERE constraint_type = 'FOREIGN' AND table_schema = 'public'
-- ORDER BY table_name;
-- Debería mostrar 4 FKs: fk_eps_fixture_partidos, fk_cuotas_fixture_partidos,
-- fk_eps_team_equipos, fk_picks_fixture_partidos
