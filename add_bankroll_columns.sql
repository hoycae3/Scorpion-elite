-- ════════════════════════════════════════════════════════════════════════════
-- SCORPION ELITE - FIX COMPLETO TABLAS BANKROLL (UN SOLO SCRIPT)
-- ════════════════════════════════════════════════════════════════════════════
-- Errores resueltos:
--   PGRST204 "No se pudo encontrar la columna 'usuario_id' de 'user_stats'"
--   PGRST204 "No se pudo encontrar la columna 'bankroll_inicial' de 'user_stats'"
--   PGRST204 "No se pudo encontrar la columna 'total_retirado' de 'user_stats'"
--
-- EJECUTAR EN: Supabase Dashboard > SQL Editor > pegar todo > Run
-- SEGURO: usa CREATE IF NOT EXISTS y ALTER ADD IF NOT EXISTS (no borra nada)
-- ════════════════════════════════════════════════════════════════════════════


-- ─────────────────────────────────────────────────────────────────────────────
-- 1) TABLA user_stats
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_stats (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(100),
    total_picks INTEGER DEFAULT 0,
    picks_ganados INTEGER DEFAULT 0,
    picks_perdidos INTEGER DEFAULT 0,
    picks_nulos INTEGER DEFAULT 0,
    roi_1x2 DECIMAL(6,2) DEFAULT 0,
    roi_over_under DECIMAL(6,2) DEFAULT 0,
    roi_btts DECIMAL(6,2) DEFAULT 0,
    roi_corners DECIMAL(6,2) DEFAULT 0,
    roi_tarjetas DECIMAL(6,2) DEFAULT 0,
    roi_remates DECIMAL(6,2) DEFAULT 0,
    roi_general DECIMAL(6,2) DEFAULT 0,
    yield_general DECIMAL(6,2) DEFAULT 0,
    roi_poisson DECIMAL(6,2) DEFAULT 0,
    roi_dixon DECIMAL(6,2) DEFAULT 0,
    roi_montecarlo DECIMAL(6,2) DEFAULT 0,
    roi_elo DECIMAL(6,2) DEFAULT 0,
    racha_actual INTEGER DEFAULT 0,
    racha_maxima INTEGER DEFAULT 0,
    mejor_tipo_pick VARCHAR(50),
    peor_tipo_pick VARCHAR(50),
    bankroll_actual DECIMAL(12,2) DEFAULT 1000.00,
    bankroll_inicial DECIMAL(12,2) DEFAULT 1000.00,
    total_retirado DECIMAL(12,2) DEFAULT 0.00,
    confianza_promedio DECIMAL(5,2) DEFAULT 0,
    precision_alta_confianza DECIMAL(5,2) DEFAULT 0,
    badges TEXT[],
    streak_tipo VARCHAR(10) DEFAULT 'neutro',
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(100) UNIQUE;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS nombre VARCHAR(100);
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_picks INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS picks_ganados INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS picks_perdidos INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS picks_nulos INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS roi_general DECIMAL(6,2) DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS yield_general DECIMAL(6,2) DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS racha_actual INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS racha_maxima INTEGER DEFAULT 0;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS bankroll_actual DECIMAL(12,2) DEFAULT 1000.00;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS bankroll_inicial DECIMAL(12,2) DEFAULT 1000.00;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS total_retirado DECIMAL(12,2) DEFAULT 0.00;
ALTER TABLE user_stats ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_userstats_usuario ON user_stats(usuario_id);
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY "userstats_all" ON user_stats FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 2) TABLA bankroll_apuestas
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bankroll_apuestas (
    id BIGSERIAL PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    fixture_id BIGINT,
    fecha DATE NOT NULL,
    equipo VARCHAR(255),
    cuota DECIMAL(6,2),
    cantidad DECIMAL(12,2),
    mercado VARCHAR(50),
    pick_id BIGINT,
    ganancia DECIMAL(12,2) DEFAULT 0,
    resultado BOOLEAN,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS usuario VARCHAR(100);
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS fixture_id BIGINT;
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS fecha DATE;
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS equipo VARCHAR(255);
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS cuota DECIMAL(6,2);
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS cantidad DECIMAL(12,2);
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS mercado VARCHAR(50);
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS pick_id BIGINT;
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS ganancia DECIMAL(12,2) DEFAULT 0;
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS resultado BOOLEAN;
ALTER TABLE bankroll_apuestas ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_bankroll_apuestas_usuario ON bankroll_apuestas(usuario);
CREATE INDEX IF NOT EXISTS idx_bankroll_apuestas_fixture ON bankroll_apuestas(fixture_id);
CREATE INDEX IF NOT EXISTS idx_bankroll_apuestas_resultado ON bankroll_apuestas(resultado);
ALTER TABLE bankroll_apuestas ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY "bankroll_apuestas_all" ON bankroll_apuestas FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 3) TABLA bankroll_retiros
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bankroll_retiros (
    id BIGSERIAL PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    fecha DATE NOT NULL,
    cantidad DECIMAL(12,2) NOT NULL,
    nota VARCHAR(255),
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE bankroll_retiros ADD COLUMN IF NOT EXISTS usuario VARCHAR(100);
ALTER TABLE bankroll_retiros ADD COLUMN IF NOT EXISTS fecha DATE;
ALTER TABLE bankroll_retiros ADD COLUMN IF NOT EXISTS cantidad DECIMAL(12,2);
ALTER TABLE bankroll_retiros ADD COLUMN IF NOT EXISTS nota VARCHAR(255);
ALTER TABLE bankroll_retiros ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_bankroll_retiros_usuario ON bankroll_retiros(usuario);
CREATE INDEX IF NOT EXISTS idx_bankroll_retiros_fecha ON bankroll_retiros(fecha);
ALTER TABLE bankroll_retiros ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY "bankroll_retiros_all" ON bankroll_retiros FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 4) TABLA bankroll_history
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bankroll_history (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) DEFAULT 'default',
    fecha DATE NOT NULL,
    bankroll_inicial DECIMAL(12,2) DEFAULT 1000.00,
    stake DECIMAL(6,2) DEFAULT 0,
    pick_id BIGINT,
    cuota DECIMAL(5,2),
    resultado VARCHAR(20),
    ganancia DECIMAL(8,2) DEFAULT 0,
    bankroll_final DECIMAL(12,2) DEFAULT 1000.00,
    estrategia VARCHAR(50) DEFAULT 'flat',
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS usuario_id VARCHAR(100);
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS fecha DATE;
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS bankroll_inicial DECIMAL(12,2) DEFAULT 1000.00;
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS stake DECIMAL(6,2) DEFAULT 0;
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS pick_id BIGINT;
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS cuota DECIMAL(5,2);
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS resultado VARCHAR(20);
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS ganancia DECIMAL(8,2) DEFAULT 0;
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS bankroll_final DECIMAL(12,2) DEFAULT 1000.00;
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS estrategia VARCHAR(50) DEFAULT 'flat';
ALTER TABLE bankroll_history ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_bankroll_history_fecha ON bankroll_history(fecha);
ALTER TABLE bankroll_history ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY "bankroll_history_all" ON bankroll_history FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- VERIFICACIÓN FINAL - debe mostrar las 4 columnas clave
-- ════════════════════════════════════════════════════════════════════════════
SELECT 'user_stats' AS tabla, column_name
FROM information_schema.columns
WHERE table_name = 'user_stats'
  AND column_name IN ('usuario_id', 'bankroll_inicial', 'total_retirado', 'bankroll_actual')
UNION ALL
SELECT 'bankroll_apuestas' AS tabla, column_name
FROM information_schema.columns
WHERE table_name = 'bankroll_apuestas'
  AND column_name IN ('usuario', 'fixture_id', 'cuota', 'cantidad', 'mercado', 'ganancia', 'resultado')
ORDER BY tabla, column_name;


