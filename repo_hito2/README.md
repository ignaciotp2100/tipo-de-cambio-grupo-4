# Monitor de Coyuntura: proyección del tipo de cambio CLP/USD

Ciencia de Datos para Economía (ICO09425) · Escuela de Ingeniería Comercial, UDP
**Integrantes:** Carla Arias · Ignacio Toledo · Tahiris Carrillo
**Repositorio:** https://github.com/ignaciotp2100/tipo-de-cambio-grupo-4

## 1. Descripción
- **Variable objetivo:** tipo de cambio observado (CLP por USD), Banco Central de Chile (`F073.TCO.PRE.Z.D`).
- **Pregunta de proyección:** ¿en qué medida incorporar variables económicas nacionales e internacionales mejora la
  proyección del tipo de cambio frente a un modelo basado solo en su historia? (horizontes de 6, 12 y 24 meses).
- **Estado (Hito 2):** extracción desde APIs, base de datos relacional poblada y consultas SQL.

## 2. Requisitos
- Python 3.10 o superior.
```bash
python -m venv .venv
source .venv/bin/activate            # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
```

## 3. Credenciales
Cada integrante crea su propio `.env` (no se sube a GitHub; está en `.gitignore`):
```bash
cp .env.example .env      # y completar BCCH_USUARIO, BCCH_PASSWORD y FRED_API_KEY (sin comillas)
```
- Banco Central de Chile (usuario y contraseña de la BDE): https://si3.bcentral.cl/Siete/es/Siete/API
- FRED (API key gratuita): https://fred.stlouisfed.org/docs/api/api_key.html

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
**Fecha de corte de los datos: 2026-09-30.** La base (`data/coyuntura.db`) se genera localmente y no se sube a GitHub.
Si antes se corrió `--demo`, borrar `data/coyuntura.db` antes del paso 2: la carga reemplaza fechas coincidentes pero
dejaría filas sintéticas en las demás (base mitad real, mitad demo).

*Opcional (adelanto del Hito 3, no requerido en el Hito 2):* `python src/analisis_coyuntura.py` genera gráficos en
`figures/` y un borrador de lectura en `reports/`, usando las mismas consultas SQL.

## 5. Estructura
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
| Tema | Series | Fuente |
|---|---|---|
| Sector externo | Tipo de cambio (objetivo), cobre, petróleo WTI, exportaciones, balanza comercial | BCCh, FRED |
| Política monetaria | TPM, Fed Funds, bono EE.UU. 10 años | BCCh, FRED |
| Actividad | Imacec | BCCh |
| Precios | IPC Chile (variación mensual) | BCCh |
| Internacional | Dólar global, VIX, S&P 500, IPC EE.UU. | FRED |

La razón económica y el signo esperado de cada serie están en `src/config.py` (diccionario `RAZON`).
El tema *Mercado laboral* queda sin series a propósito: no hay un canal directo hacia el tipo de cambio en los horizontes del proyecto.

## 8. Decisiones y limitaciones
- **Mensualización en SQL:** las series diarias se promedian por mes con `GROUP BY`; la variación a 12 meses usa
  `LAG(valor, 12) OVER (PARTITION BY id_serie ORDER BY mes)`: la partición evita mezclar series y el 12 equivale a un año
  porque la serie ya es mensual. Solo se reporta si existe el mismo mes del año anterior (sin huecos).
- **Transformaciones:** niveles/índices en variación % interanual; tasas en diferencia en puntos porcentuales.
- **Rezagos de publicación:** Imacec (~35 días), IPC y comercio exterior (~8 días) se publican con retraso; en la fase de
  pronóstico se usará solo la información disponible a cada fecha (sin *look-ahead bias*).
- **S&P 500:** FRED entrega ~10 años de historia por licencia (excepción al mínimo de 10 años).
- **Banco Mundial:** se eliminó de las fuentes respecto del Hito 1 porque ninguna serie lo justificaba.
- **Importaciones:** se reemplazan por la balanza comercial (exportaciones − importaciones) para evitar redundancia.

## 9. Errores y datos faltantes
- La carga no se detiene si una serie falla: informa `[ERROR]` y continúa; por eso se cuenta que haya un `[OK]` por serie.
- Los `NaN` del Banco Central (fines de semana, feriados) y los `.` de FRED se descartan al extraer; no se cargan.
- Las consultas ignoran nulos, y la variación a 12 meses queda vacía donde falta el mes del año anterior.

## 10. Cómo saber que la base NO es del modo demo
`python src/verificar_base.py --hasta 2026-09-30` falla si la TPM, la Fed Funds o el bono superan 50 %, o si hay fechas
posteriores al corte. Los datos demo parten cerca de 100 (la TPM llega a 200 o más) y llegan hasta la fecha de hoy.
