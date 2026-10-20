"""
verificar_catalogo.py — Etapa 1: verifica el catalogo de src/config.py contra las APIs ANTES de cargar.

Para cada serie descarga con las mismas funciones de extraccion.py y reporta primera y ultima
observacion y anios de historia. Marca: codigo inexistente, < 10 anios de historia y posible
serie descontinuada. Tambien puede buscar codigos del BCCh por texto en el titulo.

Uso:
    python src/verificar_catalogo.py
    python src/verificar_catalogo.py --buscar "cobre" "exportaciones" --frecuencia MONTHLY

Si --buscar devuelve error, busquen el codigo a mano en https://si3.bcentral.cl/siete
(el codigo aparece en la ficha de cada serie), como indica el README del kit.
"""
import argparse
from datetime import date

import pandas as pd

try:
    import config
    from extraccion import enmascarar, extraer_serie_bcch, extraer_serie_fred, pedir_json, URL_BCCH
except ImportError:
    from src import config  # type: ignore
    from src.extraccion import enmascarar, extraer_serie_bcch, extraer_serie_fred, pedir_json, URL_BCCH  # type: ignore

MIN_ANIOS = 10
MAX_DIAS_SIN_DATO = 120


def verificar():
    filas = []
    catalogo = [(s, "BCCH") for s in config.SERIES_BCCH] + [(s, "FRED") for s in config.SERIES_FRED]
    for (codigo, nombre, _frec, _unidad, _tema), fuente in catalogo:
        try:
            f = extraer_serie_bcch if fuente == "BCCH" else extraer_serie_fred
            df = f(codigo, desde="2000-01-01")
            desde, hasta = df["fecha"].min(), df["fecha"].max()
            anios = (hasta - desde).days / 365.25
            probs = []
            if anios < MIN_ANIOS:
                probs.append(f"historia {anios:.1f} anios (<{MIN_ANIOS})")
            if (date.today() - hasta.date()).days > MAX_DIAS_SIN_DATO:
                probs.append("posible serie descontinuada")
            filas.append((nombre, codigo, fuente, desde.date(), hasta.date(), round(anios, 1),
                          "OK" if not probs else "; ".join(probs)))
        except Exception as exc:  # codigo inexistente, red, credenciales
            filas.append((nombre, codigo, fuente, None, None, None, "ERROR: " + enmascarar(str(exc))[:90]))
    tabla = pd.DataFrame(filas, columns=["nombre", "codigo", "fuente", "desde", "hasta", "anios", "estado"])
    pd.set_option("display.width", 220, "display.max_colwidth", 70)
    print(tabla.to_string(index=False))
    malas = tabla[tabla["estado"] != "OK"]
    print(f"\n{len(tabla) - len(malas)}/{len(tabla)} series OK.")
    if len(malas):
        print("Corregir antes de cargar (o justificar en el README, p. ej. SP500 con ~10 anios):")
        print(malas[["nombre", "codigo", "estado"]].to_string(index=False))


def buscar(textos, frecuencia):
    params = {"user": config.BCCH_USUARIO, "pass": config.BCCH_PASSWORD,
              "function": "SearchSeries", "frequency": frecuencia}
    info = pedir_json(URL_BCCH, params).get("SeriesInfos", [])
    df = pd.DataFrame(info)
    if df.empty:
        print("La API no devolvio series. Revisen credenciales o busquen en https://si3.bcentral.cl/siete")
        return
    pd.set_option("display.width", 220, "display.max_colwidth", 90)
    for texto in textos:
        sel = df[df["spanishTitle"].str.contains(texto, case=False, na=False)]
        print(f"\n== '{texto}' ({frecuencia}): {len(sel)} series ==")
        print(sel[["seriesId", "spanishTitle", "firstObservation", "lastObservation"]].head(15).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--buscar", nargs="*", help="textos a buscar en los titulos del catalogo BCCh")
    ap.add_argument("--frecuencia", default="MONTHLY", choices=["DAILY", "MONTHLY", "QUARTERLY", "ANNUAL"])
    a = ap.parse_args()
    buscar(a.buscar, a.frecuencia) if a.buscar else verificar()
