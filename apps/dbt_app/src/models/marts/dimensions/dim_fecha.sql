
{{ calendario('2000-01-01','2035-01-01') }}

SELECT 
        TO_CHAR(dia,'YYYYMMDD') id_fecha
    ,   EXTRACT(DOY FROM dia) dia_anio
    ,   EXTRACT(MONTH FROM dia) mes
    ,   EXTRACT(YEAR FROM dia) anio 
    ,   {{ a_dia_de_semana_esp('dia') }} AS dia_semana
    ,   EXTRACT(DOW FROM dia) dia_semana_num
    ,   dia AS fecha_completa
    ,   EXTRACT(WEEK FROM dia) semana_num 
FROM  calendario