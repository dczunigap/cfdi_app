import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { SummaryData, TipoDeclaracion } from '../data/summary.model';
import { buildRecentYears } from '../../../shared/utils/ui-helpers';
import { SummaryFacade } from '../data/summary.facade';

@Component({
  selector: 'app-summary-page',
  standalone: true,
  imports: [DecimalPipe, FormsModule],
  templateUrl: './summary-page.component.html',
  styleUrls: ['./summary-page.component.css'],
})
export class SummaryPageComponent implements OnInit {
  private readonly facade = inject(SummaryFacade);
  private readonly cdr = inject(ChangeDetectorRef);

  summary: SummaryData | null = null;
  loading = false;
  filtersOpen = true;

  year: number | null = null;
  month: number | null = null;
  tipoDeclaracion: TipoDeclaracion = 'MENSUAL';

  readonly years = buildRecentYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly tiposDeclaracion: TipoDeclaracion[] = ['MENSUAL', 'ANUAL'];

  ngOnInit(): void {
    this.fetch();
  }

  fetch(): void {
    this.loading = true;
    this.facade.loadSummary(this.tipoDeclaracion, this.year, this.month).subscribe({
      next: (data) => {
        if (data) {
          this.summary = { ...data };
          this.year = data.year;
          this.month = data.month ?? null;
          this.tipoDeclaracion = data.tipo_declaracion ?? this.tipoDeclaracion;
        } else {
          this.summary = null;
        }
        this.loading = false;
        this.cdr.markForCheck();
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
    return this.facade.csvUrl(this.summary, this.tipoDeclaracion);
  }

  downloadCsv(): void {
    if (!this.csvUrl) return;
    this.facade.downloadCsv(this.csvUrl, `sat_report_${this.periodLabel(this.summary!)}.csv`);
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

}
