#!/bin/bash

# 1. Asegurar que el script se detenga si hay errores
set -e

echo "[1/3] Activando entorno virtual..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "ERROR: No se encontró la carpeta .venv"
    exit 1
fi

echo "[2/3] Actualizando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/3] Iniciando Streamlit en puerto 8502..."
# Ejecutamos con los flags necesarios para evitar bloqueos de red
streamlit run app.py \
    --server.port 8502 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false