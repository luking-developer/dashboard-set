import streamlit as st
import polars as pl
import pandas as pd
import io

# --- 1. Definición de las nuevas cabeceras (28 elementos) ---
NUEVAS_CABECERAS = [
    "Sucursal", "Area", "Distrito", "# SET", "Antifraude", "Convencional", 
    "Preensamblado", "Subterraneo", "Total", "Total clientes BT", 
    "Potencia total", "Cantidad trafos", "Codigo ET", "Codigo distribuidor", 
    "Descripciones", "Domicilio", "Estado topologia", "Tipo SET", "Subtipo SET", 
    "Urbana/Rural", "X", "Y", "Lat/Long", "Energia anual total", 
    "Energia anual comercial", "Energia anual residencial", 
    "Energia anual Industrial", "Energia anual otros"
]

def limpiar_y_procesar_xlsx(uploaded_file: io.BytesIO) -> pl.DataFrame:
    """
    Lee un archivo XLSX, elimina las 3 primeras filas y renombra las cabeceras con Polars.
    """
    
    st.info("🌉 Leyendo el archivo XLSX y omitiendo las 3 primeras filas...")
    
    try:
        # Usamos Pandas como puente robusto para la lectura de Excel.
        # header=None: Le dice a Pandas que no use ninguna fila como cabecera.
        # skiprows=3: Omite las primeras 3 filas del archivo.
        df_pd = pd.read_excel(
            uploaded_file,
            header=None,
            skiprows=3,
            engine='openpyxl',
            sheet_name=0 # Asume la primera hoja (índice 0)
        )
        
    except Exception as e:
        st.error(f"Error al intentar leer el archivo Excel: {e}")
        return pl.DataFrame()

    # --- C. Transformación y Limpieza con Polars (La Fuerza) ---
    st.info("💪 Pasando a Polars para validación y reestructuración...")
    
    # 1. Convertir a Polars
    df_pl = pl.from_pandas(df_pd)
    
    # 2. Validación de Columnas
    if df_pl.shape[1] != len(NUEVAS_CABECERAS):
        st.error(f"⚠️ **FALLO CRÍTICO DE FORMATO.**")
        st.error(f"El archivo subido tiene **{df_pl.shape[1]}** columnas después de la limpieza. Se esperaban **{len(NUEVAS_CABECERAS)}** columnas.")
        st.stop()
        
    # 3. Preparar el Renombramiento
    # Pandas, al usar header=None, nombra las columnas como 0, 1, 2, ...
    # Polars hereda estos nombres como strings '0', '1', '2', ...
    old_col_names = [str(i) for i in range(len(NUEVAS_CABECERAS))]
    column_mapping = {old_col: new_col for old_col, new_col in zip(old_col_names, NUEVAS_CABECERAS)}
    
    # 4. Renombrar las columnas
    df_final = df_pl.rename(column_mapping)
    
    return df_final


# --- 4. Aplicación Streamlit y Mecanismo de Carga ---

st.title("Polars/Streamlit: Procesador de Datos XLSX")
st.markdown("---")

uploaded_file = st.file_uploader(
    "Sube tu archivo XLSX con la tabla de datos", 
    # La manera de cargar el archivo con Streamlit, aceptando .xlsx y .xls
    type=['xlsx', 'xls'] 
)

if uploaded_file is not None:
    # uploaded_file es un objeto de tipo BytesIO, que pd.read_excel puede leer directamente.
    
    try:
        # Procesar
        df_procesado = limpiar_y_procesar_xlsx(uploaded_file)
        
        if not df_procesado.is_empty():
            st.success("✅ Procesamiento exitoso. Datos listos en Polars.")
            st.subheader("Datos Limpios (Primeras 5 Filas)")
            
            # Mostrar el DataFrame de Polars en Streamlit
            st.dataframe(df_procesado.to_pandas().head())
            
            st.download_button(
                label="Descargar Datos Limpios (CSV)",
                data=df_procesado.write_csv(None), # Polars escribe el CSV en memoria (buffer)
                file_name='datos_limpios.csv',
                mime='text/csv',
            )
            
    except Exception as e:
        st.error(f"Un error inesperado detuvo el procesamiento: {e}")