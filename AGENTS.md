# Scorpion Elite - Documentacion del Proyecto

> Ultima actualizacion: 2026-08-19/20 (5 fixes: sync acumulacion, boton landing, guardar pick, liquidacion, documentacion)

---

## Informacion General

| Item | Valor |
|------|-------|
| **Repositorio** | https://github.com/hoycae3/Scorpion-elite |
| **App Produccion** | https://scorpion-elite.onrender.com |
| **Base de datos** | Supabase (jjtifureeygvygxtpuku.supabase.co) |
| **Deploy** | Render (srv-d9e1thbbc2fs73f30jh0) - auto-deploy desde main |
| **Login** | bcrypt (tabla `usuarios` en Supabase) |
| **Stack** | Python 3.11 + Streamlit + Supabase + API-Football |

---

## Estructura del Proyecto

```
Scorpion-elite/
├── elite.py                 # ⭐ App principal Streamlit (~4400 lineas)
├── app_helpers.py           # Helpers puros y constantes (extraído de elite.py)
├── analysis_models.py       # 5 modelos matematicos (ensemble)
├── funciones_stats.py       # Stats y promedios dinamicos
├── calibration.py           # Calibracion automatica de lambdas
├── supabase_schema.sql      # Schema DB (15 tablas activas)
├── add_foreign_keys.sql     # Migracion FK (integridad referencial)
├── recalcular_lambdas.sql   # Script recalculo lambdas
├── requirements.txt         # Dependencias (versiones fijadas)
├── Dockerfile               # Docker para produccion
├── render.yaml              # Config de deploy
├── .streamlit/config.toml   # Tema oscuro + config
├── .env.example             # Template de variables de entorno
├── .gitignore                # Reglas de git
└── backups/                 # Backups (gitignored)
```

### Archivos en .gitignore (codigo muerto, NO tracked)
- `scorpion/` - modulo modular en desarrollo, no integrado
- `model_optimizer.py` - optimizador, no importado
- `data_loader.py` - loader de Excel, no usado
- `partidos_manager.py` - manager, no usado
- `test_ligas.py`, `test_sync.py` - scripts de prueba manuales

---

## Modelos Matematicos (analysis_models.py)

### Ensemble de 5 modelos:

| Modelo | Peso | Funcion |
|--------|------|---------|
| Poisson | 30% | `poisson_1x2()`, `poisson_over_under()` |
| Dixon-Coles | 25% | `dc_1x2()` |
| Monte Carlo | 20% | `monte_carlo()` (3000 simulaciones) |
| Forma Reciente | 15% | `analizar_forma_reciente()` |
| Estilo de Juego | 10% | `analizar_estilo_juego()` |

### Funcion principal: `calcular(lambda_local, lambda_visitante, ...)`
- Retorna: 1X2, Over/Under, BTTS, Corners, Tiros, Tarjetas, Tiros Arco
- Incluye `modelos` dict con scores individuales de cada modelo
- `verificar_coherencia()` ajusta BTTS y tarjetas para coherencia

### Predicciones adicionales (distribucion normal):
- `predecir_tiros()` - Over/Under 24
- `predecir_tarjetas()` - Over/Under 6
- `predecir_tiros_arco()` - Over/Under 8
- `normal_cdf()` - aproximacion Abramowitz-Stegun

---

## Sistema de Lambdas

### Calculo:
```
λ Final = (λ Dinamico × 0.6) + (λ Historico × 0.4)
```

### λ Local vs Visitante:
- `equipos_stats` tiene `lambda_local` y `lambda_visitante` separados
- El analizador usa el lambda correcto segun el rol del equipo
- **BUG CORREGIDO (2026-08-11)**: visitante ahora usa `lambda_visitante` (antes usaba `lambda_local`)

### Ponderacion exponencial (decay=0.92):
- Partido mas reciente: peso = 1.0
- Partido 5to: peso = 0.92^5 = 0.66
- Partido 10mo: peso = 0.92^10 = 0.43

### Funcion: `recalcular_lambdas_desde_historial()`
- Lee de `equipo_partidos_stats`
- Separa por `es_local=true/false`
- Calcula λ_local y λ_visitante correctos
- Boton: "🔄 Recalcular Lambdas" en pagina Carga

---

## Base de Datos (Supabase)

### 15 tablas activas:

| Tabla | Descripcion |
|-------|-------------|
| `partidos` | Partidos descargados con fixtures |
| `equipos_stats` | Stats acumuladas + lambdas |
| `equipo_partidos_stats` | Historial de partidos con stats |
| `picks` | Picks guardados |
| `bankroll_apuestas` | Apuestas del bankroll VIP |
| `bankroll_history` | Historial de bankroll |
| `bankroll_retiros` | Retiros de bankroll |
| `usuarios` | Usuarios + password_hash (bcrypt) |
| `calibracion_equipos` | Factores de correccion |
| `calibracion_historico` | Registro de resultados |
| `user_stats` | Stats acumuladas por usuario |
| `alertas` | Centro de notificaciones |
| `value_bets` | Picks con value detectado |
| `ranking` | Ranking mensual |
| `cuotas` | Cuotas de mercado |

### Tablas DEPRECATED (en schema pero no usadas):
- `partidos_stats`, `historial_predicciones`, `pesos_modelos`, `cuotas_cache`, `dias_procesados`, `match_stats`, `team_form` (tablas comentadas con `--` en supabase_schema.sql, código muerto legítimo, no se crean en DB)

### Tablas marcadas como deprecated en AGENTS.md pero REALMENTE EN USO:
- `bankroll_history`, `bankroll_retiros`, `user_stats`, `alertas`, `value_bets`, `ranking`, `cuotas` (todas con insert/select/update activo en elite.py - NO eliminar)

---

## Paginas de la App

```
PAGINA PRINCIPAL:
├── 🌐 Landing (sin login)
│   └── 4 partidos aleatorios + preview analisis
│
MENU (despues de login):
├── 👑 VIP (por defecto)
│   ├── 📥 ROI por Modelo
│   ├── 📊 Resultados
│   ├── 🏆 Bankroll (Dashboard/Agregar/Historial)
│   ├── 🎯 Value Bets
│   ├── 🔔 Alertas
│   ├── 🏆 Ranking
│   └── 🔄 Exportar
├── 📊 Partidos
│   ├── 🔄 Sincronizar
│   ├── 📊 Stats Ayer
│   ├── 🧹 Limpiar Equipos
│   └── 🔄 Recalcular Lambdas
├── 📥 Analizador
│   └── Consenso de modelos en VIP
└── 👑 Claves (solo admin)
```

---

## Sincronizacion

### Boton "🔄 Sincronizar":
- Ventana: ayer → ultima_futura + 1 dia (incremental)
- 55 ligas mundiales
- Sincronizacion INCREMENTAL (no re-descarga lo existente)
- Agrega equipos SOLO de partidos nuevos o FT (no de existentes)
- Upsert SIEMPRE: actualiza fecha/estado/score de partidos reprogramados

### Metricas de diagnostico en resumen de sync:
- `📅 Partidos guardados`: partidos nuevos insertados
- `🔄 Partidos actualizados`: existentes con fecha/estado cambiado (reprogramados)
- `🔍 Partidos descargados de API`: total de fixtures que devolvio la API
- `♻️ Partidos ya en DB (duplicados)`: fixtures que ya estaban en DB
- `📆 Fechas que devolvió la API`: fechas exactas de la respuesta
- `🚫 Errores de API`: ligas donde la API devolvio error (429/403/500)

### Boton "📊 Stats Ayer":
- Actualiza SOLO partidos de ayer (hoy-1)
- Obtiene estado FT y scores finales
- Guarda stats en `equipo_partidos_stats`

### Boton "🔄 Recalcular Lambdas":
- Recalcula λ_local/λ_visitante desde historial
- Corrige lambdas corruptos

---

## Seguridad

| Aspecto | Estado |
|---------|--------|
| Passwords | ✅ bcrypt (no texto plano) |
| SQL Injection | ✅ No vulnerable (Supabase ORM) |
| Variables entorno | ✅ os.getenv() para secrets |
| .env en gitignore | ✅ |
| RLS policies | ✅ 22 policies activas |
| Input validation | ⚠️ Basica (5 text_inputs) |

---

## Estado del Codigo (Auditoria 2026-08-11, actualizado 2026-08-12)

### Metricas:
- **elite.py**: ~4400 lineas (reducido de 4508 tras refactor helpers)
- **app_helpers.py**: 167 lineas (helpers puros extraidos de elite.py)
- **Complejidad ciclomatica**: alta, concentrada en render_*
- **Funciones mas largas**: render_analizador_page (939), sincronizar_partidos (642)
- **Imports sin usar**: 0 (limpiados)
- **Bare excepts**: 0
- **Silent excepts (except Exception:)**: 0 (corregidos, ahora loguean)
- **Funciones anidadas**: 0
- **Mojibake**: 0
- **logger.error/warning/debug**: 42 calls (aumentado tras fix de silent excepts)

### Limpieza completada (2026-08-11):
- ✅ Eliminados imports sin usar (date, Path, List, Optional)
- ✅ Eliminada duplicacion de `pp()` (importada de analysis_models)
- ✅ Extraida `_construir_pick_data()` de render_analizador_page
- ✅ Corregido bug lambda_visitante
- ✅ Consenso de modelos YA funcionaba (AGENTS.md desactualizado)

### Mejoras completadas (2026-08-12):
- ✅ CI con validacion de sintaxis antes del deploy (.github/workflows/deploy.yml)
- ✅ 9 except Exception silenciados ahora capturan y loguean errores
- ✅ Migracion de foreign keys (add_foreign_keys.sql, 1 FK viable + docs)
- ✅ Corregido AGENTS.md: 7 tablas activas NO son deprecated
- ✅ Refactor: helpers puros extraidos a app_helpers.py (COLORS, LIGAS_MAP, hash_password, verify_password, get_hoy, get_pais_emoji, crear_badges, fila_dato, safe_fmt, safe_fmt_int, calcular_value, format_money, utc_to_colombia)
- ✅ Upgrade dependencias: streamlit 1.45->1.61.1, pandas 2.2.2->3.0.5, supabase 2.5->2.31, bcrypt 4.2->5.0
- ✅ render.yaml: puerto 8501 explicito

### Pendiente:
- ❌ Tests automatizados (no existen)
- ⚠️ elite.py sigue siendo un monolito (~4400 lineas, funciones render_* largas)
- ⚠️ FKs pendientes requieren migracion de datos (ver add_foreign_keys.sql)

---

## Como Continuar en Nuevo Chat

1. **LEER ESTE ARCHIVO PRIMERO** (AGENTS.md)
2. Verificar app en produccion:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://scorpion-elite.onrender.com/
   ```
3. Probar modelos:
   ```bash
   cd /workspace/project/Scorpion-elite
   python3 -c "from analysis_models import calcular; r=calcular(1.5,1.2); print(r['p1'], r['pick_1x2'])"
   ```
4. **REGLAS IMPORTANTES:**
   - NO eliminar archivos sin confirmar con el usuario
   - NO hacer deploy automatico sin confirmar con el usuario
   - Guardar cambios en git ANTES de hacer cambios grandes
   - Los backups estan en `backups/` - NO perderlos

---

## Comandos Utiles

```bash
# Probar modelos
python3 -c "from analysis_models import calcular; r=calcular(1.5,1.2); print(r)"

# Probar pp() (Poisson)
python3 -c "from analysis_models import pp; print(pp(1.5,0))"

# Verificar sintaxis
python3 -c "import ast; ast.parse(open('elite.py').read()); print('OK')"

# Deploy en Render
curl -X POST "https://api.render.com/v1/services/srv-d9e1thbbc2fs73f30jh0/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"clearCache": "dont_clear"}'

# Verificar app
curl -s -o /dev/null -w "%{http_code}" https://scorpion-elite.onrender.com/
```

---

## Sesion 2026-08-12 - Fix Sincronizacion No Guardaba Partidos

### Problema
Usuario reporta: "Partidos guardados: 0" al sincronizar. La API devuelve
partidos pero ninguno se guarda en Supabase.

### Causas Encontradas y Corregidas

#### Causa 1: Equipos fantasmas (142 equipos nuevos innecesarios)
El codigo agregaba TODOS los equipos de TODOS los fixtures a
`equipos_unicos`, sin importar si el partido era nuevo o existente.
Esto causaba:
- Descarga de stats de 142 equipos innecesariamente
- Timeout/crash en Render antes de terminar de guardar partidos
- Metricas infladas: 752 equipos detectados, 142 nuevos

**Fix**: Solo agregar equipos a `equipos_unicos` si:
- El partido es nuevo (necesita stats para el analizador), O
- El partido termino FT (necesita procesar resultado para CASO B)
Linea ~1154: `if es_partido_nuevo or estado == 'FT':`

#### Causa 2: Bug del `if es_partido_nuevo` (partidos reprogramados)
El codigo original solo hacia upsert dentro de `if fix_id not in
partidos_existentes:`. Si un partido ya existia (con fecha vieja), no
se actualizaba la fecha nueva.

**Problema real**: La API reprograma partidos (cambia fecha pero
mantiene fixture_id). Ej: un partido del 10 de agosto se mueve al 17.
El codigo lo veia como "ya existe" y no actualizaba la fecha. Resultado:
partidos del 17 nunca aparecian en DB aunque la API los devolvia.

**Fix**: Hacer upsert SIEMPRE para actualizar fecha/estado/score de
partidos reprogramados. Solo contar como "guardado" si es nuevo.
Linea ~1239: `client.table("partidos").upsert(...)` (fuera del if)

#### Causa 3: Deploy de Render no completado
El fix se subio a GitHub pero Render tarda varios minutos en construir
y desplegar. Usuario sincronizo con codigo viejo (sin fix) la primera
vez. Solucion: esperar a que Render termine + hard refresh.

### Resultado Final
Despues de los 3 fixes + esperar deploy completo:
```
Antes: 854 partidos (1 al 16 de agosto), 0 guardados, 142 equipos nuevos
Ahora: 868 partidos (1 al 18 de agosto), 14 guardados, 5 equipos nuevos
```

### Diagnosticos Anadidos (metricas en resumen de sync)
- `🔍 Partidos descargados de API` (fixtures_totales)
- `♻️ Partidos ya en DB (duplicados)` (fixtures_duplicados)
- `📆 Fechas que devolvió la API` (fechas_api set)
- `🔄 Partidos actualizados (fecha/estado)` (partidos_actualizados)
- `🚫 Errores de API` (errores_api, primer_error_api)

### Variables anadidas
- `partidos_existentes_fechas`: dict {fixture_id: {fecha, estado}} para
  detectar partidos reprogramados (cambio de fecha o estado)
- `fechas_api`: set de fechas que devuelve la API (diagnostico)
- `fixtures_totales`, `fixtures_duplicados`: contadores de diagnostico
- `partidos_actualizados`: contador de partidos existentes actualizados

### Otros cambios
- Corregida traduccion "Fixtures" → "Partidos" en metricas
  (antes mostraba "Accesorios descargados de API")
- CASO B: cambiada deteccion de equipos existentes de
  `equipo_partidos_stats` a `equipos_stats` (tabla correcta)
- CASO B: `continue` si no hay FT pendientes (evita 575 API calls)
- Anadido manejo de errores de API (429/403/401/500) con mensaje claro

### Commits de esta sesion
- `3839574`: fix: no descargar stats de equipos de partidos ya existentes
- `b8b2c8a`: diag: mostrar fechas exactas que devuelve la API en resumen
- `867a4d8`: fix: actualizar partidos reprogramados (mismo fixture_id, fecha distinta)
- `d04457e`: diag: añadir contador de partidos actualizados (reprogramados)

### Logica de ventana de sync (ACTUALIZADA 2026-08-28: ventana fija)
```
fecha_inicio = ayer (siempre, para liquidar picks/bankroll del dia anterior)
fecha_fin = hoy + 6 dias (proximos 7 dias)
```
- La sync SIEMPRE descarga el mismo rango fijo (ayer → hoy+6).Ya NO
  avanza "un dia por cada sync" ni acumula partidos indefinidamente.

- **Limpieza automatica**: al terminar la sync, borra partidos con fecha
  anterior a ayer (que ya fueron liquidados). La DB se mantiene en ~8 dias maximo.



### DB confirmada
- Tabla `partidos`: fixture_id UNIQUE NOT NULL (no permite duplicados)
- 868 partidos del 1 al 18 de agosto (55 ligas, ~53 partidos/dia)
- Viernes/sabado = mas partidos (137 y 117), entre semana = menos (49)
- Esto es NORMAL, no hay problema

---

## Sesion 2026-08-11 - Fix Error removeChild

### Problema
Error en produccion: `NotFoundError: Failed to execute 'removeChild' on 'Node'`

### Causa
Bug de React DOM en Streamlit 1.36.0 - la reconciliacion del DOM fallaba
cuando habia `st.rerun()` + `unsafe_allow_html=True`.

### Solucion
1. Actualizar Streamlit 1.36.0 -> 1.45.0 (requirements.txt)
2. Cache-buster del CSS actualizado (v20260805 -> v20260811)
3. Verificado: HTML balanceado, sin keys duplicadas

### Commit
- `040e065`: fix: actualizar Streamlit 1.36->1.45 para corregir error removeChild

### Nota para usuario
Si el error persiste despues del deploy, hacer hard refresh:
- **Ctrl+Shift+R** (Windows/Linux) o **Cmd+Shift+R** (Mac)
- O limpiar cache del navegador

---

## Sesion 2026-08-12 - Fixes Sincronizacion (3 commits)

### Problema 1: Sync mostraba "0 partidos guardados" sin explicacion
- **Causa**: No habia `else` despues de `if resp.status_code == 200`. Errores de API (429/403/500) se ignoraban en silencio.
- **Fix**: Anadido `errores_api` counter + `primer_error_api` + mensaje claro en resumen final.
- **Commit**: `4d89fbc`

### Problema 2: Sync marcaba 563 equipos como "nuevos" cada vez
- **Causa**: Deteccion de equipos existentes consultaba `equipo_partidos_stats` (tabla de historial) en vez de `equipos_stats` (tabla principal). Si un equipo tenia stats pero no historial, se consideraba "nuevo".
- **Fix**: Cambiar consulta a `equipos_stats` (tabla correcta).
- **Commit**: `1ee743d` ( luego corregido en `551f34e`)

### Problema 3: App "se salia" (crasheaba) al sincronizar
- **Causa**: El CASO B (equipos existentes) hacia una llamada API por cada equipo (575 equipos x 10s timeout = ~96 min). Render mataba el proceso por timeout de request.
- **Fix**: El CASO B ahora SALTAR equipos sin FT pendientes en la ventana (`continue` → 0 API calls). Solo procesa equipos con FT reales en la ventana actual.
- **Commit**: `551f34e`

### Lecciones aprendidas
1. La deteccion de "equipo nuevo" debe usar la tabla PRINCIPAL (`equipos_stats`), no la de historial (`equipo_partidos_stats`)
2. El CASO B (equipos existentes) NO debe hacer llamadas API para buscar FT si no hay FT en la ventana actual
3. Con 575 equipos, una llamada API por equipo = timeout garantizado en Render free tier
4. El codigo que agrega equipos a `equipos_unicos` debe incluir TODOS los equipos (no solo de partidos nuevos) para que el CASO B funcione


---

## Sesion 2026-08-18 - Cargar Cuotas + Fixes Analizador

### Feature: Cargar Cuotas de API-Football (commit a2ed45e)
Antes la tabla `cuotas` estaba vacia porque NADA la poblaba. Solo habia
select/delete, ningun insert/upsert. La seccion "Cuotas del Mercado +
Value Bets" del analizador nunca aparecia.

**Nueva funcion** `cargar_cuotas_fixture()` en funciones_stats.py:
- Llama GET /odds de API-Football v3 con fixture_id
- Parsea response[] -> bookmaker{bets[]} -> values[]
- Mapea nombres de mercado de la API a tipo_apuesta de la BD
- Upsert en tabla cuotas con on_conflict
- Retorna: n cuotas guardadas (-1 error API, 0 sin datos)

**Boton "Cargar Cuotas"** en pagina Partidos:
- Carga cuotas de partidos proximos (hoy -> +7 dias, estado != FT)
- Incremental: no recarga partidos que ya tienen cuotas
- Barra de progreso + metricas

### Fix 1: fixture_id no llegaba a render_cuotas_mercado (commit 3df3019)
Fix: copiar selected_fixture_id a result[fixture_id] en ambas rutas.

### Fix 2: Forma reciente duplicada (commit a2ed45e)
Quitada seccion insignias grandes del analizador (ya en tabla arriba).

### Commits
- 3df3019: fix cuotas no aparecian en analizador
- a2ed45e: feat cargar cuotas + quitar forma reciente duplicada

---

## Sesion 2026-08-18 - Cuotas + Zona Horaria + DB Sync

### Resumen
Se arreglaron 9 bugs encadenados para que las cuotas del mercado y value bets aparecieran en el analizador. Tambien se sincronizo la DB con el codigo y se arreglo un bug de zona horaria.

### Bug 1: fixture_id no llegaba al analizador (3df3019)
render_cuotas_mercado(r) busca r.get(fixture_id) pero nunca se copiaba al result. Fix: copiar selected_fixture_id a result[fixture_id] en ambas rutas.

### Bug 2: Forma reciente duplicada (a2ed45e)
Quitada seccion insignias grandes del analizador (ya esta en tabla comparativa arriba).

### Bug 3: Zona horaria - fecha incorrecta (27ccba8)
API devuelve date en UTC. El codigo guardaba fecha UTC sin convertir. Un partido 19:00 Mexico (00:00 UTC dia siguiente) se guardaba con fecha del dia siguiente. Fix: convertir fecha-hora a Colombia (UTC-5) antes de guardar. Display actualizado para no re-convertir.

### Bug 4: DB desincronizada (0fb20a5)
- calibracion_equipos/historico: codigo las usa pero NO existian. Creadas via migracion_db_2026_08_18.sql.
- dias_procesados, historial_predicciones, pesos_modelos: existian pero codigo no las usa. Borradas.
- Bug schema: calibracion_equipos tenia dos PRIMARY KEY. Corregido.
Despues: 15 tablas, todas en uso activo.

### Bug 5: Parsing bookmakers plural (f965cbf)
Codigo buscaba response[].bookmaker (singular). API devuelve response[].bookmakers (plural, array). Estructura real: response[].bookmakers[].bets[].values[] con {value, odd}

### Bug 6: Columna actualizado_en no existe (4ccc2f3)
Tabla cuotas real no tiene actualizado_en. Error PGRST204. Fix: quitar del insert.

### Bug 7: Columnas equipo_local/visitante no existen (abf9c08)
Tabla cuotas real tiene 8 columnas: id, fixture_id, fecha, liga, tipo_apuesta, opcion, cuota, bookmaker. NO tiene equipo_local, equipo_visitante, creado_en, actualizado_en. Schema desactualizado. Fix: quitar del insert + actualizar schema.

### Bug 8: RLS sin politica en cuotas (fix en DB)
Tabla cuotas tenia RLS sin policy. Error 42501. Fix: crear policy cuotas_all en Supabase.

### Bug 9: Duplicados en upsert (77c0430)
API devuelve mismo bookmaker/market varias veces. Error 21000 ON CONFLICT. Fix: deduplicar por (fixture_id, bookmaker, tipo_apuesta, opcion).

### Tabla cuotas REAL (8 columnas)
id, fixture_id, fecha, liga, tipo_apuesta, opcion, cuota, bookmaker

### Botones pagina Partidos (5 botones)
1. Limpiar: borra TODOS los partidos y cuotas. Peligroso.
2. Sincronizar: descarga partidos de 55 ligas (incremental).
3. Limpiar Equipos: borra equipos_stats y equipo_partidos_stats.
4. Recalcular Lambdas: recalcula lambda_local/visitante desde historial.
5. Cargar Cuotas: descarga odds de partidos proximos (7 dias, no FT).

### Commits
3df3019, a2ed45e, 27ccba8, 0fb20a5, f965cbf, 4ccc2f3, abf9c08, 77c0430

## Sesión 2026-08-19/20 - Cinco Fixes + Revision Completa

### 1. Fix acumulación FT en sync (commit 78692de)

**Problema:** los equipos no acumulaban historial (se quedaban en 5 partidos).
Se perdia cualquier FT fuera de la ventana [ayer → ultima_futura+1].

**Fix:** el CASO B (equipos existentes) ya no guarda solo el FT de la ventana.
Para equipos CON FT pendiente trae sus últimos 10 FT y guarda TODOS los
faltantes (recupera gaps hasta 10 partidos). Compromísense entre el viejo
timeout (llamada por equipo) y el fix del 12-ago (solo ventana).

**Optimización `excluir_fixture_ids`** en
`obtener_ultimos_partidos_equipo` (funciones_stats.py): los partidos ya
guardados en DB no se reprocesan → 0 llamadas de stats para ellos y no se
sobreescriben con ceros. CASO A intacto (equipos nuevos siguen bajando 5).

**Recuperación progresiva elegida (Opción A):** equipos estancados se
recuperan cuando jueguen su próximo FT. El backfill total de todos los
equipos quedó descartado (miles de llamadas API + riesgo timeout).

### 2. Fix botón de landing (commit f772cb5)

**Problema:** clic en partido de landing no hacía nada (solo re-sorteaba
los 4 aleatorios). El handler escribía 3 claves muertas
(`partido_seleccionado`, `show_analizador`, `query_params['page']`) que
ningún router leía; y el flujo de preview gratis (`preview_partido`)
nunca se activaba. Reproducido en producción con navegador.

**Fix:** el botón ahora setea `st.session_state.preview_partido` + rerun →
activa el preview gratis ya construido (lambdas, Over/Under, BTTS + CTA
de registro).

**Comportamiento esperado de landing:** muestra 4 partidos ALEATORIOS
(random.sample) sin filtro de fecha — explica reportes de "ayer aparecía,
hoy no".

### 3. Guardar Pick(s) solo con mercados marcados (commit 1f917cd)

**Problema:** "Guardar Pick(s)" insertaba siempre las 7 predicciones en
`picks` (verificado por el usuario). La selección solo filtraba Capital.

**Fix:** `_construir_pick_data(..., mercados_seleccionados)` con mapa
`_MERCADO_CAMPOS`. Los campos de mercado no marcados se omiten (NULL en
DB). Las vistas VIP ya saltaban campos NULL → solo aparece lo marcado.
"Guardar Todo" mantiene las 7. Schema verificado: solo `fecha` es NOT NULL.

### 4. Bug CRÍTICO liquidación bankroll (commit 95bda0a)

**Problema (caro):** `apuesta_ganada()` evaluaba secuencialmente y si el
pick tenía cualquier Over/Under, TODOS los mercados (incluso Corners,
Tarjetas, Remates, Tiros Arco) se liquidaban por GOLES en vez de su stat
real. Afectaba ROI de Capital directamente.

**Fix:** evaluación explícita por mercado: 1X2=marcador, O/U=goles,
BTTS=ambos marcan, y los 4 especiales solo con `stats_reales` propio.
No evaluable → False (perdida) sin fallback cruzado.

**Tests:** 5 nuevos tests de regresión (corners no goles, remates
regresión, tarjetas/arco por stat, O/U sin predicción) → 51/51 total.

### 5. Diagnóstico error removeChild (sin fix de código)

El error `NotFoundError removeChild` reapareció tras el deploy. Causas:
caché viejo del navegador post-deploy (JS viejo + DOM nuevo) — hard
refresh (Ctrl+Shift+R). Patrón típico en Streamlit con st.rerun() +
unsafe_allow_html. No hubo HTML desbalanceado (escaneo automatizado).
Si persiste tras refresh, sospechoso: re-render de landing cada 30s.

### Flujos documentados (preguntas del usuario)

- **Clic "📊 Partidos":** 4 queries de estado + 5 botones + filtro
  calendario + práctica N+1 (2 queries por partido para el badge,
  pendiente de optimizar).
- **Seleccionar partido (Partidos):** guarda state + rerun → Analizador
  automático (tabla comparativa, picks clicables, marcador, cuotas,
  consenso, botones guardar).
- **Después de guardar pick:** DB `picks` + session
  `apuestas_pendientes_analizador` → Capital → ➕ Agregar (preselección
  es comodidad; manual siempre funciona) → APOSTAR → `bankroll_apuestas`
  → liquidación en próxima sync FT → Resultados/ROI/Historial.

### Pendientes conocidos (aprobado: no tocar sin confirmación)

- Optimización N+1 de badges en Partidos (2 queries por partido)
- 7 imports sin usar en elite.py (limpieza cosmética)
- ~22 silent excepts que convendría loguear

### Tests
- 51/51 antes del cierre de sesión (eran 47 + 5 regresión este fix)
