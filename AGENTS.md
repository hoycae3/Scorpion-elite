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
└── .github/workflows/      # GitHub Actions
```

**Archivos ELIMINADOS (funciones integradas en robot_extractor.py):**
- stats_robot.py ❌
- stats_extractor.py ❌
- scrapers.py ❌
- scrapers_fallback.py ❌

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

1. **Integrar SuperRobot con Supabase** - Guardar datos scrapeados en `equipos_stats`
2. **Integrar SuperRobot con elite.py** - Mostrar estadísticas en la app
3. **Probar scrapers de WhoScored/Soccerway** - Verificar que extraen datos reales
4. **Agregar fuentes para América Latina** - football-data NO tiene Brasil, México, Argentina, MLS

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

## 📅 Historial de Cambios (Sesión Actual)

| Fecha | Cambio |
|-------|--------|
| 2026-07-20 | Creado SuperRobot con 4 fuentes |
| 2026-07-20 | Eliminados 4 archivos duplicados |
| 2026-07-20 | Corregido nombre de tabla `estadisticas_equipos` → `equipos_stats` |
| 2026-07-20 | Agregado cloudscraper a WhoScored y Soccerway |
| 2026-07-20 | Completada extracción de datos reales en scrapers |

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
