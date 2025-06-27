{{
    config(
        materialized='view'
    )
}}

SELECT
    *
FROM
    {{ ref('snp_fuentes') }}
WHERE
    valido_hasta IS NULL