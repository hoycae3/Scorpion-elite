# Scorpion Elite - Estado del Proyecto (Julio 2026)

## 📌 Información General

| Item | Valor |
|------|-------|
| **Repositorio** | https://github.com/hoycae3/Scorpion-elite |
| **App Producción** | https://scorpion-elite.onrender.com |
| **Base de datos** | Supabase (jjtifureeygvygxtpuku.supabase.co) |
| **Deploy** | Render (srv-d9e1thbbc2fs73f30jh0) |
| **Password app** | scorpion2026 |

---

## 📁 Estructura Actual del Proyecto

```
Scorpion-elite/
├── elite.py                 # App principal Streamlit (37KB)
├── robot_extractor.py      # ⭐ SUPERROBOT - Todos los scrapers (49KB)
├── data_loader.py          # Procesa Excel de Flashscore (8KB)
├── analysis_models.py      # Modelos matemáticos (5KB)
├── supabase_schema.sql     # Schema de la base de datos
├── requirements.txt        # Dependencias
├── styles.css              # Estilos CSS
├── backups/                # Backups de archivos eliminados
│   ├── streamlit.py
│   └── dash2026_backup.py
├── stats_extractor.py     # ✅ Compatibilidad -> robot_extractor
├── stats_robot.py          # ✅ Compatibilidad -> robot_extractor
├── scrapers_fallback.py    # ✅ Compatibilidad -> robot_extractor
└── .github/workflows/      # GitHub Actions
```

**NOTA IMPORTANTE - ARCHIVOS DE COMPATIBILIDAD:**
Estos archivos NO son duplicados. Son necesarios para que `elite.py` pueda importar las funciones:
- `stats_extractor.py` → redirige a `robot_extractor.calculate_team_lambda`
- `stats_robot.py` → redirige a `robot_extractor.run_robot_batch`
- `scrapers_fallback.py` → redirige a `robot_extractor.scrape_team_fallback`

**NO ELIMINAR estos archivos de compatibilidad** o elite.py dejará de funcionar.

---

## 🤖 SUPERROBOT (robot_extractor.py) - EL ROBOT PRINCIPAL

### Fuentes de Datos

| Fuente | Datos Extraídos | Anti-Bloqueo | Cobertura |
|--------|-----------------|--------------|-----------|
| **football-data.co.uk** | Partidos, GF, GC, Victorias, Empates, Derrotas | Requests + redirects | 20+ ligas EUROPEAS |
| **Soccerway** | Resultados históricos, Marcadores, Liga | ✅ Cloudscraper | MUNDIAL |
| **WhoScored** | Corners, Tarjetas, Posesión, Remates, Faltas | ✅ Cloudscraper | MUNDIAL |
| **FBref** | Stats detalladas (posesión, remates, faltas) | ✅ Cloudscraper | 7 ligas TOP europeas |

### Flujo del SuperRobot
```
1. football-data → Goles, victorias (Europa)
        ↓ (si no encuentra)
2. Soccerway → Resultados históricos (Mundial)
        ↓ (si no encuentra)
3. WhoScored → Corners, tarjetas, posesión (Mundial)
        ↓ (si no encuentra)
4. FBref → Stats detalladas (Europa)
        ↓
5. Devuelve todo combinado
```

### Clases Principales
- `RobotExtractor` - Scraper básico FBref con cloudscraper
- `WhoScoredScraper` - Corners, tarjetas, posesión (con cloudscraper)
- `FBrefAdvancedScraper` - Stats detalladas (con cloudscraper)
- `SoccerwayScraper` - Resultados históricos (con cloudscraper)
- `SuperRobot` - Combina todas las fuentes automáticamente

---

## 🗄️ Base de Datos Supabase

### Tablas Existentes

| Tabla | Estado | Descripción |
|-------|--------|-------------|
| `partidos` | ✅ Existe | Partidos del día |
| `equipos_stats` | ✅ Existe | Estadísticas de equipos |
| `picks` | ✅ Existe | Picks guardados |

### Schema SQL (supabase_schema.sql)
```sql
CREATE TABLE IF NOT EXISTS partidos (...)
CREATE TABLE IF NOT EXISTS equipos_stats (...)
CREATE TABLE IF NOT EXISTS partidos_stats (...)
CREATE TABLE IF NOT EXISTS picks (...)
```

---

## ⚠️ Pendiente por Hacer

### 🔴 CRÍTICO - Funcionalidad

1. **Integrar SuperRobot con Supabase** - Guardar datos scrapeados en `equipos_stats`
2. **Integrar SuperRobot con elite.py** - Mostrar estadísticas en la app (ya están los espacios pero vacíos)
3. **Probar scrapers WhoScored/Soccerway** - Testear en producción
4. **Fuentes para América Latina** - football-data NO tiene Brasil, México, Argentina, MLS

### 🟡 IMPORTANTE - Mejoras

5. **Dashboard de resultados** - Historial picks vs resultados reales
6. **Métricas rendimiento** - % aciertos, ROI, streaks
7. **Exportar picks** - Descargar análisis en PDF/Excel
8. **Notificaciones** - Alertas para alta confianza

### 🟢 OPCIONAL - Extras

9. **Modo claro/oscuro** - Toggle de tema
10. **Comparar equipos** - Stats lado a lado sin analizar
11. **Filtros avanzados** - Por liga, confianza, fecha
12. **API partidos** - No depender solo del Excel

---

## 🔧 Comandos Útiles

```bash
# Probar football-data
python3 -c "from robot_extractor import get_football_data_stats; print(len(get_football_data_stats()))"

# Probar un equipo
python3 -c "from robot_extractor import get_team_stats_from_football_data; print(get_team_stats_from_football_data('Barcelona'))"

# Deploy en Render
curl -X POST "https://api.render.com/v1/services/srv-d9e1thbbc2fs73f30jh0/deploys" \
  -H "Authorization: Bearer rnd_RDmwWhiDyjbeT5wFWvXYTAonhOUY"
```

---

## 📅 Historial de Cambios

### 2026-07-22 - Sesión Dashboard

| Cambio | Descripción |
|--------|-------------|
| Nueva página Dashboard | Métricas de rendimiento, distribución por confianza/rango |
| Menú con 5 páginas | Carga, Analizador, Estadísticas, Dashboard, Claves |
| Historial de picks | Muestra últimas 20 predicciones |

### 2026-07-22 - Sesión Arreglos

| Cambio | Descripción |
|--------|-------------|
| Caché en archivo JSON | football-data ahora guarda en `/tmp/football_data_cache.json` (24h expiry) |
| Bug fix elite.py | Corregido `equipos_a_guardar` → `con_stats` para guardar stats en Supabase |
| Sin rate limiting | Los 356 equipos se cargan instantáneamente desde caché |

### 2026-07-21 - Sesión Diseño UI

| Cambio | Descripción |
|--------|-------------|
| Menú horizontal arriba | Navegación movida a la parte superior |
| Sidebar simplificado | Solo muestra usuario, plan y logout |
| Estadísticas Robot | Verticales, una debajo de otra, centradas |
| Subtítulos reducidos | Usando ##### en lugar de ### |
| Análisis Partido | Compacto y centrado con borde cyan |
| Predicciones | Cards más grandes y centradas |
| Forma Reciente | Centrada con badges de colores |

### 2026-07-20 - Sesión Anterior

| Cambio | Descripción |
|--------|-------------|
| SuperRobot creado | 4 fuentes: football-data, Soccerway, WhoScored, FBref |
| Archivos compatibilidad | stats_extractor.py, stats_robot.py, scrapers_fallback.py |
| Schema corregido | `estadisticas_equipos` → `equipos_stats` |
| cloudscraper agregado | Para WhoScored y Soccerway |

## 🔴 Errores Corregidos (para referencia)

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: 'stats_extractor'` | Creado archivo de compatibilidad `stats_extractor.py` |
| `ModuleNotFoundError: 'bs4'` | Agregado `import requests` en robot_extractor.py |
| Error "solicitudes" en botón Buscar Equipos | Corregido formato de datos en `run_robot_batch` y `scrape_team_fallback` |

---

## 🚀 Cómo Continuar en Nuevo Chat

1. **LEER ESTE ARCHIVO PRIMERO** (AGENTS.md)
2. Verificar tablas en Supabase:
   ```bash
   curl -s "https://jjtifureeygvygxtpuku.supabase.co/rest/v1/partidos?limit=1" \
     -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```
3. Probar el SuperRobot:
   ```bash
   cd /workspace/project/Scorpion-elite
   python3 -c "from robot_extractor import get_football_data_stats; print(get_football_data_stats().get('Barcelona'))"
   ```
4. **REGLAS IMPORTANTES:**
   - NO eliminar archivos sin confirmar con el usuario
   - NO hacer deploy automático sin confirmar con el usuario
   - Guardar cambios en git ANTES de hacer cambios grandes
   - Los backups están en `backups/` - NO perderlos
