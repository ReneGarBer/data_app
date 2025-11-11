WITH format_columns AS (
    SELECT 
         estado_num
        ,municipio_num
        ,fecha
        ,to_timestamp(inicio::double precision/1000) as inicio
        ,to_timestamp(fin::double precision/1000) as fin
        ,ROUND(dayl,4) as dayl
        ,ROUND(prcp,4) as prcp
        ,ROUND(srad,4) as srad
        ,ROUND(swe,4) as swe
        ,ROUND(tmax,4) as tmax
        ,ROUND(tmin,4) as tmin
        ,ROUND(vp,4) as vp
    FROM {{source('medicion_climatica','nasa_surface_weather_historic')}}
), add_cadenceia as (
    SELECT
        *
        ,'1 day' as cadencia
    FROM format_columns
)
SELECT * FROM add_cadenceia