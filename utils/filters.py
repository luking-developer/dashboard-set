import polars as pl
import streamlit as st

from utils.strings import ESTADOS_FILTER


def on_filter_change():
    curr = st.session_state.main_filter_widget
    if "TODOS" in curr and len(curr) > 1:
        if curr[-1] == "TODOS":
            st.session_state.main_filter_widget = ["TODOS"]
        else:
            st.session_state.main_filter_widget = [
                f for f in curr if f != "TODOS"
            ]

def show_filter(df):
    with st.expander("🔍 Filtros y búsqueda", expanded=False):
        col_1, col_2 = st.columns([5, 3])

        with col_1:
            f_estado = st.multiselect(
                "Estado de carga",
                options=list(ESTADOS_FILTER.keys()),
                default=list(ESTADOS_FILTER.keys())
            )
            colores_sel = [ESTADOS_FILTER[e] for e in f_estado]

        with col_2:
            search_query = st.text_input("🔎 Búsqueda global")

    # 3. Aplicar Filtros al DataFrame
    df_filtrado = df.filter(
        (pl.col("color").is_in(colores_sel))
    )

    return df_filtrado