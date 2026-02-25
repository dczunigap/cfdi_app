import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { API_BASE_URL } from '../../../core/api/api-client';
import { SummaryData, SummaryDetails, TipoDeclaracion } from './summary.model';

@Injectable({ providedIn: 'root' })
export class SummaryRepository {
  private readonly http = inject(HttpClient);

  fetch(tipoDeclaracion: TipoDeclaracion, year?: number | null, month?: number | null) {
    let params = new HttpParams();
    params = params.set('tipo_declaracion', tipoDeclaracion);
    if (year) params = params.set('year', year);
    if (month) params = params.set('month', month);
    return this.http.get<SummaryData>(`${API_BASE_URL}/summary`, { params });
  }

  fetchDetails(tipoDeclaracion: TipoDeclaracion, year?: number | null, month?: number | null) {
    let params = new HttpParams();
    params = params.set('tipo_declaracion', tipoDeclaracion);
    if (year) params = params.set('year', year);
    if (month) params = params.set('month', month);
    return this.http.get<SummaryDetails>(`${API_BASE_URL}/summary/details`, { params });
  }
}
