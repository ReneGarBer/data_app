{%- macro a_dia_de_semana_esp(date_column) -%}
    CASE EXTRACT(DOW FROM {{ date_column }} )
        WHEN  0 THEN 'domingo'
        WHEN  1 THEN 'lunes'
        WHEN  2 THEN 'martes'
        WHEN  3 THEN 'miercoles'
        WHEN  4 THEN 'jueves'
        WHEN  5 THEN 'viernes'
        WHEN  6 THEN 'sabado'
    END
{%- endmacro -%}
