WITH no_nulls AS (
    SELECT
         estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , ndvi
    FROM
        {{ source('medicion_climatica','modis_ndvi_historic')}}
    WHERE
        ndvi is not NULL
)
, remover_dups AS (
    SELECT
        DISTINCT *
    FROM
        no_nulls
)
, format_fechas AS (
    SELECT
          estado_num
        , municipio_num
        , fecha
        , to_timestamp(inicio::double precision/1000) as inicio
        , to_timestamp(fin::double precision/1000) as fin
        , ndvi
    FROM
        remover_dups
)
, renombrar_columnas AS (
    SELECT
          estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , 'ndvi' as tipo
        , ndvi as valor
    FROM
        format_fechas
)
SELECT 
     *
    ,'1 day' as cadencia
FROM renombrar_columnas