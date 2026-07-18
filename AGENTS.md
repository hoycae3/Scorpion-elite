# Scorpion Elite - Resumen del Proyecto

## 📌 Estado Actual (Julio 2026)

### Descripción
App de análisis de partidos de fútbol con predicciones matemáticas y scraping multi-fuente:
- **Flashscore**: Partidos del día y cuotas
- **Transfermarkt**: Tablas de posiciones y valor de mercado
- **Soccerway**: Resultados históricos y forma actual
- **WhoScored**: Estadísticas avanzadas (corners, tarjetas, posesión)

### Repositorio
https://github.com/hoycae3/Scorpion-elite

### App Desplegada
https://scorpion-elite-go7zv8dgdaa3uarwfsxph6.streamlit.app/

---

## 🔧 Stack Tecnológico

- **Frontend**: Streamlit (Python)
- **Base de datos**: Supabase (configurado y funcionando)
- **Scraping**: 
  - BeautifulSoup para scraping ligero
  - Múltiples fuentes de datos
- **CI/CD**: GitHub Actions (scraper diario automático)

---

## 📁 Estructura del Proyecto

```
Scorpion-elite/
├── app.py                      # App principal de Streamlit
├── scraper.py                  # Scraper legacy con APIs
├── supabase_schema.sql         # Schema extendido de la base de datos
├── requirements.txt           # Dependencias de Python
├── styles.css                  # Estilos CSS
├── .github/workflows/
│   └── scraper.yml            # GitHub Actions (multi-source scraper)
└── scorpion/
    ├── __init__.py
    └── scrapers/
        ├── __init__.py        # Exports de scrapers
        ├── base_scraper.py    # Clase base para scrapers
        ├── flashscore_scraper.py    # Partidos y cuotas
        ├── transfermarkt_scraper.py  # Tablas y estadísticas
        ├── soccerway_scraper.py      # Resultados históricos
        ├── whoscored_scraper.py      # Estadísticas avanzadas
        └── scraper_unificado.py      # Combina todos los scrapers
```

---

## 🔄 Sistema de Scraping Multi-Fuente

### Fuentes de Datos

| Fuente | Datos | Uso Principal |
|--------|-------|---------------|
| **Flashscore** | Partidos, horarios, ligas | Partidos del día |
| **Transfermarkt** | Tablas de posiciones, puntos, valor de mercado | Análisis de equipos |
| **Soccerway** | Resultados históricos, goleadores | Forma actual |
| **WhoScored** | Corners, tarjetas, posesión, duelos | Estadísticas avanzadas |

### Uso del Scraper Unificado

```python
from scorpion.scrapers import ScraperUnificado

scraper = ScraperUnificado()

# Opción 1: Scraping completo
summary = scraper.run_full_scrape()

# Opción 2: Scraping por fuente
partidos = scraper.scrape_partidos(dias=2)
equipos = scraper.scrape_transfermarkt("Premier League")
resultados = scraper.scrape_soccerway("Premier League")
stats = scraper.scrape_whoscored("England")
```

### Flujo de Datos

```
GitHub Actions (6AM UTC)
    │
    ├── Flashscore ──────► Partidos del día
    ├── Transfermarkt ───► Tablas de posiciones
    ├── Soccerway ───────► Resultados históricos
    └── WhoScored ───────► Estadísticas avanzadas
            │
            ▼
       Supabase (almacena todo)
            │
            ▼
       app.py (Streamlit)
            │
            ▼
      Usuario final
```

---

## 📊 Schema de Supabase (Extendido)

### Tablas Principales

| Tabla | Descripción | Fuente |
|-------|-------------|--------|
| `partidos` | Partidos con probabilidades y cuotas | Flashscore |
| `historial_picks` | Seguimiento de picks | App |
| `estadisticas_equipos` | Stats de equipos | Transfermarkt/Soccerway/WhoScored |
| `estadisticas_partidos` | Stats detalladas de partidos | WhoScored |
| `cuotas_mercado` | Cuotas de bookmakers | Múltiples |
| `resultados_historicos` | Resultados pasados | Soccerway |

### Campos de `partidos`
- fixture_id, fecha, hora, hora_utc
- liga, prioridad, equipo_local, equipo_visitante
- prob_home/prob_draw/prob_away
- cuota_1, cuota_x, cuota_2
- pick, cuota_pick, confianza
- source_flashscore, source_transfermarkt, source_soccerway, source_whoscored
- estado (programado/en_vivo/finalizado)

---

## 🔑 Secrets en GitHub

Configurados en:
https://github.com/hoycae3/Scorpion-elite/settings/secrets/actions

- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## 📝 Notas Importantes

- **Costo total: $0/mes** (Supabase free tier + Streamlit Cloud free)
- Los scrapers usan requests + BeautifulSoup (sin Playwright)
- Se ejecuta automáticamente cada día a las 6AM UTC
- También puede ejecutarse manualmente desde GitHub Actions con parámetro de fuente

---

## ⏳ Pendiente por Mejorar

1. ✅ **Scraping multi-fuente implementado** - Flashscore, Transfermarkt, Soccerway, WhoScored
2. ✅ **Schema extendido creado** - Nuevas tablas para estadísticas avanzadas
3. ⏳ **Integrar stats en app.py** - Mostrar estadísticas de equipos/partidos
4. ⏳ **Extraer cuotas reales** - Implementar scraping de cuotas de bookmakers

---

## 🔄 Cómo Continuar en Nuevo Chat

1. Leer este archivo AGENTS.md primero
2. Ejecutar el nuevo schema SQL en Supabase (supabase_schema.sql)
3. Probar los scrapers localmente:
   ```bash
   python -c "from scorpion.scrapers import ScraperUnificado; print('OK')"
   ```
4. Ejecutar workflow manualmente desde GitHub Actions
5. Actualizar app.py para mostrar nuevas estadísticas
