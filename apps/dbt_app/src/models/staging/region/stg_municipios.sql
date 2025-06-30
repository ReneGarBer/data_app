WITH renombrar_columnas AS (
    SELECT
          estado_num as codigo_estado
        , cve_mun as codigo_municipio
        , municipio_num as codigo_completo
        , nom_mun as municipio
    FROM
        {{ source('seeds_dimensions','municipios') }}
)
SELECT * FROM renombrar_columnas
