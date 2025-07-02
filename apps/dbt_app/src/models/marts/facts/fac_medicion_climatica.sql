WITH union_all_metrics AS (
    SELECT
          estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , cadencia
        , tipo
        , valor
    FROM
        {{ ref('stg_modis_ndvi_historic') }}
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
    FROM
        {{ ref('stg_nasa_surface_weather_historic') }}    
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
        , ROUND(valor,4) AS valor
    FROM
        union_all_metrics
)
, remove_dups AS (
    SELECT
        DISTINCT *
    FROM
        round_values
)
, order_by AS (
    SELECT
          estado_num
        , municipio_num
        , fecha
        , inicio
        , fin
        , cadencia
        , tipo
        , valor
    FROM
        remove_dups
    ORDER BY
        municipio_num, fecha
)
, agregar_fk AS (
    SELECT
          TO_CHAR(current_date,'YYYYMMDD') as id_fecha_carga
        , TO_CHAR(inicio,'YYYYMMDD') as id_fecha_inicial
        , TO_CHAR(fin,'YYYYMMDD') as id_fecha_final
        , municipio_num as id_region
        , tipo as id_tipo        
        , valor as medicion
        , cadencia
    FROM
        order_by
)
, generar_sk AS (
    SELECT 
        {{ dbt_utils.generate_surrogate_key(
            ['id_fecha_inicial'
            , 'id_fecha_final'
            ,'id_region'
            ,'id_tipo']) }} as id_medicion
        , * 
    FROM agregar_fk 
)
SELECT * FROM generar_sk