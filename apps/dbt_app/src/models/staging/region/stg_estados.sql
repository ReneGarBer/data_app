WITH renombrar_columnas AS (
    SELECT
          estado_num as codigo_estado
        , nom_edo as estado
    FROM
        {{ source('seeds_dimensions','estados') }}
)
SELECT * FROM renombrar_columnas
