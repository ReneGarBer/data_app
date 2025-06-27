SELECT
     ROW_NUMBER() OVER () AS id_tipo
    ,*
FROM
    {{ ref('stg_tipos') }}