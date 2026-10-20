"""
ejecutar_consultas.py — Ejecuta sql/03_consultas_hito2.sql sobre la base del proyecto
(data/coyuntura.db) y muestra los resultados (paso 5 del autochequeo de la pauta).

Uso:  python src/ejecutar_consultas.py [--db RUTA] [--filas 8]
"""
import argparse
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

try:
    import config
except ImportError:
    from src import config  # type: ignore

ARCHIVO_SQL = config.RUTA_SQL / "03_consultas_hito2.sql"


def cargar_consultas(ruta: Path = ARCHIVO_SQL) -> dict:
    """Separa el .sql en consultas nombradas ('-- name: id')."""
    texto = ruta.read_text(encoding="utf-8")
    bloques = re.split(r"^-- name:\s*", texto, flags=re.M)[1:]
    return {b.split("\n", 1)[0].strip(): b.split("\n", 1)[1] for b in bloques}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(config.RUTA_DB))
    ap.add_argument("--filas", type=int, default=8)
    args = ap.parse_args()
    if not Path(args.db).exists():
        sys.exit(f"No existe la base {args.db}. Corran primero: python src/carga_db.py --hasta AAAA-MM-DD")

    con = sqlite3.connect(args.db)
    pd.set_option("display.width", 200, "display.max_columns", 20)
    vacias = []
    for nombre, sql in cargar_consultas().items():
        df = pd.read_sql(sql, con)
        print(f"\n=== {nombre}: {len(df)} filas ===")
        print(df.head(args.filas).to_string(index=False))
        if df.empty:
            vacias.append(nombre)
    if vacias:
        sys.exit(f"Consultas sin resultados: {vacias}. La base esta vacia o incompleta.")


if __name__ == "__main__":
    main()
