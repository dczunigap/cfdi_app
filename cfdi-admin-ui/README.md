# cfdi-admin-ui

UI en Next.js para administrar usuarios y catalogos SAT del sistema CFDI.

## Requisitos
- Node.js 18+
- `cfdi-api` corriendo y accesible (por defecto `http://127.0.0.1:8000`)

## Instalacion
```bash
cd cfdi-admin-ui
npm install
copy .env.example .env.local
```

## Variables de entorno
- `API_BASE_URL`: base del API para el servidor (default `http://127.0.0.1:8000/api/v1`).
- `NEXT_PUBLIC_API_BASE_URL`: base publica (default `/api/proxy`).
- `AUTH_COOKIE_NAME`: nombre de la cookie (default `cfdi_users_auth`).
- `AUTH_COOKIE_TTL_SECONDS`: TTL de la cookie en segundos (default `28800`).
- `AUTH_MODE`: reservado para futuros modos (default `local`).
- `APP_TITLE`: titulo mostrado en la pantalla de acceso (default `CFDI Admin`).
- `APP_SUBTITLE`: subtitulo mostrado en la pantalla de acceso (default `Administracion de usuarios`).

## Desarrollo
```bash
npm run dev
```
La app queda en `http://localhost:3000`.

## Flujo de login y proxy
1. El login llama a `POST /api/auth/login` (route de Next).
2. Esa route autentica contra `cfdi-api` (`/api/v1/auth/login`) y guarda el JWT en una cookie httpOnly.
3. El cliente hace requests a `/api/proxy/*`, y el proxy adjunta el JWT desde la cookie.

## Produccion
```bash
npm run build
npm run start
```

## Notas
- El login usa `/api/v1/auth/login` del `cfdi-api` y guarda el JWT en cookie httpOnly.
- Las llamadas desde el cliente van a `/api/proxy/*`, que adjunta el token desde la cookie.
- Las operaciones usan los endpoints `GET/POST/PUT/DELETE /users` y los catalogos SAT.
