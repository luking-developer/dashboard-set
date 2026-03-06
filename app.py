import streamlit as st
from st_copy import copy_button
import pandas as pd
import polars as pl
import io
from utils.strings import *

# --- Definicion de las nuevas cabeceras ---
NUEVAS_CABECERAS = new_headers

def limpiar_y_procesar_xlsx(uploaded_file: io.BytesIO) -> pl.DataFrame:
    """
    Lee un archivo XLSX, elimina las 3 primeras filas, renombra y aplica logica de relleno (fillna).
    """
    
    st.info(READING_FILE)
    
    try:
        # Usamos Pandas para la lectura de Excel: header=None, skiprows=3
        df_pd = pd.read_excel(
            uploaded_file,
            header=None,
            skiprows=3,
            engine='openpyxl',
            sheet_name=0,
            dtype={3: str}  # Forzar columna "# SET" (indice 3) como string para preservar ceros iniciales
        )
        
    except Exception as e:
        st.error(f"Error al intentar leer el archivo Excel: {e}")
        return pl.DataFrame()

    # --- A. Transformacion, Validacion y Renombramiento ---
    df_pl = pl.from_pandas(df_pd)
    
    # Validacion de Columnas
    if df_pl.shape[1] != len(NUEVAS_CABECERAS):
        st.error(f"⚠️ **ERROR:** El archivo tiene **{df_pl.shape[1]}** columnas. Se esperaban **{len(NUEVAS_CABECERAS)}**.")
        st.stop()
        
    # Renombrar las columnas
    old_col_names = [str(i) for i in range(len(NUEVAS_CABECERAS))]
    column_mapping = {old_col: new_col for old_col, new_col in zip(old_col_names, NUEVAS_CABECERAS)}
    df_final = df_pl.rename(column_mapping)
    
    # Definir columnas clave
    cols_ffill = ["Sucursal", "Area", "Distrito"]
    
    # Aplicar propagacion hacia adelante (ffill) a las columnas clave
    # Si detecta None, copia el valor inmediatamente anterior.
    for col in cols_ffill:
        # Nota: fill_null(strategy="forward") es la funcion de ffill en Polars
        df_final = df_final.with_columns(
            pl.col(col).fill_null(strategy="forward")
        )

    # Relleno condicional para el resto de columnas
    
    # Identificar columnas numericas vs. de string
    # Polars infiere tipos durante la conversion de Pandas.
    
    # a) Columnas que deben rellenarse con 0 (Numericas)
    # Buscamos columnas que sean de tipo Numerico (Integer o Float) Y que NO sean las de ffill
    numerical_cols = [
        name for name, dtype in df_final.schema.items() 
        if dtype in {pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64}
        and name not in cols_ffill
    ]
    
    # b) Columnas que deben MANTENER los nulls (Strings/Otros)
    # Buscamos columnas que NO sean numericas Y NO sean las de ffill.
    string_like_cols = [
        name for name, dtype in df_final.schema.items() 
        if dtype not in {pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64}
        and name not in cols_ffill
    ]

    # Aplicar relleno con 0 a todas las columnas numericas
    df_final = df_final.with_columns(
        [pl.col(col).fill_null(0) for col in numerical_cols]
    )

    # Para string_like_cols (como Descripciones, Domicilio, etc.): 
    # Dejamos la operacion de .fill_null() fuera. Polars mantiene los valores Null/None
    # por defecto si no se les aplica ninguna funcion de relleno.

    # 4. Forzar el tipo de dato de las columnas de String/Categoria si Polars las dejo como Int/Float.
    # Esto es una limpieza extra para evitar que, si una columna de string tiene muchos None,
    # Polars la haya inferido como numerica.
    for col in string_like_cols:
         df_final = df_final.with_columns(pl.col(col).cast(pl.String))
    
    # Forzar "# SET" como string para preservar ceros iniciales
    df_final = df_final.with_columns(pl.col("# SET").cast(pl.String))
         
    # 5. Volver a propagar por si la conversion de Pandas dejo los None como None String.
    # Este paso es una doble comprobacion de robustez, no deberia ser estrictamente necesario.
    for col in cols_ffill:
        df_final = df_final.with_columns(
            pl.col(col).fill_null(strategy="forward")
        )
         
    return df_final

def buscar_primer_hueco(lista_sets, inicio_rango):
    """
    Encuentra el primer numero faltante en una secuencia.
    Si no hay huecos, devuelve el maximo + 1.
    Si la lista esta vacia, devuelve el inicio del rango.
    """
    if not lista_sets:
        return inicio_rango
    
    conjunto_sets = set(lista_sets)
    min_val = min(lista_sets)
    max_val = max(lista_sets)
    
    # Checkear si falta el numero inicial del rango
    if min_val > inicio_rango:
        return inicio_rango

    # Buscar el primer hueco entre el minimo y el maximo existente
    for i in range(min_val, max_val + 1):
        if i not in conjunto_sets:
            return i
            
    # Si no hay huecos, el siguiente es el maximo + 1
    return max_val + 1

# --- 4. Aplicacion Streamlit y Mecanismo de Carga ---
st.set_page_config(layout="wide", page_title="SETs EPE", page_icon="⚡")
st.title(APP_TITLE)
st.markdown("---")

st.info(APP_EXPLANATION)
uploaded_file = st.file_uploader(
    UPLOAD_MSG, 
    # La manera de cargar el archivo con Streamlit, aceptando .xlsx y .xls
    type=upload_format 
)

if uploaded_file is not None:
    # uploaded_file es un objeto de tipo BytesIO, que pd.read_excel puede leer directamente.
    
    try:
        # Procesar
        df_procesado = limpiar_y_procesar_xlsx(uploaded_file)
        
        if not df_procesado.is_empty():
            st.success(PROCESSING_SUCCESSFULLY)
            
            # Ancla para las metricas
            st.markdown('<div id="free_sets"></div>', unsafe_allow_html=True)
            
            # Calcular siguientes numeros libres para # SET
            set_values = df_procesado.select("# SET").to_series().drop_nulls().unique().to_list()
            # Filtrar codigos validos de 8 digitos
            valid_sets = [s for s in set_values if isinstance(s, str) and len(s) == 8 and s.isdigit()]
            
            # --- Calculo de huecos en numeracion ---
            set_values = df_procesado.select("# SET").to_series().drop_nulls().unique().to_list()
            valid_sets = [int(s) for s in set_values if isinstance(s, str) and len(s) == 8 and s.isdigit()]
            
            # Clasificacion por rango (Urbano < ...5000, Rural >= ...5000)
            # Asumimos prefijo de area (ej: 0824) y sufijo de tipo
            urbano_list = [s for s in valid_sets if (s % 10000) < 5000]
            rural_list = [s for s in valid_sets if (s % 10000) >= 5000]

            # Determinar base de numeracion (prefijo) del archivo actual
            # Si no hay datos, usamos valores por defecto
            base_prefix = (valid_sets[0] // 10000) * 10000 if valid_sets else 8240000 
            
            # Urbano
            next_urbano = buscar_primer_hueco(urbano_list, base_prefix + 1)
            
            # Rural
            next_rural = buscar_primer_hueco(rural_list, base_prefix + 5001)
            
            free_sets = st.subheader(FREE_SETS_AVAILABLE, anchor="free_sets")

            col_urbano, col_rural = st.columns(2)
            with col_urbano:
                col_data_urbano, col_copy_urbano = st.columns([10, 1])
                with col_data_urbano:
                    set_urbano = f"{next_urbano:08d}"
                    st.metric(label=URBAN_LABEL, value=set_urbano, border=True)
                with col_copy_urbano:
                    copy_urbano = copy_button(
                        set_urbano,
                        tooltip=COPY_URBAN,
                        copied_label=COPIED,
                        icon="st",
                    )
                
            with col_rural:
                col_data_rural, col_copy_rural = st.columns([10, 1])
                with col_data_rural:
                    set_rural = f"{next_rural:08d}"
                    st.metric(label=RURAL_LABEL, value=set_rural, border=True)
                with col_copy_rural:
                    copy_rural = copy_button(
                        set_rural,
                        tooltip=COPY_RURAL,
                        copied_label=COPIED,
                        icon="st",
                    )
            
            # Mostrar el DataFrame de Polars en Streamlit
            df_procesado = df_procesado.slice(0, df_procesado.height - 1)
            df_pandas = df_procesado.to_pandas()
            df_pandas["# SET"] = df_pandas["# SET"].astype(str)
            st.dataframe(df_pandas, hide_index=True)
            
            st.download_button(
                label=DOWNLOAD_DATA,
                data=df_procesado.write_csv(None), # Polars escribe el CSV en memoria (buffer)
                file_name=DOWNLOAD_FILENAME,
                mime='text/csv',
            )
            
    except Exception as e:
        st.error(f"Un error inesperado detuvo el procesamiento: {e}")