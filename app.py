import io
import warnings

import folium
import pandas as pd
import polars as pl
import streamlit as st
from st_copy import copy_button
from streamlit_folium import st_folium

from utils.metrics import calcular_metricas_y_colores
from utils.qr_code import generar_qr_base64
from utils.sets import buscar_primer_hueco
from utils.strings import *
from utils.uploaded_file import limpiar_y_procesar_xlsx

# Silenciar advertencia de estilos de Excel
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

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
            # 1. Ejecutar cálculos de carga y colores
            df_procesado = calcular_metricas_y_colores(df_procesado)

            # 2. Renderizar Mapa
            st.subheader("📍 Mapa de SETs")
            df_mapa = df_procesado.filter(pl.col("X").is_not_null() & pl.col("Y").is_not_null())

            if not df_mapa.is_empty():
                # Crear el objeto mapa centrado
                m = folium.Map(location=[df_mapa["Y"].mean(), df_mapa["X"].mean()], zoom_start=13)
                
                for row in df_mapa.to_dicts():
                    # Crear link para el QR
                    link = f"https://www.google.com/maps?q={row['Y']},{row['X']}"
                    qr_b64 = generar_qr_base64(link)
                    
                    popup_html = f"""
                    <div style="font-family:sans-serif; width:160px;">
                        <b style="color:#1f77b4;">SET {row['# SET']}</b><br>
                        <b>Carga:</b> {row['Indice_Carga']:.1f}%<br>
                        <hr>
                        <img src="data:image/png;base64,{qr_b64}" width="100" style="display:block;margin:auto;">
                        <p style="font-size:10px;text-align:center;">Escanear para GPS</p>
                    </div>
                    """
                    
                    folium.CircleMarker(
                        location=[row["Y"], row["X"]],
                        radius=7,
                        color=row["color_critico"],
                        fill=True,
                        popup=folium.Popup(popup_html, max_width=200)
                    ).add_to(m)
                
                # Mostrar mapa en Streamlit
                st_folium(m, width=1000, height=500, returned_objects=[])
            else:
                st.warning("No se encontraron coordenadas válidas para generar el mapa.")

            # 3. Mostrar tabla de datos al final
            st.dataframe(df_procesado.to_pandas(), hide_index=True)
            
            st.download_button(
                label=DOWNLOAD_DATA,
                data=df_procesado.write_csv(None), # Polars escribe el CSV en memoria (buffer)
                file_name=DOWNLOAD_FILENAME,
                mime='text/csv',
            )
            
    except Exception as e:
        st.error(f"Un error inesperado detuvo el procesamiento: {e}")