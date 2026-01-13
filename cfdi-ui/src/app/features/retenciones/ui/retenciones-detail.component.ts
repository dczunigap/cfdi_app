import { Component, inject } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgIf } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { distinctUntilChanged, filter, map, shareReplay, switchMap } from 'rxjs';

import { RetencionDetail } from '../data/retenciones.model';
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

  openXml(detail: RetencionDetail): void {
    if (!detail.xml_text) return;
    const filename = detail.uuid ? `retencion-${detail.uuid}.xml` : `retencion-${detail.id || 'detalle'}.xml`;
    const blob = new Blob([detail.xml_text], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    link.click();
    URL.revokeObjectURL(url);
  }
}
