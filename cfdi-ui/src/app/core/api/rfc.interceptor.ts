import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { API_BASE_URL } from './api-client';
import { RfcService } from '../rfc/rfc.service';

const RFC_ENDPOINTS = [
  '/facturas',
  '/retenciones',
  '/declaraciones',
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

  const url = req.url;
  const apiIndex = url.indexOf(API_BASE_URL);
  const isApi = apiIndex > -1 || url.startsWith('/api');
  if (!isApi) {
    return next(req);
  }

  const path =
    apiIndex >= 0 ? url.slice(apiIndex + API_BASE_URL.length) : url.replace(/^\/api\/?/, '/');
  const shouldAttach = RFC_ENDPOINTS.some((prefix) => path.startsWith(prefix));
  if (!shouldAttach) {
    return next(req);
  }

  return next(req.clone({ setHeaders: { 'X-RFC': rfc } }));
};
