{% test valid_id_fecha_inicial_month(model,column_name)%}
SELECT 
    *
FROM {{model}}
WHERE {{column_name}} not like '%01'
{% endtest %}