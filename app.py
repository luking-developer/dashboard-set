import streamlit as st
from st_copy import copy_button
import pandas as pd
import polars as pl
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

# Function to generate and inject JavaScript for scrolling
def scroll_to_anchor(anchor_id):
    # This JS script runs when the button is clicked and the page reruns
    js_script = f"""
    <script>
        var element = document.getElementById('{anchor_id}');
        if (element) {{
            element.scrollIntoView({{ behavior: 'smooth' }});
        }}
    </script>
    """
    st.markdown(js_script, unsafe_allow_html=True)

def limpiar_y_procesar_xlsx(uploaded_file: io.BytesIO) -> pl.DataFrame:
    """
    Lee un archivo XLSX, elimina las 3 primeras filas, renombra y aplica lógica de relleno (fillna).
    """
    
    st.info("🌉 Leyendo XLSX...")
    
    try:
        # Usamos Pandas para la lectura de Excel: header=None, skiprows=3
        df_pd = pd.read_excel(
            uploaded_file,
            header=None,
            skiprows=3,
            engine='openpyxl',
            sheet_name=0,
            dtype={3: str}  # Forzar columna "# SET" (índice 3) como string para preservar ceros iniciales
        )
        
    except Exception as e:
        st.error(f"Error al intentar leer el archivo Excel: {e}")
        return pl.DataFrame()

    # --- A. Transformación, Validación y Renombramiento ---
    df_pl = pl.from_pandas(df_pd)
    
    # 1. Validación de Columnas
    if df_pl.shape[1] != len(NUEVAS_CABECERAS):
        st.error(f"⚠️ **FALLO CRÍTICO DE FORMATO.** El archivo tiene **{df_pl.shape[1]}** columnas. Se esperaban **{len(NUEVAS_CABECERAS)}**.")
        st.stop()
        
    # 2. Renombrar las columnas
    old_col_names = [str(i) for i in range(len(NUEVAS_CABECERAS))]
    column_mapping = {old_col: new_col for old_col, new_col in zip(old_col_names, NUEVAS_CABECERAS)}
    df_final = df_pl.rename(column_mapping)
    
    # --- B. Lógica de Relleno (Fill Null) con Polars ---
    st.info("🧠 Aplicando tareas y calculando números de SETs disponibles...")
    
    # 1. Definir columnas clave
    cols_ffill = ["Sucursal", "Area", "Distrito"]
    
    # 2. Aplicar Propagación Hacia Adelante (ffill) a las columnas clave
    # Si detecta None, copia el valor inmediatamente anterior.
    for col in cols_ffill:
        # Nota: fill_null(strategy="forward") es la función de ffill en Polars
        df_final = df_final.with_columns(
            pl.col(col).fill_null(strategy="forward")
        )

    # 3. Relleno Condicional para el RESTO de columnas
    
    # Identificar columnas numéricas vs. de string
    # Polars infiere tipos durante la conversión de Pandas.
    
    # a) Columnas que deben rellenarse con 0 (Numéricas)
    # Buscamos columnas que sean de tipo Numérico (Integer o Float) Y que NO sean las de ffill
    numerical_cols = [
        name for name, dtype in df_final.schema.items() 
        if dtype in {pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64}
        and name not in cols_ffill
    ]
    
    # b) Columnas que deben MANTENER los nulls (Strings/Otros)
    # Buscamos columnas que NO sean numéricas Y NO sean las de ffill.
    string_like_cols = [
        name for name, dtype in df_final.schema.items() 
        if dtype not in {pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.Float32, pl.Float64}
        and name not in cols_ffill
    ]

    # Aplicar relleno con 0 a todas las columnas numéricas
    df_final = df_final.with_columns(
        [pl.col(col).fill_null(0) for col in numerical_cols]
    )

    # Para string_like_cols (como Descripciones, Domicilio, etc.): 
    # Dejamos la operación de .fill_null() fuera. Polars mantiene los valores Null/None
    # por defecto si no se les aplica ninguna función de relleno.

    # 4. Forzar el tipo de dato de las columnas de String/Categoría si Polars las dejó como Int/Float.
    # Esto es una limpieza extra para evitar que, si una columna de string tiene muchos None,
    # Polars la haya inferido como numérica.
    for col in string_like_cols:
         df_final = df_final.with_columns(pl.col(col).cast(pl.String))
    
    # Forzar "# SET" como string para preservar ceros iniciales
    df_final = df_final.with_columns(pl.col("# SET").cast(pl.String))
         
    # 5. Volver a propagar por si la conversión de Pandas dejó los None como None String.
    # Este paso es una doble comprobación de robustez, no debería ser estrictamente necesario.
    for col in cols_ffill:
        df_final = df_final.with_columns(
            pl.col(col).fill_null(strategy="forward")
        )
         
    return df_final

# --- 4. Aplicación Streamlit y Mecanismo de Carga ---
st.set_page_config(layout="wide", page_title="SETs EPE", page_icon="⚡")
st.title("⚡ EPE - Sub Estaciones Transformadoras")
st.markdown("---")

st.markdown("Sube tu archivo de reporte de SETs obteniéndolo desde la aplicación de **Reportes de EPE**, menú _**`Líneas y SETs > SETs por Área`**_ y luego pulsando el cuarto botón **Export report** en **formato XLSX**.")
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
            st.success("✅ Procesamiento exitoso.")
            
            # Ancla para las métricas
            st.markdown('<div id="free_sets"></div>', unsafe_allow_html=True)
            
            # Calcular siguientes números libres para # SET
            set_values = df_procesado.select("# SET").to_series().drop_nulls().unique().to_list()
            # Filtrar códigos válidos de 8 dígitos
            valid_sets = [s for s in set_values if isinstance(s, str) and len(s) == 8 and s.isdigit()]
            
            # Urbano
            urbano_sets = [int(s) for s in valid_sets if s[-4] < '5']
            next_urbano = max(urbano_sets) + 1 if urbano_sets else 10000000
            
            # Rural
            rural_sets = [int(s) for s in valid_sets if s[-4] == '5']
            next_rural = max(rural_sets) + 1 if rural_sets else 50000000
            
            free_sets = st.subheader("Números de SET disponibles", anchor="free_sets")
            # Agregar CSS global para posicionar los botones
            st.markdown("""
                <style>
                .metric-container .stElementContainer {
                    position: absolute !important;
                    top: 0 !important;
                    right: 0 !important;
                    z-index: 10 !important;
                }
                </style>
                """, unsafe_allow_html=True)
            col_urbano, col_rural = st.columns(2)
            with col_urbano:
                set_urbano = f"{next_urbano:08d}"
                copy_urbano = copy_button(
                    set_urbano,
                    tooltip="Copiar SET Urbana",
                    copied_label="Copiado!",
                    icon="st",
                )
                st.markdown("""
                    <div class="metric-container" style="position: relative; border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 8px 0; background-color: #f9f9f9;">
                      {}
                      <div style="font-size: 14px; color: #666;">🚗 # SET Urbana disponible</div>
                      <div style="font-size: 24px; font-weight: bold; margin: 8px 0;">{}</div>
                    </div>
                    <script>
                        let metric = document.currentScript.parentElement;
                        let parent = metric.parentElement;
                        let button = parent.querySelector('.stElementContainer');
                        if (button) {{
                            metric.appendChild(button);
                            button.style.position = 'absolute';
                            button.style.top = '8px';
                            button.style.right = '8px';
                            button.style.zIndex = '10';
                        }}
                    </script>
                    """.format(copy_urbano, set_urbano), unsafe_allow_html=True
                )
            with col_rural:
                set_rural = f"{next_rural:08d}"
                copy_rural = copy_button(
                    set_rural,
                    tooltip="Copiar SET Rural",
                    copied_label="Copiado!",
                    icon="st",
                )
                st.markdown("""
                    <div class="metric-container" style="position: relative; border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 8px 0; background-color: #f9f9f9;">
                    {}
                    <div style="font-size: 14px; color: #666;">🚜 # SET Rural disponible</div>
                    <div style="font-size: 24px; font-weight: bold; margin: 8px 0;">{}</div>
                    </div>
                    """.format(copy_rural, set_rural), unsafe_allow_html=True
                )

            scroll_to_anchor("free_sets")
            
            # Script para hacer scroll hasta las métricas
            st.markdown('<script>document.getElementById("free_sets").scrollIntoView();</script>', unsafe_allow_html=True)
            
            # Mostrar el DataFrame de Polars en Streamlit
            df_pandas = df_procesado.to_pandas()
            df_pandas["# SET"] = df_pandas["# SET"].astype(str)
            st.dataframe(df_pandas)
            
            st.download_button(
                label="💾 Descargar datos",
                data=df_procesado.write_csv(None), # Polars escribe el CSV en memoria (buffer)
                file_name='reporte_sets.csv',
                mime='text/csv',
            )
            
    except Exception as e:
        st.error(f"Un error inesperado detuvo el procesamiento: {e}")