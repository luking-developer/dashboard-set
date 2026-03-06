@echo off
SETLOCAL EnableDelayedExpansion

echo [1/3] Activando entorno virtual...
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: No se encontro el entorno virtual en .venv/
    exit /b
)
call ".venv\Scripts\activate.bat"

echo [2/3] Actualizando dependencias...
:: Corregido: Las comillas solo deben envolver la ruta del ejecutable, no los argumentos
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\pip.exe" install -r requirements.txt

echo [3/3] Iniciando Streamlit en puerto 8502...
:: Agregue el flag --server.address para asegurar visibilidad local
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8502 --server.headless true --server.enableCORS false --server.enableXsrfProtection false