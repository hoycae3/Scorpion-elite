# Scorpion Elite - Resumen del Proyecto

## 📌 Estado Actual (Julio 2026)

### Descripción
App de análisis de partidos de fútbol con **Excel + Scraping multi-fuente + 4 Modelos matemáticos**.

### Dashboard V2 ✅ (NUEVO!)
Ahora disponible en `app_streamlit_dashboard_v2.py` con:
- 50+ ligas con datos reales
- API-Football integración
- Comparador de cuotas (Bet365, Betano, Pinnacle)
- Sistema de alertas
- Planes de usuario (Gratis, Día, Semana, Mes, Admin)
- Stats Mundial 2026
- Motor análisis con type hints y validación

### Flujo:
1. Usuario sube Excel con partidos
2. Robot busca estadísticas de equipos (4 fuentes)
3. 4 modelos de análisis generan picks
4. Usuario apuesta

### Repositorio
https://github.com/hoycae3/Scorpion-elite

### App Desplegada
https://scorpion-elite-go7zv8dgdaa3uarwfsxph6.streamlit.app/

---

## 🔧 Stack Tecnológico

- **Frontend**: Streamlit (Python)
- **Base de datos**: Supabase
- **Scraping**: 4 fuentes (ver abajo)
- **Modelos**: Poisson, Dixon-Coles, Monte Carlo, Elo
- **API**: API-Football, Sofascore

---

## 📁 Estructura del Proyecto

```
Scorpion-elite/
├── app.py                        ✅ App principal (3 secciones)
├── app_streamlit_dashboard_v2.py  ✅ Dashboard V2 completo (NUEVO!)
├── data_loader.py                ✅ Parser de Excel
├── analysis_models.py             ✅ 4 modelos de análisis
├── stats_extractor.py             ✅ Cálculo de lambdas
├── stats_robot.py                ✅ Busca equipos en 4 fuentes
├── stats_advanced.py              ✅ Scraper WhoScored + FBref
├── robot_extractor.py            ✅ Robot con técnicas antibloqueo
├── scrapers.py                    ✅ Scraper Flashscore + Soccerway
├── scraper_fbref.py              ✅ Scraper dedicado FBref
├── supabase_schema.sql           ✅ Schema simplificado de BD
│
├── scorpion/                     ✅ Módulo modular (NUEVO!)
│   ├── models/math.py            ✅ Motor análisis refactorizado
│   ├── ui/components.py          ✅ Componentes UI reutilizables
│   ├── api/football.py           ✅ Integración API-Football
│   ├── api/scraper.py            ✅ Scraper modular
│   ├── db/database.py            ✅ Base de datos SQLite
│   └── config.py                 ✅ Configuración centralizada
│
└── requirements.txt              ✅ Dependencias
```

---

## 📊 Fuentes de Scraping

| Fuente | Datos | Prioridad | Confiabilidad |
|--------|-------|-----------|----------------|
| **football-data.co.uk** | Goles, resultados, λL, λV | 1ª | ✅ Alta (CSV público) |
| **Soccerway** | Resultados Latinoamérica | 2ª | ✅ Alta |
| **WhoScored** | Corners, tarjetas, posesión | 3ª | ⚠️ Puede bloquear |
| **FBref** | Stats avanzadas de equipos | 4ª (backup) | ⚠️ Puede bloquear |

---

## 📊 Modelos de Análisis (analysis_models.py)

| Modelo | Peso | Descripción |
|--------|------|-------------|
| **Poisson** | 35% | Distribución de probabilidad para goles |
| **Dixon-Coles** | 30% | Corrige dependencia entre goles marcados/recibidos |
| **Monte Carlo** | 20% | Simulación de 3000 partidos |
| **Elo** | 15% | Rating histórico de equipos |

---

## 🗄️ Schema de Supabase (Simplificado)

### 4 tablas:

| Tabla | Uso |
|-------|-----|
| `partidos` | Partidos del Excel (fecha, hora, liga, equipos) |
| `equipos_stats` | Stats promediadas de equipos |
| `partidos_stats` | Stats detalladas de partidos |
| `picks` | Picks realizados |

### Campos de `equipos_stats`:
- equipo, liga, temporada
- partidos_jugados, goles_favor, goles_contra
- lambda_local, lambda_visitante
- promedio_corners_total, promedio_amarillas, promedio_rojas
- promedio_tiros, promedio_tiros_arco, promedio_posesion
- source_fbdata, source_whoscored, source_fbref

---

## 🔄 Flujo de Datos

```
Excel (usuario)
    ↓
stats_robot.py
    ├── football-data (goles, λL, λV)
    ├── Soccerway (Latinoamérica)
    ├── WhoScored (corners, tarjetas)
    └── FBref (stats avanzadas)
    ↓
Supabase (equipos_stats)
    ↓
app.py → 4 Modelos de Análisis
    ↓
Picks para el usuario
```

---

## 🚀 Cómo Continuar en Nuevo Chat

1. Leer este archivo AGENTS.md primero
2. Verificar que Supabase tiene las tablas creadas (schema.sql)
3. Probar el flujo completo:
   ```bash
   python -c "from stats_robot import run_robot_batch; print('OK')"
   ```
4. Revisar analysis_models.py para entender los 4 modelos

---

## ⚠️ Notas Importantes

- El scraping de football-data es público (CSV) - siempre funciona
- WhoScored y FBref pueden bloquear requests frecuentes
- Usar rate limiting entre requests
- Para agregar más estadísticas, modificar stats_robot.py y stats_advanced.py
