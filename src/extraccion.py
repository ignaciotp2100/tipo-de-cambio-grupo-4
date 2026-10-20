"""
Extracción de series económicas desde APIs oficiales.

Fuentes soportadas:
  - Banco Central de Chile (Base de Datos Estadísticos, API SieteRestWS)
  - FRED (Federal Reserve Bank of St. Louis)

Incluye además un MODO DEMO que genera series sintéticas con la misma
estructura, para que puedan probar el pipeline completo (base de datos,
SQL, análisis, Power BI) ANTES de tener sus credenciales.

Uso desde la raíz del repositorio:
    python src/extraccion.py                      # usa las APIs (requiere .env)
    python src/extraccion.py --demo               # genera datos sintéticos de prueba
    python src/extraccion.py --hasta 2026-07-31   # fija la fecha de corte
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

import numpy as np
import pandas as pd
import requests

try:
    import config
except ImportError:  # permite ejecutar desde la raíz del repo
    from src import config  # type: ignore

URL_BCCH = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
URL_FRED = "https://api.stlouisfed.org/fred/series/observations"


# ------------------------------------------------------------
# Seguridad: nunca dejar una credencial en un mensaje de error
# ------------------------------------------------------------
def enmascarar(texto: str) -> str:
    """Reemplaza por '***' cualquier credencial que aparezca en el texto.

    `requests` incluye la URL completa en sus excepciones, y esa URL lleva la
    api_key de FRED. Sin este filtro, un traceback pegado en un chat, en un
    issue de GitHub o en una captura de pantalla publica la credencial.
    """
    for secreto in (config.FRED_API_KEY, config.BCCH_PASSWORD, config.BCCH_USUARIO):
        if secreto:
            texto = texto.replace(secreto, "***")
    return texto


def pedir_json(url: str, params: dict) -> dict:
    """Hace la petición HTTP y devuelve el JSON, sin filtrar credenciales al fallar."""
    try:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        # `from None` corta el encadenamiento: la excepción original también
        # lleva la URL con la clave, y aparecería en el traceback.
        raise RuntimeError(enmascarar(str(e))) from None


# ------------------------------------------------------------
# Banco Central de Chile
# ------------------------------------------------------------
def extraer_serie_bcch(codigo: str, desde: str = "2010-01-01", hasta: str | None = None) -> pd.DataFrame:
    """Descarga una serie desde la API del BCCh y la devuelve como DataFrame (fecha, valor)."""
    if not (config.BCCH_USUARIO and config.BCCH_PASSWORD):
        raise RuntimeError(
            "Faltan credenciales del BCCh. Copien .env.example a .env y completen "
            "BCCH_USUARIO y BCCH_PASSWORD (registro gratuito en https://si3.bcentral.cl/Siete/es/Siete/API)."
        )
    hasta = hasta or date.today().isoformat()
    params = {
        "user": config.BCCH_USUARIO,
        "pass": config.BCCH_PASSWORD,
        "timeseries": codigo,
        "firstdate": desde,
        "lastdate": hasta,
        "function": "GetSeries",
    }
    contenido = pedir_json(URL_BCCH, params)
    obs = contenido.get("Series", {}).get("Obs", [])
    if not obs:
        raise ValueError(f"La API del BCCh no devolvió observaciones para '{codigo}'. Revisen el código de la serie.")
    df = pd.DataFrame(obs)
    # La API entrega fechas dd-mm-YYYY y valores como texto; 'NaN' indica dato faltante
    df["fecha"] = pd.to_datetime(df["indexDateString"], format="%d-%m-%Y")
    df["valor"] = pd.to_numeric(df["value"], errors="coerce")
    return df[["fecha", "valor"]].dropna().reset_index(drop=True)


# ------------------------------------------------------------
# FRED
# ------------------------------------------------------------
def extraer_serie_fred(codigo: str, desde: str = "2010-01-01", hasta: str | None = None) -> pd.DataFrame:
    """Descarga una serie desde la API de FRED y la devuelve como DataFrame (fecha, valor)."""
    if not config.FRED_API_KEY:
        raise RuntimeError(
            "Falta FRED_API_KEY en el archivo .env "
            "(clave gratuita en https://fred.stlouisfed.org/docs/api/api_key.html)."
        )
    params = {
        "series_id": codigo,
        "api_key": config.FRED_API_KEY,
        "file_type": "json",
        "observation_start": desde,
        "observation_end": hasta or date.today().isoformat(),
    }
    obs = pedir_json(URL_FRED, params).get("observations", [])
    if not obs:
        raise ValueError(f"La API de FRED no devolvió observaciones para '{codigo}'.")
    df = pd.DataFrame(obs)
    df["fecha"] = pd.to_datetime(df["date"])
    df["valor"] = pd.to_numeric(df["value"], errors="coerce")  # '.' indica dato faltante en FRED
    return df[["fecha", "valor"]].dropna().reset_index(drop=True)


# ------------------------------------------------------------
# Modo demo: series sintéticas para probar el pipeline sin credenciales
# ------------------------------------------------------------
def generar_serie_demo(
    codigo: str, frecuencia: str, semilla: int, hasta: str | None = None
) -> pd.DataFrame:
    """Genera una serie sintética SIN significado económico.

    ADVERTENCIA: los valores no son datos reales ni una aproximación a ellos.
    Todas las series salen de la misma fórmula (tendencia + estacionalidad +
    ruido acumulado) y todas arrancan cerca de 100, sea la serie un índice,
    una tasa en por ciento o un tipo de cambio en pesos. Sirven para probar
    que el pipeline funciona, nunca para analizar ni para proyectar.
    """
    fin = hasta or date.today().isoformat()
    rng = np.random.default_rng(semilla)
    if frecuencia == "D":
        fechas = pd.date_range("2014-01-01", fin, freq="B")  # días hábiles
    else:
        fechas = pd.date_range("2010-01-01", fin, freq="MS")  # mensual
    n = len(fechas)
    t = np.arange(n)
    tendencia = 100 + 0.05 * t
    estacionalidad = 3 * np.sin(2 * np.pi * t / (252 if frecuencia == "D" else 12))
    ruido = rng.normal(0, 1.5, n).cumsum() * 0.3
    valores = tendencia + estacionalidad + ruido
    return pd.DataFrame({"fecha": fechas, "valor": np.round(valores, 3)})


# ------------------------------------------------------------
# Orquestación
# ------------------------------------------------------------
def extraer_todo(
    demo: bool = False, desde: str = "2010-01-01", hasta: str | None = None
) -> dict[str, pd.DataFrame]:
    """Extrae todas las series del catálogo definido en config.py.

    Parámetros:
        demo   : usar series sintéticas en vez de las APIs.
        desde  : primera fecha a solicitar.
        hasta  : fecha de corte. Fijarla hace la extracción REPRODUCIBLE:
                 dos personas que corran el pipeline en días distintos
                 obtienen la misma base. Si se omite, se usa la fecha de hoy
                 y la base cambia cada día.

    Devuelve un diccionario {codigo: DataFrame(fecha, valor)}.

    Nota: si una serie falla, se informa y se continúa con las demás. El
    proceso termina sin error aunque falten series, así que revisen la
    salida y cuenten los [OK].
    """
    resultados: dict[str, pd.DataFrame] = {}
    catalogo = config.SERIES_BCCH + config.SERIES_FRED
    fallidas: list[str] = []

    for i, (codigo, nombre, frecuencia, _unidad, _tema) in enumerate(catalogo):
        try:
            if demo:
                df = generar_serie_demo(codigo, frecuencia, semilla=i, hasta=hasta)
            elif (codigo, nombre, frecuencia, _unidad, _tema) in config.SERIES_BCCH:
                df = extraer_serie_bcch(codigo, desde=desde, hasta=hasta)
            else:
                df = extraer_serie_fred(codigo, desde=desde, hasta=hasta)
            resultados[codigo] = df
            ultima = df["fecha"].max().date() if len(df) else "sin datos"
            print(f"  [OK] {nombre}: {len(df)} observaciones, hasta {ultima}")
        except Exception as e:  # noqa: BLE001 - queremos continuar con las demás series
            fallidas.append(nombre)
            print(f"  [ERROR] {nombre} ({codigo}): {enmascarar(str(e))}")

    if fallidas:
        print(f"\n  ATENCION: {len(fallidas)} de {len(catalogo)} series fallaron: "
              f"{', '.join(fallidas)}")
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extracción de series económicas")
    parser.add_argument("--demo", action="store_true",
                        help="Generar datos sintéticos de prueba (sin credenciales)")
    parser.add_argument("--desde", default="2010-01-01", metavar="AAAA-MM-DD",
                        help="Primera fecha a solicitar (por defecto 2010-01-01)")
    parser.add_argument("--hasta", default=None, metavar="AAAA-MM-DD",
                        help="Fecha de corte. Fijarla hace la extracción reproducible.")
    args = parser.parse_args()

    modo = "DEMO (datos sintéticos)" if args.demo else "APIs oficiales"
    corte = args.hasta or f"{date.today().isoformat()} (hoy)"
    print(f"Extrayendo series | modo: {modo} | desde {args.desde} hasta {corte}")
    series = extraer_todo(demo=args.demo, desde=args.desde, hasta=args.hasta)
    if not series:
        sys.exit("No se extrajo ninguna serie. Revisen credenciales y códigos.")
    print(f"Total: {len(series)} series extraídas.")
