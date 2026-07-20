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

# Instalar Playwright y navegadores
RUN pip install playwright
RUN playwright install --with-deps chromium

# Copiar código
COPY . .

# Puerto de Streamlit
EXPOSE 8501

# Comando - Dashboard V2
CMD ["streamlit", "run", "app_streamlit_dashboard_v2.py", "--server.port=8501", "--server.address=0.0.0.0"]
