import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AppAlertService } from '../../../shared/ui/alert/alert.service';
import { downloadBlobFile } from '../../../shared/utils/ui-helpers';
import { SummaryData, TipoDeclaracion } from './summary.model';
import { SummaryRepository } from './summary.repository';

@Injectable({ providedIn: 'root' })
export class SummaryFacade {
  private readonly repo = inject(SummaryRepository);
  private readonly alerts = inject(AppAlertService);
  private readonly http = inject(HttpClient);

  loadSummary(
    tipoDeclaracion: TipoDeclaracion,
    yearValue: number | null,
    monthValue: number | null,
  ): Observable<SummaryData | null> {
    const year = Number(yearValue);
    const month = Number(monthValue);
    const hasYear = Number.isFinite(year) && year > 0;
    const hasMonth = Number.isFinite(month) && month > 0;

    if (tipoDeclaracion === 'MENSUAL' && ((hasYear && !hasMonth) || (!hasYear && hasMonth))) {
      this.alerts.warning('Selecciona ano y mes para cargar el resumen.');
      return of(null);
    }
    if (tipoDeclaracion === 'ANUAL' && !hasYear) {
      this.alerts.warning('Selecciona ano para cargar el resumen anual.');
      return of(null);
    }

    return this.repo
      .fetch(tipoDeclaracion, hasYear ? year : null, tipoDeclaracion === 'MENSUAL' && hasMonth ? month : null)
      .pipe(
        catchError((err) => {
          if (err?.status === 404) {
            this.alerts.warning('No hay datos para resumir en ese periodo.');
          } else {
            this.alerts.error('No se pudo cargar el resumen.');
          }
          return of(null);
        }),
      );
  }

  csvUrl(summary: SummaryData | null, tipoDeclaracion: TipoDeclaracion): string | null {
    if (!summary) return null;
    if ((summary.tipo_declaracion || tipoDeclaracion) === 'ANUAL') return null;
    if (!summary.month) return null;
    return `/api/v1/sat_report.csv?year=${summary.year}&month=${summary.month}`;
  }

  downloadCsv(url: string, filename: string): void {
    this.http.get(url, { responseType: 'blob' }).subscribe({
      next: (blob) => downloadBlobFile(blob, filename),
      error: () => this.alerts.error('No se pudo descargar el CSV SAT.'),
    });
  }
}
