import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { API_BASE_URL } from '../../../core/api/api-client';
import { DeclaracionSummary } from './declaracion.model';

@Injectable({ providedIn: 'root' })
export class DeclaracionRepository {
  private readonly http = inject(HttpClient);

  fetch(year: number, month: number, incomeSource: string) {
    const params = new HttpParams()
      .set('year', year)
      .set('month', month)
      .set('income_source', incomeSource);

    return this.http.get<DeclaracionSummary>(`${API_BASE_URL}/declaracion`, { params });
  }
}
