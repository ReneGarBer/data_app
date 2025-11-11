WITH unpivot as (
    {% set columnas=[
        "Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio",
        "Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    %}

    {% set incluir=["'2015' as \"anio\"","municipio_num"]%}
    {{
        unpivot(
            source('raw_data','2015'),
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
    FROM unpivot
)
, remover_dups as (
    SELECT 
        DISTINCT *
    FROM remover_nulls
)

SELECT * FROM remover_dups