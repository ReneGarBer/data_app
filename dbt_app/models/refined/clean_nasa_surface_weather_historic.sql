{{
	config(
		materialized='incremental',
		unique_key= ['municipio_num','inicio','fin']
	)
}}

SELECT
	estado_num,
	municipio_num,
	municipio,
	TO_DATE(fecha,'YYYYMMDD') as fecha,
	to_timestamp(inicio::BIGINT/1000) as inicio,
	to_timestamp(fin::BIGINT/1000) as fin,
	dayl,
	prcp,
	srad,
	swe,
	tmax,
	tmin,
	vp,
	EXTRACT(week FROM fecha::DATE) as num_de_semana	
FROM
	{{source('historic','nasa_surface_weather_historic')}}