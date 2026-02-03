import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { deleteEntities, setEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { RetencionDetail, RetencionListItem } from './retenciones.model';
import { retencionesStore, RetencionesFilters } from './retenciones.store';

@Injectable({ providedIn: 'root' })
export class RetencionesRepository {
  private readonly http = inject(HttpClient);

  fetch() {
    return this.http.get<RetencionListItem[]>(`${API_BASE_URL}/retenciones/`).subscribe((items) => {
      const normalized: RetencionListItem[] = items.filter(
        (item): item is RetencionListItem => typeof item.id === 'number'
      );
      retencionesStore.update(setEntities(normalized));
    });
  }

  setFilters(filters: Partial<RetencionesFilters>): void {
    retencionesStore.update((state) => ({
      ...state,
      ...filters,
    }));
  }

  getDetail(id: number) {
    return this.http.get<RetencionDetail>(`${API_BASE_URL}/retenciones/${id}`);
  }

  delete(id: number) {
    return this.http.delete<{ ok: boolean }>(`${API_BASE_URL}/retenciones/${id}`).pipe(
      tap(() => {
        retencionesStore.update(deleteEntities(id));
      })
    );
  }
}
