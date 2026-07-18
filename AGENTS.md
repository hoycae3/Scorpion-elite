# Scorpion Elite - Resumen del Proyecto

## 📌 Estado Actual (Julio 2026)

### Descripción
App de análisis de partidos de fútbol con predicciones matemáticas y datos reales de scraping de Flashscore.

### Repositorio
https://github.com/hoycae3/Scorpion-elite

### App Desplegada
https://scorpion-elite-go7zv8dgdaa3uarwfsxph6.streamlit.app/

### Pull Request
https://github.com/hoycae3/Scorpion-elite/pull/3

---

## 🔧 Stack Tecnológico

- **Frontend**: Streamlit (Python)
- **Base de datos**: Supabase (configurado y funcionando)
- **Scraping**: Playwright para extraer datos reales de Flashscore
- **CI/CD**: GitHub Actions (scraper diario automático)

---

## 📁 Estructura del Proyecto

```
Scorpion-elite/
├── app.py                 # App principal de Streamlit
├── scraper_real.py       # Scraper con Playwright (Flashscore)
├── scraper.py            # Scraper legacy con APIs
├── supabase_schema.sql   # Schema de la base de datos
├── requirements.txt      # Dependencias de Python
├── styles.css            # Estilos CSS
├── .github/workflows/
│   └── scraper.yml       # GitHub Actions (scraper diario)
└── scorpion/             # Módulo interno
```

---

## ✅ Estado Completado

### 1. Supabase Configurado ✅
- Schema SQL ejecutado
- Secrets configurados en GitHub:
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

### 2. Scraper Real con Playwright ✅
El nuevo `scraper_real.py` usa Playwright para extraer datos reales de Flashscore:
- Partidos de hoy y mañana (próximas 48 horas)
- Todas las ligas disponibles (principales y secundarias)
- Nombres correctos de equipos y ligas
- Priorización automática por importancia de liga

### 3. Datos en Supabase ✅
- 246 partidos únicos guardados
- Ligas incluyen: Serie A Brasil, MLS, Liga MX, Primera Nacional Argentina, Copa Argentina, Canadian Premier League, etc.

---

## 🔄 Flujo de Datos

```
GitHub Actions (6AM UTC)
    ↓
scraper_real.py → Playwright → Flashscore
    ↓
Supabase (almacena partidos del día)
    ↓
app.py → Supabase (primario) o APIs (fallback)
    ↓
Streamlit Cloud → Usuario ve la app
```

---

## 📊 Tablas de Supabase

### partidos
| Campo | Descripción |
|-------|-------------|
| fixture_id | ID único |
| fecha | Fecha del partido |
| hora_local | Hora del partido |
| liga | Nombre de la liga |
| prioridad | 1-15 según importancia |
| equipo_home | Equipo local |
| equipo_away | Equipo visitante |
| prob_home/px/away | Probabilidades % (placeholder) |
| cuota_1/x/2 | Cuotas del mercado (placeholder) |
| pick | 1, X, o 2 |
| cuota_pick | Cuota del pick |
| confianza | % de confianza |

### historial_picks
Para seguimiento de resultados de picks.

---

## 🔑 Secrets en GitHub

Los secrets están configurados en:
https://github.com/hoycae3/Scorpion-elite/settings/secrets/actions

---

## 📝 Notas Importantes

- **Costo total: $0/mes** (Supabase free tier + Streamlit Cloud free)
- El scraper usa Playwright para extraer datos reales de Flashscore
- Se ejecuta automáticamente cada día a las 6AM UTC
- También puede ejecutarse manualmente desde GitHub Actions

---

## ⏳ Pendiente por Mejorar

1. **Extraer cuotas reales** - El scraper actualmente usa valores placeholder
2. **Extraer estadísticas históricas** - Para análisis de córners y tarjetas
3. **Mejorar priorización de ligas** - Agregar más ligas importantes

---

## 🔄 Cómo Continuar en Nuevo Chat

1. Leer este archivo AGENTS.md primero
2. Merge el PR #3 para actualizar el scraper
3. Verificar conexión a Supabase
4. Ejecutar scraper_real.py si hay nuevos partidos
5. Verificar que la app muestra los datos correctamente
