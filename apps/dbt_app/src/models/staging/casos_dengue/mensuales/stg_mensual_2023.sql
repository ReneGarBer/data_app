WITH pivote as (
    {% set columnas=[
        "Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio",
        "Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    %}

    {% set incluir=["'2023' as \"anio\"","municipio_num"]%}
    {{
        pivote_fila_a_columna(
            source('raw_data','2023'),
            incluir,
            columnas,
            'mes',
            'casos')
    }}
)
, remover_nulls as (
    SELECT 
        *
    FROM pivote
    WHERE casos is not null
)
, remover_dups as (
    SELECT 
        DISTINCT *
    FROM remover_nulls
)

SELECT * FROM remover_dups