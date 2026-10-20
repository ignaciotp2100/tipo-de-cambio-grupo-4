# Monitor de Coyuntura: proyección del tipo de cambio CLP/USD

Ciencia de Datos para Economía · Escuela de Ingeniería Comercial, UDP
**Integrantes:** Carla Arias · Ignacio Toledo · Tahiris Carrillo
**Repositorio:** https://github.com/ignaciotp2100/tipo-de-cambio-grupo-4

## 1. Descripción

* **Variable objetivo:** tipo de cambio observado (CLP por USD), Banco Central de Chile (`F073.TCO.PRE.Z.D`).
* **Pregunta de proyección:** ¿en qué medida incorporar variables económicas nacionales e internacionales mejora la
proyección del tipo de cambio frente a un modelo basado solo en su historia? (muestras de 6, 12 y 24 meses).
* **Estado (Hito 2):** extracción desde APIs, base de datos relacional poblada y consultas SQL.

## 2. Requisitos

* Python 3.10 o superior.
* Git.
* Credenciales de las API del Banco Central de Chile y FRED.
  
Crear un entorno virtual desde la raíz del repositorio:
```bash
python -m venv.venv
```
Activar el entorno virtual según el sistema operativo:
- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
- Windows (Git Bash):
```bash
source .venv/Scripts/activate
```
- Linux o macOS:
 ```bash
source .venv/bin/activate
```
Instalar las dependencias necesarias:
```bash
python -m pip install -r requirements.txt
```

## 3. Credenciales

Cada integrante debe crear su propio archivo .env a partir de .env.example y completar las credenciales necesarias para acceder al APIs.

* Banco Central de Chile: https://si3.bcentral.cl/Siete/es/Siete/API
* FRED: https://fred.stlouisfed.org/docs/api/api\_key.html
  
El archivo .env debe mantenerse local y no debe subirse al repositorio.
Utilizar .env.example como plantilla, sin incluir claves reales ni credenciales personales.

## 4. Reproducción (en este orden, desde la raíz del repositorio)

```bash
# 1) Verificar el catálogo contra las APIs (existencia, historia, última fecha)
python src/verificar_catalogo.py

# 2) Cargar la base con fecha de corte FIJA y SIN --demo (esperar un [OK] por serie y ningún [ERROR])
python src/carga_db.py --hasta 2026-09-30

# 3) Verificar la base: tablas con PK/FK, series completas, sin duplicados ni datos demo
python src/verificar_base.py --hasta 2026-09-30

# 4) Ejecutar las consultas SQL sobre la base y ver sus resultados
python src/ejecutar_consultas.py
```

**Fecha de corte de los datos: 2026-09-30.** La base se genera localmente.

5. Estructura

```
src/config.py                catálogo de 14 series (código, nombre, frecuencia, unidad, tema) y razón económica de cada una
src/extraccion.py            descarga desde BCCh y FRED (kit)
src/carga_db.py              crea el esquema y carga la base SQLite (kit)
src/verificar_catalogo.py    chequeo del catálogo contra las APIs
src/verificar_base.py        integridad de la base y detección de modo demo
src/ejecutar_consultas.py    ejecuta sql/03_consultas_hito2.sql sobre la base
src/analisis_coyuntura.py    (opcional) gráficos e informe; consume las consultas SQL
sql/01_esquema.sql           esquema: temas, series, observaciones (con PK y FK) (kit)
sql/03_consultas_hito2.sql   JOIN, GROUP BY (mensualización) y ventana con PARTITION BY
```

## 6. Base de datos

Tres tablas relacionadas (`sql/01_esquema.sql`): `temas` (clave `id_tema`), `series` (clave `id_serie` = código en la API,
con `id_tema` foráneo) y `observaciones` (clave compuesta `id_serie, fecha`, con `id_serie` foráneo).

## 7. Catálogo de series (14)

|Tema|Series|Fuente|
|-|-|-|
|Sector externo|Tipo de cambio (objetivo), cobre, petróleo WTI, exportaciones, balanza comercial|BCCh, FRED|
|Política monetaria|TPM, Fed Funds, bono EE.UU. 10 años|BCCh, FRED|
|Actividad|Imacec|BCCh|
|Precios|IPC Chile (variación mensual)|BCCh|
|Internacional|Dólar global, VIX, S\&P 500, IPC EE.UU.|FRED|

La razón económica y el signo esperado de cada serie están en `src/config.py` (diccionario `RAZON`).
El tema *Mercado laboral* queda sin series a propósito: no hay un canal directo hacia el tipo de cambio.

## 8. Decisiones y limitaciones

* **Mensualización en SQL:** las series diarias se promedian por mes con `GROUP BY`; la variación a 12 meses usa
`LAG(valor, 12) OVER (PARTITION BY id_serie ORDER BY mes)`: la partición evita mezclar series y el 12 equivale a un año
. Solo se reporta si existe el mismo mes del año anterior (sin huecos).
* **Transformaciones:** niveles/índices en variación % interanual; tasas en diferencia en puntos porcentuales.
* **Rezagos de publicación:** Imacec (~35 días), IPC y comercio exterior (~8 días) se publican con retraso; en la fase de
pronóstico se usará solo la información disponible a cada fecha (sin *look-ahead bias*).
* **S&P 500:** FRED entrega ~10 años de historia por licencia (excepción al mínimo de 10 años).
* **Banco Mundial:** se eliminó de las fuentes respecto del Hito 1 porque ninguna serie lo justificaba.
* **Importaciones:** se reemplazan por la balanza comercial (exportaciones − importaciones) para evitar redundancia.
