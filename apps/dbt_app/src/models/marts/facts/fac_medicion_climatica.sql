-- ...existing code...
{{ config(
    materialized = 'incremental',
    unique_key = 'id_medicion'
) }}

/*
Estrategia incremental:
- Generamos las filas nuevas a partir de las fuentes.
- Si es ejecución incremental, filtramos por "inicio" > max(id_fecha_inicial) en la tabla destino.
- Generamos un surrogate key determinístico (id_medicion) basado en id_fecha_inicial, id_fecha_final, id_region, id_tipo.
- No se usan ORDER BY en CTEs intermedios.
*/

WITH union_all_metrics AS (
    SELECT
          estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , cadencia
        , 'ndvi' AS tipo
        , ndvi AS valor
    FROM {{ ref('stg_modis_ndvi_historic') }}

    UNION ALL

    SELECT
          estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , cadencia
        , tipo
        , valor
    FROM {{ ref('stg_nasa_surface_weather_historic_unpivote') }}
)

, round_values AS (
    SELECT
          estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , cadencia
        , tipo
        , ROUND(valor::numeric, 4) AS valor
    FROM union_all_metrics
)

, remove_dups AS (
    -- DISTINCT para eliminar duplicados exactos
    SELECT DISTINCT
        estado_num
      , municipio_num
      , fecha
      , inicio
      , fin
      , cadencia
      , tipo
      , valor
    FROM round_values
)

, incremental_source AS (
    SELECT *
    FROM remove_dups
    {% if is_incremental() %}
    WHERE inicio > (
        -- La tabla destino almacena id_fecha_inicial como 'YYYYMMDD' string; convertimos a date para comparar
        SELECT COALESCE(MAX(to_date(id_fecha_inicial, 'YYYYMMDD')), '1900-01-01'::date)
        FROM {{ this }}
    )
    {% endif %}
)

, agregar_fk AS (
    SELECT
          TO_CHAR(current_date, 'YYYYMMDD')           AS id_fecha_carga
        , TO_CHAR(inicio, 'YYYYMMDD')                 AS id_fecha_inicial
        , TO_CHAR(fin, 'YYYYMMDD')                    AS id_fecha_final
        , municipio_num                                AS id_region
        , tipo                                         AS id_tipo
        , valor                                        AS medicion
        , cadencia
    FROM incremental_source
)

, generar_sk AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(
            ['id_fecha_inicial', 'id_fecha_final', 'id_region', 'id_tipo']
        ) }} AS id_medicion
      , id_fecha_carga
      , id_fecha_inicial
      , id_fecha_final
      , id_region
      , id_tipo
      , medicion
      , cadencia
    FROM agregar_fk
)

SELECT *
FROM generar_sk