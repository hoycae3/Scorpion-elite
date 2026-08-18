-- ═══════════════════════════════════════════════════════════════════
-- MIGRACIÓN: Sincronizar DB con el código
-- Fecha: 2026-08-18
-- 
-- 1. Crea calibracion_equipos (faltaba en DB, código la usa)
-- 2. Crea calibracion_historico (faltaba en DB, código la usa)
-- 3. Borra tablas deprecated (dias_procesados, historial_predicciones, pesos_modelos)
-- ═══════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════
-- 1. CREAR TABLAS DE CALIBRACIÓN (faltaban)
-- ═══════════════════════════════════════════════════════════════════

-- Tabla calibracion_equipos
-- NOTA: el schema original tenía un bug (dos PRIMARY KEY), corregido aquí:
-- id es PK, equipo_norm es UNIQUE
CREATE TABLE IF NOT EXISTS calibracion_equipos (
    id BIGSERIAL PRIMARY KEY,
    equipo_norm TEXT UNIQUE NOT NULL,
    nombre_original TEXT,
    factor_local NUMERIC DEFAULT 1.0,
    factor_visitante NUMERIC DEFAULT 1.0,
    factor_over NUMERIC DEFAULT 1.0,
    factor_btts NUMERIC DEFAULT 1.0,
    partidos_local INT DEFAULT 0,
    partidos_visitante INT DEFAULT 0,
    errores_local JSONB DEFAULT '[]',
    errores_visitante JSONB DEFAULT '[]',
    over_real JSONB DEFAULT '[]',
    over_predicho JSONB DEFAULT '[]',
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calibracion_equipos_nombre ON calibracion_equipos(equipo_norm);

ALTER TABLE calibracion_equipos ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "calibracion_equipos_all" ON calibracion_equipos;
CREATE POLICY "calibracion_equipos_all" ON calibracion_equipos FOR ALL USING (true) WITH CHECK (true);

-- Tabla calibracion_historico
CREATE TABLE IF NOT EXISTS calibracion_historico (
    id BIGSERIAL PRIMARY KEY,
    fecha TIMESTAMPTZ DEFAULT NOW(),
    equipo_local TEXT,
    equipo_visitante TEXT,
    lambda_local_predicha NUMERIC,
    lambda_visitante_predicha NUMERIC,
    goles_local_real INT,
    goles_visitante_real INT,
    resultados JSONB,
    acertado_1x2 BOOLEAN,
    acertado_ou25 BOOLEAN,
    acertado_btts BOOLEAN,
    confianza INT,
    rango VARCHAR(5)
);

CREATE INDEX IF NOT EXISTS idx_calibracion_historico_fecha ON calibracion_historico(fecha);
CREATE INDEX IF NOT EXISTS idx_calibracion_historico_local ON calibracion_historico(equipo_local);

ALTER TABLE calibracion_historico ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "calibracion_historico_all" ON calibracion_historico;
CREATE POLICY "calibracion_historico_all" ON calibracion_historico FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════
-- 2. BORRAR TABLAS DEPRECATED (código muerto)
-- Estas tablas no se referencian en ningún archivo del proyecto
-- ═══════════════════════════════════════════════════════════════════

-- dias_procesados: 0 filas, no se usa
DROP TABLE IF EXISTS dias_procesados CASCADE;

-- historial_predicciones: 21 filas pero no se referencia en el código
DROP TABLE IF EXISTS historial_predicciones CASCADE;

-- pesos_modelos: 5 filas pero no se referencia en el código
DROP TABLE IF EXISTS pesos_modelos CASCADE;

-- ═══════════════════════════════════════════════════════════════════
-- VERIFICACIÓN
-- ═══════════════════════════════════════════════════════════════════
-- Después de ejecutar, correr esto para verificar:
-- SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public' ORDER BY tablename;
-- Debería dar 15 tablas (sin las 3 borradas, con las 2 nuevas)
