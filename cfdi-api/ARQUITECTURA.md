# Dominio y fronteras (Paso 1)

## Contextos principales
- Facturas: CFDI emitidos/recibidos, conceptos y pagos.
- Retenciones: XML de retenciones de plataformas.
- Declaraciones: PDFs de declaraciones mensuales y su resumen.
- Reportes: resumen mensual, modo declaracion y hoja SAT.

## Fronteras de responsabilidad
- Core (domain/application): reglas de negocio, calculos y casos de uso.
- Inbound: HTTP/CLI (entrada de datos y orquestacion).
- Outbound: DB, filesystem y parsers (infraestructura).

## Dependencias permitidas
- Core no depende de FastAPI, SQLAlchemy ni filesystem.
- Adapters dependen de core, no al reves.

## Flujo hexagonal (resumen)
Inbound (FastAPI) -> Use Case -> Port -> Outbound (DB/Files)
