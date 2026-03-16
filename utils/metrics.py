import polars as pl


def calcular_metricas_y_colores(df: pl.DataFrame) -> pl.DataFrame:
    # 1. Cálculo del Índice de Carga (IC)
    # IC = (Energía Anual / (Potencia Total * 8760 horas)) * 100
    # Usamos fill_null(1) en Potencia para evitar división por cero
    df = df.with_columns(
        (
            (pl.col("Energia anual total") / (pl.col("Potencia total").fill_null(1) * 8.760))
        ).alias("Indice_Carga")
    )

    # 2. Definición de colores según criticidad
    # Verde: < 50% | Amarillo: 50-80% | Naranja: 80-95% | Rojo: > 95% (Sobrecarga)
    df = df.with_columns(
        pl.when(pl.col("Indice_Carga") < 50).then(pl.lit("green"))
        .when(pl.col("Indice_Carga") < 80).then(pl.lit("orange"))
        .otherwise(pl.lit("red"))
        .alias("color_critico")
    )
    return df