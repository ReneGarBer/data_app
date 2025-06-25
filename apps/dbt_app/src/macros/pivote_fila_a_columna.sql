{%- macro pivote_fila_a_columna(
    tabla,
    incluir = [],
    columnas = [],
    columna = 'columna',
    valor = 'valor') 
-%}

    {% for col in columnas %}
        SELECT
            {% for i in incluir %}
                "{{i}}",
            {% endfor %} 
            '{{ col }}' as  {{ columna }}, 
            "{{col}}" as {{ valor }} 
        FROM {{ tabla }}
        {% if not loop.last %} 
        UNION ALL
        {% endif%}
    {% endfor %}

{%- endmacro -%}