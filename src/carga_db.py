"""
Carga de las series extraídas a la base de datos relacional (SQLite).

Flujo:
  1. Crea el esquema ejecutando sql/01_esquema.sql (si no existe).
  2. Registra el catálogo de series (tabla `series`).
  3. Inserta/actualiza las observaciones (tabla `observaciones`).

Uso desde la raíz del repositorio:
    python src/carga_db.py                      # extrae desde APIs y carga
    python src/carga_db.py --demo               # carga datos sintéticos de prueba
    python src/carga_db.py --hasta 2026-07-31   # fija la fecha de corte
"""
from __future__ import annotations

import argparse

import pandas as pd
from sqlalchemy import create_engine, text

try:
    import config
    from extraccion import extraer_todo
except ImportError:
    from src import config  # type: ignore
    from src.extraccion import extraer_todo  # type: ignore


def obtener_engine():
    config.RUTA_DATOS.mkdir(exist_ok=True)
    return create_engine(f"sqlite:///{config.RUTA_DB}")


def crear_esquema(engine) -> None:
    """Ejecuta el script DDL del esquema (idempotente)."""
    script = (config.RUTA_SQL / "01_esquema.sql").read_text(encoding="utf-8")
    with engine.begin() as conn:
        for sentencia in script.split(";"):
            if sentencia.strip():
                conn.execute(text(sentencia))
    print("[OK] Esquema creado/verificado.")


def cargar_catalogo(engine) -> None:
    """Inserta el catálogo de series definido en config.py."""
    catalogo = config.SERIES_BCCH + config.SERIES_FRED
    fuentes = ["BCCH"] * len(config.SERIES_BCCH) + ["FRED"] * len(config.SERIES_FRED)
    df = pd.DataFrame(
        [
            {"id_serie": c, "nombre": n, "fuente": f, "frecuencia": fr, "unidad": u, "id_tema": t}
            for (c, n, fr, u, t), f in zip(catalogo, fuentes)
        ]
    )
    with engine.begin() as conn:
        for _, fila in df.iterrows():
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO series (id_serie, nombre, fuente, frecuencia, unidad, id_tema) "
                    "VALUES (:id_serie, :nombre, :fuente, :frecuencia, :unidad, :id_tema)"
                ),
                fila.to_dict(),
            )
    print(f"[OK] Catálogo cargado: {len(df)} series.")


def cargar_observaciones(engine, series: dict[str, pd.DataFrame]) -> None:
    """Inserta/actualiza las observaciones de cada serie (idempotente)."""
    total = 0
    with engine.begin() as conn:
        for codigo, df in series.items():
            registros = [
                {"id_serie": codigo, "fecha": fila.fecha.date().isoformat(), "valor": float(fila.valor)}
                for fila in df.itertuples()
            ]
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO observaciones (id_serie, fecha, valor) "
                    "VALUES (:id_serie, :fecha, :valor)"
                ),
                registros,
            )
            total += len(registros)
    print(f"[OK] Observaciones cargadas/actualizadas: {total}.")


def main(demo: bool = False, desde: str = "2010-01-01", hasta: str | None = None) -> None:
    engine = obtener_engine()
    crear_esquema(engine)
    cargar_catalogo(engine)
    modo = "DEMO (datos sintéticos)" if demo else "APIs oficiales"
    corte = hasta or "hoy"
    print(f"Extrayendo series | modo: {modo} | desde {desde} hasta {corte}")
    series = extraer_todo(demo=demo, desde=desde, hasta=hasta)
    cargar_observaciones(engine, series)
    print(f"Base de datos lista en: {config.RUTA_DB}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga de series a la base de datos")
    parser.add_argument("--demo", action="store_true",
                        help="Usar datos sintéticos de prueba")
    parser.add_argument("--desde", default="2010-01-01", metavar="AAAA-MM-DD",
                        help="Primera fecha a solicitar (por defecto 2010-01-01)")
    parser.add_argument("--hasta", default=None, metavar="AAAA-MM-DD",
                        help="Fecha de corte. Fijarla hace la carga reproducible.")
    args = parser.parse_args()
    main(demo=args.demo, desde=args.desde, hasta=args.hasta)
