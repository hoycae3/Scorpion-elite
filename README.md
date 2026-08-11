# 🦂 Scorpion Elite

**Sistema de análisis estadístico para fútbol con modelos matemáticos avanzados**

---

## 📊 Sistema de Lambdas (Predicción de Goles)

El corazón del sistema es el cálculo del **lambda (λ)** - la tasa promedio de goles esperados por partido.

### Fuentes de Lambda

| Fuente | Descripción | Peso en Final |
|--------|-------------|---------------|
| **λ Dinámico** | Calculado con los últimos partidos guardados (ponderación exponencial) | 60% |
| **λ Histórico** | Promedio general de la temporada (de equipos_stats) | 40% |

### Ponderación Exponencial

Los partidos recientes pesan más que los antiguos:

```
Partidos más recientes: peso = 1.0, 0.92, 0.85, 0.78, 0.72...
 decay = 0.92 (aproximadamente 50% de peso al último tercio)
```

### Lambda Final

```
λ Final = (λ Dinámico × 0.6) + (λ Histórico × 0.4)
```

**¿Cuándo es útil?**
- Si un equipo está en racha (marca mucho), el λ dinámico sube más rápido
- Si un equipo está en mala racha, el λ dinámico baja más rápido
- El λ histórico mantiene estabilidad y no se afecta por rachas temporales

### λ Local vs Visitante

Cada equipo tiene dos lambdas separados:
- **λ Local**: goles marcados cuando juega como local
- **λ Visitante**: goles marcados cuando juega como visitante

El análisis usa el λ correspondiente al rol del equipo en el partido (local usa λ_local, visitante usa λ_visitante).

---

## 🧮 Modelos Matemáticos

El sistema combina **5 modelos estadísticos** con un enfoque de *ensemble*:

| Modelo | Peso | Descripción |
|--------|------|-------------|
| **Poisson** | 30% | Distribución de Poisson para predecir goles |
| **Dixon-Coles** | 25% | Corrige dependencia entre goles marcados/recibidos |
| **Monte Carlo** | 20% | 3,000 simulaciones de partidos |
| **Forma Reciente** | 15% | Análisis de últimos 5 partidos |
| **Estilo de Juego** | 10% | Corners, tarjetas, tiros |

### Mercados Analizados

- **1X2**: Victoria local, empate, victoria visitante
- **Over/Under 1.5, 2.5, 3.5**: Más/menos goles
- **BTTS**: Ambos equipos marcan (Sí/No)
- **Corners Total**: Total de córners estimados (Over/Under 9.5, 10.5)
- **Tiros Total**: Estimación de remates (Over/Under 22, 24, 26)
- **Tarjetas**: Total de tarjetas amarillas (Over/Under 5, 6, 7)
- **Tiros al Arco**: Remates entre los 3 palos (Over/Under 6, 8, 10)

### Consenso de Modelos

El panel VIP muestra el consenso real de modelos: cada modelo (Poisson, Dixon-Coles, Monte Carlo, Forma) muestra su probabilidad individual de victoria local. La discrepancia entre modelos determina el nivel de consenso (alto/moderado/bajo).

---

## 🔄 Fuentes de Datos

El sistema usa **API-Football** como fuente principal de datos:

| Fuente | Datos | Cobertura |
|--------|-------|-----------|
| **API-Football** | Partidos, fixtures, stats completas, equipos | Mundial (55 ligas) |
| **Supabase** | Base de datos PostgreSQL | Persistencia local |

### Sincronización Incremental

- Descarga partidos de **HOY-3 a HOY+10**
- **Stats incrementales**: solo descarga fixtures nuevos (no re-descarga los ya guardados)
- Equipos nuevos: descarga 5 partidos iniciales con stats
- Equipos existentes: 0 API calls si no hay fixtures nuevos

---

## 🗄️ Base de Datos (Supabase)

### Tablas Principales

| Tabla | Descripción |
|-------|-------------|
| `partidos` | Partidos del día con fixtures |
| `equipos_stats` | Stats acumuladas por equipo (V/E/D, GF/GC, lambdas) |
| `equipo_partidos_stats` | Historial de partidos con stats detalladas |
| `picks` | Picks generados y guardados |
| `bankroll_apuestas` | Apuestas del bankroll VIP |
| `calibracion_equipos` | Factores de corrección por equipo |
| `calibracion_historico` | Registro de resultados para calibración |
| `usuarios` | Usuarios y contraseñas (bcrypt) |

### Estructura equipo_partidos_stats

```sql
- team_id, fixture_id, fecha, liga
- goles_favor, goles_contra
- tiros_totales, tiros_arco, corners
- amarillas, rojas
- posesion, faltas
```

---

## 📁 Estructura del Proyecto

```
Scorpion-elite/
├── elite.py                 # ⭐ App principal Streamlit (~4350 líneas)
├── analysis_models.py       # Modelos matemáticos (Poisson, Dixon-Coles, Monte Carlo, Forma, Estilo)
├── funciones_stats.py       # Funciones de stats y promedios dinámicos
├── calibration.py           # Sistema de calibración automática
├── supabase_schema.sql     # Schema completo de DB (15 tablas)
├── requirements.txt         # Dependencias
├── Dockerfile              # Docker para producción
├── render.yaml             # Configuración de deploy
├── .streamlit/config.toml  # Configuración de Streamlit
├── .env.example            # Template de variables de entorno
└── backups/                # Backups (gitignored)
```

---

## 🚀 Despliegue

### Render
```bash
# Deploy automático desde GitHub (push a main)
git push origin main

# Deploy manual
curl -X POST "https://api.render.com/v1/services/srv-d9e1thbbc2fs73f30jh0/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

### URL Producción
- **App**: https://scorpion-elite.onrender.com
- **DB**: Supabase (jjtifureeygvygxtpuku.supabase.co)

---

## ⚙️ Configuración

### Sincronización

El botón "🔄 Sincronizar" descarga:
- Partidos de **HOY-3 a HOY+10** (13 días)
- Stats de equipos de **55 ligas** mundiales
- Stats de partidos **incrementales** (solo nuevos fixtures)

### Botones de Sincronización

| Botón | Función |
|-------|---------|
| **🔄 Sincronizar** | Descarga partidos y stats de equipos |
| **📊 Stats Ayer** | Actualiza stats SOLO de partidos de ayer |
| **🔄 Recalcular Lambdas** | Recalcula λ_local/λ_visitante desde historial |

### Login
- Autenticación con **bcrypt** (no texto plano)
- Usuarios gestionados en tabla `usuarios` de Supabase

---

## 🔧 Calibración Automática

El sistema ajusta los lambdas según resultados reales:

1. Después de cada partido, se compara λ predicho vs resultado real
2. Si el equipo marcó MÁS de lo predicho → factor sube (ej: 1.1)
3. Si el equipo marcó MENOS de lo predicho → factor baja (ej: 0.9)

```
λ Ajustado = λ Original × Factor de Corrección
```

---

## 📈 Progreso del Proyecto

### ✅ Implementado

| Funcionalidad | Estado |
|--------------|--------|
| Login con bcrypt | ✅ |
| Landing page pública (4 partidos aleatorios) | ✅ |
| Sincronización con 55 ligas | ✅ |
| 5 modelos matemáticos (ensemble) | ✅ |
| Consenso real de modelos en VIP | ✅ |
| Predicciones: 1X2, O/U, BTTS, Corners, Tiros, Tarjetas, Arco | ✅ |
| Sistema de calibración | ✅ |
| Ponderación exponencial de partidos | ✅ |
| λ dinámico + histórico + final | ✅ |
| Panel VIP (Bankroll, ROI, Value Bets, Alertas, Ranking) | ✅ |
| Guardar picks en Supabase | ✅ |
| Sincronización incremental (optimiza API credits) | ✅ |

### 🔄 En Desarrollo

| Funcionalidad | Estado |
|--------------|--------|
| Exportar picks a PDF | 🔄 |
| Notificaciones de alta confianza | 🔄 |
| Tests automatizados | 🔄 |

---

## ⚠️ Descargo de Responsabilidad

Este sistema es solo para uso informativo y estadístico. Las apuestas deportivas implican riesgo real de pérdida económica. No garantiza resultados.

---

## 🛠️ Tecnologías

- **Python 3.11** - Lenguaje principal
- **Streamlit** - Framework web
- **Supabase** - Base de datos PostgreSQL
- **API-Football** - Fuente de datos deportivos
- **bcrypt** - Hash de contraseñas
- **Render** - Hosting (Docker)

