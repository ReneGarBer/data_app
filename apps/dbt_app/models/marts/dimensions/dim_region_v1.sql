SELECT
	{{ dbt_utils.generate_surrogate_key(['mun.cve_mun', 'edo.estado_num']) }} as id_region
    ,edo.estado_num as codigo_estado
	,mun.cve_mun as codigo_municipio
	,mun.municipio_num as codigo_completo
	,edo.nom_edo as estado
	,mun.nom_mun as municipio
FROM 
        {{source('seeds_dimensions','municipios')}} mun 
    JOIN {{source('seeds_dimensions','estados')}} edo 
	ON mun.estado_num = edo.estado_num
