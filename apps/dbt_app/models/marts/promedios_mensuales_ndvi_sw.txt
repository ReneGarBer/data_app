SELECT 
	r.*
	,l.ndvi
FROM
	{{source('promedios_mensuales','promedios_mensuales_ndvi')}} l 
	JOIN
	{{source('promedios_mensuales','promedios_mensuales_surfaceweather')}} r
	ON l.anio = r.anio AND l.mes = r.mes AND l.municipio_num = r.municipio_num
ORDER BY r.anio,r.mes,r.municipio_num