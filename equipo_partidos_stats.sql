-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA EQUIPO_PARTIDOS_STATS
-- Estadísticas de los últimos 5 partidos jugados por cada equipo
-- Usada para calcular promedios móviles (corners, tiros, tarjetas)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS equipo_partidos_stats (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL,
    equipo VARCHAR(255),
    fixture_id BIGINT NOT NULL,
    fecha DATE,
    liga VARCHAR(255),
    es_local BOOLEAN,
    resultado VARCHAR(20),  -- 'W', 'D', 'L'
    -- Estadísticas del equipo
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    -- Tiros
    tiros_totales INTEGER DEFAULT 0,
    tiros_arco INTEGER DEFAULT 0,
    tiros_fuera INTEGER DEFAULT 0,
    -- Corners
    corners INTEGER DEFAULT 0,
    -- Tarjetas
    amarillas INTEGER DEFAULT 0,
    rojas INTEGER DEFAULT 0,
    -- Posesión
    posesion INTEGER DEFAULT 0,
    -- Faltas
    faltas INTEGER DEFAULT 0,
    -- Atajadas
    atajadas INTEGER DEFAULT 0,
    -- Creado
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    -- Unique para evitar duplicados
    UNIQUE(team_id, fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_equipo_partidos_team ON equipo_partidos_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_equipo_partidos_fecha ON equipo_partidos_stats(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_equipo_partidos_team_fecha ON equipo_partidos_stats(team_id, fecha DESC);

ALTER TABLE equipo_partidos_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "equipo_partidos_stats_all" ON equipo_partidos_stats FOR ALL USING (true) WITH CHECK (true);
