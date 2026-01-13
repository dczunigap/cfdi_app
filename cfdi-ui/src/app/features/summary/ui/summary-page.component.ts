import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { DecimalPipe, NgFor, NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { SummaryRepository } from '../data/summary.repository';
import { SummaryData, SummaryDetails } from '../data/summary.model';
import { AppAlertService } from '../../../shared/ui/alert/alert.service';

@Component({
  selector: 'app-summary-page',
  standalone: true,
  imports: [DecimalPipe, FormsModule, NgFor, NgIf],
  templateUrl: './summary-page.component.html',
  styleUrl: './summary-page.component.css',
})
export class SummaryPageComponent implements OnInit {
  summary: SummaryData | null = null;
  details: SummaryDetails | null = null;
  loading = false;

  year: number | null = null;
  month: number | null = null;

  readonly years = this.buildYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);

  constructor(
    private readonly repo: SummaryRepository,
    private readonly alerts: AppAlertService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
  }

  fetch(): void {
    const year = Number(this.year);
    const month = Number(this.month);
    if (!Number.isFinite(year) || !Number.isFinite(month) || year <= 0 || month <= 0) {
      this.alerts.warning('Selecciona ano y mes para cargar el resumen.');
      return;
    }
    this.year = year;
    this.month = month;
    this.loading = true;
    this.repo.fetch(year, month).subscribe({
      next: (data) => {
        this.summary = { ...data };
        this.loading = false;
        this.fetchDetails(data.year, data.month);
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.loading = false;
        this.summary = null;
        this.details = null;
        this.cdr.markForCheck();
        if (err?.status === 404) {
          this.alerts.warning('No hay datos para resumir en ese periodo.');
        } else {
          this.alerts.error('No se pudo cargar el resumen.');
        }
      },
    });
  }

  applyFilters(): void {
    this.fetch();
  }

  resetFilters(): void {
    this.year = null;
    this.month = null;
    this.summary = null;
    this.details = null;
  }

  periodLabel(data: SummaryData): string {
    return `${data.year}-${String(data.month).padStart(2, '0')}`;
  }

  get alertsList(): string[] {
    if (!this.summary) return [];
    const alerts: string[] = [];
    if (this.summary.ingresos_total <= 0) {
      alerts.push('Ingresos totales en cero. Verifica importaciones.');
    }
    if (this.summary.iva_neto_sugerido < 0) {
      alerts.push('IVA neto sugerido negativo. Revisa IVA acreditable y retenido.');
    }
    if (this.summary.pagos_count === 0 && this.summary.p_count > 0) {
      alerts.push('Hay complementos P sin pagos detectados.');
    }
    return alerts;
  }

  get csvUrl(): string | null {
    if (!this.summary) return null;
    return `/api/v1/sat_report.csv?year=${this.summary.year}&month=${this.summary.month}`;
  }

  private fetchDetails(year: number, month: number): void {
    this.repo.fetchDetails(year, month).subscribe({
      next: (details: SummaryDetails) => {
        this.details = { ...details };
        this.cdr.markForCheck();
      },
      error: () => {
        this.details = null;
        this.cdr.markForCheck();
      },
    });
  }

  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }
}
