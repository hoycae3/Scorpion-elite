-- Scorpion Elite - Supabase Schema (Extendido)
-- Ejecutar este script en el SQL Editor de Supabase
-- Incluye: Partidos, Picks, Estadísticas, Cuotas y datos multi-fuente

-- ═══════════════════════════════════════════════════════════════════════════════
-- TABLA PRINCIPAL DE PARTIDOS (Con cuotas y probabilidades)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS partidos (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT UNIQUE NOT NULL,
    fecha DATE NOT NULL,
    hora VARCHAR(10),
    hora_utc VARCHAR(10),
    liga VARCHAR(255),
    prioridad INTEGER DEFAULT 1,
    equipo_local VARCHAR(255) NOT NULL,
    equipo_visitante VARCHAR(255) NOT NULL,
    
    -- Probabilidades de modelos (%)
    prob_home DECIMAL(5,2),
    prob_draw DECIMAL(5,2),
    prob_away DECIMAL(5,2),
    
    -- Cuotas del mercado
    cuota_1 DECIMAL(5,2),
    cuota_x DECIMAL(5,2),
    cuota_2 DECIMAL(5,2),
    
    -- Pick y confianza
    pick VARCHAR(5),
    cuota_pick DECIMAL(5,2),
    confianza INTEGER,
    
    -- Fuentes de datos
    source_flashscore BOOLEAN DEFAULT false,
    source_transfermarkt BOOLEAN DEFAULT false,
    source_soccerway BOOLEAN DEFAULT false,
    source_whoscored BOOLEAN DEFAULT false,
    
    -- Estado
    estado VARCHAR(20) DEFAULT 'programado', -- 'programado', 'en_vivo', 'finalizado'
    resultado VARCHAR(20),
    
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para búsqueda
CREATE INDEX IF NOT EXISTS idx_partidos_fecha ON partidos(fecha);
CREATE INDEX IF NOT EXISTS idx_partidos_liga ON partidos(liga);
CREATE INDEX IF NOT EXISTS idx_partidos_estado ON partidos(estado);

-- ═══════════════════════════════════════════════════════════════════════════════
-- HISTORIAL DE PICKS (Para seguimiento de resultados)
-- ═══════════════════════════════════════════════════════════════════════════════
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
    resultado VARCHAR(20), -- 'ganado', 'perdido', 'pendiente', 'void'
    profit DECIMAL(6,2) DEFAULT 0,
    
    -- Detalles del modelo
    modelo VARCHAR(50),
    prob_predicha DECIMAL(5,2),
    prob_implicita DECIMAL(5,2),
    valor_esperado DECIMAL(5,2),
    
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_picks(fecha);
CREATE INDEX IF NOT EXISTS idx_historial_resultado ON historial_picks(resultado);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ESTADÍSTICAS DE EQUIPOS (De Transfermarkt y Soccerway)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS estadisticas_equipos (
    id BIGSERIAL PRIMARY KEY,
    equipo VARCHAR(255) NOT NULL,
    equipo_id_externo VARCHAR(100), -- ID en fuente externa
    liga VARCHAR(255),
    source VARCHAR(50), -- 'transfermarkt', 'soccerway', 'whoscored'
    
    -- Información general
    posicion_tabla INTEGER,
    puntos INTEGER DEFAULT 0,
    partido_jugados INTEGER DEFAULT 0,
    victorias INTEGER DEFAULT 0,
    empates INTEGER DEFAULT 0,
    derrotas INTEGER DEFAULT 0,
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    diferencia_goles INTEGER DEFAULT 0,
    
    -- Valor de mercado (de Transfermarkt)
    valor_mercado VARCHAR(100),
    
    -- Forma actual (últimos 5 partidos)
    ultimos_5 TEXT DEFAULT '[]', -- JSON: ["W","D","L",...]
    forma_score INTEGER DEFAULT 0,
    
    -- Estacional (para estadísticas WhoScored)
    promedio_corners_home DECIMAL(4,2) DEFAULT 0,
    promedio_corners_away DECIMAL(4,2) DEFAULT 0,
    promedio_tarjetas_home DECIMAL(4,2) DEFAULT 0,
    promedio_tarjetas_away DECIMAL(4,2) DEFAULT 0,
    promedio_posesion_home DECIMAL(4,2) DEFAULT 0,
    promedio_posesion_away DECIMAL(4,2) DEFAULT 0,
    promedio_tiros_home DECIMAL(4,2) DEFAULT 0,
    promedio_tiros_away DECIMAL(4,2) DEFAULT 0,
    
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(equipo, liga, source)
);

CREATE INDEX IF NOT EXISTS idx_stats_equipo ON estadisticas_equipos(equipo);
CREATE INDEX IF NOT EXISTS idx_stats_liga ON estadisticas_equipos(liga);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ESTADÍSTICAS DE PARTIDOS (De WhoScored - detallada por partido)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS estadisticas_partidos (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT NOT NULL,
    fecha DATE NOT NULL,
    
    -- Equipo local
    equipo_local VARCHAR(255),
    
    -- Estadísticas locales (home)
    hs_corners INTEGER DEFAULT 0,
    hs_tiros_totales INTEGER DEFAULT 0,
    hs_tiros_puerta INTEGER DEFAULT 0,
    hs_faltas INTEGER DEFAULT 0,
    hs_tarjetas_amarillas INTEGER DEFAULT 0,
    hs_tarjetas_rojas INTEGER DEFAULT 0,
    hs_posesion DECIMAL(5,2) DEFAULT 50,
    hs_pases_totales INTEGER DEFAULT 0,
    hs_precision_pases DECIMAL(5,2) DEFAULT 0,
    hs_offsides INTEGER DEFAULT 0,
    hs_porterias_defendidas INTEGER DEFAULT 0,
    hs_entradas INTEGER DEFAULT 0,
    
    -- Equipo visitante
    equipo_visitante VARCHAR(255),
    
    -- Estadísticas visitantes (away)
    as_corners INTEGER DEFAULT 0,
    as_tiros_totales INTEGER DEFAULT 0,
    as_tiros_puerta INTEGER DEFAULT 0,
    as_faltas INTEGER DEFAULT 0,
    as_tarjetas_amarillas INTEGER DEFAULT 0,
    as_tarjetas_rojas INTEGER DEFAULT 0,
    as_posesion DECIMAL(5,2) DEFAULT 50,
    as_pases_totales INTEGER DEFAULT 0,
    as_precision_pases DECIMAL(5,2) DEFAULT 0,
    as_offsides INTEGER DEFAULT 0,
    as_porterias_defendidas INTEGER DEFAULT 0,
    as_entradas INTEGER DEFAULT 0,
    
    source VARCHAR(50) DEFAULT 'whoscored',
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(fixture_id)
);

CREATE INDEX IF NOT EXISTS idx_stats_partidos_fixture ON estadisticas_partidos(fixture_id);
CREATE INDEX IF NOT EXISTS idx_stats_partidos_fecha ON estadisticas_partidos(fecha);

-- ═══════════════════════════════════════════════════════════════════════════════
-- CUOTAS DE MERCADO (De múltiples bookmakers)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS cuotas_mercado (
    id BIGSERIAL PRIMARY KEY,
    fixture_id BIGINT NOT NULL,
    fecha DATE NOT NULL,
    bookmaker VARCHAR(100) NOT NULL,
    
    -- Cuotas 1X2
    cuota_1 DECIMAL(6,2),
    cuota_x DECIMAL(6,2),
    cuota_2 DECIMAL(6,2),
    
    -- Cuotas Over/Under
    over_25 DECIMAL(6,2),
    under_25 DECIMAL(6,2),
    
    -- Cuotas Ambos Equipos Marcan
    bts_yes DECIMAL(6,2),
    bts_no DECIMAL(6,2),
    
    -- Cuotas Asian Handicap
    ah_home DECIMAL(6,2),
    ah_away DECIMAL(6,2),
    
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(fixture_id, bookmaker)
);

CREATE INDEX IF NOT EXISTS idx_cuotas_fixture ON cuotas_mercado(fixture_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- RESULTADOS HISTÓRICOS (De Soccerway)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS resultados_historicos (
    id BIGSERIAL PRIMARY KEY,
    match_id VARCHAR(50) UNIQUE,
    fecha DATE NOT NULL,
    liga VARCHAR(255),
    temporada VARCHAR(50),
    
    equipo_local VARCHAR(255) NOT NULL,
    equipo_visitante VARCHAR(255) NOT NULL,
    
    goles_local INTEGER DEFAULT 0,
    goles_visitante INTEGER DEFAULT 0,
    
    -- Goleadores (JSON array)
    goleadores TEXT DEFAULT '[]',
    
    -- Resultado para betting
    resultado VARCHAR(10), -- 'home', 'draw', 'away'
    
    source VARCHAR(50) DEFAULT 'soccerway',
    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resultados_fecha ON resultados_historicos(fecha);
CREATE INDEX IF NOT EXISTS idx_resultados_liga ON resultados_historicos(liga);
CREATE INDEX IF NOT EXISTS idx_resultados_equipo ON resultados_historicos(equipo_local);

-- ═══════════════════════════════════════════════════════════════════════════════
-- POLÍTICAS RLS (Row Level Security)
-- ═══════════════════════════════════════════════════════════════════════════════
ALTER TABLE partidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_picks ENABLE ROW LEVEL SECURITY;
ALTER TABLE estadisticas_equipos ENABLE ROW LEVEL SECURITY;
ALTER TABLE estadisticas_partidos ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuotas_mercado ENABLE ROW LEVEL SECURITY;
ALTER TABLE resultados_historicos ENABLE ROW LEVEL SECURITY;

-- Políticas para lectura pública
CREATE POLICY "Allow public read" ON partidos FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON historial_picks FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON estadisticas_equipos FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON estadisticas_partidos FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON cuotas_mercado FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON resultados_historicos FOR SELECT USING (true);

-- Políticas para inserción (solo desde el scraper con service role)
CREATE POLICY "Allow insert from service" ON partidos FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert from service" ON historial_picks FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert stats from service" ON estadisticas_equipos FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert match stats from service" ON estadisticas_partidos FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert odds from service" ON cuotas_mercado FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow insert results from service" ON resultados_historicos FOR INSERT WITH CHECK (true);

-- Políticas para actualización
CREATE POLICY "Allow update from service" ON partidos FOR UPDATE USING (true);
CREATE POLICY "Allow update from service" ON estadisticas_equipos FOR UPDATE USING (true);

-- ═══════════════════════════════════════════════════════════════════════════════
-- FUNCIONES Y TRIGGERS ÚTILES
-- ═══════════════════════════════════════════════════════════════════════════════

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a todas las tablas
CREATE TRIGGER update_partidos_updated_at BEFORE UPDATE ON partidos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_estadisticas_equipos_updated_at BEFORE UPDATE ON estadisticas_equipos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════════════════════════
-- COMENTARIOS
-- ═══════════════════════════════════════════════════════════════════════════════
COMMENT ON TABLE partidos IS 'Partidos de fútbol con predicciones y cuotas multi-fuente';
COMMENT ON TABLE historial_picks IS 'Historial de picks para seguimiento de resultados';
COMMENT ON TABLE estadisticas_equipos IS 'Estadísticas de equipos de Transfermarkt, Soccerway, WhoScored';
COMMENT ON TABLE estadisticas_partidos IS 'Estadísticas detalladas de partidos de WhoScored';
COMMENT ON TABLE cuotas_mercado IS 'Cuotas de diferentes bookmakers';
COMMENT ON TABLE resultados_historicos IS 'Resultados históricos de Soccerway';
