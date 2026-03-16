APP_TITLE = "⚡ Sub Estaciones Transformadoras EPE"
APP_EXPLANATION = "Sube tu archivo de reporte de SETs obteniéndolo desde la aplicación de **Reportes de EPE**, menú _**`Lineas y SETs > SETs por area`**_ y luego pulsando el cuarto boton **Export report** en **formato XLSX**. Ten la precaución de obtener el reporte de un único distrito para evitar inconvenientes."
UPLOAD_MSG = "Sube tu archivo XLSX con la tabla de datos"
NEW_HEADERS = [
    "Sucursal", "Area", "Distrito", "# SET", "Antifraude", "Convencional", 
    "Preensamblado", "Subterraneo", "Total", "Total clientes BT", 
    "Potencia total", "Cantidad trafos", "Codigo ET", "Codigo distribuidor", 
    "Descripciones", "Domicilio", "Estado topologia", "Tipo SET", "Subtipo SET", 
    "Urbana/Rural", "X", "Y", "Lat/Long", "Energia anual total", 
    "Energia anual comercial", "Energia anual residencial", 
    "Energia anual Industrial", "Energia anual otros"
]
PROCESSING_SUCCESSFULLY = "✅ Procesamiento exitoso."
FREE_SETS_AVAILABLE = "Números de SET disponibles"
URBAN_LABEL = "🚗 # SET Urbana disponible"
COPY_URBAN = "Copiar SET Urbana"
COPIED = "Copiado!"
RURAL_LABEL = "🚜 # SET Rural disponible"
COPY_RURAL = "Copiar SET Rural"
DOWNLOAD_DATA = "💾 Descargar datos"
DOWNLOAD_FILENAME = "reporte_sets.csv"
upload_format = ['xlsx', 'xls']
READING_FILE = "🌉 Leyendo XLSX..."
ESTADOS_FILTER = {
    "CRITICO (>85%)": "red",
    "ELEVADO (50-85%)": "orange",
    "NORMAL (<50%)": "green"
}