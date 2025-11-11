SELECT
     n.estado_num
    ,n.municipio_num
    ,n.fecha
    ,n.inicio
    ,n.fin
    ,n.dayl
    ,m.ndvi
    ,n.prcp 
    ,n.srad 
    ,n.swe 
    ,n.tmax
    ,n.tmin
    ,n.vp
FROM
    {{ref('stg_nasa_surface_weather_historic')}} n FULL OUTER JOIN {{ref('stg_modis_ndvi_historic')}} m
    ON n.estado_num = m.estado_num AND n.municipio_num = m.estado_num 
    AND n.fecha = m.fecha AND n.inicio::date = m.inicio::date AND n.fin::date = m.fin::date