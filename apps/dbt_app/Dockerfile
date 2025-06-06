# Usa una imagen ligera de Python
FROM python:3.11-slim
# Crea un directorio de trabajo
WORKDIR /dbt_app
# Copia todos los archivos al contenedor
COPY . .
# Instala dependencias necesarias del sistema
RUN apt-get update && apt-get install -y build-essential libpq-dev git && rm -rf /var/lib/apt/lists/*
# Instala dbt y el adaptador para PostgreSQL
RUN pip install --upgrade pip \
    && pip install dbt-core dbt-postgres
# Establece el directorio de perfiles por defecto
ENV DBT_PROFILES_DIR=/dbt_app
# Comando por defecto
CMD ["tail", "-f", "/dev/null"]
