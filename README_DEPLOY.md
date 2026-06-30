# SCORPION ELITE — Guia de Despliegue

## PASO 1 — Crear cuenta GitHub (2 min)
1. Ve a https://github.com/signup
2. Pon tu email, crea contrasena, verifica
3. En "What kind of work do you do?" -> Skip

## PASO 2 — Subir los archivos (3 min)
1. En GitHub haz clic en "+" arriba a la derecha -> "New repository"
2. Repository name: scorpion-elite
3. Selecciona "Private"
4. Clic en "Create repository"
5. En la pagina del repo haz clic en "uploading an existing file"
6. Arrastra app.py y requirements.txt -> clic "Commit changes"

## PASO 3 — Publicar en Streamlit Cloud (3 min)
1. Ve a https://streamlit.io/cloud
2. Clic "Sign in with GitHub" -> autoriza el acceso
3. Clic "New app"
4. Repository: scorpion-elite | Branch: main | Main file: app.py
5. Clic "Deploy" -> espera 2-3 minutos
6. Tu link listo: https://TUNOMBRE-scorpion-elite.streamlit.app

## PASO 4 — Agregar clientes
Edita USUARIOS en app.py y sube el archivo de nuevo a GitHub.
La app se actualiza sola en 1 minuto.

Ejemplo:
  "juan":  {"password": "clave123", "nombre": "Juan Garcia"},
  "maria": {"password": "clave456", "nombre": "Maria Lopez"},

## API KEYS (opcionales, mejoran los datos)
En Streamlit Cloud -> tu app -> Settings -> Secrets:
  ODDS_API_KEY = "tu_clave"        -> https://the-odds-api.com (gratis)
  FOOTBALL_DATA_KEY = "tu_clave"   -> https://www.football-data.org (gratis)

## LIGAS Y TORNEOS SOPORTADOS
- Premier League, La Liga, Bundesliga, Serie A, Ligue 1
- Champions League, Europa League
- Libertadores, Sudamericana, Copa America
- MLS, Liga MX, Primera Colombia, Argentina
- Mundial FIFA / World Cup / Copa del Mundo
- Eurocopa, Nations League
- Y muchas mas...

## BOT TELEGRAM (opcional)
1. Abre Telegram -> busca @BotFather -> /newbot
2. Guarda el TOKEN
3. Conecta con Make.com (gratis) para automatizar
