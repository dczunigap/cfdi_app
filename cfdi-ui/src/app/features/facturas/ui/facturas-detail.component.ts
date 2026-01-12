import { Component, inject } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, filter, map, shareReplay, switchMap } from 'rxjs';

import { FacturasRepository } from '../data/facturas.repository';

@Component({
  selector: 'app-facturas-detail',
  standalone: true,
  imports: [AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf, RouterLink],
  templateUrl: './facturas-detail.component.html',
  styleUrl: './facturas-detail.component.css',
})
export class FacturasDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly repo = inject(FacturasRepository);

  private readonly id$ = this.route.paramMap.pipe(
    map((params) => Number(params.get('id'))),
    filter((id) => Number.isFinite(id)),
    distinctUntilChanged(),
    shareReplay(1),
  );

  readonly detail$ = this.id$.pipe(
    switchMap((id) => this.repo.getDetail(id)),
    shareReplay(1),
  );

  readonly xml$ = this.id$.pipe(
    switchMap((id) => this.repo.getXml(id)),
    shareReplay(1),
  );

  constructor() {}
}
