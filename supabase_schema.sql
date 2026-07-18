-- Scorpion Elite - Schema Simple
-- Ejecutar en SQL Editor de Supabase

-- TABLA PARTIDOS
CREATE TABLE IF NOT EXISTS partidos (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    hora VARCHAR(10),
    liga VARCHAR(255),
    pais VARCHAR(100),
    equipo_local VARCHAR(255) NOT NULL,
    equipo_visitante VARCHAR(255) NOT NULL,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_partidos_fecha ON partidos(fecha);
CREATE INDEX IF NOT EXISTS idx_partidos_liga ON partidos(liga);

-- RLS
ALTER TABLE partidos ENABLE ROW LEVEL SECURITY;

-- Políticas (lectura y escritura pública)
DROP POLICY IF EXISTS "Allow public read" ON partidos;
DROP POLICY IF EXISTS "Allow public insert" ON partidos;
DROP POLICY IF EXISTS "Allow public update" ON partidos;
DROP POLICY IF EXISTS "Allow public delete" ON partidos;

CREATE POLICY "Allow public read" ON partidos FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON partidos FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update" ON partidos FOR UPDATE USING (true);
CREATE POLICY "Allow public delete" ON partidos FOR DELETE USING (true);

-- Función auto-update timestamp
CREATE OR REPLACE FUNCTION update_partidos_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_partidos_timestamp ON partidos;
CREATE TRIGGER update_partidos_timestamp 
    BEFORE UPDATE ON partidos
    FOR EACH ROW EXECUTE FUNCTION update_partidos_timestamp();

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA ESTADISTICAS EQUIPOS
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS estadisticas_equipos (
    id BIGSERIAL PRIMARY KEY,
    equipo VARCHAR(255) NOT NULL,
    liga VARCHAR(255),
    temporada VARCHAR(50),
    partidos_jugados INTEGER DEFAULT 0,
    victorias INTEGER DEFAULT 0,
    empates INTEGER DEFAULT 0,
    derrotas INTEGER DEFAULT 0,
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    lambda_local DECIMAL(4,2) DEFAULT 1.3,
    lambda_visitante DECIMAL(4,2) DEFAULT 1.1,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(equipo, temporada)
);

CREATE INDEX IF NOT EXISTS idx_stats_equipo ON estadisticas_equipos(equipo);

ALTER TABLE estadisticas_equipos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read" ON estadisticas_equipos;
DROP POLICY IF EXISTS "Allow public insert" ON estadisticas_equipos;
DROP POLICY IF EXISTS "Allow public update" ON estadisticas_equipos;
DROP POLICY IF EXISTS "Allow public delete" ON estadisticas_equipos;

CREATE POLICY "stats_all" ON estadisticas_equipos FOR ALL USING (true) WITH CHECK (true);
