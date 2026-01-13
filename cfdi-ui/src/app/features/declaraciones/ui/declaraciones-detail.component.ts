import { Component, inject } from '@angular/core';
import { AsyncPipe, DatePipe, JsonPipe, NgIf } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, filter, map, shareReplay, switchMap } from 'rxjs';

import { API_BASE_URL } from '../../../core/api/api-client';
import { DeclaracionesRepository } from '../data/declaraciones.repository';

@Component({
  selector: 'app-declaraciones-detail',
  standalone: true,
  imports: [AsyncPipe, DatePipe, JsonPipe, NgIf, RouterLink],
  templateUrl: './declaraciones-detail.component.html',
  styleUrl: './declaraciones-detail.component.css',
})
export class DeclaracionesDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly repo = inject(DeclaracionesRepository);

  private readonly id$ = this.route.paramMap.pipe(
    map((params) => Number(params.get('id'))),
    filter((id) => Number.isFinite(id)),
    distinctUntilChanged(),
    shareReplay(1)
  );

  readonly detail$ = this.id$.pipe(
    switchMap((id) => this.repo.getDetail(id)),
    shareReplay(1)
  );

  readonly summary$ = this.id$.pipe(
    switchMap((id) => this.repo.getSummary(id)),
    shareReplay(1)
  );

  readonly pdfUrl$ = this.detail$.pipe(
    map((detail) => {
      const filename = detail.filename ? encodeURIComponent(detail.filename) : '';
      return `${API_BASE_URL}/declaraciones/${detail.id}/archivo/${filename}`;
    }),
    shareReplay(1)
  );

  readonly jsonUrl$ = this.id$.pipe(
    map((id) => `${API_BASE_URL}/declaraciones/${id}/resumen.json`),
    shareReplay(1)
  );

  formatPeriod(year: number, month: number): string {
    return `${year}-${String(month).padStart(2, '0')}`;
  }
}
