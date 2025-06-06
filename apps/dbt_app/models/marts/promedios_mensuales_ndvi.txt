SELECT 
	 CAST(EXTRACT (year FROM fecha) AS TEXT) anio
	,CAST(EXTRACT (month FROM fecha) AS TEXT) mes
	,municipio_num
	,AVG(ndvi) ndvi
FROM 
    {{source('refined','clean_modis_ndvi_historic')}}
	--refined.clean_nasa_surface_weather_historic
GROUP BY municipio_num, anio, mes
ORDER BY municipio_num, anio, mes