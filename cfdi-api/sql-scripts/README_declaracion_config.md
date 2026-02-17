# Declaracion Config - Operacion

## Orden de ejecucion (si es ambiente nuevo)
1. `2026_02_13_rfc_catalogs.sql`
2. `2026_02_16_declaracion_config_schema.sql`
3. `2026_02_16_declaracion_config_triggers.sql`
4. `2026_02_17_declaracion_catalogos_seed.sql`
5. `2026_02_17_regimen_625_config_base.sql` (opcional, solo si quieres base para regimen 625)

## Orden de ejecucion (si ya existia esquema con ejercicio)
1. `2026_02_17_declaracion_config_remove_ejercicio.sql`
2. `2026_02_17_declaracion_catalogos_seed.sql`
3. `2026_02_17_regimen_625_config_base.sql` (opcional)

## Endpoints relevantes
- `GET /api/v1/admin/declaracion-config/catalogos`
- `GET /api/v1/admin/declaracion-config?regimen_fiscal_clave=625&tipo_declaracion=MENSUAL`
- `PUT /api/v1/admin/declaracion-config`
- `GET /api/v1/summary?tipo_declaracion=MENSUAL&year=2026&month=1`
- `GET /api/v1/summary?tipo_declaracion=ANUAL&year=2026`
- `GET /api/v1/declaracion?tipo_declaracion=MENSUAL&year=2026&month=1`
- `GET /api/v1/declaracion?tipo_declaracion=ANUAL&year=2026`

## Checklist de smoke test
1. En `cfdi-admin-ui`, abrir `Config Declaracion`.
2. Seleccionar regimen `625` y tipo `MENSUAL`; agregar/quitar usos y guardar.
3. Repetir para tipo `ANUAL`.
4. En `cfdi-ui`:
   - Resumen mensual: validar que solo use usos de tipo mensual.
   - Resumen anual: validar deducciones anuales y acumulado mensual.
   - Declaracion anual: validar que no se muestren bloques de PDF/acuse SAT.
5. Validar que RFC del usuario tenga regimen fiscal asignado.
