# Scorpion Elite - Documentacion del Proyecto

> Ultima actualizacion: 2026-08-11

---

## Informacion General

| Item | Valor |
|------|-------|
| **Repositorio** | https://github.com/hoycae3/Scorpion-elite |
| **App Produccion** | https://scorpion-elite.onrender.com |
| **Base de datos** | Supabase (jjtifureeygvygxtpuku.supabase.co) |
| **Deploy** | Render (srv-d9e1thbbc2fs73f30jh0) - auto-deploy desde main |
| **Password app** | scorpion2026 |
| **Stack** | Python + Streamlit + Supabase + API-Football |

---

## Estructura del Proyecto

    Scorpion-elite/
    +-- elite.py                 # APP PRINCIPAL Streamlit (4335 lineas)
    +-- analysis_models.py       # Modelos matematicos (Poisson, Dixon-Coles, Monte Carlo, Elo) - 907 lineas
    +-- funciones_stats.py      # Funciones de stats de partidos - 333 lineas
    +-- calibration.py           # Sistema de calibracion automatica - 399 lineas
    +-- model_optimizer.py       # Optimizador de pesos de modelos - 492 lineas
    +-- data_loader.py           # Procesa Excel de Flashscore - 243 lineas
    +-- partidos_manager.py      # Gestion de partidos - 62 lineas
    +-- supabase_schema.sql      # Schema completo de la BD
    +-- requirements.txt          # Dependencias
    +-- styles.css               # Estilos CSS
    +-- Dockerfile               # Docker para produccion
    +-- render.yaml              # Configuracion de deploy
    +-- fix_mojibake.py          # Script: limpia mojibake cirilico
    +-- fix_bare_excepts.py      # Script: reemplaza bare excepts
    +-- backups/                 # CODIGO MUERTO (8985 lineas) - en .gitignore
    +-- scorpion/                # Modulo NO CONECTADO a elite.py (1958 lineas)
        +-- __init__.py
        +-- config.py
        +-- api/ (football.py, scraper.py)
        +-- db/ (database.py)
        +-- models/ (math.py)
        +-- ui/ (components.py)

### Archivos que NO existen (referenciados en docs antiguas)

| Archivo | Estado |
|---------|--------|
| `robot_extractor.py` | NO EXISTE (era el SuperRobot) |
| `stats_extractor.py` | NO EXISTE |
| `stats_robot.py` | NO EXISTE |
| `scrapers_fallback.py` | NO EXISTE |

### Modulo scorpion/

El modulo `scorpion/` (1,958 lineas) NO esta importado en ningun archivo del proyecto.
Es codigo en desarrollo que no se usa. Decision pendiente: terminar el modulo o eliminarlo.

---

## Menu de la Aplicacion

El menu real tiene 4 paginas (no 6 como decia la documentacion anterior):

    PAGINA PRINCIPAL:
    +-- Landing (sin login)
    |   +-- 4 partidos aleatorios + preview analisis
    |
    MENU (despues de login):
    +-- VIP (por defecto)
    |   +-- Tab: ROI por modelo
    |   +-- Tab: Bankroll (Dashboard/Agregar/Historial/Config)
    |   +-- Tab: Value Bets
    |   +-- Tab: Alertas
    |   +-- Tab: Ranking
    |   +-- Tab: Exportar
    +-- Partidos
    |   +-- Sincronizar (descarga partidos + stats)
    |   +-- Limpiar Equipos
    |   +-- Recalcular Lambdas
    |   +-- Ingresar Resultados
    +-- Analizador
    |   +-- Analisis con 4 modelos matematicos
    +-- Claves (solo admin)
        +-- Crear Contrasena
        +-- Ver Contrasenas

---

## Flujo de Sincronizacion

### Boton "Sincronizar"

| Configuracion | Valor |
|---------------|-------|
| **Ventana de fechas** | HOY-2 a HOY+6 |
| **Ligas** | 55 ligas mundiales (activas, linea 1081) |
| **Goals extraction** | `f.get('goals', {})` (corregido) |
| **Upsert** | Sin DELETE, solo inserta/actualiza |

### Nota sobre la variable LIGAS

Hay dos asignaciones de `LIGAS` en elite.py:
- Linea 951: `LIGAS = [solo Argentina]` - placeholder, se ejecuta al cargar la pagina pero
  es codigo muerto porque se sobrescribe.
- Linea 1081: `LIGAS = [55 ligas]` - DENTRO del boton Sincronizar, es la que realmente se usa.

Al sincronizar, la linea 1081 pisa la 951 y se procesan las 55 ligas.

### Optimizacion de Sincronizacion (2026-08-11)

El CASO B (equipos existentes) ahora filtra FT ya guardados antes de descargar:

    PASO 1: Descargar partidos (hoy-2 a hoy+6) -> upsert a tabla partidos
    PASO 2: Sincronizar stats de equipos
      +-- CASO A: Equipo NUEVO (0 records en DB)
      |   +-- Fetch /teams/statistics + 5 partidos iniciales (~6 API calls)
      +-- CASO B: Equipo EXISTENTE (tiene records)
          +-- Consultar fixture_ids ya guardados (1 query Supabase)
          +-- Filtrar FT de la ventana que YA estan guardados (0 API calls)
          +-- Solo buscar mas FT si faltan por guardar
          +-- Upsert solo los FT pendientes

El resumen final muestra: "API calls ahorradas" (cuantas calls se evitaron).

### Otros botones

| Boton | Funcion |
|-------|---------|
| **Limpiar Equipos** | Elimina equipos sin stats |
| **Recalcular Lambdas** | Recalcula lambda_local/visitante desde historial |
| **Ingresar Resultados** | Actualiza marcadores para calibrar predicciones |

---

## Base de Datos Supabase

### Tablas (15 referenciadas en codigo)

| Tabla | Descripcion |
|-------|-------------|
| `partidos` | Partidos descargados de API-Football |
| `equipos_stats` | Stats acumuladas por equipo (lambda_local/visitante) |
| `equipo_partidos_stats` | Historial de partidos con stats detalladas |
| `picks` | Picks guardados (1X2, O/U, BTTS, corners, tiros, tarjetas) |
| `bankroll_apuestas` | Apuestas del bankroll |
| `bankroll_history` | Historial de bankroll |
| `bankroll_retiros` | Retiros de bankroll |
| `user_stats` | Stats acumuladas por usuario |
| `alertas` | Centro de notificaciones |
| `value_bets` | Picks con value detectado |
| `ranking` | Ranking mensual |
| `cuotas` | Cuotas de apuestas |
| `usuarios` | Usuarios del sistema |
| `calibracion_equipos` | Factores de calibracion por equipo |
| `calibracion_historico` | Historico de calibracion |

### Logica de Lambda

    # Lambda FINAL = 60% dinamico + 40% historico
    if lambda_dinamico_calc is not None:
        lambda_final = lambda_dinamico_calc * 0.6 + lambda_historico * 0.4
    else:
        lambda_final = lambda_historico

Ponderacion exponencial (decay=0.92): partidos recientes pesan mas.

---

## Modelos Matematicos (analysis_models.py)

| Modelo | Descripcion |
|--------|-------------|
| **Poisson** | Distribucion de Poisson para goles esperados |
| **Dixon-Coles** | Mejora de Poisson con correccion de baja puntuacion |
| **Monte Carlo** | Simulacion de 10,000 partidos |
| **Elo** | Rating Elo de equipos |

### Predicciones adicionales (funciones en analysis_models.py)

| Funcion | Linea tipica | Descripcion |
|---------|-------------|-------------|
| `predecir_tiros()` | Over/Under 24 | Distribucion normal |
| `predecir_tarjetas()` | Over/Under 6 | Distribucion normal |
| `predecir_tiros_arco()` | Over/Under 8 | Distribucion normal |
| `normal_cdf()` | - | Aproximacion Abramowitz y Stegun |

---

## Seguridad

### Configuracion de credenciales (2026-08-11)

Las credenciales se leen de variables de entorno:

    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jjtifureeygvygxtpuku.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

### Accion pendiente del usuario

Las API keys y Supabase keys fueron commiteadas previamente. Se limpiaron del codigo
pero siguen en el historial de git. El usuario debe rotar:
1. API-Football key en https://dashboard.api-football.com
2. Supabase anon key en https://supabase.com/dashboard

---

## Funcionalidades Implementadas

| Seccion | Estado |
|---------|--------|
| Login con contrasena | OK |
| Landing page (4 partidos aleatorios) | OK |
| Pagina Partidos (todos los partidos) | OK |
| Sincronizacion de partidos | OK (optimizada 2026-08-11) |
| Auto-actualizacion de picks | OK |
| Barra de progreso en sincronizacion | OK |
| Analisis con 4 modelos | OK |
| Predicciones adicionales (O/U, BTTS, corners, tiros, tarjetas) | OK |
| Bankroll (Dashboard/Agregar/Historial/Config) | OK |
| Guardar picks en Supabase | OK |
| Recalcular Lambdas | OK |
| Limpiar Bankroll | OK |
| Sistema de calibracion | OK |

---

## Problemas Conocidos / Pendientes

### Alta prioridad

| Problema | Detalle |
|----------|---------|
| **LIGAS tiene asignacion duplicada** | Linea 951 placeholder muerto + linea 1081 activa (55 ligas). Limpiar la 951 |
| **API keys en historial git** | Limpiadas del codigo actual, pero siguen en git history. Rotar keys |
| **scorpion/ no conectado** | 1,958 lineas de codigo muerto. Decidir: terminar o eliminar |

### Media prioridad

| Problema | Detalle |
|----------|---------|
| **backups/ (8985 lineas)** | Codigo muerto en .gitignore pero sigue tracked en git |
| **Consenso de modelos simulado** | Muestra 1 valor repetido 4 veces en VIP |

### Resueltos (sesion 2026-08-11)

| Problema | Solucion |
|----------|----------|
| Secretos hardcodeados | Reemplazados por os.getenv() en 8 archivos |
| Mojibake cirilico (4124 chars) | Limpiado a 0 caracteres. Script: fix_mojibake.py |
| Bare excepts (21) | Reemplazados por except Exception. Script: fix_bare_excepts.py |
| Sincronizacion ineficiente | Optimizada: filtra FT ya guardados, ahorra API calls |

---

## Comandos Utiles

    # Deploy en Render (auto-deploy desde main, pero se puede forzar)
    curl -X POST "https://api.render.com/v1/services/srv-d9e1thbbc2fs73f30jh0/deploys" \
      -H "Authorization: Bearer $RENDER_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{"clearCache": "dont_clear"}'

    # Verificar app
    curl -s -o /dev/null -w "%{http_code}" https://scorpion-elite.onrender.com/

    # Verificar sintaxis de un archivo
    python3 -c "import ast; ast.parse(open('elite.py').read()); print('OK')"

    # Limpiar mojibake (si reaparece)
    python3 fix_mojibake.py elite.py

    # Reemplazar bare excepts (si se agregan nuevos)
    python3 fix_bare_excepts.py

---

## Historial de Cambios

### 2026-08-11 - Limpieza y optimizacion

| Cambio | Commit |
|--------|--------|
| Limpieza de secretos hardcodeados (8 archivos) | d23728f |
| Optimizacion de sincronizacion (filtro FT) | ca62363 |
| Limpieza de mojibake cirilico (4124 a 0 chars) | dc4f301 |
| Reemplazo de bare excepts (21 a 0) | este commit |
| Actualizacion de AGENTS.md | este commit |

### Sesiones anteriores (resumen)

- **2026-08-07**: Rediseno Bankroll VIP, correccion BTTS, recalcular lambdas
- **2026-08-04**: Sincronizacion incremental, goals extraction, modelos matematicos reales
- **2026-08-03**: Lambda dinamico con ponderacion exponencial
- **2026-08-01**: Correcciones al sincronizar (temporada dinamica, 55 ligas)
- **2026-07-25**: Landing page publica, analisis preview gratis
- **2026-07-22**: Integracion UI con SuperRobot, dashboard
- **2026-07-20**: SuperRobot creado (4 fuentes de datos)

Nota: El "SuperRobot" (robot_extractor.py) fue eliminado del proyecto.
La obtencion de datos ahora se hace exclusivamente via API-Football en elite.py
y funciones_stats.py.
