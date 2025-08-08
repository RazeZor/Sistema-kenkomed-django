# Usa una imagen base oficial de Python
FROM python:3.10-slim

# Configura el directorio de trabajo
WORKDIR /app

# Instala las dependencias necesarias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos del proyecto
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Expone el puerto donde corre el servidor de Django
EXPOSE 8000

# Comando para iniciar el servidor de Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]