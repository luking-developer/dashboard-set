import polars as pl


def calcular_metricas_y_colores(df: pl.DataFrame) -> pl.DataFrame:
    # 1. Extraer Latitud y Longitud de la columna "Lat/Long"
    # El formato suele ser "latitud,longitud" (ej: -31.26,-61.43)
    df = df.with_columns(
        pl.col("Lat/Long").str.split(",").alias("coords")
    ).with_columns([
        pl.col("coords").list.get(0).cast(pl.Float64, strict=False).alias("Lat_Real"),
        pl.col("coords").list.get(1).cast(pl.Float64, strict=False).alias("Lon_Real")
    ])

    # 2. Limpieza de métricas
    df = df.with_columns([
        pl.col("Potencia total").cast(pl.Float64, strict=False).fill_null(0),
        pl.col("Energia anual total").cast(pl.Float64, strict=False).fill_null(0)
    ])
    
    # 3. Cálculo de Índice de Carga (Indice_Carga)
    df = df.with_columns(
        (pl.col("Energia anual total") / (pl.col("Potencia total").replace(0, 1) * 8.760)).alias("Indice_Carga")
    )

    # 4. Semáforo de criticidad (Ajustado a la escala 0-100)
    df = df.with_columns(
        pl.when(pl.col("Indice_Carga") < 50).then(pl.lit("green"))
        .when(pl.col("Indice_Carga") < 85).then(pl.lit("orange"))
        .otherwise(pl.lit("red")).alias("color")
    )
    
    return df