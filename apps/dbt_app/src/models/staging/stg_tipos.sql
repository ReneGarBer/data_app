WITH remove_nulls AS (
    SELECT
        *
    FROM {{source('seeds_dimensions','tipos')}}
    WHERE
        codigo is not null
    AND nombre is not null
)
, accepted_values AS (
    SELECT
        *
    FROM remove_nulls
    WHERE codigo in ('ndvi','daily','prcp','srad','swe','tmax','tmin','vp')
)

SELECT
    *
FROM accepted_values