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

4. **Integración con Supabase** (EN PROGRESO)
   - ✅ scraper.py creado
   - ✅ Workflow GitHub Actions creado
   - ✅ Schema SQL creado
   - ✅ app.py modificado para leer desde Supabase
   - ⏳ **Pendiente: Ejecutar SQL en Supabase**
   - ⏳ **Pendiente: Agregar secrets en GitHub**

---

## 📍 Último Paso Completado

El usuario creó el proyecto en Supabase pero necesita ejecutar el SQL.

### Cómo ejecutar el SQL en Supabase:

1. Ir a https://supabase.com y abrir el proyecto
2. En el menú lateral → **SQL Editor** (icono >_)
3. Click en **New query**
4. Copiar el contenido de `supabase_schema.sql` del repositorio
5. Click en **Run**

---

## ⏳ Pendiente por Hacer

### Paso 1: Ejecutar SQL en Supabase
- El usuario YA creó el proyecto en Supabase
- Falta ejecutar el archivo `supabase_schema.sql` en el SQL Editor

### Paso 2: Agregar secrets en GitHub
- Ir a: https://github.com/hoycae3/Scorpion-elite/settings/secrets/actions
- Agregar:
  - `SUPABASE_URL` → La URL del proyecto (ej: https://xxxx.supabase.co)
  - `SUPABASE_KEY` → service_role key (de Settings → API en Supabase)

### Paso 3: Verificar APIs
- Las 2 keys de API-Football devolvían 0 partidos
- Posiblemente necesitan renovarse

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

## 🔑 Secrets Requeridos en GitHub

Después de configurar Supabase, agregar en:
https://github.com/hoycae3/Scorpion-elite/settings/secrets/actions

| Secret | Valor |
|--------|-------|
| `SUPABASE_URL` | URL del proyecto en Supabase |
| `SUPABASE_KEY` | service_role key (Settings → API en Supabase) |

---

## 📝 Notas Importantes

- **Costo total: $0/mes** (Supabase free tier + Streamlit Cloud free)
- Las APIs de fútbol son el cuello de botella actual
- Si las keys de API-Football se agotan, buscar alternativas:
  - API-Football plan de pago
  - Football-Data.org
  - SportMonks

---

## 🔄 Cómo Continuar en Nuevo Chat

1. Leer este archivo AGENTS.md primero
2. Verificar si el usuario ejecutó el SQL en Supabase
3. Si no lo ha hecho, guiarlo paso a paso
4. Si ya lo hizo, ayudar con los secrets de GitHub
5. Probar que todo funcione correctamente
