"""
analisis_coyuntura.py — (OPCIONAL, adelanto del Hito 3) Graficos e informe de coyuntura.

Todo el calculo de mensualizacion y variaciones vive en sql/03_consultas_hito2.sql; este script
SOLO lee esos resultados con pd.read_sql, grafica y arma un borrador de lectura economica.
Cada grafico lleva titulo, unidad, fuente y periodo.

Uso:  python src/analisis_coyuntura.py [--db RUTA]
"""
import argparse
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

try:
    import config
    from ejecutar_consultas import cargar_consultas
except ImportError:
    from src import config  # type: ignore
    from src.ejecutar_consultas import cargar_consultas  # type: ignore

RAIZ = config.RAIZ
DOLAR = config.OBJETIVO
NOMBRE = {s[0]: s[1] for s in config.SERIES_BCCH + config.SERIES_FRED}
FUENTE = {**{s[0]: "Banco Central de Chile" for s in config.SERIES_BCCH},
          **{s[0]: "FRED (Fed de St. Louis)" for s in config.SERIES_FRED}}
MAX_REZAGO = 6  # meses

COBRE, TPM, FED = "F019.PPB.PRE.100.D", "F022.TPM.TIN.D001.NO.Z.D", "DFF"
DOLAR_GLOBAL, VIX = "DTWEXBGS", "VIXCLS"


def preparar(var: pd.DataFrame) -> pd.DataFrame:
    """Elige la columna ya calculada en SQL segun config.TRANSFORMACION (no recalcula nada)."""
    var = var.copy()
    var["mes"] = pd.to_datetime(var["mes"] + "-01")

    def elegir(r):
        t = config.TRANSFORMACION.get(r["id_serie"], "pct")
        return r["dif_12m"] if t == "dif" else r["valor"] if t == "nivel" else r["var_12m_pct"]

    var["transf"] = var.apply(elegir, axis=1)
    return var


def serie(var, codigo, col):
    return var[var["id_serie"] == codigo].set_index("mes")[col].dropna()


def pie(fig, unidad, codigos, desde, hasta):
    fuentes = " y ".join(sorted({FUENTE[c] for c in codigos}))
    fig.text(0.01, 0.005, f"Unidad: {unidad}. Fuente: {fuentes}. Periodo: {desde:%Y-%m} a {hasta:%Y-%m}.",
             fontsize=7.5, color="#555")


def guardar(fig, nombre):
    (RAIZ / "figures").mkdir(exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(RAIZ / "figures" / nombre, dpi=160)
    plt.close(fig)


def fig_objetivo(var):
    nivel, v12 = serie(var, DOLAR, "valor"), serie(var, DOLAR, "transf")
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    ax[0].plot(nivel.index, nivel, color="#c0392b"); ax[0].set_ylabel("CLP por USD")
    ax[0].set_title("Tipo de cambio observado: nivel mensual (promedio)")
    ax[1].plot(v12.index, v12, color="#2c3e50"); ax[1].axhline(0, color="gray", lw=.7)
    ax[1].set_ylabel("% interanual"); ax[1].set_title("Tipo de cambio observado: variacion en 12 meses")
    pie(fig, "CLP/USD y % a/a", [DOLAR], nivel.index.min(), nivel.index.max())
    guardar(fig, "01_dolar_nivel_variacion.png")


def fig_dos_ejes(var, x, titulo, archivo, ylab_x):
    df = pd.concat([serie(var, DOLAR, "transf").rename("dolar"), serie(var, x, "transf").rename("x")], axis=1).dropna()
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df.index, df["dolar"], color="#c0392b"); ax.axhline(0, color="gray", lw=.7)
    ax.set_ylabel("Dolar: % interanual", color="#c0392b")
    ax2 = ax.twinx(); ax2.plot(df.index, df["x"], color="#2980b9"); ax2.set_ylabel(ylab_x, color="#2980b9")
    ax.set_title(titulo)
    pie(fig, f"dolar % a/a; {ylab_x}", [DOLAR, x], df.index.min(), df.index.max())
    guardar(fig, archivo)
    return df["dolar"].corr(df["x"])


def fig_diferencial(var):
    df = pd.concat([(serie(var, TPM, "valor") - serie(var, FED, "valor")).rename("dif"),
                    serie(var, DOLAR, "valor").rename("dolar")], axis=1).dropna()
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df.index, df["dif"], color="#27ae60"); ax.axhline(0, color="gray", lw=.7)
    ax.set_ylabel("TPM - Fed Funds (pp)", color="#27ae60")
    ax2 = ax.twinx(); ax2.plot(df.index, df["dolar"], color="#c0392b"); ax2.set_ylabel("CLP por USD", color="#c0392b")
    ax.set_title("Diferencial de tasas Chile-EE.UU. y tipo de cambio")
    pie(fig, "pp y CLP/USD (promedios mensuales)", [DOLAR, TPM, FED], df.index.min(), df.index.max())
    guardar(fig, "04_diferencial_tasas.png")
    return df["dif"].corr(df["dolar"])


def correlaciones_rezagadas(var):
    """corr(dolar_t, X_{t-k}); k>0 => X se adelanta al dolar."""
    y = serie(var, DOLAR, "transf")
    filas = {NOMBRE[c]: {k: y.corr(serie(var, c, "transf").shift(k)) for k in range(MAX_REZAGO + 1)}
             for c in var["id_serie"].unique() if c != DOLAR}
    tabla = pd.DataFrame(filas).T.round(2)
    tabla.columns = [f"rezago {k}m" for k in tabla.columns]
    tabla.to_csv(RAIZ / "reports" / "correlaciones_rezagadas.csv", encoding="utf-8")
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(tabla) + 1.6))
    im = ax.imshow(tabla.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(tabla.shape[1])); ax.set_xticklabels(tabla.columns, fontsize=8)
    ax.set_yticks(range(tabla.shape[0])); ax.set_yticklabels(tabla.index, fontsize=7)
    for i in range(tabla.shape[0]):
        for j in range(tabla.shape[1]):
            if pd.notna(tabla.values[i, j]):
                ax.text(j, i, f"{tabla.values[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label="correlacion")
    ax.set_title("Correlacion entre el dolar (t) y cada predictor rezagado k meses")
    pie(fig, "correlacion de transformaciones interanuales", [DOLAR, TPM, FED], y.index.min(), y.index.max())
    guardar(fig, "06_correlaciones_rezagadas.png")
    return tabla


def informe(var, c_cobre, c_dif, c_vix, tabla):
    d, v = serie(var, DOLAR, "valor"), serie(var, DOLAR, "transf")
    mejores = tabla.abs().max(axis=1).sort_values(ascending=False).head(3).index.tolist()
    f = lambda x: "n/d" if x is None or pd.isna(x) else f"{x:.2f}"
    txt = f"""# Lectura de coyuntura (borrador generado desde la base)

**Periodo analizado:** {d.index.min():%Y-%m} a {d.index.max():%Y-%m}. Cifras desde `sql/03_consultas_hito2.sql`.

## 1. Donde esta el dolar
- Ultimo promedio mensual ({d.index.max():%Y-%m}): **{d.iloc[-1]:,.0f} CLP/USD**; variacion en 12 meses: **{f(v.iloc[-1])} %**.
- Maximo del periodo: {d.max():,.0f} ({d.idxmax():%Y-%m}); minimo: {d.min():,.0f} ({d.idxmin():%Y-%m}).
- COMPLETAR: que episodios explican maximos y minimos.

## 2. Mecanismos (correlaciones, mismo mes)
| Mecanismo | Correlacion | Signo esperado |
|---|---|---|
| Cobre vs dolar (var. interanual) | {f(c_cobre)} | negativo |
| Diferencial TPM-Fed vs dolar (niveles) | {f(c_dif)} | negativo |
| VIX vs dolar (var. interanual) | {f(c_vix)} | positivo |
- COMPLETAR: coincide cada signo con la teoria? Correlacion no es causalidad ni capacidad predictiva.

## 3. Que variables se adelantan al dolar
Mayor correlacion absoluta con algun rezago: **{', '.join(mejores)}** (detalle en `reports/correlaciones_rezagadas.csv`).
- COMPLETAR: interpretacion para los horizontes de proyeccion.
"""
    (RAIZ / "reports" / "lectura_coyuntura.md").write_text(txt, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(config.RUTA_DB))
    args = ap.parse_args()
    if not Path(args.db).exists():
        sys.exit(f"No existe la base {args.db}. Corran primero la carga.")
    (RAIZ / "reports").mkdir(exist_ok=True)

    con = sqlite3.connect(args.db)
    q = cargar_consultas()
    control = pd.read_sql(q["control_base"], con)
    con_serie = control[control["nombre"].notna()]            # un tema sin series no es un error
    if (con_serie["n_obs"] == 0).any():
        sys.exit("Hay series con n_obs = 0 (extraccion fallida). Revisen la carga antes de analizar.")

    var = preparar(pd.read_sql(q["variaciones_mensuales"], con))
    fig_objetivo(var)
    c_cobre = fig_dos_ejes(var, COBRE, "Dolar y precio del cobre (variaciones interanuales)", "02_dolar_vs_cobre.png", "Cobre: % interanual")
    fig_dos_ejes(var, DOLAR_GLOBAL, "Dolar y dolar global (variaciones interanuales)", "03_dolar_vs_dolar_global.png", "Dolar global: % interanual")
    c_dif = fig_diferencial(var)
    c_vix = fig_dos_ejes(var, VIX, "Dolar y VIX (variaciones interanuales)", "05_dolar_vs_vix.png", "VIX: % interanual")
    tabla = correlaciones_rezagadas(var)
    informe(var, c_cobre, c_dif, c_vix, tabla)
    print("Listo: figures/*.png, reports/lectura_coyuntura.md, reports/correlaciones_rezagadas.csv")


if __name__ == "__main__":
    main()
