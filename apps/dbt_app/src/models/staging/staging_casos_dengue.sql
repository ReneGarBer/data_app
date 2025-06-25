WITH union_all  as (
    {% set anios= range(2010,2025)%}
    {% for anio in anios %}
        SELECT
            '{{anio}}' as "anio"
            ,*
        FROM
            {{ source('raw_data', anio|string) }}
        {% if not loop.last %}
        UNION ALL
        {% endif %}
    {% endfor %}
)
, pivote as (
    {% set columnas=[
        "Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio",
        "Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    %}

    {% set incluir=["municipio_num","anio"]%}
    {{
        pivote_fila_a_columna(
            "union_all",
            incluir,
            columnas,
            'mes',
            'casos')
    }}
)
, no_nulls as (
    SELECT
        *
    FROM pivote
    WHERE "casos" is not null
)
, no_dups as (
    SELECT  
        DISTINCT *
    FROM no_nulls
)
, order_by as (
    SELECT 
        *
    FROM no_dups
    ORDER BY 1,2
)
SELECT * FROM order_by