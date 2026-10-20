-- =============================================================================
-- 03_consultas_hito2.sql  |  Monitor de Coyuntura: tipo de cambio CLP/USD
-- Las consultas se separan con marcas "-- name: <id>"; las leen
-- src/ejecutar_consultas.py y src/analisis_coyuntura.py con pd.read_sql.
-- Esquema (sql/01_esquema.sql): temas(id_tema, tema, descripcion)
--   series(id_serie TEXT = codigo en la API, nombre, fuente, frecuencia, unidad, id_tema)
--   observaciones(id_serie, fecha, valor)
-- Motor: SQLite (funciones de ventana desde la version 3.25).
-- =============================================================================

-- name: control_base
-- Control de calidad de la base: n_obs = 0 -> extraccion fallida;
-- 'hasta' antiguo -> serie descontinuada; 'desde' reciente -> poca historia.
-- (Un tema sin series, p. ej. 'Mercado laboral', aparece con nombre vacio.)
SELECT t.tema,
       s.nombre,
       COUNT(o.valor) AS n_obs,
       MIN(o.fecha)   AS desde,
       MAX(o.fecha)   AS hasta
FROM temas AS t
LEFT JOIN series        AS s ON s.id_tema  = t.id_tema
LEFT JOIN observaciones AS o ON o.id_serie = s.id_serie
GROUP BY t.tema, s.nombre
ORDER BY t.tema, n_obs;

-- name: datos_con_nombre
-- 1) JOIN: cada observacion con el nombre, la unidad y el tema de su serie.
SELECT o.fecha,
       o.valor,
       s.id_serie,
       s.nombre,
       s.unidad,
       t.tema
FROM observaciones AS o
JOIN series AS s ON s.id_serie = o.id_serie
JOIN temas  AS t ON t.id_tema  = s.id_tema
ORDER BY s.nombre, o.fecha;

-- name: variaciones_mensuales
-- 2) GROUP BY: series diarias -> promedio mensual (las mensuales quedan igual).
-- 3) Ventana con PARTITION BY id_serie: se reinicia en cada serie y corre en orden
--    temporal (ORDER BY mes) sobre series ya mensuales (12 filas = 12 meses si no hay huecos).
--    * var_12m_pct : variacion interanual en % (niveles, indices, precios)
--    * dif_12m     : diferencia en 12 meses en unidades de la serie (tasas -> puntos porcentuales)
--    * media_3m    : promedio movil de 3 meses
--    Control de huecos: la variacion solo se reporta si la fila 12 atras es
--    realmente el mismo mes del ano anterior; si no, queda en NULL (nunca un valor falso).
WITH mensual AS (
    SELECT o.id_serie,
           strftime('%Y-%m', o.fecha) AS mes,
           AVG(o.valor)               AS valor
    FROM observaciones AS o
    WHERE o.valor IS NOT NULL
    GROUP BY o.id_serie, mes
),
ventana AS (
    SELECT m.id_serie,
           m.mes,
           m.valor,
           LAG(m.valor, 12) OVER (PARTITION BY m.id_serie ORDER BY m.mes) AS valor_12,
           LAG(m.mes,   12) OVER (PARTITION BY m.id_serie ORDER BY m.mes) AS mes_12,
           AVG(m.valor) OVER (PARTITION BY m.id_serie ORDER BY m.mes
                              ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)  AS media_3m
    FROM mensual AS m
)
SELECT s.id_serie,
       s.nombre,
       t.tema,
       v.mes,
       v.valor,
       v.media_3m,
       CASE WHEN v.mes_12 = strftime('%Y-%m', date(v.mes || '-01', '-12 months'))
                 AND v.valor_12 > 0
            THEN 100.0 * (v.valor / v.valor_12 - 1.0) END AS var_12m_pct,
       CASE WHEN v.mes_12 = strftime('%Y-%m', date(v.mes || '-01', '-12 months'))
            THEN v.valor - v.valor_12 END                 AS dif_12m
FROM ventana AS v
JOIN series AS s ON s.id_serie = v.id_serie
JOIN temas  AS t ON t.id_tema  = s.id_tema
ORDER BY s.nombre, v.mes;
