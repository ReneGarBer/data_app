SELECT
	 mun.codigo_completo as id_region
	,edo.codigo_estado
	,mun.codigo_municipio
	,edo.estado
	,mun.municipio
FROM 
        {{ref('stg_estados')}} edo
    JOIN {{ref('stg_municipios')}} mun
	ON mun.codigo_estado = edo.codigo_estado
