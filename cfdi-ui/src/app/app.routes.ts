import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'importacion',
  },
  {
    path: 'importacion',
    loadComponent: () =>
      import('./features/importacion/ui/importacion-page.component').then(
        (m) => m.ImportacionPageComponent,
      ),
  },
  {
    path: 'summary',
    loadComponent: () =>
      import('./features/summary/ui/summary-page.component').then(
        (m) => m.SummaryPageComponent,
      ),
  },
  {
    path: 'reportes',
    redirectTo: 'summary',
    pathMatch: 'full',
  },
  {
    path: 'declaracion',
    loadComponent: () =>
      import('./features/declaracion/ui/declaracion-page.component').then(
        (m) => m.DeclaracionPageComponent,
      ),
  },
  {
    path: 'facturas',
    loadComponent: () =>
      import('./features/facturas/ui/facturas-page.component').then((m) => m.FacturasPageComponent),
  },
  {
    path: 'facturas/:id',
    loadComponent: () =>
      import('./features/facturas/ui/facturas-detail.component').then(
        (m) => m.FacturasDetailComponent,
      ),
  },
  {
    path: 'retenciones',
    loadComponent: () =>
      import('./features/retenciones/ui/retenciones-page.component').then(
        (m) => m.RetencionesPageComponent,
      ),
  },
  {
    path: 'retenciones/:id',
    loadComponent: () =>
      import('./features/retenciones/ui/retenciones-detail.component').then(
        (m) => m.RetencionesDetailComponent,
      ),
  },
  {
    path: 'declaraciones',
    loadComponent: () =>
      import('./features/declaraciones/ui/declaraciones-page.component').then(
        (m) => m.DeclaracionesPageComponent,
      ),
  },
  {
    path: 'declaraciones/:id',
    loadComponent: () =>
      import('./features/declaraciones/ui/declaraciones-detail.component').then(
        (m) => m.DeclaracionesDetailComponent,
      ),
  },
];
