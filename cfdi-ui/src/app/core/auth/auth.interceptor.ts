import { inject } from '@angular/core';
import { HttpInterceptorFn } from '@angular/common/http';

import { AuthService } from './auth.service';
import { API_BASE_URL } from '../api/api-client';

const SKIP_AUTH_PATHS = ['/auth/login'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const url = req.url;
  const apiIndex = url.indexOf(API_BASE_URL);
  const isApi = apiIndex > -1 || url.startsWith('/api');
  if (!isApi) {
    return next(req);
  }
  const path =
    apiIndex >= 0 ? url.slice(apiIndex + API_BASE_URL.length) : url.replace(/^\/api\/?/, '/');
  if (SKIP_AUTH_PATHS.some((prefix) => path.startsWith(prefix))) {
    return next(req);
  }
  const auth = inject(AuthService);
  const token = auth.getToken();
  if (!token) {
    return next(req);
  }
  return next(req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }));
};
