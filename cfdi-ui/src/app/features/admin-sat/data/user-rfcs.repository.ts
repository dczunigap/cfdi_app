import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { deleteEntities, setEntities, upsertEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { UserRfc } from './user-rfcs.model';
import { userRfcsStore } from './user-rfcs.store';

type UserRfcResponse = {
  user_id: number;
  rfc: string;
};

@Injectable({ providedIn: 'root' })
export class UserRfcsRepository {
  private readonly http = inject(HttpClient);

  fetch(userId: number) {
    return this.http
      .get<UserRfcResponse[]>(`${API_BASE_URL}/user-rfcs`, { params: { user_id: userId } })
      .pipe(
        tap((items) => {
          const normalized = items.map((item) => ({
            key: `${item.user_id}:${item.rfc}`,
            user_id: item.user_id,
            rfc: item.rfc,
          }));
          userRfcsStore.update(setEntities(normalized));
        })
      );
  }

  add(userId: number, rfc: string) {
    return this.http
      .post<UserRfcResponse>(`${API_BASE_URL}/user-rfcs`, { user_id: userId, rfc })
      .pipe(
        tap((item) => {
          const normalized: UserRfc = {
            key: `${item.user_id}:${item.rfc}`,
            user_id: item.user_id,
            rfc: item.rfc,
          };
          userRfcsStore.update(upsertEntities(normalized));
        })
      );
  }

  remove(userId: number, rfc: string) {
    const key = `${userId}:${rfc}`;
    return this.http.delete<{ ok: boolean }>(`${API_BASE_URL}/user-rfcs/${userId}/${rfc}`).pipe(
      tap(() => {
        userRfcsStore.update(deleteEntities(key));
      })
    );
  }

  clear() {
    userRfcsStore.update(setEntities([]));
  }
}
