PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Configuracion base para regimen fiscal 625
-- Tipo MENSUAL: G01, G03, I03, I04, I08
-- Tipo ANUAL: D01..D10

INSERT OR IGNORE INTO regimen_declaracion_config (
    regimen_fiscal_id,
    tipo_declaracion_clave,
    activo,
    incluir_acumulado_mensual_en_anual,
    created_at,
    updated_at
)
SELECT
    r.id,
    'MENSUAL',
    1,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM catalogo_regimen_fiscal r
WHERE r.clave = '625'
  AND r.activo = 1;

INSERT OR IGNORE INTO regimen_declaracion_config (
    regimen_fiscal_id,
    tipo_declaracion_clave,
    activo,
    incluir_acumulado_mensual_en_anual,
    created_at,
    updated_at
)
SELECT
    r.id,
    'ANUAL',
    1,
    1,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM catalogo_regimen_fiscal r
WHERE r.clave = '625'
  AND r.activo = 1;

UPDATE regimen_declaracion_config
SET
    activo = 1,
    incluir_acumulado_mensual_en_anual = 1,
    updated_at = CURRENT_TIMESTAMP
WHERE regimen_fiscal_id IN (
    SELECT id FROM catalogo_regimen_fiscal WHERE clave = '625'
)
AND tipo_declaracion_clave IN ('MENSUAL', 'ANUAL');

-- Reemplaza detalle para asegurar base limpia y consistente
DELETE FROM regimen_declaracion_config_detalle
WHERE config_id IN (
    SELECT c.id
    FROM regimen_declaracion_config c
    JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
    WHERE r.clave = '625'
      AND c.tipo_declaracion_clave IN ('MENSUAL', 'ANUAL')
);

-- MENSUAL
INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'G01', 1, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'MENSUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'G03', 2, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'MENSUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'I03', 3, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'MENSUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'I04', 4, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'MENSUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'I08', 5, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'MENSUAL';

-- ANUAL
INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D01', 1, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D02', 2, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D03', 3, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D04', 4, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D05', 5, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D06', 6, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D07', 7, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D08', 8, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D09', 9, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

INSERT OR IGNORE INTO regimen_declaracion_config_detalle (config_id, uso_cfdi_clave, orden, created_at)
SELECT c.id, 'D10', 10, CURRENT_TIMESTAMP
FROM regimen_declaracion_config c
JOIN catalogo_regimen_fiscal r ON r.id = c.regimen_fiscal_id
WHERE r.clave = '625' AND c.tipo_declaracion_clave = 'ANUAL';

COMMIT;
PRAGMA foreign_keys = ON;
