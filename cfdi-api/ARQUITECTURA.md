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

# SAT (credenciales y SOAP)

## Objetivo
Separar la orquestacion del SAT (SOAP/WS-Security/PKCS12) del dominio y los casos de uso.

## Puertos
- `SatCredentialsRepository`: persistencia de credenciales SAT.
- `SatCrypto`: cifrado/descifrado de PFX y password.
- `SatGateway`: interfaz para operaciones SAT (autenticar, solicitar/verificar/descargar).

## Adapters
- `adapters/outbound/db/repositories/sat_credentials.py` implementa `SatCredentialsRepository`.
- `adapters/services/sat/crypto/*` implementa `SatCrypto` (Fernet).
- `adapters/services/sat/sat_gateway.py` implementa `SatGateway` (SOAP).
- `adapters/services/sat/soap/*` encapsula transporte y parsing.
- `adapters/services/sat/wsse/*` encapsula WS-Security y firma XML.
- `adapters/services/sat/pkcs12/*` encapsula manejo de PFX.

## Use cases
- `application/sat/use_cases.py` orquesta alta/baja de credenciales y autenticacion SAT
  via `SatGateway`, sin conocer detalles de SOAP/WSSE.
