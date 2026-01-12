import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { setEntities } from '@ngneat/elf-entities';

import { API_BASE_URL } from '../../../core/api/api-client';
import { RetencionDetail, RetencionListItem } from './retenciones.model';
import { retencionesStore, RetencionesFilters } from './retenciones.store';

@Injectable({ providedIn: 'root' })
export class RetencionesRepository {
  constructor(private readonly http: HttpClient) {}

  fetch() {
    return this.http.get<RetencionListItem[]>(`${API_BASE_URL}/retenciones`).subscribe((items) => {
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
}
