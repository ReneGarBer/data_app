With union_all_monthly AS (
    {% set anios= range(2010,2025)%}
    {% for anio in anios %}
        {% set model_name= 'stg_mensual_' ~ anio %}
        SELECT
            *
            ,'1 month' as cadencia
        FROM
            {{ ref(model_name) }}
        {% if not loop.last %}
        UNION ALL
        {% endif %}
    {% endfor %}
)
, agregar_fecha_final AS (
    SELECT
         CASE 
            WHEN "mes"='Enero'  THEN CONCAT("anio",'-','01-31')
            WHEN 
                "mes"='Febrero' 
                AND 
                    (("anio"::int % 4 = 0 AND "anio"::int % 100 != 0) OR ("anio"::int % 400 = 0)) 
                THEN CONCAT("anio",'-','02-29')
            WHEN 
                "mes"='Febrero' 
                AND 
                    NOT (("anio"::int % 4 = 0 AND "anio"::int % 100 != 0) OR ("anio"::int % 400 = 0)) 
                THEN CONCAT("anio",'-','02-28')
            WHEN "mes"='Marzo'  THEN CONCAT("anio",'-','03-31')
            WHEN "mes"='Abril'  THEN CONCAT("anio",'-','04-30')
            WHEN "mes"='Mayo'  THEN CONCAT("anio",'-','05-31')
            WHEN "mes"='Junio'  THEN CONCAT("anio",'-','06-30')
            WHEN "mes"='Julio'  THEN CONCAT("anio",'-','07-31')
            WHEN "mes"='Agosto'  THEN CONCAT("anio",'-','08-31')
            WHEN "mes"='Septiembre'  THEN CONCAT("anio",'-','09-30')
            WHEN "mes"='Octubre'  THEN CONCAT("anio",'-','10-31')
            WHEN "mes"='Noviembre'  THEN CONCAT("anio",'-','11-30')
            WHEN "mes"='Diciembre'  THEN CONCAT("anio",'-','12-31')
            ELSE '9999-12-31'
         END as  fecha_final
        ,municipio_num
        ,cadencia
        ,casos
    FROM
        union_all_monthly
)
, agregar_fk AS (
SELECT
         ROW_NUMBER() OVER() as id_casos_dengue
        ,TO_CHAR(current_date,'YYYYMMDD') as id_fecha_carga
        ,TO_CHAR((fecha_final::date - cadencia::interval),'YYYYMMDD') as id_fecha_inicial
        ,REPLACE(fecha_final, '-', '') as id_fecha_final
        ,3 as id_fuente
        ,LPAD(municipio_num ::text, 5, '0') as id_region
        ,cadencia
        ,casos
    FROM
        agregar_fecha_final
)
SELECT * FROM agregar_fk