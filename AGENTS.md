# Scorpion Elite - Documentacion del Proyecto

> Ultima actualizacion: 2026-08-11 (post-auditoria completa)

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
├── elite.py                 # ⭐ App principal Streamlit (~4350 lineas)
├── analysis_models.py       # 5 modelos matematicos (ensemble)
├── funciones_stats.py       # Stats y promedios dinamicos
├── calibration.py           # Calibracion automatica de lambdas
├── supabase_schema.sql      # Schema DB (15 tablas activas)
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
- `bankroll_history`, `bankroll_retiros`, `user_stats`, `alertas`, `value_bets`, `ranking`, `cuotas` (marcadas como deprecated en supabase_schema.sql)

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
- Ventana: HOY-3 a HOY+10 (13 dias)
- 55 ligas mundiales
- Sincronizacion INCREMENTAL (no re-descarga lo existente)
- Agrega TODOS los equipos de TODOS los fixtures

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

## Estado del Codigo (Auditoria 2026-08-11)

### Metricas:
- **elite.py**: ~4350 lineas, 40+ funciones
- **Complejidad ciclomatica**: 708 (alta, concentrada en render_*)
- **Funciones mas largas**: render_analizador_page (937), render_vip_page (874)
- **Imports sin usar**: 0 (limpiados)
- **Bare excepts**: 0
- **Funciones anidadas**: 0
- **Mojibake**: 0
- **logger.error/warning**: 33 calls

### Limpieza completada (2026-08-11):
- ✅ Eliminados imports sin usar (date, Path, List, Optional)
- ✅ Eliminada duplicacion de `pp()` (importada de analysis_models)
- ✅ Extraida `_construir_pick_data()` de render_analizador_page
- ✅ Corregido bug lambda_visitante
- ✅ Consenso de modelos YA funcionaba (AGENTS.md desactualizado)

### Pendiente:
- ❌ Tests automatizados (no existen)
- ⚠️ elite.py sigue siendo un monolito (4350 lineas)
- ⚠️ Funciones render_* largas (>900 lineas cada una)

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

