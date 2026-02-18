import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { API_BASE_URL } from '../../../core/api/api-client';
import { AppAlertService } from '../../../shared/ui/alert/alert.service';
import { downloadBlobFile } from '../../../shared/utils/ui-helpers';
import { DeclaracionPdf, DeclaracionSummary } from './declaracion.model';
import { DeclaracionRepository } from './declaracion.repository';

export type DeclaracionTipo = 'MENSUAL' | 'ANUAL';

@Injectable({ providedIn: 'root' })
export class DeclaracionFacade {
  private readonly repo = inject(DeclaracionRepository);
  private readonly alerts = inject(AppAlertService);
  private readonly http = inject(HttpClient);

  loadDeclaracion(
    tipoDeclaracion: DeclaracionTipo,
    yearValue: number | null,
    monthValue: number | null,
    incomeSource: string,
  ): Observable<DeclaracionSummary | null> {
    const year = Number(yearValue);
    const month = Number(monthValue);
    if (!Number.isFinite(year) || year <= 0) {
      this.alerts.warning('Selecciona ano para cargar la declaracion.');
      return of(null);
    }
    if (tipoDeclaracion === 'MENSUAL' && (!Number.isFinite(month) || month <= 0)) {
      this.alerts.warning('Selecciona ano y mes para cargar la declaracion.');
      return of(null);
    }

    return this.repo.fetch(year, tipoDeclaracion === 'MENSUAL' ? month : null, incomeSource, tipoDeclaracion).pipe(
      catchError((err) => {
        if (err?.status === 404) {
          this.alerts.warning('No hay datos para ese periodo.');
        } else {
          this.alerts.error('No se pudo cargar el modo declaracion.');
        }
        return of(null);
      }),
    );
  }

  csvUrl(tipoDeclaracion: DeclaracionTipo, yearValue: number | null, monthValue: number | null, incomeSource: string): string | null {
    if (tipoDeclaracion === 'ANUAL') return null;
    const year = Number(yearValue);
    const month = Number(monthValue);
    if (!Number.isFinite(year) || !Number.isFinite(month) || year <= 0 || month <= 0) return null;
    return `${API_BASE_URL}/sat_report.csv?year=${year}&month=${month}&income_source=${incomeSource}`;
  }

  hojaUrl(tipoDeclaracion: DeclaracionTipo, yearValue: number | null, monthValue: number | null, incomeSource: string): string | null {
    if (tipoDeclaracion === 'ANUAL') return null;
    const year = Number(yearValue);
    const month = Number(monthValue);
    if (!Number.isFinite(year) || !Number.isFinite(month) || year <= 0 || month <= 0) return null;
    return `${API_BASE_URL}/sat_hoja.txt?year=${year}&month=${month}&income_source=${incomeSource}`;
  }

  pdfUrl(pdf: DeclaracionPdf): string {
    return `${API_BASE_URL}/declaraciones/${pdf.id}/archivo/${encodeURIComponent(pdf.filename)}`;
  }

  downloadFile(url: string, filename: string, onErrorMessage: string): void {
    this.http.get(url, { responseType: 'blob' }).subscribe({
      next: (blob) => downloadBlobFile(blob, filename),
      error: () => this.alerts.error(onErrorMessage),
    });
  }

  openPdf(pdf: DeclaracionPdf): void {
    this.http.get(this.pdfUrl(pdf), { responseType: 'blob' }).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        window.open(url, '_blank', 'noopener');
        setTimeout(() => window.URL.revokeObjectURL(url), 5000);
      },
      error: () => this.alerts.error('No se pudo abrir el PDF.'),
    });
  }
}
