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
                {% if 'as' in i %}
                    {% set parts = i.split(' as ')%}
                        {{parts[0]}} as {{parts[1]}},
                {% else %}
                    "{{i}}",
                {% endif %}
            {% endfor %} 
            '{{ col }}' as  {{ columna }}, 
            "{{col}}" as {{ valor }} 
        FROM {{ tabla }}
        {% if not loop.last %} 
        UNION ALL
        {% endif%}
    {% endfor %}

{%- endmacro -%}