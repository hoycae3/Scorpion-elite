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
