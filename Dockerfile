FROM python:3.9-slim

# Instalar FFmpeg, git Y CURL (Agregamos curl aquí)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto de Streamlit
EXPOSE 8501

# Chequeo de salud (Ahora sí funcionará porque instalamos curl)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando de inicio
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]