import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';
import { AuthShellComponent } from './layouts/auth-shell.component';
import { MainShellComponent } from './layouts/main-shell.component';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'welcome',
  },
  {
    path: '',
    component: AuthShellComponent,
    children: [
      {
        path: 'login',
        loadComponent: () =>
          import('./features/auth/ui/login-page.component').then((m) => m.LoginPageComponent),
      },
      {
        path: 'welcome',
        canActivate: [authGuard],
        loadComponent: () =>
          import('./features/auth/ui/welcome-page.component').then(
            (m) => m.WelcomePageComponent,
          ),
      },
    ],
  },
  {
    path: '',
    component: MainShellComponent,
    canActivateChild: [authGuard],
    children: [
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
        path: 'declaracion',
        loadComponent: () =>
          import('./features/declaracion/ui/declaracion-page.component').then(
            (m) => m.DeclaracionPageComponent,
          ),
      },
      {
        path: 'facturas',
        loadComponent: () =>
          import('./features/facturas/ui/facturas-page.component').then(
            (m) => m.FacturasPageComponent,
          ),
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
        path: 'platform-rfcs',
        loadComponent: () =>
          import('./features/platform-rfcs/ui/platform-rfcs-page.component').then(
            (m) => m.PlatformRfcsPageComponent,
          ),
      },
      {
        path: 'admin-sat',
        loadComponent: () =>
          import('./features/admin-sat/ui/admin-sat-page.component').then(
            (m) => m.AdminSatPageComponent,
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
    ],
  },
];
