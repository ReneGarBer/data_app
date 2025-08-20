WITH join_region AS (
    SELECT 
        d.id_region,
        d.estado,
        d.municipio,
        f.id_fecha_inicial,
        f.id_fecha_final,
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
        di.fecha_completa AS fecha_inicial,
        di.dia_anio AS dia_anio_inicial,
        df.fecha_completa AS fecha_final,
        df.dia_anio AS dia_anio_final,
        f.id_tipo,
        f.medicion
    FROM join_region f
    JOIN {{ref("dim_fecha")}} di ON f.id_fecha_inicial = di.id_fecha
    JOIN {{ref("dim_fecha")}} df ON f.id_fecha_final = df.id_fecha
)
SELECT 
    id_region,
    estado,
    municipio,
    fecha_inicial,
    dia_anio_inicial,
    fecha_final,
    id_tipo,
    medicion
FROM join_fecha
ORDER BY 2,3,4,5,6,7