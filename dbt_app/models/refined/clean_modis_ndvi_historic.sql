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
	TO_DATE(fecha,'YYY-MM-DD') as fecha,
	to_timestamp(inicio::BIGINT/1000) as inicio,
	to_timestamp(fin::BIGINT/1000) as fin,
	ndvi,
	EXTRACT(week FROM fecha::DATE) as num_de_semana	
FROM
	{{source('historic','modis_ndvi_historic')}}
WHERE ndvi is not null
