import { Component, inject } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgIf } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, filter, map, shareReplay, switchMap } from 'rxjs';

import { RetencionesRepository } from '../data/retenciones.repository';

@Component({
  selector: 'app-retenciones-detail',
  standalone: true,
  imports: [AsyncPipe, DatePipe, DecimalPipe, NgIf, RouterLink],
  templateUrl: './retenciones-detail.component.html',
  styleUrl: './retenciones-detail.component.css',
})
export class RetencionesDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly repo = inject(RetencionesRepository);

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

  formatPeriod(ejercicio: number | null, mesIni: number | null): string {
    if (!ejercicio || !mesIni) return '-';
    return `${ejercicio}-${String(mesIni).padStart(2, '0')}`;
  }
}
