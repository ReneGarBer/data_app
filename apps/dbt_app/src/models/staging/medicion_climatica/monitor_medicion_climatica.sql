WITH jalisco AS (
	SELECT
		 municipio_num
	FROM
		{{source('seeds_dimensions','municipios')}}
	WHERE
		municipio_num like '14%'
)
, calendario AS (
	SELECT
		TO_CHAR(generate_series(
			'2010-01-01'::date,
			'2025-01-01'::date,
			interval '1 month')::date,'YYYY') fecha
)
, cross_join AS (
	SELECT 
		* 
	FROM jalisco CROSS JOIN calendario
	ORDER BY 1,2
)
, missing_years_nasa AS (
	SELECT
		 DISTINCT c.*
		 ,'nasa_surface_weather_historic' as "fuente"
	FROM
		cross_join c LEFT JOIN {{ source('medicion_climatica','nasa_surface_weather_historic') }} r
		ON c.municipio_num = r.municipio_num AND c.fecha = TO_CHAR(r.fecha::date,'YYYY')
	WHERE
		r.municipio_num is null or r.fecha is null
)
, mising_years_modis AS (
	SELECT
		 DISTINCT c.*
		 ,'modis_ndvi_historic' as "fuente"
	FROM
		cross_join c LEFT JOIN  {{ source('medicion_climatica','modis_ndvi_historic') }} r
		ON c.municipio_num = r.municipio_num AND c.fecha = TO_CHAR(r.fecha::date,'YYYY')
	WHERE
		r.municipio_num is null or r.fecha is null
)

SELECT
	*
FROM 
	missing_years_nasa

UNION ALL

SELECT
	*
FROM 
	mising_years_modis