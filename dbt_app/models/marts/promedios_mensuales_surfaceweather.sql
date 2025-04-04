SELECT 
	 CAST(EXTRACT (year FROM fecha) AS TEXT) anio
	,CAST(EXTRACT (month FROM fecha) AS TEXT) mes
	,municipio_num
	,AVG(dayl) dayl
	,AVG(prcp) prcp
	,AVG(srad) srad
	,AVG(swe) swe
	,AVG(tmax) tmax
	,AVG(tmin) tmin
	,AVG(vp) vp
FROM 
    {{source('refined','clean_nasa_surface_weather_historic')}}
GROUP BY municipio_num, anio, mes
ORDER BY municipio_num, anio, mes