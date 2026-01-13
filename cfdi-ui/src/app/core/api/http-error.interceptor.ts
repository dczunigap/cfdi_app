import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { AppAlertService } from '../../shared/ui/alert/alert.service';

export const httpErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const alerts = inject(AppAlertService);
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err?.status === 0) {
        alerts.error('Sin conexion con el servidor.');
      } else if (err.status === 401) {
        alerts.warning('No autorizado.');
      } else if (err.status >= 500) {
        alerts.error('Error del servidor.');
      }
      return throwError(() => err);
    })
  );
};
