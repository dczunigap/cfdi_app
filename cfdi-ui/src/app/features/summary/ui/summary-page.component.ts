import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import { SummaryRepository } from '../data/summary.repository';
import { SummaryData, TipoDeclaracion } from '../data/summary.model';
import { AppAlertService } from '../../../shared/ui/alert/alert.service';

@Component({
  selector: 'app-summary-page',
  standalone: true,
  imports: [DecimalPipe, FormsModule],
  templateUrl: './summary-page.component.html',
  styleUrl: './summary-page.component.css',
})
export class SummaryPageComponent implements OnInit {
  private readonly repo = inject(SummaryRepository);
  private readonly alerts = inject(AppAlertService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly http = inject(HttpClient);

  summary: SummaryData | null = null;
  loading = false;
  filtersOpen = true;

  year: number | null = null;
  month: number | null = null;
  tipoDeclaracion: TipoDeclaracion = 'MENSUAL';

  readonly years = this.buildYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly tiposDeclaracion: TipoDeclaracion[] = ['MENSUAL', 'ANUAL'];

  ngOnInit(): void {
    this.fetch();
  }

  fetch(): void {
    const year = Number(this.year);
    const month = Number(this.month);
    const hasYear = Number.isFinite(year) && year > 0;
    const hasMonth = Number.isFinite(month) && month > 0;
    if (this.tipoDeclaracion === 'MENSUAL' && ((hasYear && !hasMonth) || (!hasYear && hasMonth))) {
      this.alerts.warning('Selecciona ano y mes para cargar el resumen.');
      return;
    }
    if (this.tipoDeclaracion === 'ANUAL' && !hasYear) {
      this.alerts.warning('Selecciona ano para cargar el resumen anual.');
      return;
    }
    this.loading = true;
    this.repo.fetch(
      this.tipoDeclaracion,
      hasYear ? year : null,
      this.tipoDeclaracion === 'MENSUAL' && hasMonth ? month : null,
    ).subscribe({
      next: (data) => {
        this.summary = { ...data };
        this.year = data.year;
        this.month = data.month ?? null;
        this.tipoDeclaracion = data.tipo_declaracion ?? this.tipoDeclaracion;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.loading = false;
        this.summary = null;
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

  toggleFilters(): void {
    this.filtersOpen = !this.filtersOpen;
  }

  resetFilters(): void {
    this.tipoDeclaracion = 'MENSUAL';
    this.year = null;
    this.month = null;
    this.summary = null;
  }

  periodLabel(data: SummaryData): string {
    if (this.isAnualData(data)) return `${data.year}`;
    return `${data.year}-${String(data.month ?? '').padStart(2, '0')}`;
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
    if (this.isAnualData(this.summary)) return null;
    if (!this.summary.month) return null;
    return `/api/v1/sat_report.csv?year=${this.summary.year}&month=${this.summary.month}`;
  }

  downloadCsv(): void {
    if (!this.csvUrl) return;
    this.http.get(this.csvUrl, { responseType: 'blob' }).subscribe({
      next: (blob) => this.downloadBlob(blob, `sat_report_${this.periodLabel(this.summary!)}.csv`),
      error: () => this.alerts.error('No se pudo descargar el CSV SAT.'),
    });
  }

  get declaracionParams(): { year: number; month?: number; tipo_declaracion: TipoDeclaracion } | null {
    if (!this.summary) return null;
    return {
      year: this.summary.year,
      month: this.summary.month,
      tipo_declaracion: this.isAnualData(this.summary) ? 'ANUAL' : 'MENSUAL',
    };
  }

  onTipoDeclaracionChange(): void {
    if (this.tipoDeclaracion === 'ANUAL') {
      this.month = null;
    }
  }

  isAnualData(data: SummaryData | null): boolean {
    return (data?.tipo_declaracion || this.tipoDeclaracion) === 'ANUAL';
  }

  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  }
}
