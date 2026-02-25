import { Component, inject } from '@angular/core';
import { AsyncPipe, DatePipe, JsonPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, distinctUntilChanged, filter, map, of, shareReplay, switchMap, tap } from 'rxjs';
import { HttpClient } from '@angular/common/http';

import { API_BASE_URL } from '../../../core/api/api-client';
import { DeclaracionesRepository } from '../data/declaraciones.repository';
import { AppAlertService } from '../../../shared/ui/alert/alert.service';
import { DeclaracionSummary } from '../data/declaraciones.model';

@Component({
  selector: 'app-declaraciones-detail',
  standalone: true,
  imports: [AsyncPipe, DatePipe, JsonPipe, RouterLink],
  templateUrl: './declaraciones-detail.component.html',
  styleUrl: './declaraciones-detail.component.css',
})
export class DeclaracionesDetailComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly repo = inject(DeclaracionesRepository);
  private readonly alerts = inject(AppAlertService);
  private readonly http = inject(HttpClient);

  detailError: string | null = null;
  summaryError: string | null = null;

  private readonly id$ = this.route.paramMap.pipe(
    map((params) => Number(params.get('id'))),
    filter((id) => Number.isFinite(id)),
    distinctUntilChanged(),
    shareReplay(1)
  );

  readonly detail$ = this.id$.pipe(
    switchMap((id) =>
      this.repo.getDetail(id).pipe(
        tap(() => {
          this.detailError = null;
        }),
        catchError(() => {
          this.detailError = 'No se pudo cargar el detalle de la declaracion.';
          return of(null);
        })
      )
    ),
    shareReplay(1)
  );

  readonly summary$ = this.id$.pipe(
    switchMap((id) =>
      this.repo.getSummary(id).pipe(
        tap(() => {
          this.summaryError = null;
        }),
        catchError(() => {
          this.summaryError = 'No se pudo cargar el resumen JSON.';
          return of(null);
        })
      )
    ),
    shareReplay(1)
  );

  formatPeriod(year: number, month: number): string {
    return `${year}-${String(month).padStart(2, '0')}`;
  }

  copySummary(summary: DeclaracionSummary | null): void {
    if (!summary) {
      this.alerts.warning('No hay JSON para copiar.');
      return;
    }
    const text = JSON.stringify(summary, null, 2);
    navigator.clipboard.writeText(text).then(
      () => this.alerts.success('JSON copiado al portapapeles.'),
      () => this.alerts.error('No se pudo copiar el JSON.')
    );
  }

  openPdf(detail: { id: number; filename: string | null; original_name?: string | null }): void {
    const filename = detail.filename ? encodeURIComponent(detail.filename) : '';
    const url = `${API_BASE_URL}/declaraciones/${detail.id}/archivo/${filename}`;
    this.http.get(url, { responseType: 'blob' }).subscribe({
      next: (blob) => this.openBlob(blob),
      error: () => this.alerts.error('No se pudo abrir el PDF.'),
    });
  }

  openJson(id: number): void {
    const url = `${API_BASE_URL}/declaraciones/${id}/resumen.json`;
    this.http.get(url, { responseType: 'blob' }).subscribe({
      next: (blob) => this.openBlob(blob),
      error: () => this.alerts.error('No se pudo abrir el JSON.'),
    });
  }

  private openBlob(blob: Blob): void {
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank', 'noopener');
    setTimeout(() => window.URL.revokeObjectURL(url), 5000);
  }
}
