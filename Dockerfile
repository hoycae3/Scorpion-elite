FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Puerto de Streamlit
EXPOSE 8501

# Configurar Streamlit para evitar errores de inotify
ENV STREAMLIT_SERVER_FILE_WATCHER_TYPE=none
ENV STREAMLIT_SERVER_HEADLESS=true

# Crear .env desde variables de entorno (Render las provee)
# Si no están configuradas, usar valores por defecto (para desarrollo local)
RUN if [ -n "$ADMIN_PASSWORD" ]; then \
    echo "ADMIN_PASSWORD=$ADMIN_PASSWORD" > /app/.env; \
    echo "SUPABASE_URL=$SUPABASE_URL" >> /app/.env; \
    echo "SUPABASE_KEY=$SUPABASE_KEY" >> /app/.env; \
    fi

# Comando - elite.py
CMD ["streamlit", "run", "elite.py", "--server.port=8501", "--server.address=0.0.0.0"]
