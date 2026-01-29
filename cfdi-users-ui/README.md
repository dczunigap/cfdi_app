# cfdi-users-ui

UI en Next.js para administrar usuarios del sistema CFDI (alta, edicion y baja) contra el API `/api/v1/users`.

## Requisitos
- Node.js 18+
- `cfdi-api` corriendo y accesible (por defecto `http://127.0.0.1:8000`)

## Instalacion
```bash
cd cfdi-users-ui
npm install
copy .env.example .env.local
```

## Variables de entorno
- `ADMIN_USER` y `ADMIN_PASS`: credenciales del superusuario (obligatorias).
- `NEXT_PUBLIC_API_BASE_URL`: base del API (default `http://127.0.0.1:8000/api/v1`).
- `AUTH_COOKIE_NAME`: nombre de la cookie (default `cfdi_users_auth`).
- `AUTH_COOKIE_TTL_SECONDS`: TTL de la cookie en segundos (default `28800`).
- `AUTH_MODE`: reservado para futuros modos (default `local`).
- `APP_TITLE`: titulo mostrado en la pantalla de acceso (default `CFDI USERS`).
- `APP_SUBTITLE`: subtitulo mostrado en la pantalla de acceso (default `Administracion de usuarios`).

## Desarrollo
```bash
npm run dev
```
La app queda en `http://localhost:3000`.

## Produccion
```bash
npm run build
npm run start
```

## Notas
- La ruta `/users` requiere sesion iniciada con el superusuario.
- Las operaciones usan los endpoints `GET/POST/PUT/DELETE /users` del `cfdi-api`.
