import io

import pandas as pd
import polars as pl
import streamlit as st

from utils.strings import NEW_HEADERS, READING_FILE


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
    if df_pl.shape[1] != len(NEW_HEADERS):
        st.error(f"⚠️ **ERROR:** El archivo tiene **{df_pl.shape[1]}** columnas. Se esperaban **{len(NEW_HEADERS)}**.")
        st.stop()
        
    # Renombrar las columnas
    old_col_names = [str(i) for i in range(len(NEW_HEADERS))]
    column_mapping = {old_col: new_col for old_col, new_col in zip(old_col_names, NEW_HEADERS)}
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