-- ================================================
-- FIX: Corregir fechas de partidos (bug UTC)
-- Ejecutar en: Supabase Dashboard > SQL Editor
-- ================================================

-- 1. Verificar fechas actuales (muestra un resumen)
SELECT 
    fecha,
    COUNT(*) as cantidad
FROM partidos
GROUP BY fecha
ORDER BY fecha DESC
LIMIT 20;

-- 2. Corregir fechas restando 1 día
-- Esto asume que hay un desfase de +1 día por el bug de zona horaria
UPDATE partidos
SET fecha = fecha - INTERVAL '1 day',
    actualizado_en = NOW()
WHERE fecha > '2025-01-01';  -- Solo partidos reales

-- 3. Verificar fechas corregidas
SELECT 
    fecha,
    COUNT(*) as cantidad
FROM partidos
GROUP BY fecha
ORDER BY fecha DESC
LIMIT 20;

-- 4. Verificar que no hay duplicados después de la corrección
SELECT 
    fecha,
    equipo_local,
    equipo_visitante,
    COUNT(*) as duplicados
FROM partidos
GROUP BY fecha, equipo_local, equipo_visitante
HAVING COUNT(*) > 1;

-- 5. Eliminar duplicados si hay (mantener el más reciente)
DELETE FROM partidos a
USING partidos b
WHERE a.id < b.id
AND a.fecha = b.fecha
AND a.equipo_local = b.equipo_local
AND a.equipo_visitante = b.equipo_visitante;
