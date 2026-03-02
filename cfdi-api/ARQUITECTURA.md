# Arquitectura de cfdi-api

Backend Python (FastAPI) con arquitectura hexagonal ligera (ports and adapters).

## Contextos principales
- Facturas: CFDI emitidos/recibidos, conceptos y pagos.
- Retenciones: XML de retenciones de plataformas.
- Declaraciones: PDFs de declaraciones mensuales y su resumen.
- Reportes: resumen mensual, modo declaracion y hoja SAT.
- SAT: credenciales, autenticacion, solicitud/verificacion/descarga de paquetes.

## Capas y responsabilidades
- Domain (`app/domain`): entidades y reglas puras del negocio.
- Application (`app/application`): casos de uso/servicios que orquestan flujo.
- Ports (`app/ports`): contratos (interfaces/protocols) que usa application.
- Inbound adapters (`app/adapters/inbound`): entrada HTTP (FastAPI routes/schemas/deps).
- Outbound adapters (`app/adapters/outbound` y `app/adapters/services`): DB, storage FS/R2, SAT SOAP/mock, parsers.
- Infra (`app/infra`): ejecucion de jobs RQ y conexion de cola.

## Reglas de dependencia
- Core (domain + application) no depende de FastAPI, SQLAlchemy ni filesystem.
- Application depende de ports (abstracciones), no de implementaciones concretas.
- Adapters implementan ports y pueden depender de frameworks/librerias externas.
- Direccion esperada: `inbound -> application -> ports -> outbound`.

## Diagrama de capas
```mermaid
flowchart LR
    Client[Cliente: UI / Bot / Postman] --> Inbound[Inbound Adapters<br/>FastAPI routes/schemas/deps]
    Inbound --> App[Application<br/>Use Cases / Services]
    App --> Ports[Ports<br/>Protocols/Interfaces]
    Ports --> OutDB[Outbound Adapter<br/>SQL Repositories]
    Ports --> OutSAT[Outbound Adapter<br/>SAT Gateway SOAP/Mock]
    Ports --> OutStorage[Outbound Adapter<br/>Storage FS/R2]

    OutDB --> DB[(SQLite / SQL DB)]
    OutSAT --> SAT[(SAT SOAP)]
    OutStorage --> ST[(Filesystem / R2)]

    Domain[Domain entities and business rules] --- App
```

## Diagrama tecnico por componentes
```mermaid
flowchart TB
    subgraph API["app/adapters/inbound/http"]
      Routes["api/v1/routes/*.py"]
      Deps["deps.py (DB/Auth/X-RFC)"]
      Schemas["api/v1/schemas/*.py"]
    end

    subgraph APP["app/application"]
      UC_F["facturas/use_cases.py"]
      UC_RET["retenciones/use_cases.py"]
      UC_DEC["declaraciones/use_cases.py"]
      UC_SAT["sat/use_cases.py"]
      SVC_SAT["sat/descargas_service.py"]
      SVC_REP["reportes/service.py"]
    end

    subgraph PORTS["app/ports"]
      P_FACT["facturas_repo.py"]
      P_RET["retenciones_repo.py"]
      P_DEC["declaraciones_repo.py"]
      P_SAT_GW["sat_gateway.py"]
      P_SAT_CRED["sat_credentials_repo.py"]
      P_SAT_DESC["sat_descargas_repo.py"]
      P_SAT_ST["sat_storage.py"]
      P_SAT_ZIP["sat_zip_processor.py"]
      P_PDF_ST["pdf_storage.py"]
    end

    subgraph OUT["app/adapters/outbound + app/adapters/services"]
      SQL["db/repositories/*.py"]
      SOAP["services/sat/sat_gateway.py"]
      MOCK["services/sat/mock_gateway.py"]
      ST_FS["outbound/files/*storage*.py"]
      ST_R2["outbound/r2/*storage_r2.py"]
      PARSERS["services/parsers/*.py"]
    end

    subgraph INFRA["app/infra/queue"]
      RQTasks["rq_tasks.py"]
      RQConn["rq_conn.py"]
    end

    Routes --> UC_F
    Routes --> UC_RET
    Routes --> UC_DEC
    Routes --> UC_SAT
    Routes --> SVC_SAT
    Routes --> SVC_REP
    Deps --> Routes
    Schemas --> Routes

    UC_F --> P_FACT
    UC_RET --> P_RET
    UC_DEC --> P_DEC
    UC_SAT --> P_SAT_GW
    UC_SAT --> P_SAT_CRED
    SVC_SAT --> P_SAT_GW
    SVC_SAT --> P_SAT_CRED
    SVC_SAT --> P_SAT_DESC
    SVC_SAT --> P_SAT_ST
    SVC_SAT --> P_SAT_ZIP

    P_FACT --> SQL
    P_RET --> SQL
    P_DEC --> SQL
    P_SAT_CRED --> SQL
    P_SAT_DESC --> SQL
    P_SAT_GW --> SOAP
    P_SAT_GW --> MOCK
    P_SAT_ST --> ST_FS
    P_SAT_ST --> ST_R2
    P_SAT_ZIP --> PARSERS
    P_PDF_ST --> ST_FS
    P_PDF_ST --> ST_R2
    RQTasks --> SVC_SAT
    RQTasks --> RQConn
```

## Flujo tecnico SAT (secuencia real)
```mermaid
sequenceDiagram
    participant C as Cliente
    participant R as Route sat_descargas.py
    participant S as application/sat/descargas_service.py
    participant CR as SatCredentialsRepository
    participant GW as SatGateway (SOAP or mock)
    participant DR as SatDescargasRepository
    participant ST as SatStorage (FS or R2)
    participant DB as DB
    participant Q as RQ Worker

    C->>R: POST /api/v1/sat/descargas (X-RFC)
    R->>S: crear_solicitud_descarga(...)
    S->>CR: get_by_rfc(rfc)
    S->>GW: autenticar(...)
    S->>GW: solicitar_descarga(...)
    S->>DR: create(estado=SOLICITADA)
    DR->>DB: INSERT
    R-->>C: SatDescargaResponse

    alt SAT_AUTOVERIFY=1
      R->>Q: verificar_descarga_job(id)
      Q->>S: verificar_descarga(id)
      S->>GW: verificar_descarga(...)
      S->>DR: update(estado)
      alt estado=LISTA
        Q->>S: descargar_y_procesar(id)
        S->>GW: descargar_paquete(...)
        S->>ST: save_zip(...)
        S->>DB: upsert CFDI/retenciones
        S->>DR: update(estado=COMPLETADA)
      end
    end
```

## SAT: puertos y adapters
### Puertos
- `SatCredentialsRepository`: persistencia de credenciales SAT.
- `SatCrypto`: cifrado/descifrado de PFX y password.
- `SatGateway`: autenticar, solicitar/verificar/descargar paquetes SAT.
- `SatStorage`: persistencia y lectura de ZIP descargados.
- `SatZipProcessor`: procesamiento de ZIPs SAT (parsear XML e importar CFDI/retenciones).

### Implementaciones
- `adapters/outbound/db/repositories/sat_credentials.py` -> `SatCredentialsRepository`.
- `adapters/outbound/db/repositories/sat_descargas.py` -> `SatDescargasRepository`.
- `adapters/services/sat/crypto/*` -> `SatCrypto` (Fernet).
- `adapters/services/sat/sat_gateway.py` -> `SatGateway` SOAP.
- `adapters/services/sat/mock_gateway.py` -> `SatGateway` mock para pruebas.
- `adapters/outbound/files/sat_storage_fs.py` y `adapters/outbound/r2/sat_storage_r2.py` -> `SatStorage`.
- `adapters/services/parsers/sat_zip_processor.py` -> `SatZipProcessor`.
- `adapters/services/sat/soap/*`, `wsse/*`, `pkcs12/*` encapsulan detalles tecnicos SAT.

## Ensamblado de la app
- `app/main.py` crea la app FastAPI.
- Incluye router API con prefijo `/api/v1`.
- Inicializa metadatos SQLAlchemy al arranque (`Base.metadata.create_all`).
- Cierra engine al apagar.

## Nota de actualizacion
Documento validado contra la estructura de codigo actual:
- `app/main.py`
- `app/adapters/inbound/http/api/v1/routes/__init__.py`
- `app/application/sat/descargas_service.py`
- `app/ports/sat_gateway.py`
- `app/infra/queue/rq_tasks.py`
