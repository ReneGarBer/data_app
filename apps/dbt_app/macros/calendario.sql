{%- macro calendario(desde,hasta) -%}
    WITH calendario AS (
        SELECT
            generate_series('{{ desde }}'::date,'{{ hasta }}'::date, '1 day')::date as "dia"
    )
{%- endmacro -%}