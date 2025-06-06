{{ calendario('2010-01-01','2035-01-01') }}

SELECT 
        TO_CHAR(dia,'YYYYMMDD') id_fecha
    ,   EXTRACT(DOY FROM dia)::int dia_anio
    ,   EXTRACT(MONTH FROM dia)::int mes
    ,   EXTRACT(YEAR FROM dia)::varchar anio 
    ,   {{ a_dia_de_semana_esp('dia') }} AS dia_semana
    ,   EXTRACT(DOW FROM dia)::int dia_semana_num
    ,   dia AS fecha_completa
    ,   EXTRACT(WEEK FROM dia)::int semana_num 
FROM  calendario