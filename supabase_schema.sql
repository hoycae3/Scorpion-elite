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
    liga_id BIGINT,
    equipo_local VARCHAR(255) NOT NULL,
    equipo_visitante VARCHAR(255) NOT NULL,
    logo_local VARCHAR(500),
    logo_visitante VARCHAR(500),
    goles_local INTEGER,
    goles_visitante INTEGER,
    estado VARCHAR(50) DEFAULT 'programado',
    team_id_local BIGINT,
    team_id_visitante BIGINT,
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
    team_id BIGINT,
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
    corners_favor INTEGER DEFAULT 0,
    corners_contra INTEGER DEFAULT 0,
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
    fixture_id BIGINT UNIQUE,
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
    
    -- 1X2
    prediccion_1x2 VARCHAR(10),
    prob_1x2 DECIMAL(5,2),
    p1 DECIMAL(5,2),
    px DECIMAL(5,2),
    p2 DECIMAL(5,2),
    
    -- Over/Under
    prediccion_ou VARCHAR(20),
    prob_ou DECIMAL(5,2),
    over_25 DECIMAL(5,2),
    under_25 DECIMAL(5,2),
    
    -- BTTS
    prediccion_btts VARCHAR(10),
    prob_btts DECIMAL(5,2),
    btts_yes DECIMAL(5,2),
    btts_no DECIMAL(5,2),
    
    -- Corners
    prediccion_corners VARCHAR(20),
    corners_total_estimado DECIMAL(5,2),
    
    -- Remates
    prediccion_remates VARCHAR(20),
    remates_total_estimado DECIMAL(5,2),
    remates_local DECIMAL(5,2),
    remates_visitante DECIMAL(5,2),
    over_remates DECIMAL(5,2),
    under_remates DECIMAL(5,2),
    
    -- Tarjetas
    prediccion_tarjetas VARCHAR(20),
    tarjetas_total_estimado DECIMAL(5,2),
    tarjetas_over_prob DECIMAL(5,2),
    tarjetas_under_prob DECIMAL(5,2),
    
    -- Tiros Arco
    prediccion_arco VARCHAR(20),
    arco_total_estimado DECIMAL(5,2),
    arco_local DECIMAL(5,2),
    arco_visitante DECIMAL(5,2),
    arco_over_prob DECIMAL(5,2),
    arco_under_prob DECIMAL(5,2),
    
    -- Confianza
    confianza INTEGER,
    rango VARCHAR(5),
    
    -- Resultados (para evaluar después)
    resultado_1x2 VARCHAR(10),
    resultado_ou VARCHAR(20),
    resultado_btts VARCHAR(10),
    resultado_remates VARCHAR(20),
    resultado_tarjetas VARCHAR(20),
    resultado_arco VARCHAR(20),
    acertado_1x2 BOOLEAN,
    acertado_ou BOOLEAN,
    acertado_btts BOOLEAN,
    acertado_remates BOOLEAN,
    acertado_tarjetas BOOLEAN,
    acertado_arco BOOLEAN,
    
    -- Metadatos
    lambda_local DECIMAL(5,2),
    lambda_visitante DECIMAL(5,2),
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_picks_fecha ON picks(fecha);
CREATE INDEX IF NOT EXISTS idx_picks_resultado ON picks(resultado_1x2);

ALTER TABLE picks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "picks_all" ON picks FOR ALL USING (true) WITH CHECK (true);

-- ALTER para agregar columnas si la tabla ya existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prediccion_1x2') THEN
        ALTER TABLE picks ADD COLUMN prediccion_1x2 VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prob_1x2') THEN
        ALTER TABLE picks ADD COLUMN prob_1x2 DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'p1') THEN
        ALTER TABLE picks ADD COLUMN p1 DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'px') THEN
        ALTER TABLE picks ADD COLUMN px DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'p2') THEN
        ALTER TABLE picks ADD COLUMN p2 DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prediccion_ou') THEN
        ALTER TABLE picks ADD COLUMN prediccion_ou VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prob_ou') THEN
        ALTER TABLE picks ADD COLUMN prob_ou DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'over_25') THEN
        ALTER TABLE picks ADD COLUMN over_25 DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'under_25') THEN
        ALTER TABLE picks ADD COLUMN under_25 DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prediccion_btts') THEN
        ALTER TABLE picks ADD COLUMN prediccion_btts VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prob_btts') THEN
        ALTER TABLE picks ADD COLUMN prob_btts DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'btts_yes') THEN
        ALTER TABLE picks ADD COLUMN btts_yes DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'btts_no') THEN
        ALTER TABLE picks ADD COLUMN btts_no DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prediccion_corners') THEN
        ALTER TABLE picks ADD COLUMN prediccion_corners VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'corners_total_estimado') THEN
        ALTER TABLE picks ADD COLUMN corners_total_estimado DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prediccion_remates') THEN
        ALTER TABLE picks ADD COLUMN prediccion_remates VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'remates_total_estimado') THEN
        ALTER TABLE picks ADD COLUMN remates_total_estimado DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'remates_local') THEN
        ALTER TABLE picks ADD COLUMN remates_local DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'remates_visitante') THEN
        ALTER TABLE picks ADD COLUMN remates_visitante DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'over_remates') THEN
        ALTER TABLE picks ADD COLUMN over_remates DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'under_remates') THEN
        ALTER TABLE picks ADD COLUMN under_remates DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'prediccion_tarjetas') THEN
        ALTER TABLE picks ADD COLUMN prediccion_tarjetas VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'tarjetas_total_estimado') THEN
        ALTER TABLE picks ADD COLUMN tarjetas_total_estimado DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'tarjetas_over_prob') THEN
        ALTER TABLE picks ADD COLUMN tarjetas_over_prob DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'tarjetas_under_prob') THEN
        ALTER TABLE picks ADD COLUMN tarjetas_under_prob DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'rango') THEN
        ALTER TABLE picks ADD COLUMN rango VARCHAR(5);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'resultado_1x2') THEN
        ALTER TABLE picks ADD COLUMN resultado_1x2 VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'resultado_ou') THEN
        ALTER TABLE picks ADD COLUMN resultado_ou VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'resultado_btts') THEN
        ALTER TABLE picks ADD COLUMN resultado_btts VARCHAR(10);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'resultado_remates') THEN
        ALTER TABLE picks ADD COLUMN resultado_remates VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'resultado_tarjetas') THEN
        ALTER TABLE picks ADD COLUMN resultado_tarjetas VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'acertado_1x2') THEN
        ALTER TABLE picks ADD COLUMN acertado_1x2 BOOLEAN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'acertado_ou') THEN
        ALTER TABLE picks ADD COLUMN acertado_ou BOOLEAN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'acertado_btts') THEN
        ALTER TABLE picks ADD COLUMN acertado_btts BOOLEAN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'acertado_remates') THEN
        ALTER TABLE picks ADD COLUMN acertado_remates BOOLEAN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'acertado_tarjetas') THEN
        ALTER TABLE picks ADD COLUMN acertado_tarjetas BOOLEAN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'lambda_local') THEN
        ALTER TABLE picks ADD COLUMN lambda_local DECIMAL(5,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'picks' AND column_name = 'lambda_visitante') THEN
        ALTER TABLE picks ADD COLUMN lambda_visitante DECIMAL(5,2);
    END IF;
END $$;

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

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLAS VIP - Dashboard Elite para usuarios que pagan
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA BANKROLL_HISTORY
-- Seguimiento del bankroll del usuario a lo largo del tiempo
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS bankroll_history (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) DEFAULT 'default',
    fecha DATE NOT NULL,
    bankroll_inicial DECIMAL(12,2) DEFAULT 1000.00,
    stake DECIMAL(6,2) DEFAULT 0,
    pick_id BIGINT,
    cuota DECIMAL(5,2),
    resultado VARCHAR(20),  -- 'win', 'loss', 'push'
    ganancia DECIMAL(8,2) DEFAULT 0,
    bankroll_final DECIMAL(12,2) DEFAULT 1000.00,
    estrategia VARCHAR(50) DEFAULT 'flat',  -- 'flat', 'kelly', 'porcentaje'
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bankroll_fecha ON bankroll_history(fecha);
CREATE INDEX IF NOT EXISTS idx_bankroll_usuario ON bankroll_history(usuario_id);

ALTER TABLE bankroll_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "bankroll_all" ON bankroll_history FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA USER_STATS
-- Estadísticas acumuladas por usuario
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_stats (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(100),
    -- Contadores
    total_picks INTEGER DEFAULT 0,
    picks_ganados INTEGER DEFAULT 0,
    picks_perdidos INTEGER DEFAULT 0,
    picks_nulos INTEGER DEFAULT 0,
    -- ROI por tipo de mercado
    roi_1x2 DECIMAL(6,2) DEFAULT 0,
    roi_over_under DECIMAL(6,2) DEFAULT 0,
    roi_btts DECIMAL(6,2) DEFAULT 0,
    roi_corners DECIMAL(6,2) DEFAULT 0,
    roi_tarjetas DECIMAL(6,2) DEFAULT 0,
    roi_remates DECIMAL(6,2) DEFAULT 0,
    -- ROI general
    roi_general DECIMAL(6,2) DEFAULT 0,
    yield_general DECIMAL(6,2) DEFAULT 0,
    -- ROI por modelo
    roi_poisson DECIMAL(6,2) DEFAULT 0,
    roi_dixon DECIMAL(6,2) DEFAULT 0,
    roi_montecarlo DECIMAL(6,2) DEFAULT 0,
    roi_elo DECIMAL(6,2) DEFAULT 0,
    -- Rachas
    racha_actual INTEGER DEFAULT 0,
    racha_maxima INTEGER DEFAULT 0,
    mejor_tipo_pick VARCHAR(50),  -- '1X2', 'Over/Under', etc.
    peor_tipo_pick VARCHAR(50),
    -- Bankroll
    bankroll_actual DECIMAL(12,2) DEFAULT 1000.00,
    bankroll_inicial DECIMAL(12,2) DEFAULT 1000.00,
    -- Confianza
    confianza_promedio DECIMAL(5,2) DEFAULT 0,
    precision_alta_confianza DECIMAL(5,2) DEFAULT 0,  -- % acierto en picks >90%
    -- Badges
    badges TEXT[],  -- Array de badges ganados
    streak_tipo VARCHAR(10) DEFAULT 'neutro',  -- 'ganando', 'perdiendo', 'neutro'
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_userstats_usuario ON user_stats(usuario_id);

ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "userstats_all" ON user_stats FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA ALERTAS
-- Alertas y notificaciones para el usuario VIP
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS alertas (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) DEFAULT 'default',
    tipo VARCHAR(50) NOT NULL,  -- 'alta_confianza', 'value_bet', 'streak', 'resultado'
    titulo VARCHAR(255),
    mensaje TEXT,
    prioridad VARCHAR(20) DEFAULT 'media',  -- 'alta', 'media', 'baja'
    leida BOOLEAN DEFAULT FALSE,
    pick_id BIGINT,
    liga VARCHAR(255),
    fecha DATE,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alertas_usuario ON alertas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_alertas_tipo ON alertas(tipo);
CREATE INDEX IF NOT EXISTS idx_alertas_leida ON alertas(leida);

ALTER TABLE alertas ENABLE ROW LEVEL SECURITY;
CREATE POLICY "alertas_all" ON alertas FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA VALUE_BETS
-- Picks donde la probabilidad del modelo > cuota del mercado (VALUE)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS value_bets (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) DEFAULT 'default',
    fixture_id BIGINT,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    equipo_local VARCHAR(255),
    equipo_visitante VARCHAR(255),
    -- Probabilidades del modelo
    prob_modelo DECIMAL(5,2) NOT NULL,
    -- Cuota del mercado (ingresada por usuario o scrapeada)
    cuota_mercado DECIMAL(5,2) NOT NULL,
    -- Probabilidad implícita de la cuota
    prob_implicita DECIMAL(5,2),
    -- Value (prob_modelo - prob_implicita)
    value DECIMAL(5,2),
    -- Tipo de apuesta
    tipo VARCHAR(50),  -- '1X2', 'Over/Under', 'BTTS', etc.
    detalle VARCHAR(100),  -- 'Over 2.5', 'Local', etc.
    -- Resultado
    resultado VARCHAR(20),
    ganancia DECIMAL(8,2),
    -- Recomendación
    recomendado BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_valuebets_fecha ON value_bets(fecha);
CREATE INDEX IF NOT EXISTS idx_valuebets_usuario ON value_bets(usuario_id);
CREATE INDEX IF NOT EXISTS idx_valuebets_value ON value_bets(value);

ALTER TABLE value_bets ENABLE ROW LEVEL SECURITY;
CREATE POLICY "valuebets_all" ON value_bets FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA RANKING
-- Ranking mensual de usuarios por ROI
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS ranking (
    id BIGSERIAL PRIMARY KEY,
    usuario_id VARCHAR(100) NOT NULL,
    nombre VARCHAR(100),
    mes INTEGER NOT NULL,
    ano INTEGER NOT NULL,
    total_picks INTEGER DEFAULT 0,
    roi DECIMAL(6,2) DEFAULT 0,
    yield DECIMAL(6,2) DEFAULT 0,
    posicion INTEGER,
    badges TEXT[],
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(usuario_id, mes, ano)
);

CREATE INDEX IF NOT EXISTS idx_ranking_periodo ON ranking(ano, mes);
CREATE INDEX IF NOT EXISTS idx_ranking_posicion ON ranking(posicion);

ALTER TABLE ranking ENABLE ROW LEVEL SECURITY;
CREATE POLICY "ranking_all" ON ranking FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA CUOTAS
-- Guarda TODAS las cuotas de partidos (1X2, Over/Under, BTTS, etc.)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS cuotas (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT NOT NULL,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    equipo_local VARCHAR(255),
    equipo_visitante VARCHAR(255),
    -- Tipo de apuesta
    tipo_apuesta VARCHAR(100) NOT NULL,  -- 'Match Winner', 'Over/Under', 'Both Teams To Score'
    -- Opciones y cuotas
    opcion VARCHAR(50) NOT NULL,  -- '1', 'X', '2', 'Yes', 'No', 'Over 2.5', 'Under 2.5', etc.
    cuota DECIMAL(6,2),
    -- Casa de apuestas
    bookmaker VARCHAR(100),
    -- Metadatos
    creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    actualizado_en DATE,
    -- Unique constraint para evitar duplicados
    UNIQUE(fixture_id, bookmaker, tipo_apuesta, opcion)
);

CREATE INDEX IF NOT EXISTS idx_cuotas_fixture ON cuotas(fixture_id);
CREATE INDEX IF NOT EXISTS idx_cuotas_fecha ON cuotas(fecha);
CREATE INDEX IF NOT EXISTS idx_cuotas_tipo ON cuotas(tipo_apuesta);

ALTER TABLE cuotas ENABLE ROW LEVEL SECURITY;
CREATE POLICY "cuotas_all" ON cuotas FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA CUOTAS_CACHE (alternativa simplificada)
-- Guarda cuotas de partidos para revisión posterior
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS cuotas_cache (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    equipo_local VARCHAR(255),
    equipo_visitante VARCHAR(255),
    -- Cuotas 1X2
    cuota_1 DECIMAL(5,2),
    cuota_X DECIMAL(5,2),
    cuota_2 DECIMAL(5,2),
    -- Cuotas Over/Under
    cuota_over_25 DECIMAL(5,2),
    cuota_under_25 DECIMAL(5,2),
    cuota_over_35 DECIMAL(5,2),
    cuota_under_35 DECIMAL(5,2),
    -- Cuotas BTTS
    cuota_btts_yes DECIMAL(5,2),
    cuota_btts_no DECIMAL(5,2),
    -- Cuotas Corners
    cuota_corners_over_95 DECIMAL(5,2),
    cuota_corners_under_95 DECIMAL(5,2),
    -- Casa de apuestas
    casa_apuestas VARCHAR(100),
    -- Metadatos
    buscado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cuotas_cache_fixture ON cuotas_cache(fixture_id);
CREATE INDEX IF NOT EXISTS idx_cuotas_cache_fecha ON cuotas_cache(fecha);

ALTER TABLE cuotas_cache ENABLE ROW LEVEL SECURITY;
CREATE POLICY "cuotas_cache_all" ON cuotas_cache FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLAS DE CALIBRACIÓN (Fix #4 - migrar de /tmp a Supabase)
-- ═══════════════════════════════════════════════════════════════════════════════

-- TABLA CALIBRACION_EQUIPOS
-- Guarda factores de corrección por equipo
CREATE TABLE IF NOT EXISTS calibracion_equipos (
    id BIGSERIAL PRIMARY KEY,
    equipo_norm TEXT PRIMARY KEY,  -- nombre normalizado (lowercase, sin acentos)
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
CREATE POLICY "calibracion_equipos_all" ON calibracion_equipos FOR ALL USING (true) WITH CHECK (true);

-- TABLA CALIBRACION_HISTORICO
-- Guarda histórico de picks para análisis
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
CREATE POLICY "calibracion_historico_all" ON calibracion_historico FOR ALL USING (true) WITH CHECK (true);
-- Tabla para trackear qué días se procesaron las estadísticas
CREATE TABLE IF NOT EXISTS dias_procesados (
    fecha DATE PRIMARY KEY,
    equipos_procesados INTEGER DEFAULT 0,
    fecha_procesamiento TIMESTAMP DEFAULT NOW()
);

-- Permitir upsert
ALTER TABLE dias_procesados ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all" ON dias_procesados FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA MATCH_STATS
-- Estadísticas detalladas de partidos (tiros, corners, tarjetas, posesión)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS match_stats (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT UNIQUE NOT NULL,
    stats_data JSONB DEFAULT '[]',
    h2h_data JSONB DEFAULT '[]',
    actualizado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_match_stats_fixture ON match_stats(fixture_id);

ALTER TABLE match_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "match_stats_all" ON match_stats FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA TEAM_FORM
-- Forma/recientes de equipos (últimos 5 partidos)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS team_form (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT UNIQUE NOT NULL,
    equipo VARCHAR(255),
    liga_id BIGINT,
    forma_data JSONB DEFAULT '[]',
    actualizado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_team_form_team ON team_form(team_id);

ALTER TABLE team_form ENABLE ROW LEVEL SECURITY;
CREATE POLICY "team_form_all" ON team_form FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA EQUIPO_PARTIDOS_STATS
-- Estadísticas detalladas de cada partido individual de los equipos
-- (Corners, Tiros, Tarjetas, etc.)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS equipo_partidos_stats (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL,
    equipo VARCHAR(255),
    fixture_id BIGINT NOT NULL,
    fecha DATE,
    liga VARCHAR(255),
    es_local BOOLEAN DEFAULT false,
    resultado CHAR(1) DEFAULT '-',
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    tiros_totales INTEGER DEFAULT 0,
    tiros_arco INTEGER DEFAULT 0,
    tiros_fuera INTEGER DEFAULT 0,
    corners INTEGER DEFAULT 0,
    amarillas INTEGER DEFAULT 0,
    rojas INTEGER DEFAULT 0,
    posesion INTEGER DEFAULT 0,
    faltas INTEGER DEFAULT 0,
    ahorradas INTEGER DEFAULT 0,
    actualizado_en TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_equipo_partidos_team ON equipo_partidos_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_equipo_partidos_fixture ON equipo_partidos_stats(fixture_id);

ALTER TABLE equipo_partidos_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "equipo_partidos_stats_all" ON equipo_partidos_stats FOR ALL USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA USUARIOS
-- Usuarios del sistema (login)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    password_hash TEXT NOT NULL,
    nombre TEXT,
    plan TEXT DEFAULT 'vip',
    fecha_inicio DATE,
    dias INTEGER DEFAULT 36500,
    activo BOOLEAN DEFAULT true,
    es_admin BOOLEAN DEFAULT false,
    creado_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
CREATE POLICY "usuarios_all" ON usuarios FOR ALL USING (true) WITH CHECK (true);

