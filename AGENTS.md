# Scorpion Elite - Resumen del Proyecto

## 📌 Estado Actual (Julio 2026)

### Descripción
App de análisis de partidos de fútbol con predicciones matemáticas y datos reales de APIs deportivas.

### Repositorio
https://github.com/hoycae3/Scorpion-elite

### App Desplegada
https://scorpion-elite-go7zv8dgdaa3uarwfsxph6.streamlit.app/

---

## 🔧 Stack Tecnológico

- **Frontend**: Streamlit (Python)
- **Base de datos**: Supabase (gratuito, en proceso de configuración)
- **APIs de datos**: 
  - API-Football (2 keys: e3926f829cd848f4b2b54d722ca29701, 124c9519df145caf883cd82f0b2a4671)
  - TheSportsDB (fallback)
  - Flashscore (último fallback)
- **CI/CD**: GitHub Actions

---

## 📁 Estructura del Proyecto

```
Scorpion-elite/
├── app.py                 # App principal de Streamlit
├── scraper.py            # Script para obtener datos y guardar en Supabase
├── supabase_schema.sql   # Schema de la base de datos
├── SUPABASE_SETUP.md     # Instrucciones de configuración
├── requirements.txt      # Dependencias de Python
├── styles.css            # Estilos CSS
├── .github/workflows/
│   └── scraper.yml       # GitHub Actions (scraper diario 6AM UTC)
└── scorpion/             # Módulo interno
```

---

## ✅ Lo Que Hemos Hecho

1. **Frontend completo** con Streamlit
   - Header con logo Scorpion
   - Selector de deporte y fecha
   - Partidos destacados
   - Mejor Pick del día con análisis
   - Predicciones Poisson, Dixon-Coles, Monte Carlo, Elo

2. **Sistema de APIs** con fallback
   - API-Football (primaria, pero agotada actualmente)
   - TheSportsDB (fallback)
   - Flashscore (último fallback)

3. **Sistema de caché** implementado
   - Partidos: 5 minutos TTL
   - Predicciones/cuotas: 10 minutos TTL

4. **Integración con Supabase** (pendiente de configurar)
   - scraper.py creado
   - Workflow GitHub Actions creado
   - Schema SQL creado

---

## ⏳ Pendiente por Hacer

### 1. Configurar Supabase (REQUIRED)
El usuario necesita:
1. Crear cuenta en https://supabase.com
2. Ejecutar `supabase_schema.sql` en SQL Editor
3. Agregar secrets en GitHub:
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (service_role key)

### 2. Verificar que APIs funcionan
- Las 2 keys de API-Football actualmente devuelven 0 partidos
- Necesitan regenerarse o conseguir nuevas keys

### 3. El scraper se ejecutará automáticamente
- GitHub Actions ejecuta scraper.py cada día a las 6:00 AM UTC
- Guardará partidos + predicciones + cuotas en Supabase

---

## 🎯 Flujo de Datos (Goal)

```
GitHub Actions (6AM)
    ↓
scraper.py → API-Football + TheSportsDB + Flashscore
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
| hora_local | Hora ajustada (UTC-3) |
| liga | Nombre de la liga |
| prioridad | 1-15 según importancia |
| equipo_home | Equipo local |
| equipo_away | Equipo visitante |
| prob_home/px/away | Probabilidades % |
| cuota_1/x/2 | Cuotas del mercado |
| pick | 1, X, o 2 |
| cuota_pick | Cuota del pick |
| confianza | % de confianza |

### historial_picks
Para seguimiento de resultados de picks.

---

## 🔑 Variables de Entorno

En Streamlit Cloud (Settings → Secrets):
- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## 📝 Notas Importantes

- **Costo total: $0/mes** (Supabase free tier + Streamlit Cloud free)
- Las APIs de fútbol son el cuello de botella actual
- Si las keys de API-Football se agotan, buscar alternativas:
  - API-Football plan de pago
  - Football-Data.org
  - SportMonks

---

## 🔄 Cómo Continuar

1. Si el chat se reinicia, leer este archivo primero
2. Verificar estado de Supabase y APIs
3. Revisar logs de GitHub Actions si el scraper falla
4. La app tiene fallback automático si Supabase no está configurado
