FROM python:3.9-slim

# Instalar FFmpeg, curl y git
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

# Exponer el puerto
EXPOSE 8501

# Chequeo de salud (FastAPI no tiene ruta default de healthcheck, así que comprobamos la raíz o creamos una)
HEALTHCHECK CMD curl --fail http://localhost:8501/ || exit 1

# Comando de inicio cambiado a Uvicorn
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8501"]