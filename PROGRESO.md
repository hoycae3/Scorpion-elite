# 🦂 Scorpion Elite - Estado del Proyecto

## 📌 Fecha: Julio 2026

---

## 🔄 Flujo Actual de la App

```
1. Usuario sube EXCEL con partidos
          ↓
2. App parsea: fecha, hora, liga, equipos
          ↓
3. Usuario presiona "🔄 Buscar Equipos del Excel"
          ↓
4. stats_robot.py busca estadísticas de cada equipo:
   - football-data.co.uk (goles, resultados)
   - Soccerway (Latinoamérica)
   - WhoScored (corners, tarjetas, posesión)
   - FBref (stats avanzadas de equipos)
          ↓
5. Calcula λL (lambda local) y λV (lambda visitante)
          ↓
6. Guarda en Supabase.equipos_stats
          ↓
7. Análisis con 4 MODELOS → Picks
```

---

## ✅ Lo que FUNCIONA

| Sección | Estado | Descripción |
|---------|--------|-------------|
| **Login** | ✅ | Contraseña: scorpion2026 |
| **Carga Excel** | ✅ | Subir .xlsx/.csv con partidos |
| **Guardar Supabase** | ✅ | Guarda partidos en tabla `partidos` |
| **Buscar Equipos** | ✅ | Botón que busca stats de equipos |
| **Scraping 4 fuentes** | ✅ | FD, SW, WhoScored, FBref |
| **Picks** | ✅ | Genera picks para apostar |

---

## 📊 Fuentes de Scraper (stats_robot.py)

| Fuente | Datos que extrae | Prioridad |
|--------|------------------|-----------|
| **football-data.co.uk** | Goles, resultados, λL, λV | 1ª |
| **Soccerway** | Resultados Latinoamérica | 2ª |
| **WhoScored** | Corners, tarjetas, posesión | 3ª |
| **FBref** | Stats avanzadas de equipos | 4ª (backup) |

---

## 📊 Modelos de Análisis Implementados

Tienes **4 modelos combinados** en `analysis_models.py`:

| Modelo | Peso | Descripción |
|--------|------|-------------|
| **Poisson** | 35% | Distribución de probabilidad para goles |
| **Dixon-Coles** | 30% | Corrige dependencia entre goles marcados/recibidos |
| **Monte Carlo** | 20% | Simulación de 3000 partidos |
| **Elo** | 15% | Rating histórico de equipos |

---

## 📁 Archivos Principales

```
Scorpion-elite/
├── app.py              ✅ App principal de Streamlit
├── data_loader.py      ✅ Parser de Excel
├── analysis_models.py  ✅ 4 modelos de análisis
├── stats_extractor.py  ✅ Cálculo de lambdas
├── stats_robot.py      ✅ Busca equipos en 4 fuentes
├── stats_advanced.py   ✅ Scraper WhoScored + FBref
├── supabase_schema.sql ✅ Schema simplificado de BD
└── requirements.txt    ✅ Dependencias
```

---

## 🗄️ Schema Simplificado (Supabase)

### 4 tablas:

| Tabla | Campos principales |
|-------|------------------|
| `partidos` | fixture_id, fecha, hora, liga, equipos |
| `equipos_stats` | equipo, liga, λL, λV, goles, corners, tarjetas, tiros, posesión |
| `partidos_stats` | Stats detalladas de partidos (corners, tarjetas, atajadas) |
| `picks` | Picks realizados con resultado |

### Campos de `equipos_stats`:
- equipo, liga, temporada
- partidos_jugados, goles_favor, goles_contra
- lambda_local, lambda_visitante
- promedio_corners_local/visitante/total
- promedio_amarillas, promedio_rojas
- promedio_tiros, promedio_tiros_arco
- promedio_posesion
- source_fbdata, source_whoscored, source_fbref

---

## ⏳ Pendiente

1. Probar scraping de WhoScored y FBref en producción
2. Integrar stats avanzadas en análisis Poisson
3. Dashboard de rendimiento de picks

---

## ⚠️ Nota Importante

Los sitios pueden bloquear scraping. El orden de búsqueda es:
1. football-data (CSV público - siempre funciona)
2. Soccerway (Latinoamérica)
3. WhoScored (puede bloquear)
4. FBref (backup, puede bloquear)
