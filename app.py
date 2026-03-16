import io
import warnings

import folium
import pandas as pd
import polars as pl
import streamlit as st
from st_copy import copy_button
from streamlit_folium import st_folium

from utils.filters import show_filter
from utils.metrics import calcular_metricas_y_colores
from utils.qr_code_handler import generar_qr_base64
from utils.sets import buscar_primer_hueco
from utils.strings import *
from utils.uploaded_file import limpiar_y_procesar_xlsx

# Silenciar advertencia de estilos de Excel
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# --- Aplicacion Streamlit y Mecanismo de Carga ---
st.set_page_config(layout="wide", page_title="SETs EPE", page_icon="⚡")
st.title(APP_TITLE)
st.markdown("---")

st.text(UPLOAD_MSG)
col_1, col_2 = st.columns([3.5, 4.5])
with col_1:
    uploaded_file = st.file_uploader(
        label=UPLOAD_MSG,
        label_visibility="collapsed",
        # La manera de cargar el archivo con Streamlit, aceptando .xlsx y .xls
        type=upload_format 
    )

with col_2:
    st.info(APP_EXPLANATION)

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

            if "coords" in df_procesado.columns:
                df_procesado = df_procesado.drop("coords")

            df_mapa = df_procesado.filter(
                pl.col("Lat_Real").is_not_null() & 
                pl.col("Lon_Real").is_not_null()
            )

            if not df_mapa.is_empty():
                # 2. Renderizar Mapa
                st.subheader("📍 Mapa de estado de red")
                df_mapa = show_filter(df_mapa)

                cantidad_registros = df_mapa.height
                with st.spinner(f"Procesando {cantidad_registros} registros y generando mapa interactivo..."):
                    # 1. Configuración base
                    c_lat, c_lon = df_mapa["Lat_Real"].mean(), df_mapa["Lon_Real"].mean()
                    m = folium.Map(location=[c_lat, c_lon], zoom_start=14, prefer_canvas=False)

                    for row in df_mapa.to_dicts():
                        lat, lon = row["Lat_Real"], row["Lon_Real"]
                        nombre_set = str(row['# SET'])
                        indice_carga = round(row.get("Indice_Carga", 0), 2)

                        if indice_carga is None:
                            indice_carga = 0
                        
                        # Generar QR
                        qr_link = f"https://www.google.com/maps?q={lat},{lon}"
                        qr_img = generar_qr_base64(qr_link)
                        
                        # HTML del Popup simplificado al máximo
                        # Usamos comillas simples para evitar conflictos con el JS interno de Folium
                        popup_html = f"""
                        <div style='width:160px; text-align:center; font-family:sans-serif;'>
                            <b>SET {nombre_set}</b><br>
                            Carga: {indice_carga:.2f}%<br>
                            <hr style='margin:5px;'>
                            <img src='data:image/png;base64,{qr_img}' width='100'><br>
                            <a href='{qr_link}' target='_blank' style='font-size:10px;'>Abrir Maps</a>
                        </div>
                        """
                        
                        # 2. El Marcador Circular
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=9,
                            color=row.get("color", "blue"),
                            fill=True,
                            fill_opacity=0.8,
                            popup=folium.Popup(popup_html, max_width=200),
                            # Tooltip que se comporta como etiqueta pero es más ligero
                            tooltip=folium.Tooltip(f"SET {nombre_set}", permanent=False) 
                        ).add_to(m)

                        # 3. Etiqueta de texto (Recuperada)
                        # La dejamos fija para asegurar que el sistema funciona primero
                        folium.map.Marker(
                            [lat, lon],
                            icon=folium.DivIcon(
                                icon_size=(150,36),
                                icon_anchor=(0,0),
                                html=f'<div style="font-size: 9pt; font-weight: bold; color: black; text-shadow: 1px 1px white;">{nombre_set}</div>',
                            )
                        ).add_to(m)

                    # 4. Renderizado con Key única para forzar actualización
                    st_folium(
                        m, 
                        width="100%", 
                        height=600, 
                        returned_objects=[], 
                        key="mapa_final_v1"
                    )
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