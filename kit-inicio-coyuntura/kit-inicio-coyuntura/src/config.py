"""
Configuración central del proyecto.

Las credenciales se leen desde el archivo .env (NUNCA subir credenciales a GitHub).
Copien .env.example a .env y completen sus claves.
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
# CATÁLOGO DE SERIES DEL PROYECTO
# Cada equipo debe editar este catálogo con sus propias series.
# Los códigos del BCCh se buscan en https://si3.bcentral.cl/siete
# (el código aparece en la ficha de cada serie).
# ============================================================
SERIES_BCCH = [
    # (codigo, nombre, frecuencia, unidad, id_tema)
    ("F073.TCO.PRE.Z.D", "Tipo de cambio observado (CLP/USD)", "D", "CLP/USD", 5),
    ("F022.TPM.TIN.D001.NO.Z.D", "Tasa de Política Monetaria (TPM)", "D", "% anual", 4),
    ("F074.IPC.VAR.Z.Z.C.M", "IPC, variación mensual", "M", "var. % mensual", 2),
    ("F032.IMC.IND.Z.Z.EP18.Z.Z.0.M", "Imacec (índice)", "M", "índice 2018=100", 1),
    # Agreguen aquí el resto de sus series...
]

SERIES_FRED = [
    # (codigo, nombre, frecuencia, unidad, id_tema)
    ("CPIAUCSL", "IPC Estados Unidos (índice)", "M", "índice", 6),
    ("FEDFUNDS", "Tasa Fed Funds (EE.UU.)", "M", "% anual", 6),
    # Agreguen aquí el resto de sus series...
]
