import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { FacturaDetail, FacturaListItem } from './facturas.model';
import { facturasStore, FacturasFilters } from './facturas.store';
import { deleteEntities, setEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class FacturasRepository {
  constructor(private readonly http: HttpClient) {}

  fetch(params?: { year?: number; month?: number; tipo?: string; naturaleza?: string }) {
    let httpParams = new HttpParams();
    if (params?.year) httpParams = httpParams.set('year', params.year);
    if (params?.month) httpParams = httpParams.set('month', params.month);
    if (params?.tipo) httpParams = httpParams.set('tipo', params.tipo);
    if (params?.naturaleza) httpParams = httpParams.set('naturaleza', params.naturaleza);

    return this.http
      .get<FacturaListItem[]>(`${API_BASE_URL}/facturas`, { params: httpParams })
      .subscribe((items) => {
        const normalized: FacturaListItem[] = items.filter(
          (item): item is FacturaListItem => typeof item.id === 'number'
        );
        facturasStore.update(setEntities(normalized));
      });
  }

  setFilters(filters: Partial<FacturasFilters>): void {
    facturasStore.update((state) => ({
      ...state,
      ...filters,
    }));
  }

  getDetail(id: number) {
    return this.http.get<FacturaDetail>(`${API_BASE_URL}/facturas/${id}`);
  }

  getXml(id: number) {
    return this.http.get(`${API_BASE_URL}/facturas/${id}/xml`, {
      responseType: 'text',
    });
  }

  delete(id: number) {
    return this.http.delete<{ ok: boolean }>(`${API_BASE_URL}/facturas/${id}`).pipe(
      tap(() => {
        facturasStore.update(deleteEntities(id));
      })
    );
  }

  exportCsv(
    params?: { year?: number; month?: number; tipo?: string; naturaleza?: string }
  ): Observable<HttpResponse<Blob>> {
    let httpParams = new HttpParams();
    if (params?.year) httpParams = httpParams.set('year', params.year);
    if (params?.month) httpParams = httpParams.set('month', params.month);
    if (params?.tipo) httpParams = httpParams.set('tipo', params.tipo);
    if (params?.naturaleza) httpParams = httpParams.set('naturaleza', params.naturaleza);

    return this.http.get(`${API_BASE_URL}/facturas/export.csv`, {
      params: httpParams,
      observe: 'response',
      responseType: 'blob' as 'blob',
    }) as Observable<HttpResponse<Blob>>;
  }
}
