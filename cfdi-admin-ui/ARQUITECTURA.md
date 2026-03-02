# Arquitectura de cfdi-admin-ui

Frontend Next.js (App Router) con enfoque **BFF + modulos por feature**.

## Que significa BFF + modulos por feature

### BFF (Backend for Frontend)
Es una capa backend ligera dentro del mismo frontend (aqui, API routes de Next en `app/api/*`) que:
- recibe requests del navegador,
- maneja autenticacion (cookie httpOnly con JWT),
- reenvia llamadas al backend real (`cfdi-api`),
- oculta detalles sensibles al cliente (token y URL interna del API).

En este proyecto, el BFF vive en:
- `app/api/auth/login/route.ts`
- `app/api/auth/logout/route.ts`
- `app/api/auth/me/route.ts`
- `app/api/proxy/[...path]/route.ts`

### Modulos por feature
La app se organiza por dominio funcional, no por tipo tecnico global.
Cada feature agrupa su UI, su API y sus tipos:
- `features/users/*`
- `features/admin-sat/*`
- `features/platform-rfcs/*`
- `features/declaracion-config/*`
- `features/auth/*`

Beneficios:
- menor acoplamiento entre modulos,
- cambios localizados por negocio,
- escalado mas simple por equipo o por funcionalidad.

## Estructura principal
- `app/`: rutas y layouts de Next (UI routing + API routes BFF).
- `features/`: componentes, hooks, APIs y tipos por modulo funcional.
- `lib/`: utilidades compartidas (`env`, `api`, `errors`).
- `components/`: componentes UI reutilizables.

## Diagrama de capas (BFF)
```mermaid
flowchart LR
    Browser[Navegador] --> Pages[Next Pages / Components]
    Pages --> FeatureApi[features/*/api.ts]
    FeatureApi --> ApiClient[lib/api.ts]
    ApiClient --> BFF[Next API Routes<br/>app/api/*]
    BFF --> CFDI[cfdi-api /api/v1]
    CFDI --> BFF --> Pages --> Browser
```

## Diagrama tecnico por componentes
```mermaid
flowchart TB
    subgraph App["app (Next App Router)"]
      Layout["layout.tsx + providers.tsx"]
      Pages["*/page.tsx"]
      ApiRoutes["api/auth/* + api/proxy/[...path]/route.ts"]
    end

    subgraph Features["features"]
      FUsers["users: components + hooks + api + types"]
      FSat["admin-sat: components + api + types + validators"]
      FPlat["platform-rfcs: components + api + types"]
      FDec["declaracion-config: components + api + types"]
      FAuth["auth: login component"]
    end

    subgraph Lib["lib"]
      Env["env.ts"]
      Api["api.ts"]
      Err["errors.ts"]
    end

    subgraph Backend["Backend"]
      Proxy["/api/proxy/*"]
      Auth["/api/auth/login|logout|me"]
      RealApi["cfdi-api /api/v1"]
    end

    Layout --> Pages
    Pages --> FUsers
    Pages --> FSat
    Pages --> FPlat
    Pages --> FDec
    Pages --> FAuth
    FUsers --> Api
    FSat --> Api
    FPlat --> Api
    FDec --> Api
    FAuth --> Auth
    Api --> Proxy
    ApiRoutes --> Proxy
    ApiRoutes --> Auth
    Env --> Api
    Proxy --> RealApi
    Auth --> RealApi
    Err --> FUsers
```

## Secuencia real: login + llamadas autenticadas
```mermaid
sequenceDiagram
    participant U as Usuario
    participant UI as LoginPage (client)
    participant BFFAuth as /api/auth/login
    participant API as cfdi-api /auth/login
    participant Cookie as Cookie httpOnly
    participant UIFeature as Feature UI (users/admin-sat)
    participant BFFProxy as /api/proxy/*
    participant APISec as cfdi-api protegido

    U->>UI: Envia correo/password
    UI->>BFFAuth: POST /api/auth/login
    BFFAuth->>API: POST /api/v1/auth/login
    API-->>BFFAuth: access_token
    BFFAuth-->>Cookie: Set-Cookie httpOnly
    BFFAuth-->>UI: { ok: true }

    UIFeature->>BFFProxy: GET /api/proxy/users
    BFFProxy->>Cookie: Lee token
    BFFProxy->>APISec: Reenvia con Authorization
    APISec-->>BFFProxy: datos
    BFFProxy-->>UIFeature: respuesta
```

## Referencias clave
- `app/providers.tsx` (React Query provider)
- `app/api/auth/login/route.ts`
- `app/api/auth/logout/route.ts`
- `app/api/auth/me/route.ts`
- `app/api/proxy/[...path]/route.ts`
- `proxy.ts` (proteccion de rutas privadas)
- `features/users/hooks/use-users.ts`
- `features/users/api.ts`
- `lib/api.ts`
- `lib/env.ts`

## Endurecimiento aplicado (Sprint 1)
- Middleware (`proxy.ts`) protege rutas privadas:
  - `/users/*`
  - `/admin-sat/*`
  - `/platform-rfcs/*`
  - `/declaracion-config/*`
  - `/rfc-users/*`
- El cliente ya no inyecta token via variable publica (`NEXT_PUBLIC_API_TOKEN`).
- La autenticacion de usuario queda centralizada en cookie httpOnly + BFF (`/api/auth/*` y `/api/proxy/*`).
