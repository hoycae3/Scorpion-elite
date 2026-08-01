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

## 📅 Resumen Sesión Actual (2026-07-26)

### ✅ Dashboard VIP Completo Implementado

**Nueva página 👑 VIP** con 6 módulos:

| Módulo | Descripción |
|--------|-------------|
| 📊 **ROI por Modelo** | ROI por tipo de pick (1X2, O/U, BTTS, Corners, Tarjetas, Remates) y por rango de confianza |
| 💰 **Bankroll** | Simulador con 3 estrategias: Flat, Porcentaje Fijo, Kelly Fraccional |
| 🎯 **Value Bets** | Detector de value - compara prob. modelo vs cuota implícita |
| 🔔 **Alertas** | Sistema de alertas VIP (alta confianza, streaks, resultados) |
| 🏆 **Ranking** | Ranking mensual, badges y logros |
| 📄 **Exportar** | Descargar reportes en CSV/Excel/JSON |

**Tablas Supabase nuevas:**
- `bankroll_history` - Seguimiento de bankroll
- `user_stats` - Estadísticas acumuladas por usuario
- `alertas` - Centro de notificaciones
- `value_bets` - Picks con value detectado
- `ranking` - Ranking mensual de usuarios

### 📊 Menú Actualizado (6 páginas)

```
📂 Carga | 📊 Analizador | 📈 Estadísticas | 👑 VIP | 📉 Dashboard | 🔑 Claves
```

---

## 📅 Resumen Sesión Anterior (2026-07-25)

### ✅ Login funciona correctamente
- Botón "🔐 Iniciar Sesión" en landing page
- Solo 1 botón, flujo limpio

### ✅ Métricas reales en landing page
- Consulta Supabase en tiempo real
- Muestra: Aciertos reales, Picks guardados, Yield real

### ✅ Partidos reales en landing page
- Consulta tabla `partidos` de Supabase
- Análisis preview gratis sin login

---

## 🔧 Detalles Técnicos

- `st.session_state.preview_partido` - Almacena partido seleccionado para análisis
- `st.session_state.logged` - Estado de autenticación
- `st.session_state.show_login` - Control de visibilidad del login
- Página VIP usa `usuario_id` del session_state para aislamiento de datos

---

## 📁 Estructura Actual del Proyecto

```
Scorpion-elite/
├── elite.py                 # ⭐ APP PRINCIPAL Streamlit (~2756 líneas)
│                            # 6 páginas: Carga, Analizador, Estadísticas, VIP, Dashboard, Claves
├── robot_extractor.py      # ⭐ SUPERROBOT - Todos los scrapers (49KB)
├── data_loader.py          # Procesa Excel de Flashscore
├── analysis_models.py      # 4 modelos matemáticos (Poisson, Dixon-Coles, Monte Carlo, Elo)
├── calibration.py          # Sistema de calibración automática
├── model_optimizer.py     # Optimizador de pesos de modelos
├── supabase_schema.sql     # Schema completo (incluye tablas VIP)
├── requirements.txt        # Dependencias
├── styles.css              # Estilos CSS
├── Dockerfile              # Docker para producción
├── render.yaml             # Configuración de deploy
├── backups/                # Backups de archivos eliminados
├── stats_extractor.py     # ✅ Compatibilidad -> robot_extractor
├── stats_robot.py          # ✅ Compatibilidad -> robot_extractor
├── scrapers_fallback.py    # ✅ Compatibilidad -> robot_extractor
└── scorpion/               # 🔄 NUEVO MÓDULO (en desarrollo)
    ├── __init__.py
    ├── config.py           # Configuración centralizada
    ├── api/
    │   ├── football.py     # API de football-data
    │   └── scraper.py      # Scraper unificado
    ├── db/
    │   └── database.py     # Conexión a Supabase
    ├── models/
    │   └── math.py         # Modelos matemáticos
    └── ui/
        └── components.py   # Componentes UI reutilizables
```

### ⚠️ ARCHIVOS DE COMPATIBILIDAD (NO ELIMINAR)
- `stats_extractor.py` → redirige a `robot_extractor.calculate_team_lambda`
- `stats_robot.py` → redirige a `robot_extractor.run_robot_batch`
- `scrapers_fallback.py` → redirige a `robot_extractor.scrape_team_fallback`

---

## 🤖 SUPERROBOT (robot_extractor.py) - EL ROBOT PRINCIPAL

### Fuentes de Datos

| Fuente | Datos Extraídos | Anti-Bloqueo | Cobertura |
|--------|-----------------|--------------|-----------|
| **football-data.co.uk** | Partidos, GF, GC, Victorias, Empates, Derrotas | Requests + redirects | 20+ ligas EUROPEAS |
| **API-Football** | Stats completas | API oficial | MUNDIAL (88/mes) |
| **Soccerway** | Resultados históricos, Marcadores, Liga | ✅ Cloudscraper | MUNDIAL |
| **WhoScored** | Corners, Tarjetas, Posesión, Remates, Faltas | ✅ Cloudscraper | MUNDIAL |
| **FBref** | Stats detalladas (posesión, remates, faltas) | ✅ Cloudscraper | 7 ligas TOP europeas |

### Flujo del SuperRobot (5 PASOS)
```
PASO 1: football-data.co.uk → TODOS los equipos europeos (sin límite)
         ↓ (si no encuentra)
PASO 2: API-Football → Equipos no encontrados (máx 88)
         ↓ (si se acaban los 88)
PASO 3: Soccerway → Equipos no encontrados (mundial)
         ↓ (si no encuentra)
PASO 4: WhoScored → Equipos no encontrados (mundial)
         ↓ (si no encuentra)
PASO 5: FBref → Equipos no encontrados (europa +)
         ↓
✅ Devuelve todo combinado
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

## ✅ LO QUE FUNCIONA (Implementado)

| Sección | Estado | Descripción |
|---------|--------|-------------|
| **Login** | ✅ | Contraseña: scorpion2026 |
| **Carga Excel** | ✅ | Subir .xlsx/.csv con partidos de Flashscore |
| **Buscar Equipos** | ✅ | Botón que busca stats de equipos (4 fuentes) |
| **Scraping 4 fuentes** | ✅ | FD, SW, WhoScored, FBref |
| **4 Modelos Análisis** | ✅ | Poisson, Dixon-Coles, Monte Carlo, Elo |
| **Sistema Calibración** | ✅ | Ajuste automático según resultados reales |
| **Optimizador Modelos** | ✅ | Pesos ajustables por % de acierto |
| **Picks** | ✅ | Genera picks: 1X2, O/U, BTTS, Corners, Tarjetas, Remates |
| **Dashboard** | ✅ | Métricas rendimiento, % aciertos, distribución rangos |
| **Actualizar Resultados** | ✅ | Ingresar marcador real y ver aciertos |
| **Guardar Supabase** | ✅ | Guarda picks en tabla `picks` |
| **Menú 5 páginas** | ✅ | Carga, Analizador, Estadísticas, Dashboard, Claves |
| **Panel Equipo Manual** | ✅ | Ultra compacto con stats claras |
| **Refactorización** | ✅ | Seguridad, rendimiento, CSS externo |
| **Módulo scorpion/** | 🔄 | En desarrollo (api, db, models, ui) |

---

## 📋 Flujo de Usuario (Landing Page)

```
1. Usuario entra a la página
2. Ve landing page con botón "🔐 Iniciar Sesión"
3. Ve métricas REALES (de Supabase)
4. Ve partidos del día (de Supabase)
5. Puede hacer clic en "📊 Analizar" de cualquier partido
6. Ve PREVIEW del análisis (stats + predicciones básicas)
7. Ve botón "← Volver a partidos"
8. Puede iniciar sesión para acceso completo al Analizador
```

---

## 🔑 Login del Analizador (Requiere Login)

| Funcionalidad | Disponible |
|---------------|------------|
| Análisis con 4 modelos | ✅ Solo logueado |
| Guardar picks en Supabase | ✅ Solo logueado |
| Dashboard con métricas | ✅ Solo logueado |
| Preview en landing | ✅ GRATIS (sin login) |

---

## ⚠️ Pendiente por Hacer

### 🔴 CRÍTICO - Funcionalidad

1. **Probar análisis de partidos** - ¿Funciona el preview en producción?
2. **Testar flujo completo login** - ¿El usuario puede guardar picks?
3. **Fuentes para América Latina** - football-data NO tiene Brasil, México, Argentina, MLS

### 🟡 IMPORTANTE - Mejoras

4. **Mejorar UI del análisis preview** - Más visual, gráficos
5. **Exportar picks** - Descargar análisis en PDF/Excel
6. **Notificaciones** - Alertas para alta confianza
7. **ROI y streaks** - Métricas de rendimiento en Dashboard

### 🟢 OPCIONAL - Extras

8. **Modo claro/oscuro** - Toggle de tema
9. **Comparar equipos** - Stats lado a lado sin analizar
10. **Filtros avanzados** - Por liga, confianza, fecha

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

### 2026-07-25 - Sesión Preview Análisis ✅

| Cambio | Descripción |
|--------|-------------|
| Login fijo | Un solo botón, flujo limpio |
| Métricas reales | Sin valores de demostración |
| Partidos reales | De Supabase, no hardcodeados |
| Análisis preview | Gratis en landing, muestra stats y predicciones |

### 2026-07-25 - Sesión Landing Page Pública ✅

| Cambio | Descripción |
|--------|-------------|
| Landing Page | Nueva vista pública para usuarios no autenticados |
| Hero Section | Título, subtítulo, CTA "Comenzar Ahora" |
| KPIs en Vivo | Aciertos %, Picks Analizados, Yield % |
| Demo Analizador | Seleccionar partido y ver pronóstico de ejemplo |
| Tabla Planes | Plan Gratuito vs Elite VIP |
| Login mejorado | Botón "Iniciar Sesión" en landing |

### 2026-07-25 - Sesión Raspadores y Fallbacks ✅

| Cambio | Descripción |
|--------|-------------|
| Flujo 5 pasos | Integrados: football-data → API-Football → Soccerway → WhoScored → FBref |
| Fallbacks | Si API-Football se acaba (88), busca en Soccerway, WhoScored, FBref |
| Cobertura mundial | Ahora busca equipos en TODO el mundo |

### 2026-07-25 - Sesión Refactorización y UI ✅

| Cambio | Descripción |
|--------|-------------|
| Cliente Supabase | `@st.cache_resource` - cacheado y reutilizado |
| Credenciales | Defaults de fallback (seguras pero sobreescribibles) |
| SQLite | Context managers para thread-safety |
| CSS externo | `styles.css` con `@st.cache_data` |
| safe_rerun() | Eliminado → usar `st.rerun()` directo |
| Debug login | Eliminado (expucía contraseña) |
| Panel Equipo | Ultra compacto Opción D con labels claros |

### 2026-07-22 - Sesión Integración UI con SuperRobot ✅

| Cambio | Descripción |
|--------|-------------|
| Estadísticas avanzadas | Ahora muestra: V/E/D, diferencia de goles, tiros al arco |
| Fuente de datos visible | Badge que muestra de dónde vienen los datos (🏦 football-data.co.uk, etc.) |
| Últimos 5 partidos | Lista con resultado, marcador, corners y tarjetas |
| Campo source | Se guarda en Supabase al buscar equipos |
| AGENTS.md actualizado | Documenta estado real del proyecto |

### 2026-07-22 - Sesión Actualización Docs

| Cambio | Descripción |
|--------|-------------|
| Dashboard ✅ | Ya está implementado con métricas de rendimiento, % aciertos 1X2/O/U/BTTS |
| Calibración ✅ | Sistema completo en `calibration.py` - ajusta lambdas según resultados |
| Optimizador ✅ | `model_optimizer.py` - pesos ajustables por % de acierto de cada modelo |
| Picks avanzados ✅ | Soporta: 1X2, Over/Under, BTTS, Corners, Tarjetas, Remates |
| Módulo scorpion/ | Nuevo código modular (api, db, models, ui) - en desarrollo |

### 2026-07-21 - Sesión Dashboard

| Cambio | Descripción |
|--------|-------------|
| Nueva página Dashboard | Métricas de rendimiento, distribución por confianza/rango |
| Menú con 5 páginas | Carga, Analizador, Estadísticas, Dashboard, Claves |
| Actualizar resultados | Input inline para marcador, corners, tarjetas, remates |
| Calibración inline | Resetear calibración desde Dashboard |

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

### 2026-07-20 - Sesión SuperRobot

| Cambio | Descripción |
|--------|-------------|
| SuperRobot creado | 4 fuentes: football-data, Soccerway, WhoScored, FBref |
| Archivos compatibilidad | stats_extractor.py, stats_robot.py, scrapers_fallback.py |
| Schema corregido | `estadisticas_equipos` → `equipos_stats` |
| cloudscraper agregado | Para WhoScored y Soccerway |

---

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

---

## 📅 Sesión 2026-07-31 (09:40) - Sincronización Inteligente

### ✅ LOGGING ACTUAL DEL BOTÓN "🔄 Sincronizar"

**Lógica implementada:**

| Datos | Ventana | Comportamiento |
|-------|---------|----------------|
| **Partidos** | HOY → HOY+6 (7 días) | Solo agrega partidos nuevos |
| **Stats equipos** | HOY → HOY+3 (3 días) | **Actualiza** stats de equipos existentes |

**Flujo:**
1. **Primera vez:** Descarga ventana completa (7 días partidos, 3 días stats equipos)
2. **Siguientes clicks:** Solo agrega lo que falta (partidos día nuevo, actualiza stats equipos)

**Variables clave:**
- `partidos_existentes` - Set de fixture_ids ya en BD
- `equipos_existentes` - Set de nombres de equipos ya en BD  
- `fecha_inicio` / `fecha_fin` - Determinan rango a descargar
- `fecha_equipos_fin` - HOY+3 para stats de equipos

**Commit hash funcional:** `2dbf812`

### ❌ DESCARTADO
- Tabla `sync_log` - No usar, verificar BD directamente
- Descargar equipos por cada partido - Ahora solo ventana HOY+3

### 🔧 Comandos de recuperación
```bash
# Restaurar a estado funcional conocido
git checkout 2dbf812 -- elite.py
```
