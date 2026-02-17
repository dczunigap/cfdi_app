PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Respaldo temporal de configuraciones existentes.
-- Si hay multiples filas por regimen+tipo (por diferentes ejercicios),
-- se conservara la mas reciente por id.
CREATE TABLE IF NOT EXISTS _tmp_config_keep_ids (
  old_id INTEGER PRIMARY KEY
);

DELETE FROM _tmp_config_keep_ids;

INSERT INTO _tmp_config_keep_ids (old_id)
SELECT MAX(id) AS old_id
FROM regimen_declaracion_config
GROUP BY regimen_fiscal_id, tipo_declaracion_clave;

CREATE TABLE IF NOT EXISTS regimen_declaracion_config_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regimen_fiscal_id INTEGER NOT NULL,
    tipo_declaracion_clave TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    incluir_acumulado_mensual_en_anual INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_config_regimen
      FOREIGN KEY (regimen_fiscal_id)
      REFERENCES catalogo_regimen_fiscal (id),
    CONSTRAINT fk_config_tipo_decl
      FOREIGN KEY (tipo_declaracion_clave)
      REFERENCES catalogo_tipo_declaracion (clave),
    CONSTRAINT ux_config_regimen_tipo
      UNIQUE (regimen_fiscal_id, tipo_declaracion_clave)
);

INSERT INTO regimen_declaracion_config_new (
    regimen_fiscal_id,
    tipo_declaracion_clave,
    activo,
    incluir_acumulado_mensual_en_anual,
    created_at,
    updated_at
)
SELECT
    c.regimen_fiscal_id,
    c.tipo_declaracion_clave,
    c.activo,
    c.incluir_acumulado_mensual_en_anual,
    c.created_at,
    c.updated_at
FROM regimen_declaracion_config c
JOIN _tmp_config_keep_ids k ON k.old_id = c.id;

CREATE TABLE IF NOT EXISTS _tmp_config_id_map (
  old_id INTEGER PRIMARY KEY,
  new_id INTEGER NOT NULL
);

DELETE FROM _tmp_config_id_map;

INSERT INTO _tmp_config_id_map (old_id, new_id)
SELECT
  c.id AS old_id,
  n.id AS new_id
FROM regimen_declaracion_config c
JOIN _tmp_config_keep_ids k ON k.old_id = c.id
JOIN regimen_declaracion_config_new n
  ON n.regimen_fiscal_id = c.regimen_fiscal_id
 AND n.tipo_declaracion_clave = c.tipo_declaracion_clave;

CREATE TABLE IF NOT EXISTS regimen_declaracion_config_detalle_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    uso_cfdi_clave TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_config_detalle_config
      FOREIGN KEY (config_id)
      REFERENCES regimen_declaracion_config_new (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_config_detalle_uso
      FOREIGN KEY (uso_cfdi_clave)
      REFERENCES catalogo_uso_cfdi_deduccion (clave),
    CONSTRAINT ux_config_detalle
      UNIQUE (config_id, uso_cfdi_clave)
);

INSERT OR IGNORE INTO regimen_declaracion_config_detalle_new (
    config_id,
    uso_cfdi_clave,
    orden,
    created_at
)
SELECT
    m.new_id AS config_id,
    d.uso_cfdi_clave,
    d.orden,
    d.created_at
FROM regimen_declaracion_config_detalle d
JOIN _tmp_config_id_map m ON m.old_id = d.config_id;

DROP TABLE regimen_declaracion_config_detalle;
ALTER TABLE regimen_declaracion_config_detalle_new RENAME TO regimen_declaracion_config_detalle;

DROP TABLE regimen_declaracion_config;
ALTER TABLE regimen_declaracion_config_new RENAME TO regimen_declaracion_config;

CREATE INDEX IF NOT EXISTS ix_config_regimen
  ON regimen_declaracion_config (regimen_fiscal_id);

CREATE INDEX IF NOT EXISTS ix_config_detalle_config
  ON regimen_declaracion_config_detalle (config_id);

DROP TABLE IF EXISTS _tmp_config_id_map;
DROP TABLE IF EXISTS _tmp_config_keep_ids;

COMMIT;
PRAGMA foreign_keys = ON;
