import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'facturas',
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
];
