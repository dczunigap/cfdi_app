# CfdiUi

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 21.0.5.

## Arquitectura

- Ver detalle tecnico y diagramas Mermaid en [ARQUITECTURA.md](./ARQUITECTURA.md).

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.

## Environment

- `apiBaseUrl`: base URL del API (default `/api/v1`)
- `authEnabled`: habilita guard de autenticación (default `true`)
- `authValidationMode`: `local` (solo exp del JWT) o `server` (valida con `GET /auth/me`)

## Data layer convention

- Los `repository` devuelven `Observable` (sin `subscribe` interno).
- La suscripción se maneja en `facade` o `component`, con control explícito de errores y ciclo de vida.

## Filtros de Facturas

- El modulo de facturas ya no usa filtro manual `uso_cfdi`.
- El UI filtra deducibilidad en memoria, usando el catalogo de `/deducciones/catalogo`.
- Parametros de deduccion usados en API/MCP:
  - `tipo_declaracion`: `MENSUAL|ANUAL`
  - `deducibilidad`: `TODAS|DEDUCIBLES|NO_DEDUCIBLES`

## Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

## Running unit tests

To execute unit tests with the [Vitest](https://vitest.dev/) test runner, use the following command:

```bash
npm run test:unit
```

To execute the Angular/Karma tests (if needed), use:

```bash
npm test
```

To run lint/typecheck, use:

```bash
npm run lint
```

## Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

## Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.
