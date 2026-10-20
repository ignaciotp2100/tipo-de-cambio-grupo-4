# Conectar Power BI al proyecto

El requisito del trabajo es que el monitor se conecte a la **base de datos
relacional** (`data/coyuntura.db`), no a archivos CSV pegados a mano.

## Opción recomendada: conector ODBC de SQLite

1. Instalar el driver ODBC de SQLite (una sola vez):
   descargar desde <http://www.ch-werner.de/sqliteodbc/> el instalador
   `sqliteodbc_w64.exe` (Windows 64 bits) e instalarlo.
2. En Windows, abrir **Orígenes de datos ODBC (64 bits)** → pestaña
   *DSN de usuario* → **Agregar** → elegir *SQLite3 ODBC Driver*.
3. En *Database Name*, seleccionar la ruta completa a `data/coyuntura.db`
   del repositorio clonado. Darle un nombre al DSN, por ejemplo `coyuntura`.
4. En Power BI Desktop: **Obtener datos** → **ODBC** → elegir el DSN
   `coyuntura` → cargar la vista **`vista_monitor`** (ya trae variaciones
   interanuales y promedios móviles calculados en SQL) y, si quieren
   modelar relaciones en Power BI, también las tablas `series`, `temas`
   y `observaciones`.
5. Al presionar **Actualizar** en Power BI, el tablero tomará los datos
   nuevos cada vez que ejecuten `python src/carga_db.py`.

## Contenido mínimo del monitor (según enunciado)

- Evolución de la variable objetivo y de los indicadores de contexto
  (nivel y variación interanual).
- La proyección del equipo comparada contra la trayectoria efectiva en el
  período de evaluación (pueden cargar la proyección como una tabla más
  en la base de datos).
- Un panel de síntesis tipo "semáforo" de la coyuntura.

## Consejos de diseño

- Menos es más: 3-4 páginas bien pensadas superan a 10 páginas de gráficos.
- Usen segmentadores (slicers) por tema y por rango de fechas.
- Títulos que digan algo: "Inflación converge al rango meta" comunica más
  que "Gráfico IPC".
- Verifiquen que el tablero se entienda sin que ustedes lo expliquen: esa
  es la prueba que hará el docente.
