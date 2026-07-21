-- Scorpion Elite - Schema Simplificado
-- Julio 2026
-- Simplificado para uso real

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA PARTIDOS
-- Partidos subidos desde Excel
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS partidos (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    hora VARCHAR(10),
    hora_utc VARCHAR(10),
    pais VARCHAR(100),
    liga VARCHAR(255),
    equipo_local VARCHAR(255) NOT NULL,
    equipo_visitante VARCHAR(255) NOT NULL,
    goles_local INTEGER,
    goles_visitante INTEGER,
    estado VARCHAR(50) DEFAULT 'programado',
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partidos_fecha ON partidos(fecha);
CREATE INDEX IF NOT EXISTS idx_partidos_liga ON partidos(liga);
CREATE INDEX IF NOT EXISTS idx_partidos_estado ON partidos(estado);

ALTER TABLE partidos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "partidos_all" ON partidos FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA EQUIPOS_STATS
-- Estadísticas PROMEDIO por equipo
-- Esta es la tabla principal para los modelos de predicción
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS equipos_stats (
    id BIGSERIAL PRIMARY KEY,
    equipo VARCHAR(255) NOT NULL,
    pais VARCHAR(100),
    liga VARCHAR(255),
    temporada VARCHAR(50) DEFAULT '2024-25',
    -- Partidos y resultados
    partidos_jugados INTEGER DEFAULT 0,
    victorias INTEGER DEFAULT 0,
    empates INTEGER DEFAULT 0,
    derrotas INTEGER DEFAULT 0,
    -- Goles
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    promedio_goles_local DECIMAL(4,2) DEFAULT 0,
    promedio_goles_visitante DECIMAL(4,2) DEFAULT 0,
    -- Lambda para Poisson
    lambda_local DECIMAL(4,2) DEFAULT 1.3,
    lambda_visitante DECIMAL(4,2) DEFAULT 1.1,
    -- Tiros
    promedio_tiros DECIMAL(4,2) DEFAULT 0,
    promedio_tiros_arco DECIMAL(4,2) DEFAULT 0,
    -- Corners
    promedio_corners_local DECIMAL(4,2) DEFAULT 0,
    promedio_corners_visitante DECIMAL(4,2) DEFAULT 0,
    promedio_corners_total DECIMAL(4,2) DEFAULT 0,
    -- Tarjetas
    promedio_amarillas DECIMAL(4,2) DEFAULT 0,
    promedio_rojas DECIMAL(4,2) DEFAULT 0,
    -- Posesión
    promedio_posesion DECIMAL(4,2) DEFAULT 0,
    -- Fuentes
    source_fbdata BOOLEAN DEFAULT FALSE,
    source_whoscored BOOLEAN DEFAULT FALSE,
    source_fbref BOOLEAN DEFAULT FALSE,
    ultimo_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(equipo, temporada)
);

CREATE INDEX IF NOT EXISTS idx_equipos_nombre ON equipos_stats(equipo);
CREATE INDEX IF NOT EXISTS idx_equipos_liga ON equipos_stats(liga);

ALTER TABLE equipos_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "equipos_all" ON equipos_stats FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA PARTIDOS_STATS
-- Estadísticas DETALLADAS de partidos específicos (histórico)
-- Para cuando quieras ver qué pasó en un partido específico
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS partidos_stats (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT,
    fecha DATE,
    liga VARCHAR(255),
    equipo_local VARCHAR(255),
    equipo_visitante VARCHAR(255),
    -- Goles
    goles_local INTEGER,
    goles_visitante INTEGER,
    -- Tiros
    tiros_local INTEGER,
    tiros_visitante INTEGER,
    tiros_arco_local INTEGER,
    tiros_arco_visitante INTEGER,
    -- Corners
    corners_local INTEGER,
    corners_visitante INTEGER,
    corners_total INTEGER,
    -- Tarjetas
    amarillas_local INTEGER,
    amarillas_visitante INTEGER,
    rojas_local INTEGER,
    rojas_visitante INTEGER,
    -- Posesión
    posesion_local INTEGER,
    posesion_visitante INTEGER,
    -- Atajadas (guardadas)
    atajadas_local INTEGER,
    atajadas_visitante INTEGER,
    -- Faltas y otras
    faltas_local INTEGER,
    faltas_visitante INTEGER,
    fueras_juego_local INTEGER,
    fueras_juego_visitante INTEGER,
    source VARCHAR(50),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_partidos_stats_fixture ON partidos_stats(fixture_id);
CREATE INDEX IF NOT EXISTS idx_partidos_stats_fecha ON partidos_stats(fecha);
CREATE INDEX IF NOT EXISTS idx_partidos_stats_local ON partidos_stats(equipo_local);

ALTER TABLE partidos_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "partidos_stats_all" ON partidos_stats FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA PICKS
-- Picks realizados para seguimiento
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS picks (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    equipo_local VARCHAR(255),
    equipo_visitante VARCHAR(255),
    -- Pick info
    pick VARCHAR(10) NOT NULL,
    cuota DECIMAL(5,2),
    stake DECIMAL(10,2) DEFAULT 0,
    -- Resultado
    resultado VARCHAR(20) DEFAULT 'pending',
    ganancia DECIMAL(10,2) DEFAULT 0,
    -- Análisis
    confianza INTEGER,
    modelos_used VARCHAR(100),
    probabilidad_modelo DECIMAL(5,2),
    -- Metadatos
    notes TEXT,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_picks_fecha ON picks(fecha);
CREATE INDEX IF NOT EXISTS idx_picks_resultado ON picks(resultado);

ALTER TABLE picks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "picks_all" ON picks FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA HISTORIAL_PREDICCIONES
-- Guarda TODAS las predicciones para calcular % de acierto por modelo
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS historial_predicciones (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    equipo_local VARCHAR(255),
    equipo_visitante VARCHAR(255),
    -- Resultado real
    goles_local INTEGER,
    goles_visitante INTEGER,
    resultado_real VARCHAR(10),  -- '1', 'X', '2'
    total_goles INTEGER,  -- Para Over/Under
    ambos_marcan VARCHAR(10),  -- 'SI', 'NO'
    -- Predicciones Poisson
    poisson_1 DECIMAL(5,2),
    poisson_X DECIMAL(5,2),
    poisson_2 DECIMAL(5,2),
    poisson_acierto BOOLEAN,
    -- Predicciones Dixon-Coles
    dc_1 DECIMAL(5,2),
    dc_X DECIMAL(5,2),
    dc_2 DECIMAL(5,2),
    dc_acierto BOOLEAN,
    -- Predicciones Monte Carlo
    mc_1 DECIMAL(5,2),
    mc_X DECIMAL(5,2),
    mc_2 DECIMAL(5,2),
    mc_acierto BOOLEAN,
    -- Predicciones Forma Reciente
    forma_local_pct DECIMAL(5,2),
    forma_visitante_pct DECIMAL(5,2),
    forma_acierto BOOLEAN,
    -- Predicciones Estilo
    estilo_local VARCHAR(50),
    estilo_visitante VARCHAR(50),
    -- Predicción final COMBINADA (la que se usó)
    prediccion_final VARCHAR(10),
    probabilidad_final DECIMAL(5,2),
    -- Pesos usados en ese momento
    peso_poisson DECIMAL(5,2),
    peso_dixon DECIMAL(5,2),
    peso_montecarlo DECIMAL(5,2),
    peso_forma DECIMAL(5,2),
    peso_estilo DECIMAL(5,2),
    -- Confianza y rango
    confianza INTEGER,
    rango VARCHAR(5),
    -- Veredicto
    acierto BOOLEAN,
    -- Metadatos
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_predicciones(fecha);
CREATE INDEX IF NOT EXISTS idx_historial_acierto ON historial_predicciones(acierto);
CREATE INDEX IF NOT EXISTS idx_historial_fixture ON historial_predicciones(fixture_id);

ALTER TABLE historial_predicciones ENABLE ROW LEVEL SECURITY;
CREATE POLICY "historial_all" ON historial_predicciones FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA PESOS_MODELOS
-- Almacena los pesos ÓPTIMOS aprendidos del historial
-- Se actualizan automáticamente después de N predicciones
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS pesos_modelos (
    id BIGSERIAL PRIMARY KEY,
    modelo VARCHAR(50) NOT NULL,
    peso DECIMAL(5,2) NOT NULL,
    -- Métricas de este modelo
    total_predicciones INTEGER DEFAULT 0,
    aciertos INTEGER DEFAULT 0,
    porcentaje_acierto DECIMAL(5,2) DEFAULT 0,
    -- Configuración
    es_activo BOOLEAN DEFAULT TRUE,
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pesos iniciales (los que usamos ahora)
INSERT INTO pesos_modelos (modelo, peso, es_activo) VALUES
    ('poisson', 0.30, TRUE),
    ('dixon_coles', 0.25, TRUE),
    ('monte_carlo', 0.20, TRUE),
    ('forma_reciente', 0.15, TRUE),
    ('estilo_juego', 0.10, TRUE)
ON CONFLICT DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_pesos_modelo ON pesos_modelos(modelo);
CREATE INDEX IF NOT EXISTS idx_pesos_activo ON pesos_modelos(es_activo);

ALTER TABLE pesos_modelos ENABLE ROW LEVEL SECURITY;
CREATE POLICY "pesos_all" ON pesos_modelos FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- FUNCIONES AUTO-UPDATE
-- ═══════════════════════════════════════════════════════════════════════════════

-- Función para actualizar timestamp en equipos
CREATE OR REPLACE FUNCTION update_equipos_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ultimo_update = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_equipos_timestamp ON equipos_stats;
CREATE TRIGGER update_equipos_timestamp 
    BEFORE UPDATE ON equipos_stats
    FOR EACH ROW EXECUTE FUNCTION update_equipos_timestamp();
