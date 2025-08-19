{% test url_valido(model, column_name) %}

SELECT *
FROM {{ model }}
WHERE {{ column_name }} !~* '^https?://[a-z0-9\-._~:/?#\[\]@!$&''()*+,;=%]%'

{% endtest %}