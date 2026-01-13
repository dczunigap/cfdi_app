import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { API_BASE_URL } from '../../../core/api/api-client';
import { SummaryData, SummaryDetails } from './summary.model';

@Injectable({ providedIn: 'root' })
export class SummaryRepository {
  constructor(private readonly http: HttpClient) {}

  fetch(year?: number | null, month?: number | null) {
    let params = new HttpParams();
    if (year) params = params.set('year', year);
    if (month) params = params.set('month', month);
    return this.http.get<SummaryData>(`${API_BASE_URL}/summary`, { params });
  }

  fetchDetails(year?: number | null, month?: number | null) {
    let params = new HttpParams();
    if (year) params = params.set('year', year);
    if (month) params = params.set('month', month);
    return this.http.get<SummaryDetails>(`${API_BASE_URL}/summary/details`, { params });
  }
}
