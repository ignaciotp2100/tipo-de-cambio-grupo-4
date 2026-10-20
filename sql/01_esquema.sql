-- ============================================================
-- Esquema de la base de datos del proyecto
-- Monitor de Coyuntura y Proyección Macroeconómica
-- Ciencia de Datos para Economía (ICO09425)
--
-- Motor: SQLite (compatible con PostgreSQL con cambios menores)
-- ============================================================

-- Tabla 1: Catálogo de series
-- Una fila por cada serie económica que usa el proyecto.
CREATE TABLE IF NOT EXISTS series (
    id_serie      TEXT PRIMARY KEY,      -- código en la fuente (ej: 'F073.TCO.PRE.Z.D' en BCCh, 'CPIAUCSL' en FRED)
    nombre        TEXT NOT NULL,         -- nombre legible (ej: 'Tipo de cambio observado')
    fuente        TEXT NOT NULL,         -- 'BCCH', 'FRED', 'INE', etc.
    frecuencia    TEXT NOT NULL,         -- 'D' diaria, 'M' mensual, 'Q' trimestral
    unidad        TEXT,                  -- 'CLP/USD', 'var. % interanual', 'índice', etc.
    id_tema       INTEGER REFERENCES temas(id_tema)
);

-- Tabla 2: Clasificación temática de los indicadores
CREATE TABLE IF NOT EXISTS temas (
    id_tema     INTEGER PRIMARY KEY,
    tema        TEXT NOT NULL,           -- 'Actividad', 'Precios', 'Mercado laboral', 'Política monetaria', 'Sector externo'
    descripcion TEXT
);

-- Tabla 3: Observaciones
-- Una fila por (serie, fecha). Es la tabla de hechos del proyecto.
CREATE TABLE IF NOT EXISTS observaciones (
    id_serie    TEXT NOT NULL REFERENCES series(id_serie),
    fecha       DATE NOT NULL,
    valor       REAL,
    PRIMARY KEY (id_serie, fecha)
);

-- Índice para acelerar consultas por fecha
CREATE INDEX IF NOT EXISTS idx_obs_fecha ON observaciones(fecha);

-- Carga inicial de temas
INSERT OR IGNORE INTO temas (id_tema, tema, descripcion) VALUES
    (1, 'Actividad',           'Indicadores de actividad económica y producción'),
    (2, 'Precios',             'Inflación y sus componentes'),
    (3, 'Mercado laboral',     'Empleo, desempleo y salarios'),
    (4, 'Política monetaria',  'TPM y tasas de interés'),
    (5, 'Sector externo',      'Tipo de cambio, términos de intercambio, commodities'),
    (6, 'Internacional',       'Indicadores de economías relevantes (EE.UU., China, etc.)');
