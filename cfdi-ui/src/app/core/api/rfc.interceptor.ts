import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { API_BASE_URL } from './api-client';
import { RfcService } from '../rfc/rfc.service';

const RFC_ENDPOINTS = [
  '/sat',
  '/summary',
  '/summary/details',
  '/declaracion',
  '/sat_hoja',
  '/sat_report',
];

export const rfcInterceptor: HttpInterceptorFn = (req, next) => {
  const rfcService = inject(RfcService);
  const rfc = rfcService.selectedRfc();
  if (!rfc) {
    return next(req);
  }

  if (!req.url.startsWith(API_BASE_URL)) {
    return next(req);
  }

  const path = req.url.slice(API_BASE_URL.length);
  const shouldAttach = RFC_ENDPOINTS.some((prefix) => path.startsWith(prefix));
  if (!shouldAttach) {
    return next(req);
  }

  return next(req.clone({ setHeaders: { 'X-RFC': rfc } }));
};
