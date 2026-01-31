import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { setEntities, upsertEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { SatDescarga, SatDescargaCreatePayload } from './sat-descargas.model';
import { satDescargasStore } from './sat-descargas.store';

@Injectable({ providedIn: 'root' })
export class SatDescargasRepository {
  private readonly http = inject(HttpClient);

  create(payload: SatDescargaCreatePayload) {
    return this.http.post<SatDescarga>(`${API_BASE_URL}/sat/descargas`, payload).pipe(
      tap((row) => {
        satDescargasStore.update(upsertEntities(row));
      })
    );
  }

  fetchById(id: number) {
    return this.http.get<SatDescarga>(`${API_BASE_URL}/sat/descargas/${id}`).pipe(
      tap((row) => {
        satDescargasStore.update(upsertEntities(row));
      })
    );
  }

  fetchList(params: { estado?: string | null; limit?: number; offset?: number }) {
    const query = new URLSearchParams();
    if (params.estado) query.set('estado', params.estado);
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    if (params.offset !== undefined) query.set('offset', String(params.offset));
    const suffix = query.toString();
    const url = suffix ? `${API_BASE_URL}/sat/descargas?${suffix}` : `${API_BASE_URL}/sat/descargas`;
    return this.http.get<SatDescarga[]>(url).pipe(
      tap((rows) => {
        satDescargasStore.update(setEntities(rows));
      })
    );
  }

  verify(id: number) {
    return this.http.post<SatDescarga>(`${API_BASE_URL}/sat/descargas/${id}/verify`, {}).pipe(
      tap((row) => {
        satDescargasStore.update(upsertEntities(row));
      })
    );
  }

  process(id: number) {
    return this.http.post<SatDescarga>(`${API_BASE_URL}/sat/descargas/${id}/process`, {}).pipe(
      tap((row) => {
        satDescargasStore.update(upsertEntities(row));
      })
    );
  }

  downloadZip(id: number) {
    return this.http.get(`${API_BASE_URL}/sat/descargas/${id}/zip`, { responseType: 'blob' });
  }
}
