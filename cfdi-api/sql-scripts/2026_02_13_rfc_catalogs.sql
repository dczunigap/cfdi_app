PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS catalogo_tipo_persona (
    clave TEXT PRIMARY KEY,
    descripcion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS catalogo_regimen_fiscal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_persona_clave TEXT NOT NULL,
    clave TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT fk_catalogo_regimen_tipo_persona FOREIGN KEY (tipo_persona_clave) REFERENCES catalogo_tipo_persona (clave),
    CONSTRAINT ux_regimen_fiscal_tipo_clave UNIQUE (tipo_persona_clave, clave)
);

INSERT OR IGNORE INTO catalogo_tipo_persona (clave, descripcion) VALUES
    ('PM', 'Persona Moral'),
    ('PF', 'Persona Fisica'),
    ('EXT', 'Residente en el extranjero sin establecimiento permanente');

INSERT OR IGNORE INTO catalogo_regimen_fiscal (tipo_persona_clave, clave, descripcion, activo) VALUES
    ('PM', '601', 'General de Ley Personas Morales', 1),
    ('PM', '603', 'Personas Morales con Fines no Lucrativos', 1),
    ('PM', '620', 'Sociedades Cooperativas de Produccion que optan por diferir ingresos', 1),
    ('PM', '622', 'Actividades Agricolas, Ganaderas, Silvicolas y Pesqueras', 1),
    ('PM', '623', 'Opcional para Grupos de Sociedades', 1),
    ('PM', '624', 'Coordinados', 1),
    ('PM', '626', 'Regimen Simplificado de Confianza (RESICO - PM)', 1),
    ('PF', '605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios', 1),
    ('PF', '606', 'Arrendamiento', 1),
    ('PF', '607', 'Regimen de Enajenacion o Adquisicion de Bienes', 1),
    ('PF', '608', 'Demas ingresos', 1),
    ('PF', '611', 'Ingresos por Dividendos (socios y accionistas)', 1),
    ('PF', '612', 'Personas Fisicas con Actividades Empresariales y Profesionales', 1),
    ('PF', '614', 'Ingresos por Intereses', 1),
    ('PF', '615', 'Regimen de los ingresos por obtencion de premios', 1),
    ('PF', '616', 'Sin obligaciones fiscales', 1),
    ('PF', '621', 'Incorporacion Fiscal', 1),
    ('PF', '625', 'Actividades Empresariales con ingresos por Plataformas Tecnologicas', 1),
    ('PF', '626', 'Regimen Simplificado de Confianza (RESICO - PF)', 1),
    ('EXT', '610', 'Residentes en el Extranjero sin Establecimiento Permanente en Mexico', 1);

CREATE TABLE IF NOT EXISTS rfcs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rfc TEXT NOT NULL UNIQUE,
    regimen_fiscal_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rfcs_regimen FOREIGN KEY (regimen_fiscal_id) REFERENCES catalogo_regimen_fiscal (id)
);

INSERT OR IGNORE INTO rfcs (rfc, regimen_fiscal_id, created_at, updated_at)
SELECT
    x.rfc,
    r.id AS regimen_fiscal_id,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM (
    SELECT
        UPPER(TRIM(ur.rfc)) AS rfc,
        CASE
            WHEN UPPER(TRIM(ur.rfc)) = 'XEXX010101000' THEN 'EXT'
            WHEN LENGTH(TRIM(ur.rfc)) = 12 THEN 'PM'
            ELSE 'PF'
        END AS tipo_persona_clave,
        CASE
            WHEN UPPER(TRIM(ur.rfc)) = 'XEXX010101000' THEN '610'
            WHEN LENGTH(TRIM(ur.rfc)) = 12 THEN '601'
            ELSE '612'
        END AS regimen_clave_default
    FROM user_rfcs ur
    GROUP BY UPPER(TRIM(ur.rfc))
) x
JOIN catalogo_regimen_fiscal r
    ON r.tipo_persona_clave = x.tipo_persona_clave
   AND r.clave = x.regimen_clave_default;

CREATE TABLE IF NOT EXISTS user_rfcs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    rfc_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_user_rfcs_new_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_user_rfcs_new_rfc FOREIGN KEY (rfc_id) REFERENCES rfcs (id)
);

INSERT INTO user_rfcs_new (id, user_id, rfc_id, created_at)
SELECT
    ur.id,
    ur.user_id,
    r.id,
    ur.created_at
FROM user_rfcs ur
JOIN rfcs r ON r.rfc = UPPER(TRIM(ur.rfc));

DROP TABLE user_rfcs;
ALTER TABLE user_rfcs_new RENAME TO user_rfcs;

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_rfc ON user_rfcs (user_id, rfc_id);
CREATE INDEX IF NOT EXISTS ix_user_rfcs_user_id ON user_rfcs (user_id);
CREATE INDEX IF NOT EXISTS ix_user_rfcs_rfc_id ON user_rfcs (rfc_id);
CREATE INDEX IF NOT EXISTS ix_rfcs_rfc ON rfcs (rfc);

COMMIT;
PRAGMA foreign_keys = ON;
