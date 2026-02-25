# Arquitectura de cfdi-ui

Frontend Angular (standalone components) con arquitectura modular por `core`, `features`, `shared` y `layouts`.

## Capas y responsabilidades
- `core`: infraestructura transversal (auth, API base, interceptors, RFC).
- `features`: modulos de negocio (facturas, retenciones, declaraciones, sat-descargas, etc.).
- `shared`: componentes/servicios reutilizables de UI (alerts, loading, imports, helpers).
- `layouts`: shells de navegacion (`AuthShellComponent` y `MainShellComponent`).

## Ensamblado de la app
- `src/main.ts`: bootstrap de la aplicacion standalone.
- `src/app/app.config.ts`: providers globales (router, HttpClient, interceptors, animations).
- `src/app/app.routes.ts`: rutas lazy por feature y guards de autenticacion.

## Diagrama de capas
```mermaid
flowchart LR
    Browser[Navegador] --> Router[Angular Router]
    Router --> Layouts[Layouts<br/>AuthShell / MainShell]
    Layouts --> UI[Feature UI Components]
    UI --> Data[Feature Data Layer<br/>Repository/Facade]
    Data --> Store[State Layer<br/>Elf Stores/Queries]
    Data --> Api[HttpClient]
    Api --> Interceptors[Interceptors<br/>loading, auth, rfc, http-error]
    Interceptors --> Backend[cfdi-api<br/>/api/v1]
```

## Diagrama tecnico por carpetas
```mermaid
flowchart TB
    subgraph Core["src/app/core"]
      Auth["auth/* (service, guard, interceptor)"]
      ApiCore["api/* (api-client, rfc/http-error interceptors)"]
      Rfc["rfc/rfc.service.ts"]
    end

    subgraph Features["src/app/features"]
      UI["*/ui/*.component.ts"]
      Repo["*/data/*.repository.ts"]
      Store["*/data/*.store.ts"]
      Queries["*/data/*.queries.ts"]
      Facade["*/data/*.facade.ts (algunos modulos)"]
    end

    subgraph Shared["src/app/shared"]
      SharedUi["ui/* (loading, alert, imports, rfc-selector)"]
      Utils["utils/ui-helpers.ts"]
    end

    subgraph AppBoot["App bootstrap"]
      Main["main.ts"]
      Config["app.config.ts"]
      Routes["app.routes.ts"]
    end

    Main --> Config --> Routes
    Routes --> UI
    Auth --> Routes
    UI --> Repo
    UI --> Facade
    Repo --> Store
    Queries --> UI
    Repo --> ApiCore
    Rfc --> ApiCore
    SharedUi --> UI
    Utils --> Facade
```

## Flujo tecnico de una pantalla (ejemplo: sat-descargas)
```mermaid
sequenceDiagram
    participant U as Usuario
    participant C as sat-descargas-page.component
    participant R as sat-descargas.repository
    participant S as sat-descargas.store
    participant I as Interceptors (auth/rfc/loading/http-error)
    participant A as cfdi-api

    U->>C: Crear solicitud
    C->>R: create(payload)
    R->>I: POST /sat/descargas
    I->>A: Request con Authorization + X-RFC
    A-->>I: SatDescarga
    I-->>R: response
    R->>S: upsertEntities(row)
    S-->>C: satDescargas$ (queries)
    C-->>U: UI actualizada
```

## Notas de diseno actuales
- Estado global por feature con `@ngneat/elf`.
- Carga de modulos por `loadComponent` (lazy) en rutas.
- Base URL de backend via `environment.apiBaseUrl` (default `/api/v1`).
- Guard de autenticacion configurable con `authEnabled`.
- Validacion de sesion configurable con `authValidationMode` (`local` o `server`).

## Referencias clave en el codigo
- `src/main.ts`
- `src/app/app.config.ts`
- `src/app/app.routes.ts`
- `src/app/core/auth/auth.service.ts`
- `src/app/core/auth/auth.guard.ts`
- `src/app/core/api/rfc.interceptor.ts`
- `src/app/features/facturas/data/facturas.repository.ts`
- `src/app/features/sat-descargas/data/sat-descargas.repository.ts`
