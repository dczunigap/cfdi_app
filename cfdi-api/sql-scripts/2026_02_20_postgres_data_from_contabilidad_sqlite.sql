-- Auto-generated data migration from SQLite.
-- Source: C:/codigos_fuente/cfdi_app/cfdi-api/database/contabilidad.sqlite
-- Target: PostgreSQL 14+

BEGIN;

-- Clean target tables before insert
TRUNCATE TABLE "user_rfcs", "regimen_declaracion_config_detalle", "rfcs", "regimen_declaracion_config", "pagos", "conceptos", "catalogo_regimen_fiscal", "catalogo_uso_cfdi_deduccion", "users", "sat_descargas", "sat_credentials", "rfc_phones", "retenciones_plataforma", "platform_rfcs", "facturas", "declaraciones_pdf", "catalogo_tipo_persona", "catalogo_tipo_declaracion" RESTART IDENTITY CASCADE;

-- catalogo_tipo_declaracion: 2 rows
INSERT INTO "catalogo_tipo_declaracion" ("clave", "descripcion", "activo", "created_at", "updated_at") VALUES ('MENSUAL', 'Declaracion mensual', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_tipo_declaracion" ("clave", "descripcion", "activo", "created_at", "updated_at") VALUES ('ANUAL', 'Declaracion anual', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');

-- catalogo_tipo_persona: 3 rows
INSERT INTO "catalogo_tipo_persona" ("clave", "descripcion") VALUES ('PM', 'Persona Moral');
INSERT INTO "catalogo_tipo_persona" ("clave", "descripcion") VALUES ('PF', 'Persona Fisica');
INSERT INTO "catalogo_tipo_persona" ("clave", "descripcion") VALUES ('EXT', 'Residente en el extranjero sin establecimiento permanente');

-- users: 2 rows
INSERT INTO "users" ("id", "username", "email", "password_hash", "is_active", "last_login_at", "created_at", "updated_at", "is_admin") VALUES (1, 'admin', 'admin@empresa.com', 'pbkdf2_sha256$390000$WGwg_AixCUNQUnq8-rLR9g$Y54__7-1SYYe-VdjKIO0fhymh6BeAj4uaEPYx8lTllo', TRUE, '2026-02-20 21:13:37.486797', '2026-01-27 23:57:39.361182', '2026-02-20 21:13:37.503336', FALSE);
INSERT INTO "users" ("id", "username", "email", "password_hash", "is_active", "last_login_at", "created_at", "updated_at", "is_admin") VALUES (2, 'sys_admin', 'sys_admin@empresa.com', 'pbkdf2_sha256$390000$WGwg_AixCUNQUnq8-rLR9g$Y54__7-1SYYe-VdjKIO0fhymh6BeAj4uaEPYx8lTllo', TRUE, '2026-02-18 02:21:47.351569', '2026-02-04 01:59:18', '2026-02-18 02:21:47.355566', TRUE);

-- catalogo_uso_cfdi_deduccion: 15 rows
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D01', 'Honorarios medicos, dentales y gastos hospitalarios', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D02', 'Gastos medicos por incapacidad o discapacidad', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D03', 'Gastos funerales (hasta una UMA anual)', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D04', 'Donativos a instituciones autorizadas', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D05', 'Intereses reales efectivamente pagados por creditos hipotecarios (casa habitacion)', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D06', 'Aportaciones voluntarias al SAR o planes personales de retiro', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D07', 'Primas por seguros de gastos medicos', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D08', 'Gastos de transporte escolar obligatorio', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D09', 'Depositos en cuentas especiales para el ahorro y primas de seguros de vida', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('D10', 'Pagos por servicios educativos (colegiaturas)', 'ANUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('G01', 'Adquisicion de mercancias', 'MENSUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('G03', 'Gastos en general', 'MENSUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('I03', 'Equipo de transporte', 'MENSUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('I04', 'Equipo de computo y accesorios', 'MENSUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');
INSERT INTO "catalogo_uso_cfdi_deduccion" ("clave", "descripcion", "tipo_declaracion_clave", "activo", "created_at", "updated_at") VALUES ('I08', 'Inversiones', 'MENSUAL', 1, '2026-02-17 04:23:21', '2026-02-17 04:23:21');

-- catalogo_regimen_fiscal: 20 rows
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (1, 'PM', '601', 'General de Ley Personas Morales', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (2, 'PM', '603', 'Personas Morales con Fines no Lucrativos', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (3, 'PM', '620', 'Sociedades Cooperativas de Produccion que optan por diferir ingresos', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (4, 'PM', '622', 'Actividades Agricolas, Ganaderas, Silvicolas y Pesqueras', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (5, 'PM', '623', 'Opcional para Grupos de Sociedades', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (6, 'PM', '624', 'Coordinados', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (7, 'PM', '626', 'Regimen Simplificado de Confianza (RESICO - PM)', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (8, 'PF', '605', 'Sueldos y Salarios e Ingresos Asimilados a Salarios', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (9, 'PF', '606', 'Arrendamiento', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (10, 'PF', '607', 'Regimen de Enajenacion o Adquisicion de Bienes', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (11, 'PF', '608', 'Demas ingresos', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (12, 'PF', '611', 'Ingresos por Dividendos (socios y accionistas)', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (13, 'PF', '612', 'Personas Fisicas con Actividades Empresariales y Profesionales', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (14, 'PF', '614', 'Ingresos por Intereses', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (15, 'PF', '615', 'Regimen de los ingresos por obtencion de premios', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (16, 'PF', '616', 'Sin obligaciones fiscales', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (17, 'PF', '621', 'Incorporacion Fiscal', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (18, 'PF', '625', 'Actividades Empresariales con ingresos por Plataformas Tecnologicas', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (19, 'PF', '626', 'Regimen Simplificado de Confianza (RESICO - PF)', 1);
INSERT INTO "catalogo_regimen_fiscal" ("id", "tipo_persona_clave", "clave", "descripcion", "activo") VALUES (20, 'EXT', '610', 'Residentes en el Extranjero sin Establecimiento Permanente en Mexico', 1);

-- regimen_declaracion_config: 2 rows
INSERT INTO "regimen_declaracion_config" ("id", "regimen_fiscal_id", "tipo_declaracion_clave", "activo", "incluir_acumulado_mensual_en_anual", "created_at", "updated_at") VALUES (1, 18, 'MENSUAL', 1, 1, '2026-02-17 04:27:28', '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config" ("id", "regimen_fiscal_id", "tipo_declaracion_clave", "activo", "incluir_acumulado_mensual_en_anual", "created_at", "updated_at") VALUES (2, 18, 'ANUAL', 1, 1, '2026-02-17 04:27:28', '2026-02-17 04:27:28');

-- regimen_declaracion_config_detalle: 15 rows
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (6, 2, 'D01', 1, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (7, 2, 'D02', 2, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (8, 2, 'D03', 3, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (9, 2, 'D04', 4, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (10, 2, 'D05', 5, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (11, 2, 'D06', 6, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (12, 2, 'D07', 7, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (13, 2, 'D08', 8, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (14, 2, 'D09', 9, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (15, 2, 'D10', 10, '2026-02-17 04:27:28');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (170, 1, 'G01', 1, '2026-02-17 18:30:49.057384');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (171, 1, 'G03', 2, '2026-02-17 18:30:49.057391');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (172, 1, 'I03', 3, '2026-02-17 18:30:49.057392');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (173, 1, 'I04', 4, '2026-02-17 18:30:49.057394');
INSERT INTO "regimen_declaracion_config_detalle" ("id", "config_id", "uso_cfdi_clave", "orden", "created_at") VALUES (174, 1, 'I08', 5, '2026-02-17 18:30:49.057395');


SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM "users"), 1), true);
SELECT setval(pg_get_serial_sequence('catalogo_regimen_fiscal', 'id'), COALESCE((SELECT MAX(id) FROM "catalogo_regimen_fiscal"), 1), true);
SELECT setval(pg_get_serial_sequence('regimen_declaracion_config', 'id'), COALESCE((SELECT MAX(id) FROM "regimen_declaracion_config"), 1), true);
SELECT setval(pg_get_serial_sequence('regimen_declaracion_config_detalle', 'id'), COALESCE((SELECT MAX(id) FROM "regimen_declaracion_config_detalle"), 1), true);


COMMIT;
