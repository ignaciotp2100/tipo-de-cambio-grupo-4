# Kit de Inicio — Monitor de Coyuntura y Proyección Macroeconómica

**Ciencia de Datos para Economía (ICO09425) — Trabajo Semestral**

Este repositorio es la plantilla oficial del trabajo semestral. Contiene un
pipeline funcionando de punta a punta: extracción desde APIs oficiales →
base de datos relacional (SQLite) → consultas SQL → análisis en Python →
vista para Power BI. Su tarea es **adaptarlo y extenderlo** para su variable
objetivo asignada.

## Estructura del repositorio

```
├── README.md                  <- Este archivo (edítenlo con su proyecto)
├── requirements.txt           <- Dependencias de Python
├── .env.example               <- Plantilla de credenciales (copiar a .env)
├── .gitignore                 <- Excluye .env y la base de datos del repo
├── sql/
│   ├── 01_esquema.sql         <- Esquema de la base de datos (3 tablas)
│   └── 02_consultas_ejemplo.sql <- Consultas con JOIN, GROUP BY y ventanas
├── src/
│   ├── config.py              <- Configuración y CATÁLOGO DE SERIES (editar aquí)
│   ├── extraccion.py          <- Descarga desde BCCh y FRED (+ modo demo)
│   ├── carga_db.py            <- Carga a SQLite
│   └── exportar_powerbi.py    <- Crea la vista que consume Power BI
├── notebooks/
│   ├── 01_pipeline_datos.ipynb    <- Extracción, carga y consultas SQL
│   └── 02_analisis_ejemplo.ipynb  <- Coyuntura, ARIMA y evaluación de pronósticos
├── dashboard/
│   └── README_powerbi.md      <- Cómo conectar Power BI a la base de datos
└── data/                      <- Base de datos local (no se sube a GitHub)
```

## Puesta en marcha (10 minutos)

**1. Clonar e instalar dependencias**

```bash
git clone <url-de-su-repositorio>
cd kit-inicio-coyuntura
pip install -r requirements.txt
```

**2. Probar el pipeline SIN credenciales (modo demo)**

El modo demo genera series sintéticas con la estructura real, para que
verifiquen que todo funciona antes de tramitar sus claves:

```bash
python src/carga_db.py --demo
python src/exportar_powerbi.py
```

Si ven `Base de datos lista en: .../data/coyuntura.db`, el pipeline funciona.

**3. Obtener credenciales (gratuitas)**

- **Banco Central de Chile:** registrarse en
  <https://si3.bcentral.cl/Siete/es/Siete/API> y anotar usuario y contraseña.
- **FRED:** solicitar API key en
  <https://fred.stlouisfed.org/docs/api/api_key.html>.

Luego copiar la plantilla y completar las claves:

```bash
cp .env.example .env
# editar .env con sus credenciales
```

**4. Cargar datos reales**

```bash
python src/carga_db.py
python src/exportar_powerbi.py
```

**Fecha de corte.** Por defecto se descarga hasta el día de hoy, así que la base
cambia cada vez que la corren. Para que dos integrantes que ejecuten el pipeline
en días distintos obtengan **exactamente la misma base**, fijen el corte:

```bash
python src/carga_db.py --hasta 2026-07-31
python src/carga_db.py --desde 2015-01-01 --hasta 2026-07-31
```

Fijar el corte es lo que hace reproducible la extracción, y es también la
primera defensa contra el sesgo de anticipación cuando evalúen pronósticos.

**Revisen la salida.** Si una serie falla (código equivocado, API caída), se
informa con `[ERROR]` y el proceso **continúa con las demás**. El script termina
sin error aunque falten series. Cuenten los `[OK]`: deben ser tantos como series
tenga su catálogo.

**5. Definir SUS series**

Editar el catálogo en `src/config.py` (`SERIES_BCCH` y `SERIES_FRED`).
Los códigos del BCCh se encuentran en la ficha de cada serie en
<https://si3.bcentral.cl/siete>. Recuerden el mínimo de **12 series** del
enunciado.

## Reglas importantes

- **NUNCA** suban el archivo `.env` a GitHub (el `.gitignore` ya lo excluye,
  no lo modifiquen). Subir credenciales es falta grave.
- Todos los integrantes deben hacer commits desde la primera semana.
- El análisis debe poder reproducirse con: `pip install -r requirements.txt`,
  `.env` con credenciales propias, y `python src/carga_db.py`.

## Qué deben completar ustedes

- [ ] Reemplazar este README con la descripción de SU proyecto
- [ ] Catálogo de series propio (≥ 12 series) en `src/config.py`
- [ ] Consultas SQL propias en `sql/` (JOIN, GROUP BY, ventana)
- [ ] Análisis de coyuntura y de relaciones (notebooks propios)
- [ ] Dos modelos de proyección + evaluación fuera de muestra vs. benchmark ingenuo
- [ ] Monitor en Power BI conectado a `data/coyuntura.db`
- [ ] Informe final y presentación
