PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Catalogo tipo de declaracion
INSERT OR IGNORE INTO catalogo_tipo_declaracion (clave, descripcion, activo)
VALUES
  ('MENSUAL', 'Declaracion mensual', 1),
  ('ANUAL', 'Declaracion anual', 1);

-- Deducciones personales para declaracion anual
INSERT OR IGNORE INTO catalogo_uso_cfdi_deduccion (clave, descripcion, tipo_declaracion_clave, activo)
VALUES
  ('D01', 'Honorarios medicos, dentales y gastos hospitalarios', 'ANUAL', 1),
  ('D02', 'Gastos medicos por incapacidad o discapacidad', 'ANUAL', 1),
  ('D03', 'Gastos funerales (hasta una UMA anual)', 'ANUAL', 1),
  ('D04', 'Donativos a instituciones autorizadas', 'ANUAL', 1),
  ('D05', 'Intereses reales efectivamente pagados por creditos hipotecarios (casa habitacion)', 'ANUAL', 1),
  ('D06', 'Aportaciones voluntarias al SAR o planes personales de retiro', 'ANUAL', 1),
  ('D07', 'Primas por seguros de gastos medicos', 'ANUAL', 1),
  ('D08', 'Gastos de transporte escolar obligatorio', 'ANUAL', 1),
  ('D09', 'Depositos en cuentas especiales para el ahorro y primas de seguros de vida', 'ANUAL', 1),
  ('D10', 'Pagos por servicios educativos (colegiaturas)', 'ANUAL', 1);

-- Claves de uso CFDI para deducciones de declaracion mensual
INSERT OR IGNORE INTO catalogo_uso_cfdi_deduccion (clave, descripcion, tipo_declaracion_clave, activo)
VALUES
  ('G01', 'Adquisicion de mercancias', 'MENSUAL', 1),
  ('G03', 'Gastos en general', 'MENSUAL', 1),
  ('I03', 'Equipo de transporte', 'MENSUAL', 1),
  ('I04', 'Equipo de computo y accesorios', 'MENSUAL', 1),
  ('I08', 'Inversiones', 'MENSUAL', 1);

COMMIT;
PRAGMA foreign_keys = ON;
