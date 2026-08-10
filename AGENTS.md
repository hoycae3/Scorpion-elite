# Scorpion Elite - Estado del Proyecto (Agosto 2026)

---

## 📅 Sesión 2026-08-07 - Cambios Finales

### ✅ Landing Page: 4 Partidos Aleatorios
- Landing page muestra solo **4 partidos aleatorios** para atraer usuarios
- Sin login necesario para ver el preview del análisis
- Mensaje: "Análisis gratuito sin registro"

### ✅ Página Carga: Lista Completa
- Dentro de la app (después de login) muestra **TODOS los partidos**
- Organizados por: País → Liga → Fecha/Hora
- Badges: 🟢 Con stats | 🟡 Sin stats | 🔴 Desconocido

### ✅ Botón Limpiar Bankroll
- Ubicación: **VIP → Bankroll → Historial**
- Botón "🗑️ Limpiar Todo" para eliminar todas las apuestas
- Muestra conteo antes y después de limpiar

### ✅ Auto-actualización de Picks
- Mejorada búsqueda por fixture_id O nombres de equipos
- Al sincronizar partidos terminados (FT), se actualizan picks automáticamente
- Muestra mensaje: "🎯 Se actualizaron X picks con los resultados"

### ✅ Barra de Progreso en Sincronización
- Barra visual durante el proceso de sincronización
- Mensajes de estado en cada paso

---

## 📅 Sesión 2026-08-04 - Corrección Goals Extraction

### 🎯 Problema Identificado:
La API de Football devuelve los `goals` en la **raíz del fixture** (`f`), NO dentro de `teams`.

### 🔧 Corrección Aplicada:

#### elite.py (línea 967):
```python
# ❌ INCORRECTO (antes):
goals = teams.get('goals', {})

# ✅ CORRECTO (ahora):
goals = f.get('goals', {}) or {}
```

#### funciones_stats.py (línea 111):
```python
# ❌ INCORRECTO (antes):
goals = teams.get('goals', {})

# ✅ CORRECTO (ahora):
goals = f.get('goals', {}) or {}
```

### 📋 Estructura Correcta de la API:
```python
# El fixture 'f' tiene esta estructura:
{
    'fixture': {...},
    'teams': {'home': {...}, 'away': {...}},  # Nombres, IDs, winner
    'goals': {'home': 2, 'away': 1},  # ← Goles AQUÍ
    'score': {...}
}
```

### 🔄 Lógica de Local vs Visitante:
```python
# Determinar si el equipo es local o visitante
if home_team.get('id') == team_id:
    es_local = True
    gf = goals.get('home')  # Goles a favor si es local
    gv = goals.get('away')  # Goles en contra si es local
else:
    es_local = False
    gf = goals.get('away')  # Goles a favor si es visitante
    gv = goals.get('home')  # Goles en contra si es visitante
```

---

## 📅 Sesión 2026-08-04 - Resumen Final de Configuración

### 🔧 Configuración Actual del Botón "🔄 Sincronizar":

| Configuración | Valor |
|---------------|-------|
| **Ventana de fechas** | HOY-2 a HOY+6 |
| **Ligas habilitadas** | 55 ligas mundiales |
| **Equipos únicos** | TODOS los equipos de fixtures (nuevos y existentes) |
| **Goals extraction** | `f.get('goals', {})` ✅ |
| **Upsert** | Sin DELETE, solo inserta/actualiza |

### 📋 Botones de Sincronización:

| Botón | Función |
|-------|---------|
| **🔄 Sincronizar** | Descarga partidos HOY-2 a HOY+6, actualiza stats de equipos |
| **📊 Stats Ayer** | Actualiza stats SOLO de partidos de ayer |

### 📊 Flujo de Uso Diario:

```
DÍA 1 (MAÑANA):
├── Click "🔄 Sincronizar"
│   └── Descarga partidos de HOY-2 a HOY+6
│   └── Guarda stats de equipos nuevos
│   └── Guarda fixtures FT recientes
│
DÍA 2 (MAÑANA SIGUIENTE):
├── Click "🔄 Sincronizar"
│   └── Descarga partidos de ayer (ahora FT)
│   └── Click "📊 Stats Ayer"
│       └── Actualiza stats de partidos de ayer
```

---

## 📅 Sesión 2026-08-04 - Lambda Dinámico con Ponderación Exponencial

### Problema Anterior:
- Se borraban partidos más antiguos de `equipo_partidos_stats` (limitaba a 5)
- Lambda se calculaba con solo los últimos 5 partidos
- No había acumulación histórica

### Solución Implementada:

#### 1. `funciones_stats.py`:
```python
def guardar_stats_equipo():
    # ★ NO BORRA PARTIDOS - Acumula TODOS los partidos históricos
    # Usa upsert para no duplicar
    
def calcular_promedios_equipo(client, team_id, max_partidos=None):
    # ★ USA TODOS LOS PARTIDOS DISPONIBLES
    # ★ Aplica decaimiento exponencial: decay=0.92
    # Retorna: lambda_ponderado, partidos_total, promedios dinámicos
```

#### 2. `elite.py`:
```python
# Combina lambda dinámico con base
lambda_final = lambda_ponderado * 0.7 + lambda_base * 0.3

# Muestra en UI
"📊 X partidos históricos"
```

### Flujo de Lambda Dinámico:

| Día | Partidos Acumulados | Lambda Calculada |
|-----|---------------------|-----------------|
| 1 | 5 | Se calcula con 5 partidos |
| 2 | 6 (+1 nuevo) | Se recalcula con 6 |
| 3 | 7 (+1 nuevo) | Se recalcula con 7 |
| ... | ... | ... |

### Ponderación Exponencial:
```
Partidos recientes pesan más:
- decay = 0.92
- Partido más reciente: peso = 1.0
- Partido 5to: peso = 0.92^5 ≈ 0.66
- Partido 10mo: peso = 0.92^10 ≈ 0.43
```

---

## 📅 Sesión 2026-08-04 - Modelos Matemáticos Reales para Predicciones Adicionales

### 🎯 Problema Anterior:
Las predicciones de Tiros, Tarjetas y Tiros Arco usaban **fórmulas heurísticas simples**:
```python
# ANTES (heurística simple)
remates_over_prob = min(90, max(10, 50 + (remates_total - 24) * 2))
tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))
arco_over_prob = min(90, max(10, 50 + (arco_total - 8) * 3))
```

### ✅ Solución Implementada:

#### 1. `analysis_models.py` - Nuevas funciones:

| Función | Descripción | Línea típica |
|---------|-------------|-------------|
| `predecir_tiros()` | Over/Under 24 | 24 |
| `predecir_tarjetas()` | Over/Under 6 | 6 |
| `predecir_tiros_arco()` | Over/Under 8 | 8 |
| `normal_cdf()` | Función de distribución normal (aproximación Abramowitz & Stegun) | - |

#### 2. Cómo funcionan los modelos:

```python
# Usan distribución normal con:
# - Media: suma de promedios de ambos equipos
# - Varianza: aproximación Poisson (varianza ≈ media)

def predecir_tiros(tiros_local, tiros_visitante, ...):
    total_estimado = tiros_local + tiros_visitante
    # Calcular P(Over 24) usando distribución normal
    z = (24.5 - media) / desviacion
    over_24 = (1 - normal_cdf(z)) * 100
```

### 🔄 Flujo de Datos:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1️⃣ equipo_partidos_stats (Supabase)                                  │
│      └─→ Guarda cada partido histórico del equipo                      │
│                                                                         │
│  2️⃣ calcular_promedios_equipo()                                       │
│      └─→ Lee de equipo_partidos_stats                                  │
│      └─→ Aplica PONDERACIÓN EXPONENCIAL (decay=0.92)                  │
│      └─→ Retorna: promedio_tiros, promedio_amarillas, promedio_arco   │
│                                                                         │
│  3️⃣ elite.py → botón "ANALIZAR"                                       │
│      └─→ Usa promedios_dinamicos_local/visitante                      │
│      └─→ Llama a calcular() con estos datos                           │
│                                                                         │
│  4️⃣ analysis_models.py → calcular()                                    │
│      └─→ predecir_tiros() → usa promedio_tiros → Over/Under 24        │
│      └─→ predecir_tarjetas() → usa promedio_amarillas → Over/Under 6  │
│      └─→ predecir_tiros_arco() → usa promedio_arco → Over/Under 8      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 💾 Botón Guardar Actualizado:

Ahora guarda TODAS las predicciones en la tabla `picks`:
- ✅ 1X2: pick, prob, p1, px, p2
- ✅ Over/Under: pick, prob, over_25, under_25
- ✅ BTTS: pick, prob, btts_yes, btts_no
- ✅ Corners: pick, total_estimado
- ✅ Tiros: pick, total, local, visitante, over_prob
- ✅ Tarjetas: pick, total, over_prob, under_prob
- ✅ Tiros Arco: pick, total, local, visitante, over_prob, under_prob
- ✅ Confianza y Rango

---

## 📅 Sesión 2026-08-07 - Rediseño Bankroll VIP

### 🎨 Nuevo Diseño Bankroll

**Características implementadas:**

| Característica | Descripción |
|----------------|-------------|
| **Bankroll Card** | Diseño tipo tarjeta grande verde con gradiente |
| **Individual** | Seleccionar picks y apostar cada uno separado |
| **Combinada** | Seleccionar 2+ picks, multiplica cuotas automáticamente |
| **Cuota editable** | Usuario puede modificar la cuota antes de apostar |
| **3 tabs** | Dashboard, Agregar, Historial |

**Flujo de uso:**

```
1. Dashboard → Ver bankroll actual con métricas
2. Agregar → Seleccionar picks con checkboxes → Editar cuota → Apostar
3. Historial → Ver apuestas guardadas, actualizar resultados
```

**Código clave:**

```python
# Selector de picks con cuota editable
for i, opt in enumerate(opciones):
    sel = st.checkbox("", key=f"sel_pick_{i}")
    cantidad_input = st.number_input("Cuota", value=float(opt['cuota']), key=f"cuota_{i}")
    cantidades_dict[i] = cantidad_input

# Combinada: multiplicar cuotas
cuota_total = 1.0
for i in seleccionados:
    cuota_total *= cantidades_dict.get(i, opciones[i]['cuota'])
```

### 🔧 Errores Corregidos:

| Error | Solución |
|--------|----------|
| `safe_fmt` UnboundLocalError | Usar inline: `(opt.get('prob') or 0):.0f` |
| `NoneType.__format__` | Verificar valores antes de formatear |

### 📊 Sistema de "Sin Datos":

Cuando NO hay datos reales (equipos sin sincronizar), ahora muestra `?` en todos los campos.

| Campo | Sin datos |
|-------|-----------|
| PJ | `?` |
| VED | `?-?-?` |
| Goles | `?` |
| Promedios | `?` |
| Lambda | `?` |
| Forma | `?` |
| OU 2.5 | `?` |
| BTTS | `?` |
| Corners | `?` |
| Tiros | `?` |
| TArco | `?` |
| Tarjetas | `?` |
| Marcador | `?` |

### 🔧 Código Clave:

```python
def safe_fmt(val, fmt='.1f'):
    """Convierte valor a string, manteniendo '?' si no hay datos"""
    if val == '?' or val is None:
        return '?'
    try:
        return f'{float(val):{fmt}}'
    except:
        return str(val)

def safe_fmt_int(val):
    """Convierte valor a string entero"""
    if val == '?' or val is None:
        return '?'
    try:
        return f'{int(float(val))}'
    except:
        return str(val)
```

### 📝 Lógica de Lambda:

```python
# Calcular lambda_historico (basado en goles/pj)
lambda_historico_local = gf_l / pj_l if pj_l > 0 else 1.3

# Lambda FINAL = 60% dinamico + 40% historico
if lambda_dinamico_local_calc is not None:
    lambda_local_final = lambda_dinamico_local_calc * 0.6 + lambda_historico_local * 0.4
else:
    lambda_local_final = lambda_historico_local
```

---

## 📋 REVISIÓN DE CÓDIGO (2026-08-07)

### ✅ Lo que FUNCIONA:

| Componente | Estado | Notas |
|------------|--------|-------|
| Login con contraseña | ✅ | `render_login_form()` |
| Landing page (4 partidos aleatorios) | ✅ | Solo 4 partidos para preview |
| Página Carga (todos los partidos) | ✅ | Por país/liga |
| Sincronización de partidos | ✅ | 55 ligas, ventana HOY-2 a HOY+6 |
| Auto-actualización de picks | ✅ | Por fixture_id o nombres |
| Barra de progreso | ✅ | Durante sincronización |
| Análisis con 4 modelos | ✅ | Poisson, Dixon-Coles, Monte Carlo, Elo |
| Predicciones adicionales | ✅ | O/U, BTTS, Corners, Tiros, Tarjetas, Arco |
| Bankroll (Dashboard/Agregar/Historial) | ✅ | Con botón limpiar |
| Guardar picks en Supabase | ✅ | Todas las predicciones |
| Limpiar Bankroll | ✅ | En VIP → Historial |

### ⚠️ PROBLEMAS ENCONTRADOS:

#### 1. **Código de Consenso (SIMULADO)**
- **Ubicación:** Al final de la página VIP
- **Problema:** Usa el mismo valor para todos los modelos:
```python
probabilidades = [
    ultimo.get('p1', 0) or 00,    # ← Mismo valor
    ultimo.get('p1', 0) or 00,    # ← Mismo valor (dice "Simulado")
    ultimo.get('p1', 0) or 00,    # ← Mismo valor
    ultimo.get('p1', 0) or 00,    # ← Mismo valor
]
```
- **Solución:** Guardar scores de cada modelo individual para mostrar consenso real

#### 2. **except: vacíos** (Ocultan errores)
- 20+ lugares con `except: pass` o `except: continue`
- **Ubicaciones:** líneas 124, 219, 228, 942, 1246, 1423, 1555, 1644, 1688, 1741
- **Recomendación:** Agregar logging para debugging

#### 3. **Variables no inicializadas en except**
- Algunos `except` no inicializan variables que se usan después
- Puede causar errores si ciertos queries fallan

### ❌ CÓDIGO DUPLICADO:

| Sección | Duplicado | Notas |
|---------|-----------|-------|
| Búsqueda de stats por equipo | ❌ NO | Usa `client.table('equipos_stats').select()` en 2 lugares, pero lógica diferente |
| Función `get_pais_emoji()` | ❌ NO | Definida dentro de cada bloque (línea 1598) |
| `safe_fmt()` / `safe_fmt_int()` | ❌ NO | Definidas en analizador, no duplicadas |

### 📁 ESTRUCTURA DE PÁGINAS ACTUAL:

```
PÁGINA PRINCIPAL:
├── 🌐 Landing (sin login)
│   └── 4 partidos aleatorios + preview análisis
│
MENU (después de login):
├── 👑 VIP (por defecto)
│   ├── Dashboard
│   ├── Agregar
│   ├── Historial (🗑️ Limpiar)
│   └── Config
├── 📊 Partidos
│   ├── 🔄 Sincronizar
│   ├── 📊 Stats Ayer
│   └── 🧹 Limpiar Equipos
├── 📥 Analizador
└── 🔑 Claves
```

### 🔧 LO QUE FALTA O ESTÁ INCOMPLETO:

| Funcionalidad | Estado | Notas |
|---------------|--------|-------|
| Consenso de modelos | ⚠️ Simulado | Solo muestra 1 valor repetido 4 veces |
| Páginas "Estadísticas" y "Dashboard" | ❌ Eliminadas | No existen en el menú actual |
| Exportar picks | ⚠️ Parcial | Existe botón pero no verificado |
| Ranking mensual | ⚠️ Parcial | Existe en código pero no accesible |
| Notificaciones/Alertas | ⚠️ Parcial | Tab existe pero funcionalidad limitada |
| Value Bets detector | ⚠️ Parcial | Tab existe pero básico |

### 📊 MÉTRICAS:

- **Líneas de código:** 4,201
- **Funciones principales:** 15+ (db_*, render_*, get_*, css, etc.)
- **Imports:** 12 módulos
- **Páginas reales:** 4 (VIP, Partidos, Analizador, Claves)

### 🚀 RECOMENDACIONES:

1. **Alta prioridad:**
   - Implementar consenso real de modelos (guardar p1 de cada modelo)
   - Agregar manejo de errores con logging en vez de `except: pass`

2. **Media prioridad:**
   - Reintegrar páginas "Estadísticas" y "Dashboard" al menú
   - Verificar funcionalidad de exportación de picks
   - Implementar sistema de alertas completo

3. **Baja prioridad:**
   - Limpiar `except:` vacíos
   - Agregar tests unitarios
   - Documentar funciones principales

---

## 📌 Información General

| Item | Valor |
|------|-------|
| **Repositorio** | https://github.com/hoycae3/Scorpion-elite |
| **App Producción** | https://scorpion-elite.onrender.com |
| **Base de datos** | Supabase (jjtifureeygvygxtpuku.supabase.co) |
| **Deploy** | Render (srv-d9e1thbbc2fs73f30jh0) |
| **Password app** | scorpion2026 |

---

## 📅 Resumen Sesión Actual (2026-08-01)

### ✅ Correcciones al Botón Sincronizar

**Problemas corregidos:**

| Problema | Solución |
|----------|----------|
| `season = 2026` hardcodeado | Cálculo dinámico según mes actual |
| Ventana de solo 2 días | Ahora busca **7 días** (HOY → HOY+6) |
| Solo 35 ligas | Ahora **55 ligas** con formato unificado |
| No mostraba info de temporada | Ahora muestra: `⚽ Temporada: 2026 \| Pretemporada: True/False` |

**Ligas incluidas (55):**
- 🏆 9 torneos internacionales (Champions, Libertadores, Sudamericana, etc.)
- 🇪🇺 19 ligas europeas (La Liga, Premier, Bundesliga, Serie A, Ligue 1, etc.)
- 🇧🇷 3 Brasil, 🇦🇷 3 Argentina, 🇨🇴 2 Colombia, 🇨🇱 2 Chile, etc.
- 🇺🇸 3 USA (MLS, USL), 🇲🇽 2 México (Liga MX)
- 🇯🇵 Japón, 🇰🇷 Corea, 🇸🇦 Arabia, 🇪🇬 Egipto

**Lógica de temporada:**
```
Si mes >= 8 (agos-dic) → season = año_actual
Si mes < 8 (ene-jul) → season = año_actual - 1
```

---

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

1. **Probar sincronización en producción** - Verificar que busque con temporada correcta
2. **Testar flujo completo login** - ¿El usuario puede guardar picks?
3. **Verificar cobertura de ligas** - ¿Las 55 ligas funcionan correctamente?

### 🟡 IMPORTANTE - Mejoras

4. **Mejorar UI del análisis preview** - Más visual, gráficos
5. **Exportar picks** - Descargar análisis en PDF/Excel
6. **Notificaciones** - Alertas para alta confianza
7. **Pretemporada** - Agregar opción de buscar partidos de pretemporada o liga anterior

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
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "dont_clear"}'

# Verificar app
curl -s -o /dev/null -w "%{http_code}" https://scorpion-elite.onrender.com/
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

## 📅 Sesión 2026-08-01 - Correcciones al Sincronizar

### Cambios realizados:

| Cambio | Descripción |
|--------|-------------|
| **Temporada dinámica** | `season = 2026` hardcodeado → cálculo automático (mes >= 8 → año actual, sino año-1) |
| **Ventana 7 días** | Cambiado de 2 a 7 días (HOY → HOY+6) |
| **Mostrar info** | Ahora muestra: "⚽ Temporada: 2026 \| Pretemporada: True/False" |
| **Botones corregidos** | Sincronizar y Equipos usan el mismo cálculo dinámico |
| **55 ligas** | Reemplazada lista corta (35) con completa (55 ligas) |
| **Formato unificado** | Ambos botones usan diccionarios con `id`, `name`, `pais` |

### Lógica implementada:

| Datos | Ventana | Comportamiento |
|-------|---------|----------------|
| **Partidos** | HOY → HOY+6 (7 días) | Solo agrega partidos nuevos |
| **Stats equipos** | De partidos guardados | Usa `upsert` - actualiza solo si es nuevo |

---

## 📅 Sesión 2026-08-03 - Lambda Dinámico con Ponderación Exponencial

### Problema Anterior:
- Se borraban partidos más antiguos de `equipo_partidos_stats` (limitaba a 5)
- Lambda se calculaba con solo los últimos 5 partidos
- No había acumulación histórica

### Solución Implementada:

#### 1. `funciones_stats.py`:
```python
def guardar_stats_equipo():
    # ★ NO BORRA PARTIDOS - Acumula TODOS los partidos históricos
    # Usa upsert para no duplicar
    
def calcular_promedios_equipo(client, team_id, max_partidos=None):
    # ★ USA TODOS LOS PARTIDOS DISPONIBLES
    # ★ Aplica decaimiento exponencial: decay=0.92
    # Retorna: lambda_ponderado, partidos_total, promedios dinámicos
```

#### 2. `elite.py`:
```python
# Combina lambda dinámico con base
lambda_final = lambda_ponderado * 0.7 + lambda_base * 0.3

# Muestra en UI
"📊 X partidos históricos"
```

### Flujo de Lambda Dinámico:

| Día | Partidos Acumulados | Lambda Calculada |
|-----|---------------------|-----------------|
| 1 | 5 | Se calcula con 5 partidos |
| 2 | 6 (+1 nuevo) | Se recalcula con 6 |
| 3 | 7 (+1 nuevo) | Se recalcula con 7 |
| ... | ... | ... |

### Ponderación Exponencial:
```
Partidos recientes pesan más:
- decay = 0.92
- Partido más reciente: peso = 1.0
- Partido 5to: peso = 0.92^5 ≈ 0.66
- Partido 10mo: peso = 0.92^10 ≈ 0.43
```

### Nota importante:
- En pretemporada (agos-feb) no habrá partidos de liga - es normal
- La app buscará con la temporada correcta automáticamente

---

## 📅 Sesión 2026-08-03 - Modelos Matemáticos Reales para Predicciones Adicionales

### 🎯 Problema Anterior:
Las predicciones de Tiros, Tarjetas y Tiros Arco usaban **fórmulas heurísticas simples**:
```python
# ANTES (heurística simple)
remates_over_prob = min(90, max(10, 50 + (remates_total - 24) * 2))
tarjetas_over_prob = min(90, max(10, 50 + (tarjetas_total - 6) * 5))
arco_over_prob = min(90, max(10, 50 + (arco_total - 8) * 3))
```

### ✅ Solución Implementada:

#### 1. `analysis_models.py` - Nuevas funciones:

| Función | Descripción | Línea típica |
|---------|-------------|-------------|
| `predecir_tiros()` | Over/Under 24 | 24 |
| `predecir_tarjetas()` | Over/Under 6 | 6 |
| `predecir_tiros_arco()` | Over/Under 8 | 8 |
| `normal_cdf()` | Función de distribución normal (aproximación Abramowitz & Stegun) | - |

#### 2. Cómo funcionan los modelos:

```python
# Usan distribución normal con:
# - Media: suma de promedios de ambos equipos
# - Varianza: aproximación Poisson (varianza ≈ media)

def predecir_tiros(tiros_local, tiros_visitante, ...):
    total_estimado = tiros_local + tiros_visitante
    # Calcular P(Over 24) usando distribución normal
    z = (24.5 - media) / desviacion
    over_24 = (1 - normal_cdf(z)) * 100
```

### 🔄 Flujo de Datos:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1️⃣ equipo_partidos_stats (Supabase)                                  │
│      └─→ Guarda cada partido histórico del equipo                      │
│                                                                         │
│  2️⃣ calcular_promedios_equipo()                                       │
│      └─→ Lee de equipo_partidos_stats                                  │
│      └─→ Aplica PONDERACIÓN EXPONENCIAL (decay=0.92)                  │
│      └─→ Retorna: promedio_tiros, promedio_amarillas, promedio_arco   │
│                                                                         │
│  3️⃣ elite.py → botón "ANALIZAR"                                       │
│      └─→ Usa promedios_dinamicos_local/visitante                      │
│      └─→ Llama a calcular() con estos datos                           │
│                                                                         │
│  4️⃣ analysis_models.py → calcular()                                    │
│      └─→ predecir_tiros() → usa promedio_tiros → Over/Under 24        │
│      └─→ predecir_tarjetas() → usa promedio_amarillas → Over/Under 6  │
│      └─→ predecir_tiros_arco() → usa promedio_arco → Over/Under 8      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 📱 UI del Analizador (Rediseñada):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🏠 JAGUARES (15 part.)              ✈️ ATLÉTICO NACIONAL (25 part.)     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐ │
│  │     PJ    V    E    D          │  │     PJ    V    E    D          │ │
│  │     20   5    3    12         │  │     25   18    1    6         │ │
│  └────────────────────────────────┘  └────────────────────────────────┘ │
│                                                                             │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐ │
│  │ ⚽ GF: 20   GC: 35           │  │ ⚽ GF: 49   GC: 21           │ │
│  │ λ Ajustada: 🔽 1.85          │  │ λ Ajustada: 🔼 0.81          │ │
│  └────────────────────────────────┘  └────────────────────────────────┘ │
│                                                                             │
│  ┌────────────────────────────────┐  ┌────────────────────────────────┐ │
│  │ 📈 Promedios por partido:      │  │ 📈 Promedios por partido:      │ │
│  │ 🔫 Tiros: 12.0   🎯 Arco: 4.0│  │ 🔫 Tiros: 10.5  🎯 Arco: 3.5│ │
│  │ 🟨 Amarillas: 3.0  🌽 Córners:│  │ 🟨 Amarillas: 2.5  🌽 Córners:│ │
│  └────────────────────────────────┘  └────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  🎯 PROBABILIDADES (1X2)                                                  │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐                         │
│  │ 🏠 Jaguares │  │🤝 Empate │  │✈️ Atlético  │                         │
│  │    35.2%    │  │  28.1%  │  │    36.7%    │                         │
│  └──────────────┘  └──────────┘  └──────────────┘                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 PREDICCIONES ADICIONALES (MODELO MATEMÁTICO)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │📈 O/U 2.5│ │⚽ BTTS │ │🌽Córners│ │🔫 Tiros │ │🎯 Arco │ │🟨Amaril│ │
│  │ - 2.5  │ │ ✅ Sí │ │ + 10.5 │ │ Total │ │ Total │ │ Total │ │
│  │ 65%   │ │ 58%   │ │ 40%    │ │ 22    │ │ 7.5   │ │ 5.5   │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│                                                                             │
│  🔫 Tiros: 22.5 → 📈 Over 24 (74%)                                        │
│  🎯 Arco: 7.5 → 📉 Under 8 (68%)                                          │
│  🟨 Amarillas: 5.5 → 📈 Over 6 (48%)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                        💾 GUARDAR PARTIDO                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 💾 Botón Guardar Actualizado:

Ahora guarda TODAS las predicciones en la tabla `picks`:
- ✅ 1X2: pick, prob, p1, px, p2
- ✅ Over/Under: pick, prob, over_25, under_25
- ✅ BTTS: pick, prob, btts_yes, btts_no
- ✅ Corners: pick, total_estimado
- ✅ Tiros: pick, total, local, visitante, over_prob
- ✅ Tarjetas: pick, total, over_prob, under_prob
- ✅ Tiros Arco: pick, total, local, visitante, over_prob, under_prob
- ✅ Confianza y Rango

### 📊 Schema SQL actualizado (supabase_schema.sql):

Nuevas columnas en tabla `picks`:
```sql
-- Tiros Arco
prediccion_arco VARCHAR(20),
arco_total_estimado DECIMAL(5,2),
arco_local DECIMAL(5,2),
arco_visitante DECIMAL(5,2),
arco_over_prob DECIMAL(5,2),
arco_under_prob DECIMAL(5,2),

-- Resultados arco
resultado_arco VARCHAR(20),
acertado_arco BOOLEAN,
```

### 📁 Archivos modificados:

| Archivo | Cambios |
|---------|---------|
| `analysis_models.py` | +260 líneas (nuevas funciones de predicción) |
| `elite.py` | ~+100 líneas (UI rediseñada, guardar actualizado) |
| `supabase_schema.sql` | +15 líneas (campos arco en picks) |

---

## 🔴 PENDIENTE - Por hacer

### 🔴 CRÍTICO - Funcionalidad

1. **Probar sincronización en producción** - Verificar que busque con temporada correcta
2. **Testar flujo completo login** - ¿El usuario puede guardar picks?
3. **Verificar cobertura de ligas** - ¿Las 55 ligas funcionan correctamente?
4. **Agregar columnas de arco a tabla picks en Supabase** - Ejecutar ALTER TABLE

### 🟡 IMPORTANTE - Mejoras

5. **Mejorar UI del análisis preview** - Más visual, gráficos
6. **Exportar picks** - Descargar análisis en PDF/Excel
7. **Notificaciones** - Alertas para alta confianza
8. **Pretemporada** - Agregar opción de buscar partidos de pretemporada o liga anterior

### 🟢 OPCIONAL - Extras

9. **Modo claro/oscuro** - Toggle de tema
10. **Comparar equipos** - Stats lado a lado sin analizar
11. **Filtros avanzados** - Por liga, confianza, fecha
12. **Sincronizar resultados automáticamente** - De Flashscore o API

---

## ⚙️ Cómo se Ajustan los Modelos (Auto-calibración)

### 1️⃣ Calibración por Equipo (`calibration.py`)
```python
# Después de cada partido:
error_local = goles_reales - lambda_predicha

# Si marcó MÁS de lo predicho → factor sube (ej: 1.1)
# Si marcó MENOS de lo predicho → factor baja (ej: 0.9)
```

### 2️⃣ Optimizador de Pesos (`model_optimizer.py`)
```python
# Históricamente:
# Poisson acertó 58% → peso sube a 0.35
# Dixon-Coles acertó 52% → peso baja a 0.22
# Monte Carlo acertó 55% → peso sube a 0.23
```

### ⚠️ IMPORTANTE:
Para que la calibración funcione, el usuario debe **ingresar los resultados reales** usando el botón "Actualizar Resultado" en el Dashboard.

---

## 🚀 Deploy en Render

Para ver los cambios en producción:
```bash
curl -X POST "https://api.render.com/v1/services/srv-d9e1thbbc2fs73f30jh0/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "dont_clear"}'
```

Para agregar columnas faltantes a Supabase:
```sql
ALTER TABLE picks ADD COLUMN IF NOT EXISTS prediccion_arco VARCHAR(20);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_total_estimado DECIMAL(5,2);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_local DECIMAL(5,2);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_visitante DECIMAL(5,2);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_over_prob DECIMAL(5,2);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS arco_under_prob DECIMAL(5,2);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS resultado_arco VARCHAR(20);
ALTER TABLE picks ADD COLUMN IF NOT EXISTS acertado_arco BOOLEAN;
```

---

## 📅 Sesión 2026-08-04 - Corrección Crítica de Sincronización

### 🎯 Problemas Identificados y Corregidos:

| Bug | Descripción | Solución |
|-----|-------------|----------|
| **Equipos omitidos** | Equipos de partidos existentes no se agregaban a `equipos_unicos` | ✅ Ahora TODOS los equipos se agregan siempre |
| **Rango fechas insuficiente** | Solo HOY → HOY+6 | ✅ Ahora HOY-3 → HOY+10 |
| **Excepciones silenciosas** | `except: pass` ocultaba errores | ✅ Ahora muestran `st.warning()` |
| **Variable indefinida** | `equipos_con_stats` nunca definida | ✅ Corregido a `equipos_unicos` |
| **guardar_stats_equipo()** | Retornaba solo boolean | ✅ Ahora retorna tuple (success, msg, count) |

### 🔧 Cambios Técnicos:

#### 1. `elite.py` - Lógica de equipos_unicos (CORREGIDA):
```python
# ★ ANTES (BUG): Equipos solo se agregaban si partido era nuevo
if fix_id not in partidos_existentes:
    # Agregar equipos aquí... (fallaba si partido ya existía)
    equipos_unicos[team_id_local] = {...}

# ★ AHORA (CORRECTO): Equipos SIEMPRE se agregan de TODOS los fixtures
if team_id_local:
    equipos_unicos[team_id_local] = {...}
if team_id_visitante:
    equipos_unicos[team_id_visitante] = {...}
# Guardar partido nuevo solo si es nuevo
if fix_id not in partidos_existentes:
    client.table("partidos").upsert(...).execute()
```

#### 2. `elite.py` - Rango de Fechas (AMPLIADO):
```python
# ★ ANTES: 7 días
fecha_inicio = hoy_str  # HOY
fecha_fin = (hoy + timedelta(days=6)).strftime('%Y-%m-%d')  # HOY+6

# ★ AHORA: 13 días (incluye partidos recientes finalizados)
fecha_inicio = (hoy - timedelta(days=3)).strftime('%Y-%m-%d')  # HOY-3
fecha_fin = (hoy + timedelta(days=10)).strftime('%Y-%m-%d')  # HOY+10
```

#### 3. `funciones_stats.py` - guardar_stats_equipo() (MEJORADO):
```python
def guardar_stats_equipo(client, team_id, equipo, partidos_stats):
    """
    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    # Ahora muestra errores individuales pero continúa con otros partidos
    # Usa logging para debugging
    # Retorna conteo de partidos guardados
```

### ✅ Resultado Esperado:
- Al sincronizar, TODOS los equipos de TODOS los partidos (nuevos y existentes) se agregarán a `equipos_unicos`
- Cada equipo obtendrá sus estadísticas actualizadas en `equipos_stats`
- Los últimos 5 partidos de cada equipo se guardarán en `equipo_partidos_stats`
- Errores ya no se ocultan - se muestran en pantalla

### 📊 Tabla `equipo_partidos_stats` - Estructura:
```sql
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
    corners INTEGER DEFAULT 0,
    amarillas INTEGER DEFAULT 0,
    UNIQUE(team_id, fixture_id)  -- Evita duplicados
);
```

---

## 📅 Sesión 2026-08-04 - Sincronización Incremental Implementada

### 🎯 Objetivo:
Optimizar el uso de API credits de API-Football descargando solo los datos necesarios.

### 🔄 Lógica de Sincronización Incremental:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLICK "🔄 SINCRONIZAR"                                                    │
│  ├── PASO 1: Descargar partidos (hoy-2 a hoy+6)                           │
│  │   └── Upsert a tabla `partidos`                                        │
│  │   └──收集 FT fixtures por equipo en `equipos_ft_fixtures`              │
│  │   └── Agregar TODOS los equipos a `equipos_unicos`                    │
│  │                                                                          │
│  └── PASO 2: Sincronizar stats de equipos                                 │
│      ├── Verificar qué equipos ya tienen stats en `equipo_partidos_stats` │
│      │                                                                          │
│      ├── CASO A: EQUIPO NUEVO (0 records en DB)                           │
│      │   └── Fetch /teams/statistics → guardar en `equipos_stats`         │
│      │   └── Fetch 5 partidos iniciales con stats                         │
│      │   └── Upsert a `equipo_partidos_stats`                            │
│      │                                                                          │
│      └── CASO B: EQUIPO EXISTENTE (tiene records)                          │
│          └── Verificar qué fixture_ids ya están guardados                   │
│          └── Para cada FT en ventana de búsqueda:                          │
│              ├── Si fixture_id YA existe → SKIP (0 API calls)             │
│              └── Si fixture_id FALTA → Fetch /fixtures/statistics        │
│                  └── Upsert solo ese partido a `equipo_partidos_stats`    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 📊 Métricas en Resumen Final:

| Métrica | Descripción |
|---------|-------------|
| 🏆 **Ligas procesadas** | Número de ligas consultadas |
| 📅 **Partidos guardados** | Partidos nuevos upsertados |
| 👥 **Equipos detectados** | Equipos únicos encontrados |
| 🆕 **Equipos nuevos** | Equipos sin stats previas |
| ♻️ **Equipos existentes** | Equipos con stats previas |
| 📊 **Stats equipos descargadas** | Equipos con `equipos_stats` actualizado |
| 📈 **Stats FT incrementales** | Stats de partidos FT nuevos guardados |

### 💡 Beneficios:
- **Nuevo equipo**: Descarga 5 partidos iniciales → ~5-6 API calls
- **Equipo existente sin FT nuevos**: 0 API calls
- **Equipo existente con 1 FT nuevo**: 1 API call (en lugar de 5+)

### 📝 Código Clave:

```python
# Equipos existentes - solo fetch partidos FT no guardados
ft_en_ventana = equipos_ft_fixtures.get(team_id, [])
fixtures_necesarios = [f for f in ft_en_ventana 
                       if f['fixture_id'] not in fixtures_guardados]

if fixtures_necesarios:
    for fix_info in fixtures_necesarios:
        # Fetch stats del partido específico (1 API call)
        stats_partido = obtener_stats_partido(...)
```

### ✅ Verificación:
1. **Nuevo equipo**: Al sincronizar, debe mostrar `🆕 X partidos iniciales cargados`
2. **Equipo existente sin cambios**: Sin mensajes de fetch (0 API calls)
3. **Equipo existente con FT nuevo**: Debe mostrar stats incrementales guardadas

---

## 📅 Sesión 2026-08-04 - Botón "Stats Ayer" para Actualizar Partidos

### 🎯 Objetivo:
Agregar botón `📊 Stats Ayer` para actualizar únicamente los partidos de ayer (hoy-1) que ya están guardados en Supabase.

### 📋 Lógica Implementada:

```
BOTÓN: 📊 Stats Ayer
├── PASO 1: Consultar partidos de ayer en Supabase
│   └── SELECT * FROM partidos WHERE fecha = (hoy - 1)
│   └── Si no hay partidos → mensaje y salir
│
├── PASO 2: Para cada partido de ayer
│   ├── GET /fixtures?id={fixture_id}
│   │   └── Actualizar estado (FT) y scores en tabla `partidos`
│   │
│   └── Si estado == 'FT':
│       ├── GET /fixtures/statistics?fixture={fixture_id}
│       ├── Extraer stats: corners, tiros, tarjetas, posesión
│       └── UPSERT en `equipo_partidos_stats` (para local y visitante)
│
└── RESUMEN: Mostrar stats actualizadas y errores
```

### 🔧 Flujo Detallado:

1. **Consulta Supabase**: Obtiene fixture_ids de partidos con fecha = ayer
2. **Para cada fixture**:
   - Consulta API para obtener estado actual y scores
   - Actualiza tabla `partidos` con estado FT y scores finales
   - Si el partido está FT, obtiene estadísticas detalladas
   - Inserta/actualiza stats en `equipo_partidos_stats` para ambos equipos
3. **Reporte**: Muestra resumen con stats actualizadas y errores

### 📊 Columnas de Stats Guardadas:
- `fixture_id`, `team_id`, `equipo`, `fecha`, `liga`
- `es_local`, `resultado` (W/D/L)
- `goles_favor`, `goles_contra`
- `tiros_totales`, `tiros_arco`, `tiros_fuera`
- `corners`, `amarillas`, `rojas`
- `posesion`, `faltas`, `ahorradas`

### ✅ Beneficios:
- Solo consume API credits para partidos de ayer
- No descarga partidos nuevos
- Actualiza stats incrementales solo donde es necesario

---

## 📅 Sesión 2026-08-04 - Corrección Goals Extraction

### 🎯 Problema Identificado:
La API de Football devuelve los `goals` en la **raíz del fixture** (`f`), NO dentro de `teams`.

### 🔧 Corrección Aplicada:

#### elite.py (línea 967):
```python
# ❌ INCORRECTO (antes):
goals = teams.get('goals', {})

# ✅ CORRECTO (ahora):
goals = f.get('goals', {}) or {}
```

#### funciones_stats.py (línea 111):
```python
# ❌ INCORRECTO (antes):
goals = teams.get('goals', {})

# ✅ CORRECTO (ahora):
goals = f.get('goals', {}) or {}
```

### 📋 Estructura Correcta de la API:
```python
# El fixture 'f' tiene esta estructura:
{
    'fixture': {...},
    'teams': {'home': {...}, 'away': {...}},  # Nombres, IDs, winner
    'goals': {'home': 2, 'away': 1},  # ← Goles AQUÍ
    'score': {...}
}
```

### 🔄 Lógica de Local vs Visitante:
```python
# Determinar si el equipo es local o visitante
if home_team.get('id') == team_id:
    es_local = True
    gf = goals.get('home')  # Goles a favor si es local
    gv = goals.get('away')  # Goles en contra si es local
else:
    es_local = False
    gf = goals.get('away')  # Goles a favor si es visitante
    gv = goals.get('home')  # Goles en contra si es visitante
```

---

## 📅 Sesión 2026-08-04 - Resumen Final de Configuración

### 🔧 Configuración Actual del Botón "🔄 Sincronizar":

| Configuración | Valor |
|---------------|-------|
| **Ventana de fechas** | HOY-2 a HOY+6 |
| **Ligas habilitadas** | 55 ligas mundiales |
| **Equipos únicos** | TODOS los equipos de fixtures (nuevos y existentes) |
| **Goals extraction** | `f.get('goals', {})` ✅ |
| **Upsert** | Sin DELETE, solo inserta/actualiza |

### 📋 Botones de Sincronización:

| Botón | Función |
|-------|---------|
| **🔄 Sincronizar** | Descarga partidos HOY-2 a HOY+6, actualiza stats de equipos |
| **📊 Stats Ayer** | Actualiza stats SOLO de partidos de ayer |

### 📊 Flujo de Uso Diario:

```
DÍA 1 (MAÑANA):
├── Click "🔄 Sincronizar"
│   └── Descarga partidos de HOY-2 a HOY+6
│   └── Guarda stats de equipos nuevos
│   └── Guarda fixtures FT recientes
│
DÍA 2 (MAÑANA SIGUIENTE):
├── Click "🔄 Sincronizar"
│   └── Descarga partidos de ayer (ahora FT)
│   └── Click "📊 Stats Ayer"
│       └── Actualiza stats de partidos de ayer
```

### 📁 Archivos Clave:

| Archivo | Propósito |
|---------|-----------|
| `elite.py` | App principal, lógica de sincronización |
| `funciones_stats.py` | Funciones para obtener stats de partidos |
| `equipos_stats` | Tabla: stats acumuladas por equipo |
| `equipo_partidos_stats` | Tabla: historial de partidos con stats |
| `partidos` | Tabla: partidos descargados |

### ✅ Estado Verificado:

| Componente | Estado |
|------------|--------|
| Goals extraction | ✅ `f.get('goals', {})` en elite.py línea 967 |
| Goals extraction | ✅ `f.get('goals', {})` en funciones_stats.py línea 111 |
| Ventana fechas | ✅ HOY-2 a HOY+6 |
| 55 ligas | ✅ Habilitadas |
| Filtro Argentina | ✅ ELIMINADO |
| Upsert sin DELETE | ✅ Implementado |
| Emojis Unicode | ✅ Restaurados (🐸🔑⚽📅🔄👑🎯📊) |

### 📅 Sesión 2026-08-04 - Corrección Emojis

**Problema:** Los emojis se habían corrompido (caracteres cirílicos como рҹ"җ, рҹ"„)

**Solución:** Script Python para reemplazar todos los caracteres corruptos con emojis Unicode correctos

**Emojis restaurados:**
- 🐸 Scorpion (página principal)
- 🔑 Acceder/Login
- 🔄 Sincronizar
- ⚽ Balón de fútbol
- 📅 Fecha
- 👑 VIP
- 🎯 Predicciones/Diana
- 📊 Dashboard/Stats
- 🔔 Alertas
- 📋 Listas

---

## 📅 Sesión 2026-08-07 - Rediseño Bankroll VIP

### 🎨 Nuevo Diseño Bankroll

**Características implementadas:**

| Característica | Descripción |
|----------------|-------------|
| **Bankroll Card** | Diseño tipo tarjeta grande verde con gradiente |
| **Individual** | Seleccionar picks y apostar cada uno separado |
| **Combinada** | Seleccionar 2+ picks, multiplica cuotas automáticamente |
| **Cuota editable** | Usuario puede modificar la cuota antes de apostar |
| **3 tabs** | Dashboard, Agregar, Historial |

**Flujo de uso:**

```
1. Dashboard → Ver bankroll actual con métricas
2. Agregar → Seleccionar picks con checkboxes → Editar cuota → Apostar
3. Historial → Ver apuestas guardadas, actualizar resultados
```

**Código clave:**

```python
# Selector de picks con cuota editable
for i, opt in enumerate(oppciones):
    sel = st.checkbox("", key=f"sel_pick_{i}")
    cantidad_input = st.number_input("Cuota", value=float(opt['cuota']), key=f"cuota_{i}")
    cantidades_dict[i] = cantidad_input

# Combinada: multiplicar cuotas
cuota_total = 1.0
for i in seleccionados:
    cuota_total *= cantidades_dict.get(i, opciones[i]['cuota'])
```

### 🔧 Errores Corregidos:

| Error | Solución |
|--------|----------|
| `safe_fmt` UnboundLocalError | Usar inline: `(opt.get('prob') or 0):.0f` |
| `NoneType.__format__` | Verificar valores antes de formatear |

### 📊 Sistema de "Sin Datos":

Cuando NO hay datos reales (equipos sin sincronizar), ahora muestra `?` en todos los campos.

| Campo | Sin datos |
|-------|-----------|
| PJ | `?` |
| VED | `?-?-?` |
| Goles | `?` |
| Promedios | `?` |
| Lambda | `?` |
| Forma | `?` |
| OU 2.5 | `?` |
| BTTS | `?` |
| Corners | `?` |
| Tiros | `?` |
| TArco | `?` |
| Tarjetas | `?` |
| Marcador | `?` |

### 🔧 Código Clave:

```python
def safe_fmt(val, fmt='.1f'):
    """Convierte valor a string, manteniendo '?' si no hay datos"""
    if val == '?' or val is None:
        return '?'
    try:
        return f'{float(val):{fmt}}'
    except:
        return str(val)

def safe_fmt_int(val):
    """Convierte valor a string entero"""
    if val == '?' or val is None:
        return '?'
    try:
        return f'{int(float(val))}'
    except:
        return str(val)
```

### 📝 Lógica de Lambda:

```python
# Calcular lambda_historico (basado en goles/pj)
lambda_historico_local = gf_l / pj_l if pj_l > 0 else 1.3

# Lambda FINAL = 60% dinamico + 40% historico
if lambda_dinamico_local_calc is not None:
    lambda_local_final = lambda_dinamico_local_calc * 0.6 + lambda_historico_local * 0.4
else:
    lambda_local_final = lambda_historico_local
```

### 📋 Linter para VS Code:

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.lintOnSave": true,
    "python.analysis.typeCheckingMode": "basic"
}
```



---

## Sesion 2026-08-07 - Debugging y Correccion de BTTS

### Problema Identificado
El usuario veia "BTTS: No 8%" con lambdas altos (1.51 y 1.43).

### Diagnostico
DEBUG revelo: orig=(1.44, 0.11) - lambda visitante era 0.11!

### Bugs Corregidos

1. **lambda_visitante incorrecto**: Ahora usa lambda_local de la BD
2. **Codigo duplicado**: Eliminadas 52 lineas fuera de if/elif/else
3. **DEBUG mal ubicado**: Corregida su posicion

### Formula BTTS (Correcta)
- Poisson: (1 - pp(lambda_l, 0)) * (1 - pp(lambda_v, 0)) * 100
- Coherencia: promedio con btts_prob
- Pick: "Si" si > 50%, "No" si no

### Correccion BD
UPDATE equipos_stats SET lambda_visitante = lambda_local WHERE lambda_visitante < 0.5;

### Commits
- b230e60: fix lambda_visitante -> lambda_local
- 16691fb: eliminar codigo duplicado

---

## Estado Actual 2026-08-07

### Funcionalidades
- Login, Landing, Sincronizacion, Stats, Modelos, Predicciones, Bankroll, VIP

### Archivos
- elite.py (~3400 lineas)
- analysis_models.py (~900 lineas)
- robot_extractor.py (~1500 lineas)

### Tablas Supabase
- partidos, equipos_stats, equipo_partidos_stats, picks, bankroll_apuestas
