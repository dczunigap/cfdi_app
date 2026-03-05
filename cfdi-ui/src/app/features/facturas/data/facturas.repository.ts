import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import {
  Deducibilidad,
  DeduccionesCatalogResponse,
  FacturaDetail,
  FacturaListItem,
  TipoDeclaracion,
} from './facturas.model';
import { facturasStore, FacturasFilters } from './facturas.store';
import { deleteEntities, setEntities } from '@ngneat/elf-entities';

@Injectable({ providedIn: 'root' })
export class FacturasRepository {
  private readonly http = inject(HttpClient);

  fetch(params?: {
    year?: number;
    month?: number;
    tipo?: string;
    naturaleza?: string;
    deducibilidad?: Deducibilidad;
    tipo_declaracion?: TipoDeclaracion;
  }) {
    let httpParams = new HttpParams();
    if (params?.year) httpParams = httpParams.set('year', params.year);
    if (params?.month) httpParams = httpParams.set('month', params.month);
    if (params?.tipo) httpParams = httpParams.set('tipo', params.tipo);
    if (params?.naturaleza) httpParams = httpParams.set('naturaleza', params.naturaleza);
    if (params?.deducibilidad) httpParams = httpParams.set('deducibilidad', params.deducibilidad);
    if (params?.tipo_declaracion) httpParams = httpParams.set('tipo_declaracion', params.tipo_declaracion);

    return this.http
      .get<FacturaListItem[]>(`${API_BASE_URL}/facturas/`, { params: httpParams })
      .pipe(
        tap((items) => {
          const normalized: FacturaListItem[] = items.filter(
            (item): item is FacturaListItem => typeof item.id === 'number'
          );
          facturasStore.update(setEntities(normalized));
      })
    );
  }

  getDeduccionesCatalog(tipoDeclaracion: TipoDeclaracion) {
    const params = new HttpParams().set('tipo_declaracion', tipoDeclaracion);
    return this.http.get<DeduccionesCatalogResponse>(`${API_BASE_URL}/deducciones/catalogo`, { params });
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
    params?: {
      year?: number;
      month?: number;
      tipo?: string;
      naturaleza?: string;
      deducibilidad?: Deducibilidad;
      tipo_declaracion?: TipoDeclaracion;
    }
  ): Observable<HttpResponse<Blob>> {
    let httpParams = new HttpParams();
    if (params?.year) httpParams = httpParams.set('year', params.year);
    if (params?.month) httpParams = httpParams.set('month', params.month);
    if (params?.tipo) httpParams = httpParams.set('tipo', params.tipo);
    if (params?.naturaleza) httpParams = httpParams.set('naturaleza', params.naturaleza);
    if (params?.deducibilidad) httpParams = httpParams.set('deducibilidad', params.deducibilidad);
    if (params?.tipo_declaracion) httpParams = httpParams.set('tipo_declaracion', params.tipo_declaracion);

    return this.http.get(`${API_BASE_URL}/facturas/export.csv`, {
      params: httpParams,
      observe: 'response' as const,
      responseType: 'blob' as const,
    });
  }
}
