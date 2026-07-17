# Configuración de Supabase para Scorpion Elite

## Paso 1: Crear proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com) y crea una cuenta gratuita
2. Crea un nuevo proyecto
3. Copia las credenciales de la Settings → API:
   - **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
   - **anon/public key**: `eyJhbGc...`

## Paso 2: Crear tablas

1. En tu proyecto de Supabase, ve a **SQL Editor**
2. Copia y ejecuta el contenido de `supabase_schema.sql`

## Paso 3: Agregar Secrets en GitHub

1. Ve a tu repositorio en GitHub: `https://github.com/hoycae3/Scorpion-elite`
2. Ve a **Settings → Secrets and variables → Actions**
3. Agrega los siguientes secrets:

| Secret Name | Value |
|-------------|-------|
| `SUPABASE_URL` | Tu Project URL de Supabase |
| `SUPABASE_KEY` | Tu `service_role` key (de Settings → API → service_role key) |

⚠️ **Importante**: Usa la `service_role` key para que el scraper pueda escribir en la base de datos.

## Paso 4: Verificar configuración

El scraper se ejecutará automáticamente cada día a las **6:00 AM UTC**.

Para probar manualmente:
1. Ve a **Actions** en tu repositorio
2. Selecciona "Daily Match Scraper"
3. Click en **Run workflow**

## Estructura de la base de datos

### Tabla `partidos`
| Campo | Descripción |
|-------|-------------|
| fixture_id | ID único del partido en API-Football |
| fecha | Fecha del partido |
| hora_local | Hora en zona horaria local |
| liga | Nombre de la liga |
| prioridad | Prioridad de la liga (1-15) |
| equipo_home | Nombre del equipo local |
| equipo_away | Nombre del equipo visitante |
| prob_home | Probabilidad victoria local (%) |
| prob_draw | Probabilidad empate (%) |
| prob_away | Probabilidad victoria visitante (%) |
| cuota_1 | Cuota victoria local |
| cuota_x | Cuota empate |
| cuota_2 | Cuota victoria visitante |
| pick | Pick recomendado (1, X, 2) |
| cuota_pick | Cuota del pick |
| confianza | Nivel de confianza (%) |

## Costo

✅ **$0/month** - El tier gratuito de Supabase incluye:
- 500 MB base de datos
- 1 GB transferencia
- 50K usuarios activos mensuales
- Suficiente para esta aplicación
