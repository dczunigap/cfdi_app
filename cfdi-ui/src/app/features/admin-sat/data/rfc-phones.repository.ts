import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { deleteEntities, setEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { RfcPhone } from './rfc-phones.model';
import { rfcPhonesStore } from './rfc-phones.store';

@Injectable({ providedIn: 'root' })
export class RfcPhonesRepository {
  constructor(private readonly http: HttpClient) {}

  fetch() {
    return this.http.get<RfcPhone[]>(`${API_BASE_URL}/rfc-phones`).subscribe((items) => {
      const normalized = (items || []).filter((item): item is RfcPhone => !!item.id);
      rfcPhonesStore.update(setEntities(normalized));
    });
  }

  upsert(payload: { phone: string; rfc: string }) {
    return this.http.post<RfcPhone>(`${API_BASE_URL}/rfc-phones`, payload).pipe(
      tap((item) => {
        if (item?.id) {
          rfcPhonesStore.update(setEntities([item]));
        } else {
          this.fetch();
        }
      })
    );
  }

  delete(id: number) {
    return this.http.delete<{ ok: boolean }>(`${API_BASE_URL}/rfc-phones/${id}`).pipe(
      tap(() => {
        rfcPhonesStore.update(deleteEntities(id));
      })
    );
  }
}
