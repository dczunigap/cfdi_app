import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass, UpperCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { DeclaracionCheck, DeclaracionPdf, DeclaracionSummary } from '../data/declaracion.model';
import { buildRecentYears } from '../../../shared/utils/ui-helpers';
import { DeclaracionFacade, DeclaracionTipo } from '../data/declaracion.facade';

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
  private readonly facade = inject(DeclaracionFacade);
  private readonly cdr = inject(ChangeDetectorRef);

  summary: DeclaracionSummary | null = null;
  loading = false;
  filtersOpen = true;

  year: number | null = null;
  month: number | null = null;
  tipoDeclaracion: DeclaracionTipo = 'MENSUAL';
  incomeSource = 'auto';

  readonly years = buildRecentYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly tiposDeclaracion: DeclaracionTipo[] = ['MENSUAL', 'ANUAL'];
  readonly incomeSources: IncomeSourceOption[] = [
    { value: 'auto', label: 'Auto (usar plataforma si existe)' },
    { value: 'plataforma', label: 'Solo plataforma (Retenciones)' },
    { value: 'cfdi', label: 'Solo CFDI ingreso' },
    { value: 'ambos', label: 'Sumar ambos (solo si NO son las mismas ventas)' },
  ];

  load(): void {
    this.loading = true;
    this.facade.loadDeclaracion(this.tipoDeclaracion, this.year, this.month, this.incomeSource).subscribe({
      next: (data) => {
        if (data) {
          this.summary = { ...data };
          this.tipoDeclaracion = data.tipo_declaracion ?? this.tipoDeclaracion;
        } else {
          this.summary = null;
        }
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  clear(): void {
    this.tipoDeclaracion = 'MENSUAL';
    this.year = null;
    this.month = null;
    this.summary = null;
  }

  toggleFilters(): void {
    this.filtersOpen = !this.filtersOpen;
  }

  get csvUrl(): string | null {
    return this.facade.csvUrl(this.tipoDeclaracion, this.year, this.month, this.incomeSource);
  }

  get hojaUrl(): string | null {
    return this.facade.hojaUrl(this.tipoDeclaracion, this.year, this.month, this.incomeSource);
  }

  downloadCsv(): void {
    if (!this.csvUrl) return;
    this.facade.downloadFile(
      this.csvUrl,
      `sat_report_${this.periodLabelFromInputs()}.csv`,
      'No se pudo descargar el CSV SAT.',
    );
  }

  downloadHoja(): void {
    if (!this.hojaUrl) return;
    this.facade.downloadFile(
      this.hojaUrl,
      `hoja_sat_${this.periodLabelFromInputs()}.txt`,
      'No se pudo generar la hoja SAT.',
    );
  }

  periodLabel(data: DeclaracionSummary): string {
    if (this.isAnualData(data)) return `${data.year}`;
    return `${data.year}-${String(data.month ?? '').padStart(2, '0')}`;
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
    return this.facade.pdfUrl(pdf);
  }

  openPdf(pdf: DeclaracionPdf): void {
    this.facade.openPdf(pdf);
  }

  private periodLabelFromInputs(): string {
    const year = Number(this.year);
    const month = Number(this.month);
    const safeYear = Number.isFinite(year) ? year : new Date().getFullYear();
    const safeMonth = Number.isFinite(month) && month > 0 ? month : 1;
    return `${safeYear}-${String(safeMonth).padStart(2, '0')}`;
  }

  onTipoDeclaracionChange(): void {
    if (this.tipoDeclaracion === 'ANUAL') {
      this.month = null;
    }
  }

  isAnualData(data: DeclaracionSummary | null): boolean {
    return (data?.tipo_declaracion || this.tipoDeclaracion) === 'ANUAL';
  }

  showAcuseSection(data: DeclaracionSummary): boolean {
    return data.mostrar_conciliacion_acuse_sat ?? !this.isAnualData(data);
  }

  showDeclaracionPdfSection(data: DeclaracionSummary): boolean {
    return data.mostrar_declaracion_presentada ?? !this.isAnualData(data);
  }

}
