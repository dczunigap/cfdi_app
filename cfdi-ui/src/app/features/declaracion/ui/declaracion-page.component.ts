import { ChangeDetectorRef, Component } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass, NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

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
  imports: [DatePipe, DecimalPipe, FormsModule, NgClass, NgFor, NgIf, RouterLink, UpperCasePipe],
  templateUrl: './declaracion-page.component.html',
  styleUrl: './declaracion-page.component.css',
})
export class DeclaracionPageComponent {
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

  constructor(
    private readonly repo: DeclaracionRepository,
    private readonly alerts: AppAlertService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

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

  periodLabel(data: DeclaracionSummary): string {
    return `${data.year}-${String(data.month).padStart(2, '0')}`;
  }

  checkBadgeClass(check: DeclaracionCheck): string {
    switch (check.level) {
      case 'ok':
        return 'border-emerald-200 bg-emerald-50 text-emerald-800';
      case 'warn':
        return 'border-amber-200 bg-amber-50 text-amber-900';
      case 'error':
        return 'border-rose-200 bg-rose-50 text-rose-900';
      default:
        return 'border-indigo-200 bg-indigo-50 text-indigo-900';
    }
  }

  statusBadgeClass(status: string): string {
    switch (status) {
      case 'ok':
        return 'border-emerald-200 bg-emerald-50 text-emerald-800';
      case 'warn':
        return 'border-amber-200 bg-amber-50 text-amber-900';
      case 'error':
        return 'border-rose-200 bg-rose-50 text-rose-900';
      default:
        return 'border-indigo-200 bg-indigo-50 text-indigo-900';
    }
  }

  pdfLabel(pdf: DeclaracionPdf): string {
    return pdf.original_name || pdf.filename;
  }

  pdfUrl(pdf: DeclaracionPdf): string {
    return `${API_BASE_URL}/declaraciones/${pdf.id}/archivo/${encodeURIComponent(pdf.filename)}`;
  }

  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }
}
