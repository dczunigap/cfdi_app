import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { deleteEntities, setEntities, upsertEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { PlatformRfc } from './platform-rfcs.model';
import { platformRfcsStore } from './platform-rfcs.store';

interface PlatformRfcCreatePayload {
  rfc: string;
  nombre?: string | null;
}

@Injectable({ providedIn: 'root' })
export class PlatformRfcsRepository {
  constructor(private readonly http: HttpClient) {}

  fetch() {
    return this.http.get<PlatformRfc[]>(`${API_BASE_URL}/platform-rfcs`).subscribe((items) => {
      const normalized: PlatformRfc[] = items.filter(
        (item): item is PlatformRfc => typeof item.id === 'number'
      );
      platformRfcsStore.update(setEntities(normalized));
    });
  }

  add(payload: PlatformRfcCreatePayload) {
    return this.http.post<PlatformRfc>(`${API_BASE_URL}/platform-rfcs`, payload).pipe(
      tap((item) => {
        platformRfcsStore.update(upsertEntities([item]));
      })
    );
  }

  delete(id: number) {
    return this.http.delete<{ ok: boolean }>(`${API_BASE_URL}/platform-rfcs/${id}`).pipe(
      tap(() => {
        platformRfcsStore.update(deleteEntities(id));
      })
    );
  }
}
