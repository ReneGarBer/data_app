{% snapshot snp_fuentes %}
{{
    config(
        strategy = 'check',
        unique_key = 'id',
        check_cols = [
            'descripcion'
            ,'estado'
            ,'fecha_disponibilidad_final'
            ,'nombre'
        ],
        snapshot_meta_column_names={
            "dbt_valid_from": "valido_desde",
            "dbt_valid_to": "valido_hasta",
            "dbt_updated_at": "fecha_actualizacion",
        }
    )
}}
SELECT
    *
FROM {{source('raw_data','fuentes')}}
{% endsnapshot %}