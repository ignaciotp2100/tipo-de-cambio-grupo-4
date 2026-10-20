-- ============================================================
-- Consultas SQL de ejemplo
-- Cada consulta ilustra una técnica exigida en el trabajo:
-- JOIN, GROUP BY y funciones de ventana.
-- Adapten estas consultas a sus propias series.
-- ============================================================

-- ------------------------------------------------------------
-- Consulta 1 (JOIN): últimas observaciones de cada serie,
-- con su nombre legible y tema.
-- ------------------------------------------------------------
SELECT s.nombre,
       t.tema,
       o.fecha,
       o.valor,
       s.unidad
FROM observaciones o
JOIN series s ON s.id_serie = o.id_serie
JOIN temas  t ON t.id_tema  = s.id_tema
WHERE o.fecha = (SELECT MAX(fecha) FROM observaciones o2 WHERE o2.id_serie = o.id_serie)
ORDER BY t.tema, s.nombre;

-- ------------------------------------------------------------
-- Consulta 2 (GROUP BY): promedio anual de cada serie mensual.
-- Útil para tablas resumen del informe.
-- ------------------------------------------------------------
SELECT s.nombre,
       strftime('%Y', o.fecha)      AS anio,
       ROUND(AVG(o.valor), 2)       AS promedio_anual,
       COUNT(*)                     AS n_observaciones
FROM observaciones o
JOIN series s ON s.id_serie = o.id_serie
WHERE s.frecuencia = 'M'
GROUP BY s.nombre, anio
ORDER BY s.nombre, anio;

-- ------------------------------------------------------------
-- Consulta 3 (función de ventana): variación interanual (12 meses)
-- calculada directamente en SQL con LAG.
-- Esta es la transformación más usada en análisis de coyuntura.
-- ------------------------------------------------------------
SELECT id_serie,
       fecha,
       valor,
       LAG(valor, 12) OVER (PARTITION BY id_serie ORDER BY fecha)  AS valor_12m_atras,
       ROUND( 100.0 * (valor / LAG(valor, 12) OVER (PARTITION BY id_serie ORDER BY fecha) - 1), 2) AS var_interanual_pct
FROM observaciones
WHERE id_serie IN (SELECT id_serie FROM series WHERE frecuencia = 'M')
ORDER BY id_serie, fecha;

-- ------------------------------------------------------------
-- Consulta 4 (función de ventana): promedio móvil de 3 meses,
-- para suavizar series volátiles antes de graficarlas.
-- ------------------------------------------------------------
SELECT id_serie,
       fecha,
       valor,
       ROUND(AVG(valor) OVER (
             PARTITION BY id_serie
             ORDER BY fecha
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS promedio_movil_3m
FROM observaciones
ORDER BY id_serie, fecha;
