PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- 1) Catalogo de tipo de declaracion (MENSUAL / ANUAL)
CREATE TABLE IF NOT EXISTS catalogo_tipo_declaracion (
    clave TEXT PRIMARY KEY,
    descripcion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2) Catalogo de claves uso CFDI para deducciones
CREATE TABLE IF NOT EXISTS catalogo_uso_cfdi_deduccion (
    clave TEXT PRIMARY KEY,
    descripcion TEXT NOT NULL,
    tipo_declaracion_clave TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_uso_cfdi_tipo_decl
      FOREIGN KEY (tipo_declaracion_clave)
      REFERENCES catalogo_tipo_declaracion (clave)
);

CREATE INDEX IF NOT EXISTS ix_uso_cfdi_tipo_decl
  ON catalogo_uso_cfdi_deduccion (tipo_declaracion_clave);

-- 3) Configuracion por regimen + tipo
CREATE TABLE IF NOT EXISTS regimen_declaracion_config (
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

CREATE INDEX IF NOT EXISTS ix_config_regimen
  ON regimen_declaracion_config (regimen_fiscal_id);

-- 4) Detalle de usos permitidos por configuracion
CREATE TABLE IF NOT EXISTS regimen_declaracion_config_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER NOT NULL,
    uso_cfdi_clave TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_config_detalle_config
      FOREIGN KEY (config_id)
      REFERENCES regimen_declaracion_config (id)
      ON DELETE CASCADE,
    CONSTRAINT fk_config_detalle_uso
      FOREIGN KEY (uso_cfdi_clave)
      REFERENCES catalogo_uso_cfdi_deduccion (clave),
    CONSTRAINT ux_config_detalle
      UNIQUE (config_id, uso_cfdi_clave)
);

CREATE INDEX IF NOT EXISTS ix_config_detalle_config
  ON regimen_declaracion_config_detalle (config_id);

COMMIT;
PRAGMA foreign_keys = ON;
