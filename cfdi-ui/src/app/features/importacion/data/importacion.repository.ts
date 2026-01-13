import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from '../../../core/api/api-client';

export interface ImportXmlResult {
  cfdi_insertados: number;
  cfdi_duplicados: number;
  retenciones_insertadas: number;
  retenciones_duplicadas: number;
  errores: number;
}

export interface ImportPdfResult {
  insertados: number;
  duplicados: number;
  errores: number;
}

@Injectable({ providedIn: 'root' })
export class ImportacionRepository {
  constructor(private readonly http: HttpClient) {}

  importXml(files: File[]) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    return this.http.post<ImportXmlResult>(`${API_BASE_URL}/importar`, formData);
  }

  importPdf(files: File[], year?: number | null, month?: number | null) {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    let params = new HttpParams();
    if (year) params = params.set('year', year);
    if (month) params = params.set('month', month);
    return this.http.post<ImportPdfResult>(`${API_BASE_URL}/importar_pdf`, formData, { params });
  }
}
