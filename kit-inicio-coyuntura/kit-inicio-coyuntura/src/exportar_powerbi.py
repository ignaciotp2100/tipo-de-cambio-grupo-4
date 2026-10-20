"""
Prepara la vista consolidada que consumirá Power BI.

Power BI Desktop puede conectarse directamente a SQLite mediante el
conector ODBC (ver dashboard/README_powerbi.md). Este script crea además
una VISTA en la base de datos con los datos ya transformados (variación
interanual y promedio móvil), para que el modelado en Power BI sea simple.

Uso:
    python src/exportar_powerbi.py
"""
from __future__ import annotations

from sqlalchemy import text

try:
    from carga_db import obtener_engine
except ImportError:
    from src.carga_db import obtener_engine  # type: ignore

VISTA = """
CREATE VIEW IF NOT EXISTS vista_monitor AS
SELECT o.id_serie,
       s.nombre,
       t.tema,
       s.frecuencia,
       s.unidad,
       o.fecha,
       o.valor,
       ROUND(100.0 * (o.valor / LAG(o.valor, 12) OVER (PARTITION BY o.id_serie ORDER BY o.fecha) - 1), 2)
           AS var_interanual_pct,
       ROUND(AVG(o.valor) OVER (PARTITION BY o.id_serie ORDER BY o.fecha
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 3)
           AS promedio_movil_3
FROM observaciones o
JOIN series s ON s.id_serie = o.id_serie
JOIN temas  t ON t.id_tema  = s.id_tema
"""


def main() -> None:
    engine = obtener_engine()
    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS vista_monitor"))
        conn.execute(text(VISTA))
        n = conn.execute(text("SELECT COUNT(*) FROM vista_monitor")).scalar()
    print(f"[OK] Vista 'vista_monitor' creada ({n} filas). Conecten Power BI a data/coyuntura.db.")


if __name__ == "__main__":
    main()
