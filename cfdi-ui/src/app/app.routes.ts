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
];
