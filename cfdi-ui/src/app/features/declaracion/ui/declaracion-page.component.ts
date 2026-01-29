import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass, UpperCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';

import { API_BASE_URL } from '../../../core/api/api-client';
import { DeclaracionRepository } from '../data/declaracion.repository';
import { DeclaracionCheck, DeclaracionPdf, DeclaracionSummary } from '../data/declaracion.model';
import { AppAlertService } from '../../../shared/ui/alert/alert.service';

type IncomeSourceOption = {
  value: string;
  label: string;
};

@Component({
  selector: 'app-declaracion-page',
  standalone: true,
  imports: [DatePipe, DecimalPipe, FormsModule, NgClass, RouterLink, UpperCasePipe],
  templateUrl: './declaracion-page.component.html',
  styleUrl: './declaracion-page.component.css',
})
export class DeclaracionPageComponent {
  private readonly repo = inject(DeclaracionRepository);
  private readonly alerts = inject(AppAlertService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly http = inject(HttpClient);

  summary: DeclaracionSummary | null = null;
  loading = false;
  filtersOpen = true;

  year: number | null = null;
  month: number | null = null;
  incomeSource = 'auto';

  readonly years = this.buildYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly incomeSources: IncomeSourceOption[] = [
    { value: 'auto', label: 'Auto (usar plataforma si existe)' },
    { value: 'plataforma', label: 'Solo plataforma (Retenciones)' },
    { value: 'cfdi', label: 'Solo CFDI ingreso' },
    { value: 'ambos', label: 'Sumar ambos (solo si NO son las mismas ventas)' },
  ];

  load(): void {
    const year = Number(this.year);
    const month = Number(this.month);
    if (!Number.isFinite(year) || !Number.isFinite(month) || year <= 0 || month <= 0) {
      this.alerts.warning('Selecciona ano y mes para cargar la declaracion.');
      return;
    }

    this.loading = true;
    this.repo.fetch(year, month, this.incomeSource).subscribe({
      next: (data) => {
        this.summary = { ...data };
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.loading = false;
        this.summary = null;
        this.cdr.markForCheck();
        if (err?.status === 404) {
          this.alerts.warning('No hay datos para ese periodo.');
        } else {
          this.alerts.error('No se pudo cargar el modo declaracion.');
        }
      },
    });
  }

  clear(): void {
    this.year = null;
    this.month = null;
    this.summary = null;
  }

  toggleFilters(): void {
    this.filtersOpen = !this.filtersOpen;
  }

  get csvUrl(): string | null {
    const year = Number(this.year);
    const month = Number(this.month);
    if (!Number.isFinite(year) || !Number.isFinite(month) || year <= 0 || month <= 0) return null;
    return `${API_BASE_URL}/sat_report.csv?year=${year}&month=${month}&income_source=${this.incomeSource}`;
  }

  get hojaUrl(): string | null {
    const year = Number(this.year);
    const month = Number(this.month);
    if (!Number.isFinite(year) || !Number.isFinite(month) || year <= 0 || month <= 0) return null;
    return `${API_BASE_URL}/sat_hoja.txt?year=${year}&month=${month}&income_source=${this.incomeSource}`;
  }

  downloadCsv(): void {
    if (!this.csvUrl) return;
    this.http.get(this.csvUrl, { responseType: 'blob' }).subscribe({
      next: (blob) => this.downloadBlob(blob, `sat_report_${this.periodLabelFromInputs()}.csv`),
      error: () => this.alerts.error('No se pudo descargar el CSV SAT.'),
    });
  }

  downloadHoja(): void {
    if (!this.hojaUrl) return;
    this.http.get(this.hojaUrl, { responseType: 'blob' }).subscribe({
      next: (blob) => this.downloadBlob(blob, `hoja_sat_${this.periodLabelFromInputs()}.txt`),
      error: () => this.alerts.error('No se pudo generar la hoja SAT.'),
    });
  }

  periodLabel(data: DeclaracionSummary): string {
    return `${data.year}-${String(data.month).padStart(2, '0')}`;
  }

  checkBadgeClass(check: DeclaracionCheck): string {
    switch (check.level) {
      case 'ok':
        return 'badge-success';
      case 'warn':
        return 'badge-warn';
      case 'error':
        return 'badge-danger';
      default:
        return 'badge-info';
    }
  }

  statusBadgeClass(status: string): string {
    switch (status) {
      case 'ok':
        return 'badge-success';
      case 'warn':
        return 'badge-warn';
      case 'error':
        return 'badge-danger';
      default:
        return 'badge-info';
    }
  }

  pdfLabel(pdf: DeclaracionPdf): string {
    return pdf.original_name || pdf.filename;
  }

  pdfUrl(pdf: DeclaracionPdf): string {
    return `${API_BASE_URL}/declaraciones/${pdf.id}/archivo/${encodeURIComponent(pdf.filename)}`;
  }

  openPdf(pdf: DeclaracionPdf): void {
    const url = this.pdfUrl(pdf);
    this.http.get(url, { responseType: 'blob' }).subscribe({
      next: (blob) => this.openBlob(blob),
      error: () => this.alerts.error('No se pudo abrir el PDF.'),
    });
  }

  private openBlob(blob: Blob): void {
    const url = window.URL.createObjectURL(blob);
    window.open(url, '_blank', 'noopener');
    setTimeout(() => window.URL.revokeObjectURL(url), 5000);
  }

  private periodLabelFromInputs(): string {
    const year = Number(this.year);
    const month = Number(this.month);
    const safeYear = Number.isFinite(year) ? year : new Date().getFullYear();
    const safeMonth = Number.isFinite(month) ? month : 1;
    return `${safeYear}-${String(safeMonth).padStart(2, '0')}`;
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  }

  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }
}
