# 🦂 Scorpion Elite V4 Pro

**Sistema de análisis estadístico para apuestas deportivas de fútbol**

Scorpion Elite es una aplicación web que combina múltiples modelos matemáticos con datos reales de equipos para generar predicciones sobre partidos de fútbol y distintos mercados de apuestas.

---

## ¿Cómo funciona?

### 1. Motor de Análisis Matemático

El sistema utiliza **4 modelos estadísticos** combinados mediante ponderación:

| Modelo | Peso | Descripción |
|--------|------|-------------|
| **Poisson** | 35% | Distribución de probabilidad para predecir goles |
| **Dixon-Coles** | 30% | Corrige la dependencia entre goles marcados y recibidos |
| **Monte Carlo** | 20% | Simulación de 3,000 partidos para estimar probabilidades |
| **Elo** | 15% | Rating histórico del equipo (forma y fortaleza) |

El sistema combina estos 4 resultados para dar una **probabilidad final** con un nivel de **confianza** (0-100%).

### 2. Fuentes de Datos

El sistema consulta automáticamente múltiples APIs:

- **API-Football**: Stats oficiales de temporada (goles, tiros, tarjetas)
- **Understat**: xG (goles esperados) para ligas europeas top
- **TheSportsDB**: Resultados últimos partidos de cualquier equipo
- **ClubElo**: Ratings Elo de equipos europeos

### 3. Mercados Analizados

Para cada partido, el sistema calcula probabilidades para:

- **Resultado 1X2**: Victoria local, empate, victoria visitante
- **Over/Under**: 0.5, 1.5, 2.5, 3.5 goles
- **BTTS**: Ambos equipos marcan (Sí/No)
- **Corners**: Over 7.5, 8.5, 9.5, 10.5
- **Tarjetas**: Over 1.5, 2.5, 3.5
- **Tiros al arco**: Estimados por equipo

### 4. Clasificación de Picks

Cada análisis recibe una clasificación:

| Rango | Condición | Descripción |
|-------|-----------|-------------|
| **A+** | Confianza ≥75% + datos reales + liga top | Mejor selección |
| **B** | Confianza ≥55% | Buena opción |
| **C** | Confianza ≥40% | Especulativa |
| **D** | Confianza <40% | Baja confianza |

---

## Estructura del Proyecto

```
Scorpion-elite/
├── app.py              # Aplicación principal (Streamlit)
├── requirements.txt    # Dependencias Python
└── README.md          # Este archivo
```

---

## Requisitos e Instalación

### Dependencias

```
streamlit>=1.32.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.1.0
openpyxl>=3.1.2
Pillow>=10.0.0
```

### Instalación local

```bash
pip install -r requirements.txt
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`

### Variables de Entorno (Opcionales)

Para mejorar la calidad de los datos, puedes configurar:

```bash
export API_FOOTBALL_KEY="tu_api_key"           # https://www.api-football.com
export ADMIN_PASSWORD="tu_contrasena_segura"   # Contraseña admin
```

---

## Funcionalidades por Plan de Usuario

| Característica | Gratis | Día | Semana | Mes |
|----------------|--------|-----|--------|-----|
| Análisis individual | ✅ 5/día | ✅ | ✅ | ✅ |
| Análisis por liga | ❌ | ✅ | ✅ | ✅ |
| Datos reales de API | Limitado | ✅ | ✅ | ✅ |
| Exportar Excel | ❌ | ✅ | ✅ | ✅ |
| Escalera | ❌ | ❌ | ✅ | ✅ |
| Combinadas | ❌ | ❌ | ❌ | ✅ |
| Historial personal | ❌ | ❌ | ✅ | ✅ |

---

## Flujo de Uso

### Para Administradores

1. **Acceder** con credenciales admin
2. **Analizar partido**: Escribir equipo local, visitante y liga
3. **Revisar modelos**: Ver comparación de los 4 modelos estadísticos
4. **Publicar picks**: Seleccionar mercados para compartir con clientes
5. **Gestionar usuarios**: Ver clientes activos y sus planes

### Para Clientes

1. **Iniciar sesión** con su número de documento
2. **Ver picks del día**: Picks publicados por el administrador
3. **Analizar partido**: Análisis individual (según plan)
4. **Exportar Excel**: Descargar análisis completo con formato profesional
5. **Escalera/Combinadas**: Construir apuestas progresivas (planes superiores)

---

## Ligas y Torneos Soportados

**Europa:**
- Premier League, La Liga, Bundesliga, Serie A, Ligue 1
- Champions League, Europa League, Conference League
- Eredivisie, Primeira Liga, Super Lig, Saudi Pro League

**América:**
- Libertadores, Sudamericana, Copa America
- MLS, Liga MX, Primera Colombia, Primera Argentina, Brasileirao

**Otros:**
- Mundial FIFA, Eurocopa, Nations League

---

## Arquitectura Técnica

### Base de Datos (SQLite)

El sistema usa SQLite para almacenar:

- **usuarios**: Credenciales y planes de clientes
- **picks**: Picks publicados por el admin
- **historial**: Análisis realizados por usuarios
- **escalera**: Estado de escaleras activas

### Modelos Matemáticos

```python
# Cálculo de probabilidades combinadas
p1 = p1_po * 0.35 + p1_dc * 0.30 + p1_mc * 0.20 + p1_el * 0.15
```

### Cálculo de xG Ajustado

```python
# xG local ajustado por estadísticas del oponente
xl = gml * (gcv / promedio_gc_liga) * factor_local
```

---

## Despliegue en Streamlit Cloud

1. Crear repositorio en GitHub
2. Subir `app.py` y `requirements.txt`
3. Conectar con Streamlit Cloud
4. Configurar Secrets en Streamlit (opcional):
   ```
   API_FOOTBALL_KEY = "tu_clave"
   ADMIN_PASSWORD = "tu_contrasena"
   ```

---

## Descargo de Responsabilidad

⚠️ **IMPORTANTE**: Este sistema es solo para uso informativo y estadístico. Las apuestas deportivas implican riesgo real de pérdida económica. El sistema no garantiza resultados y no debe usarse como única fuente de decisión para apostar dinero real.

---

## Tecnologías

- **Python 3.8+**
- **Streamlit**: Framework web
- **SQLite**: Base de datos ligera
- **Requests + BeautifulSoup**: Obtención de datos web
- **OpenPyXL**: Exportación a Excel
- **APIs Externas**: API-Football, Understat, TheSportsDB, ClubElo
