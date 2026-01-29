import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { deleteEntities, setEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { SatCredential } from './sat-credentials.model';
import { satCredentialsStore } from './sat-credentials.store';

@Injectable({ providedIn: 'root' })
export class SatCredentialsRepository {
  private readonly http = inject(HttpClient);

  fetch() {
    return this.http.get<SatCredential[]>(`${API_BASE_URL}/sat/credentials`).subscribe((items) => {
      const normalized = items.filter((item): item is SatCredential => !!item.rfc);
      satCredentialsStore.update(setEntities(normalized));
    });
  }

  upsert(payload: FormData) {
    return this.http.post<{ status: string; rfc: string }>(`${API_BASE_URL}/sat/credentials`, payload).pipe(
      tap(() => {
        this.fetch();
      })
    );
  }

  delete(rfc: string) {
    return this.http.delete<{ status: string; rfc: string }>(`${API_BASE_URL}/sat/credentials/${rfc}`).pipe(
      tap(() => {
        satCredentialsStore.update(deleteEntities(rfc));
      })
    );
  }
}
