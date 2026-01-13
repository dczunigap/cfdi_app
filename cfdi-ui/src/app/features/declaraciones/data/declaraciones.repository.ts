import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { setEntities } from '@ngneat/elf-entities';

import { API_BASE_URL } from '../../../core/api/api-client';
import { DeclaracionDetail, DeclaracionListItem, DeclaracionSummary } from './declaraciones.model';
import { declaracionesStore, DeclaracionesFilters } from './declaraciones.store';

@Injectable({ providedIn: 'root' })
export class DeclaracionesRepository {
  constructor(private readonly http: HttpClient) {}

  fetch() {
    return this.http
      .get<DeclaracionListItem[]>(`${API_BASE_URL}/declaraciones`)
      .subscribe((items) => {
        const normalized = items.filter(
          (item): item is DeclaracionListItem => typeof item.id === 'number'
        );
        declaracionesStore.update(setEntities(normalized));
        this.loadSummaries(normalized);
      });
  }

  setFilters(filters: Partial<DeclaracionesFilters>): void {
    declaracionesStore.update((state) => ({
      ...state,
      ...filters,
    }));
  }

  getDetail(id: number) {
    return this.http.get<DeclaracionDetail>(`${API_BASE_URL}/declaraciones/${id}`);
  }

  getSummary(id: number) {
    return this.http.get<DeclaracionSummary>(`${API_BASE_URL}/declaraciones/${id}/resumen.json`);
  }

  private loadSummaries(items: DeclaracionListItem[]): void {
    const { summaries } = declaracionesStore.getValue();
    items.forEach((item) => {
      if (!summaries[item.id]) {
        this.getSummary(item.id).subscribe((summary) => {
          declaracionesStore.update((state) => ({
            ...state,
            summaries: {
              ...state.summaries,
              [item.id]: summary,
            },
          }));
        });
      }
    });
  }
}
