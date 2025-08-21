WITH pivote as (
    {% set columnas=[
        "Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio",
        "Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    %}

    {% set incluir=["'2021' as \"anio\"","municipio_num"]%}
    {{
        pivote_fila_a_columna(
            source('raw_data','2021'),
            incluir,
            columnas,
            'mes',
            'casos')
    }}
)
, remover_nulls as (
    SELECT
         anio
        ,municipio_num
        ,mes
        ,COALESCE(casos,0) casos
    FROM pivote
)
, remover_dups as (
    SELECT 
        DISTINCT *
    FROM remover_nulls
)

SELECT * FROM remover_dups