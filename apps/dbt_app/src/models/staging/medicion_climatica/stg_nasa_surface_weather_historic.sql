WITH pivote AS (
    {% set columnas=[
          "dayl"
        , "prcp"
        , "srad"
        , "swe"
        , "tmax"
        , "tmin"
        , "vp"] 
    %}
    {% set incluir=[
         "estado_num"
        ,"municipio_num"
        ,"municipio"
        ,"fecha"
        ,"inicio"
        ,"fin"]
    %}
    {{  
        pivote_fila_a_columna(
             source('medicion_climatica','nasa_surface_weather_historic')
            ,incluir
            ,columnas
            ,'tipo'
            ,'valor'
        )
    }}
)
, no_nulls AS (
    SELECT
          estado_num
        , municipio_num
        , municipio
        , fecha
        , inicio
        , fin
        , tipo
        , valor
    FROM
        pivote
    WHERE
        valor is not null
)
, no_dups AS (
    SELECT
        DISTINCT *
    FROM
        no_nulls
)
, format_fechas AS (
    SELECT
          estado_num
        , municipio_num
        , municipio
        , fecha
        , to_timestamp(inicio::double precision/1000) as inicio
        , to_timestamp(fin::double precision/1000) as fin
        , tipo
        , valor    
    FROM
        no_dups
)

SELECT 
     *
    ,'1 day' as cadencia    
FROM format_fechas