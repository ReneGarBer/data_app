WITH join_dims AS (
    SELECT 
        f.id_region,
        dr.estado,
        dr.municipio,
        dfi.anio AS anio_inicio,
        dfi.mes AS mes_inicio,
        dfi.fecha_completa AS fecha_inicio,
        dff.anio AS anio_fin,
        dff.mes AS mes_fin,
        dff.fecha_completa AS fecha_fin,
        f.casos
    FROM  {{ref("fac_casos_dengue")}} f
    JOIN {{ref("dim_region")}} dr ON f.id_region = dr.id_region
    JOIN {{ref("dim_fecha")}} dfi ON f.id_fecha_inicial = dfi.id_fecha
    JOIN {{ref("dim_fecha")}} dff ON f.id_fecha_final = dff.id_fecha
), lag AS (
    SELECT
        id_region,
        estado,
        municipio,
        anio_inicio,
        mes_inicio,
        fecha_inicio,
        anio_fin,
        mes_fin,
        fecha_fin,
        casos,
        COALESCE(lag(casos) OVER (PARTITION BY id_region, anio_inicio ORDER BY anio_inicio, mes_inicio),0) AS casos_lag
    FROM join_dims
), fix_mes_12 AS (
    SELECT
        id_region,
        estado,
        municipio,
        anio_inicio,
        mes_inicio,
        fecha_inicio,
        anio_fin,
        mes_fin,
        fecha_fin,
        casos_lag,
        CASE
        WHEN (casos < casos_lag) THEN casos_lag
        ELSE casos
        END AS casos_acumulados
    FROM lag
), substract AS (
    SELECT
        id_region,
        estado,
        municipio,
        anio_inicio as anio,
        mes_inicio as mes,
        fecha_inicio as inicio_de_mes,
        fecha_fin as fin_de_mes,
        casos_acumulados,
        (casos_acumulados - casos_lag) AS casos
    FROM fix_mes_12
)
SELECT * FROM substract
ORDER BY 1,2,3,4