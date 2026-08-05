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

---

## 🧮 Modelos Matemáticos

El sistema combina **4 modelos estadísticos** para generar predicciones:

| Modelo | Peso | Descripción |
|--------|------|-------------|
| **Poisson** | 35% | Distribución de Poisson para predecir goles |
| **Dixon-Coles** | 30% | Corrige dependencia entre goles marcados/recibidos |
| **Monte Carlo** | 20% | 3,000 simulaciones de partidos |
| **Elo** | 15% | Rating histórico del equipo |

### Mercados Analizados

- **1X2**: Victoria local, empate, victoria visitante
- **Over/Under 2.5**: Más/menos de 2.5 goles
- **BTTS**: Ambos equipos marcan (Sí/No)
- **Corners Total**: Total de córners estimados
- **Tiros Total**: Estimación de remates al arco
- **Tarjetas**: Total de tarjetas amarillas
- **Tiros al Arco**: Remates entre los 3 palos

---

## 🔄 Fuentes de Datos (SUPERROBOT)

El sistema consulta múltiples fuentes automáticamente:

| Fuente | Datos | Anti-Bloqueo | Cobertura |
|--------|-------|--------------|-----------|
| **football-data.co.uk** | Partidos, GF, GC, V/E/D | Requests | 20+ ligas europeas |
| **API-Football** | Stats completas | API oficial | Mundial (88/mes) |
| **Soccerway** | Resultados históricos | cloudscraper | Mundial |
| **WhoScored** | Corners, Tarjetas, Posesión | cloudscraper | Mundial |
| **FBref** | Stats detalladas | cloudscraper | 7 ligas top europeas |

### Flujo del Robot

```
1. football-data.co.uk → Equipos europeos (sin límite)
   ↓ (si no encuentra)
2. API-Football → Equipos no encontrados (máx 88)
   ↓ (si se acaban los 88)
3. Soccerway → Equipos no encontrados (mundial)
   ↓ (si no encuentra)
4. WhoScored → Equipos no encontrados (mundial)
   ↓ (si no encuentra)
5. FBref → Equipos no encontrados (europa +)
```

---

## 🗄️ Base de Datos (Supabase)

### Tablas Principales

| Tabla | Descripción |
|-------|-------------|
| `partidos` | Partidos del día con fixtures |
| `equipos_stats` | Stats acumuladas por equipo (V/E/D, GF/GC, lambdas) |
| `equipo_partidos_stats` | Historial de partidos con stats detalladas |
| `picks` | Picks generados y guardados |
| `calibracion_equipos` | Factores de corrección por equipo |
| `calibracion_historico` | Registro de resultados para calibración |

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
├── elite.py                 # App principal Streamlit (~2800 líneas)
├── robot_extractor.py      # SUPERROBOT - Todos los scrapers
├── funciones_stats.py       # Funciones de stats y promedios
├── analysis_models.py       # Modelos matemáticos (Poisson, etc.)
├── calibration.py           # Sistema de calibración automática
├── supabase_schema.sql     # Schema completo de DB
├── requirements.txt         # Dependencias
├── styles.css              # Estilos CSS
└── backups/                # Backups de archivos
```

---

## 🚀 Despliegue

### Render
```bash
# Deploy automático desde GitHub
curl -X POST "https://api.render.com/v1/services/srv-XXX/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

### URL Producción
- **App**: https://scorpion-elite.onrender.com
- **DB**: Supabase (jjtifureeygvygxtpuku.supabase.co)

---

## ⚙️ Configuración

### Sincronización

El botón "🔄 Sincronizar" descarga:
- Partidos de **HOY-2 a HOY+6**
- Stats de equipos de **55 ligas** mundiales
- Stats de partidos **incrementales** (solo nuevos fixtures)

### Login
- **Contraseña**: `scorpion2026`
- Ubicado en landing page

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
| Login con contraseña | ✅ |
| Landing page pública | ✅ |
| Sincronización con 55 ligas | ✅ |
| Scraping de 5 fuentes | ✅ |
| 4 modelos matemáticos | ✅ |
| Predicciones: 1X2, O/U, BTTS, Corners, Tiros, Tarjetas | ✅ |
| Sistema de calibración | ✅ |
| Ponderación exponencial de partidos | ✅ |
| Mostrar λ dinámico + histórico + final | ✅ |
| Dashboard con métricas | ✅ |
| Guardar picks en Supabase | ✅ |
| Panel VIP | ✅ |

### 🔄 En Desarrollo

| Funcionalidad | Estado |
|--------------|--------|
| Mejorar UI del análisis preview | 🔄 |
| Exportar picks a PDF | 🔄 |
| Notificaciones de alta confianza | 🔄 |
| Modo claro/oscuro | 🔄 |

---

## ⚠️ Descargo de Responsabilidad

Este sistema es solo para uso informativo y estadístico. Las apuestas deportivas implican riesgo real de pérdida económica. No garantiza resultados.

---

## 🛠️ Tecnologías

- **Python 3.8+** - Lenguaje principal
- **Streamlit** - Framework web
- **Supabase** - Base de datos PostgreSQL
- **cloudscraper** - Anti-bloqueo para scrapers
- **Render** - Hosting
