import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { API_BASE_URL } from '../../../core/api/api-client';
import { DeclaracionSummary } from './declaracion.model';

@Injectable({ providedIn: 'root' })
export class DeclaracionRepository {
  private readonly http = inject(HttpClient);

  fetch(year: number, month: number | null, incomeSource: string, tipoDeclaracion: 'MENSUAL' | 'ANUAL') {
    const params = new HttpParams()
      .set('year', year)
      .set('tipo_declaracion', tipoDeclaracion)
      .set('income_source', incomeSource);
    const safeParams = month ? params.set('month', month) : params;

    return this.http.get<DeclaracionSummary>(`${API_BASE_URL}/declaracion`, { params: safeParams });
  }
}
