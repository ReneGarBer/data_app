{{
    config(
        materialized='view'
    )
}}

WITH join_dim_fecha AS (
    SELECT
         l.id_medicion
        ,l.id_fecha_inicial
        ,l.id_fecha_final
        ,l.id_region
        ,l.id_tipo
        ,l.medicion
        ,r.id_fecha
        ,r.mes
        ,r.anio
    FROM
        {{ref('fac_medicion_climatica')}} l JOIN {{ref('dim_fecha')}} r
        ON l.id_fecha_inicial = r.id_fecha
)
, min_max_fecha as (
    SELECT
         id_region
        ,MIN(id_fecha_inicial) OVER (PARTITION BY anio, mes)::date fecha_inicial
        ,MAX(id_fecha_final) OVER (PARTITION BY anio, mes)::date fecha_final
        ,mes
        ,anio
        ,id_tipo
        ,medicion
    FROM
        join_dim_fecha
)
, avg as (
    SELECT
         id_region
        ,fecha_inicial
        ,fecha_final
        ,mes
        ,anio
        ,id_tipo
        ,ROUND(AVG(medicion),4) as promedio_mensual
    FROM
        min_max_fecha
    GROUP BY
        1,6,5,4,3,2

)
SELECT
    *
FROM
    avg