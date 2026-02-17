PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TRIGGER IF NOT EXISTS trg_tipo_decl_updated_at
AFTER UPDATE ON catalogo_tipo_declaracion
FOR EACH ROW
BEGIN
  UPDATE catalogo_tipo_declaracion
  SET updated_at = CURRENT_TIMESTAMP
  WHERE clave = NEW.clave;
END;

CREATE TRIGGER IF NOT EXISTS trg_uso_cfdi_updated_at
AFTER UPDATE ON catalogo_uso_cfdi_deduccion
FOR EACH ROW
BEGIN
  UPDATE catalogo_uso_cfdi_deduccion
  SET updated_at = CURRENT_TIMESTAMP
  WHERE clave = NEW.clave;
END;

CREATE TRIGGER IF NOT EXISTS trg_config_updated_at
AFTER UPDATE ON regimen_declaracion_config
FOR EACH ROW
BEGIN
  UPDATE regimen_declaracion_config
  SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.id;
END;

COMMIT;
PRAGMA foreign_keys = ON;
