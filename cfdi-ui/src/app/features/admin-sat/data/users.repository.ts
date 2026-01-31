import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { setEntities } from '@ngneat/elf-entities';
import { tap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { AdminUser } from './users.model';
import { usersStore } from './users.store';

@Injectable({ providedIn: 'root' })
export class AdminUsersRepository {
  private readonly http = inject(HttpClient);

  fetch() {
    return this.http.get<AdminUser[]>(`${API_BASE_URL}/users`).pipe(
      tap((items) => {
        usersStore.update(setEntities(items));
      })
    );
  }
}
