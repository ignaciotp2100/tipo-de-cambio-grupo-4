"""
Configuración central del proyecto.

Las credenciales se leen desde el archivo .env (NUNCA subir credenciales a GitHub).
Copien .env.example a .env y completen sus claves.

Proyecto: Monitor de Coyuntura — proyección del tipo de cambio CLP/USD.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Rutas del proyecto
RAIZ = Path(__file__).resolve().parents[1]
RUTA_DATOS = RAIZ / "data"
RUTA_DB = RUTA_DATOS / "coyuntura.db"
RUTA_SQL = RAIZ / "sql"

# Cargar credenciales desde .env
load_dotenv(RAIZ / ".env")

# --- Banco Central de Chile ---
# Registro gratuito en: https://si3.bcentral.cl/Siete/es/Siete/API
BCCH_USUARIO = os.getenv("BCCH_USUARIO", "")
BCCH_PASSWORD = os.getenv("BCCH_PASSWORD", "")

# --- FRED (Reserva Federal de St. Louis) ---
# API key gratuita en: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# ============================================================
# CATÁLOGO DE SERIES (14)   —   formato exigido por extraccion.py y carga_db.py:
#   (codigo, nombre, frecuencia, unidad, id_tema)
# id_tema (tabla `temas`): 1 Actividad · 2 Precios · 3 Mercado laboral
#                          4 Política monetaria · 5 Sector externo · 6 Internacional
#
# ESTADO DE LOS CÓDIGOS
#   VERIFICADO : confirmado en la documentación oficial de la API BDE o ya incluido en el kit.
#   VERIFICAR  : candidato; confirmar con `python src/verificar_catalogo.py` ANTES de cargar.
#   VERIFICADO  : placeholder; buscar con `python src/verificar_catalogo.py --buscar ...`.
#                Mientras no se reemplace, la carga mostrará [ERROR] para esa serie (a propósito).
# ============================================================
SERIES_BCCH = [
    ("F073.TCO.PRE.Z.D", "Tipo de cambio observado (CLP/USD)", "D", "CLP/USD", 5),                 # VERIFICADO (objetivo)
    ("F019.PPB.PRE.40.M", "Precio del cobre refinado BML", "M", "cUS$/libra", 5),                 # VERIFICADO
    ("F022.TPM.TIN.D001.NO.Z.D", "Tasa de Política Monetaria (TPM)", "D", "% anual", 4),          # VERIFICADO
    ("F032.IMC.IND.Z.Z.EP18.Z.Z.0.M", "Imacec (índice)", "M", "índice 2018=100", 1),              # VERIFICADO
    ("F074.IPC.VAR.Z.Z.C.M", "IPC, variación mensual", "M", "var. % mensual", 2),                 # VERIFICADO (kit)
    ("F068.B1.FLU.Z.0.C.N.Z.Z.Z.Z.6.0.M", "Exportaciones de bienes", "M", "millones de US$", 5),            # VERIFICADO
    ("F068.B1.VAR.T0.0.S.N.Z.Z.Z.Z.6.0.M", "Balanza comercial", "M", "millones de US$", 5),                        # VERIFICADO
]

SERIES_FRED = [
    ("DFF", "Tasa Fed Funds efectiva (EE.UU.)", "D", "% anual", 4),
    ("DGS10", "Bono del Tesoro EE.UU. a 10 años", "D", "% anual", 4),
    ("DTWEXBGS", "Dólar global (índice amplio)", "D", "índice ene-2006=100", 6),
    ("VIXCLS", "VIX (volatilidad S&P 500)", "D", "índice", 6),
    ("SP500", "S&P 500", "D", "índice", 6),                    # FRED entrega solo ~10 años (licencia)
    ("DCOILWTICO", "Petróleo WTI", "D", "US$/barril", 5),
    ("CPIAUCSL", "IPC Estados Unidos (índice)", "M", "índice 1982-84=100", 6),
]

# ------------------------------------------------------------
# Metadatos propios (no los usan extraccion.py ni carga_db.py)
# ------------------------------------------------------------
OBJETIVO = "F073.TCO.PRE.Z.D"

# Transformación para el análisis:
#   "pct"   -> variación % interanual (niveles, índices, precios)
#   "dif"   -> diferencia en 12 meses, en unidades de la serie (tasas -> puntos porcentuales; balanza, que puede ser <= 0)
#   "nivel" -> la serie ya es una tasa de variación: se usa tal cual
TRANSFORMACION = {
    "F073.TCO.PRE.Z.D": "pct", "F019.PPB.PRE.40.M": "pct", "F022.TPM.TIN.D001.NO.Z.D": "dif",
    "F032.IMC.IND.Z.Z.EP18.Z.Z.0.M": "pct", "F074.IPC.VAR.Z.Z.C.M": "nivel",
    "F068.B1.FLU.Z.0.C.N.Z.Z.Z.Z.6.0.M": "pct", "F068.B1.VAR.T0.0.S.N.Z.Z.Z.Z.6.0.M": "dif",
    "DFF": "dif", "DGS10": "dif", "DTWEXBGS": "pct", "VIXCLS": "pct", "SP500": "pct",
    "DCOILWTICO": "pct", "CPIAUCSL": "pct",
}

# Razón económica de cada serie (Etapa 1 de la guía) y rezago de publicación aproximado.
RAZON = {
    "F073.TCO.PRE.Z.D": "Variable a proyectar. Se publica con 1 día hábil de desfase.",
    "F019.PPB.PRE.40.M": "un mayor precio aumenta los ingresos por exportaciones y puede fortalecer el peso (signo esperado: negativo). Dato del mismo día.",
    "F022.TPM.TIN.D001.NO.Z.D": "Parte chilena del diferencial de tasas: TPM más alta atrae capital (carry trade) y aprecia el peso (negativo). Calendario de RPM conocido.",
    "F032.IMC.IND.Z.Z.EP18.Z.Z.0.M": "Actividad doméstica: mejores perspectivas atraen inversión (negativo). Rezago de publicación ~35 días: contextualiza, no anticipa en tiempo real.",
    "F074.IPC.VAR.Z.Z.C.M": "Diferencial de inflación con EE.UU. y canal de reacción de la TPM. Rezago ~8 días.",
    "F068.B1.FLU.Z.0.C.N.Z.Z.Z.Z.6.0.M": "Oferta de divisas por comercio: más exportaciones aprecian el peso (negativo). Rezago ~8 días.",
    "F068.B1.VAR.T0.0.S.N.Z.Z.Z.Z.6.0.M": "Flujo neto de divisas (exportaciones - importaciones); reemplaza a las importaciones por separado, redundantes con la balanza. Rezago ~8 días.",
    "DFF": "Parte estadounidense del diferencial: más tasa Fed atrae capital a EE.UU. y deprecia el peso (positivo).",
    "DGS10": "Tasas largas de EE.UU.: expectativas de la Fed y costo de oportunidad de activos emergentes (positivo).",
    "DTWEXBGS": "Fortaleza generalizada del USD: si sube frente a todas las monedas, el CLP también se deprecia (positivo).",
    "VIXCLS": "Aversión al riesgo: en pánico los inversores se refugian en USD (positivo).",
    "SP500": "Apetito por riesgo: caídas bursátiles globales castigan monedas emergentes (negativo). Historia limitada a ~10 años por licencia de FRED.",
    "DCOILWTICO": "Chile es importador neto de energía: petróleo caro empeora términos de intercambio (positivo).",
    "CPIAUCSL": "Contraparte del diferencial de inflación y determinante de la trayectoria de tasas de la Fed (positivo).",
}

assert len(SERIES_BCCH) + len(SERIES_FRED) >= 12, "El catálogo debe tener 12 o más series"
