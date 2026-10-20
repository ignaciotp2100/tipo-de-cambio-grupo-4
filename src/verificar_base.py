"""
verificar_base.py — Chequeo de la base ANTES de crear el tag (pauta Hito 2, dim. 1 y 2).

Comprueba:
  1. >= 3 tablas con llaves primarias y foraneas definidas.
  2. >= 12 series con observaciones y ninguna serie del catalogo sin datos.
  3. Sin observaciones duplicadas ni huerfanas.
  4. Sin senales del modo --demo: tasas (tema Politica monetaria) con valores cercanos
     o superiores a 100, o fechas posteriores a la fecha de corte.
Sale con codigo 1 si algo falla.

Uso:  python src/verificar_base.py --hasta 2026-09-30 [--db RUTA]
"""
import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

try:
    import config
except ImportError:
    from src import config  # type: ignore

MIN_SERIES = 12
TABLAS = ["temas", "series", "observaciones"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(config.RUTA_DB))
    ap.add_argument("--hasta", default=None, metavar="AAAA-MM-DD",
                    help="fecha de corte usada en la carga; detecta datos posteriores (tipico del modo demo)")
    args = ap.parse_args()
    if not Path(args.db).exists():
        sys.exit(f"No existe la base {args.db}. Corran primero: python src/carga_db.py --hasta AAAA-MM-DD")

    con = sqlite3.connect(args.db)
    fallos = []

    def check(ok, msg):
        print(("[OK]    " if ok else "[FALLA] ") + msg)
        if not ok:
            fallos.append(msg)

    existentes = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    check(all(t in existentes for t in TABLAS), f"tablas presentes: {sorted(existentes)}")
    for t in TABLAS:
        if t not in existentes:
            continue
        info = con.execute(f"PRAGMA table_info({t})").fetchall()
        pks = [c[1] for c in info if c[5]]
        fks = con.execute(f"PRAGMA foreign_key_list({t})").fetchall()
        check(bool(pks), f"{t}: llave primaria = {pks}")
        if t != "temas":
            check(bool(fks), f"{t}: llaves foraneas = {[(f[3], f[2]) for f in fks]}")

    n_series = con.execute(
        "SELECT COUNT(*) FROM (SELECT id_serie FROM observaciones GROUP BY id_serie HAVING COUNT(valor) > 0)"
    ).fetchone()[0]
    n_catalogo = con.execute("SELECT COUNT(*) FROM series").fetchone()[0]
    check(n_series >= MIN_SERIES, f"series con datos: {n_series} (minimo {MIN_SERIES})")
    check(n_series == n_catalogo, f"series con datos ({n_series}) = series del catalogo ({n_catalogo})")

    dup = con.execute("SELECT COUNT(*) FROM (SELECT 1 FROM observaciones GROUP BY id_serie, fecha HAVING COUNT(*) > 1)").fetchone()[0]
    check(dup == 0, f"observaciones duplicadas (id_serie, fecha): {dup}")
    huerf = con.execute("SELECT COUNT(*) FROM observaciones o LEFT JOIN series s ON s.id_serie=o.id_serie WHERE s.id_serie IS NULL").fetchone()[0]
    check(huerf == 0, f"observaciones sin serie (huerfanas): {huerf}")
    sin_tema = con.execute("SELECT COUNT(*) FROM series s LEFT JOIN temas t ON t.id_tema=s.id_tema WHERE t.id_tema IS NULL").fetchone()[0]
    check(sin_tema == 0, f"series sin tema: {sin_tema}")
    vacias = con.execute("SELECT s.nombre FROM series s LEFT JOIN observaciones o ON o.id_serie=s.id_serie GROUP BY s.id_serie HAVING COUNT(o.valor)=0").fetchall()
    check(not vacias, f"series sin observaciones (extraccion fallida o codigo pendiente): {[v[0] for v in vacias]}")

    if args.hasta:
        post = con.execute("SELECT COUNT(*) FROM observaciones WHERE fecha > ?", (args.hasta,)).fetchone()[0]
        check(post == 0, f"observaciones posteriores a la fecha de corte {args.hasta}: {post}")

    tasas = pd.read_sql(
        """SELECT s.nombre, MAX(o.valor) AS maximo, MAX(o.fecha) AS ultima
           FROM series s JOIN observaciones o ON s.id_serie = o.id_serie
           WHERE s.id_tema = 4 GROUP BY s.nombre""", con)
    print(tasas.to_string(index=False))
    check(bool((tasas["maximo"] < 50).all()) if len(tasas) else False,
          "tasas con valores plausibles (< 50 %); si TPM ~100 o mas, la base es del modo --demo")

    print(f"\n{'TODO OK' if not fallos else str(len(fallos)) + ' problema(s): corregir antes del tag'}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
