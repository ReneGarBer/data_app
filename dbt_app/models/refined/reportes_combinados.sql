{% set reportes = []  %}
{% set fuente = "reportes" %}
{% for source in graph.sources.values() %}
    {% if source.source_name == fuente %}
        {% do reportes.append(source.name) %}
    {% endif %}
{% endfor %}

WITH combined_data AS (
    {% for reporte in reportes %}
    {% set anio = reporte[-4:] %}
    SELECT 
        {{anio}} as anio
        ,*
    FROM {{ source(fuente,reporte) }}
    {% if not loop.last %}
    UNION ALL
    {% endif %}
    {% endfor %}
)
{% set meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]%}
SELECT 
    a.anio
    ,t.cvegeoedo
    ,t.cve_mun
    ,t.nom_mun AS municipio
    ,a."Indicador" AS indicador
    ,a."Unidad de Medida" AS unidad_de_medida ,
    {% for mes in meses %}
        COALESCE(a."{{mes}}",0) as {{ mes }}{% if not loop.last %}, {% endif %}
    {% endfor %}
FROM combined_data a
    JOIN ( 
        SELECT
            cvegeoedo
            ,cvegeomuni::int
            ,cve_mun
            ,nom_mun
	FROM {{source("geografica","municipios")}} 
	WHERE cvegeoedo = '14') t 
    ON t.cvegeomuni = a.cvegeomuni
ORDER BY a.anio,a.cvegeomuni