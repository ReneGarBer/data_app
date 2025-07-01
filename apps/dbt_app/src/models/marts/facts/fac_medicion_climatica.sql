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
        union_all_metrics
    ORDER BY
        municipio_num, fecha
)
, agregar_pk_fk AS (
    SELECT
          ROW_NUMBER() OVER() id_medicion
        , TO_CHAR(current_date,'YYYYMMDD') as id_fecha_carga
        , TO_CHAR(inicio,'YYYYMMDD') as id_fecha_inicial
        , TO_CHAR(fin,'YYYYMMDD') as id_fecha_final
        , municipio_num as id_region
        , tipo as id_tipo        
        , valor as medicion
        , cadencia
    FROM
        order_by
)
SELECT * FROM agregar_pk_fk