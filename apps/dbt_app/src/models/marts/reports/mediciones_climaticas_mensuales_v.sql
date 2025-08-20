WITH join_region AS (
    SELECT 
        d.id_region,
        d.estado,
        d.municipio,
        f.id_fecha_inicial,
        f.id_tipo,
        f.medicion
    FROM {{ref("fac_medicion_climatica")}} f
        JOIN {{ref("dim_region")}} d ON f.id_region = d.id_region
    WHERE (f.cadencia = '1 day'::text)
), join_fecha AS (
    SELECT 
        f.id_region,
        f.estado,
        f.municipio,
        d.anio as anio,
        d.mes as mes,
        d.fecha_completa AS fecha,
        f.id_tipo,
        f.medicion
    FROM join_region f
    JOIN {{ref("dim_fecha")}} d ON f.id_fecha_inicial = d.id_fecha
), avg_semanal AS (
    SELECT
        id_region,
        estado,
        municipio,
        anio,
        mes,
        MIN(fecha) fecha_inicial,
        MAX(fecha) fecha_final,
        id_tipo,
        ROUND(AVG(medicion),4) as promedio_mensual
    FROM join_fecha
    GROUP BY 1,2,3,4,5,8
)
SELECT 
    *
FROM avg_semanal
ORDER BY 2,3,4,5,8