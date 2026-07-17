-- Scorpion Elite - Supabase Schema
-- Ejecutar este script en el SQL Editor de Supabase

-- Tabla principal de partidos
CREATE TABLE IF NOT EXISTS partidos (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    hora_utc VARCHAR(10),
    hora_local VARCHAR(10),
    liga VARCHAR(255),
    liga_id INTEGER,
    pais VARCHAR(100),
    prioridad INTEGER DEFAULT 0,
    equipo_home VARCHAR(255) NOT NULL,
    equipo_away VARCHAR(255) NOT NULL,
    prob_home INTEGER DEFAULT 50,
    prob_draw INTEGER DEFAULT 30,
    prob_away INTEGER DEFAULT 20,
    cuota_1 DECIMAL(5,2) DEFAULT 1.90,
    cuota_x DECIMAL(5,2) DEFAULT 3.50,
    cuota_2 DECIMAL(5,2) DEFAULT 4.00,
    pick VARCHAR(5),
    cuota_pick DECIMAL(5,2) DEFAULT 1.90,
    confianza INTEGER DEFAULT 50,
    valor DECIMAL(5,2) DEFAULT 0,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para búsqueda por fecha
CREATE INDEX IF NOT EXISTS idx_partidos_fecha ON partidos(fecha);

-- Índice para búsqueda por liga
CREATE INDEX IF NOT EXISTS idx_partidos_liga ON partidos(liga_id);

-- Índice para búsqueda por prioridad
CREATE INDEX IF NOT EXISTS idx_partidos_prioridad ON partidos(prioridad DESC);

-- Tabla de historial de picks (para estadísticas)
CREATE TABLE IF NOT EXISTS historial_picks (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT NOT NULL,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    equipo_home VARCHAR(255),
    equipo_away VARCHAR(255),
    pick VARCHAR(5),
    cuota DECIMAL(5,2),
    confianza INTEGER,
    resultado VARCHAR(20), -- 'ganado', 'perdido', 'pendiente'
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para historial
CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_picks(fecha);

-- Políticas RLS (Row Level Security) - permite lectura pública
ALTER TABLE partidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_picks ENABLE ROW LEVEL SECURITY;

-- Política para lectura pública
CREATE POLICY "Allow public read" ON partidos FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON historial_picks FOR SELECT USING (true);

-- Política para inserción (solo desde el scraper con service role)
CREATE POLICY "Allow insert from service" ON partidos FOR INSERT WITH CHECK (true);

-- Comentario de ayuda
COMMENT ON TABLE partidos IS 'Partidos de fútbol del día con predicciones';
COMMENT ON TABLE historial_picks IS 'Historial de picks para seguimiento de resultados';
