import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { DatePipe, DecimalPipe, NgClass, UpperCasePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideDownload, lucideEraser, lucideFileText, lucideSearch } from '@ng-icons/lucide';

import { buildRecentYears } from '../../../shared/utils/ui-helpers';
import { DeclaracionCheck, DeclaracionPdf, DeclaracionSummary } from '../../declaracion/data/declaracion.model';
import { DeclaracionFacade, DeclaracionTipo } from '../../declaracion/data/declaracion.facade';

type PresentationView = 'detalle' | 'ejecutiva' | 'timeline';

// type IncomeSourceOption = {
//   value: string;
//   label: string;
// };

@Component({
  selector: 'app-declaracion-plataformas-page',
  standalone: true,
  imports: [DatePipe, DecimalPipe, FormsModule, NgClass, RouterLink, UpperCasePipe, NgIcon],
  providers: [provideIcons({ lucideDownload, lucideEraser, lucideFileText, lucideSearch })],
  templateUrl: './declaracion-plataformas-page.component.html',
  styleUrl: './declaracion-plataformas-page.component.css',
})
export class DeclaracionPlataformasPageComponent {
  private readonly facade = inject(DeclaracionFacade);
  private readonly cdr = inject(ChangeDetectorRef);

  summary: DeclaracionSummary | null = null;
  loading = false;
  filtersOpen = true;

  year: number | null = null;
  month: number | null = null;
  tipoDeclaracion: DeclaracionTipo = 'MENSUAL';
  incomeSource = 'auto';
  presentationView: PresentationView = 'timeline';

  readonly years = buildRecentYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly tiposDeclaracion: DeclaracionTipo[] = ['MENSUAL', 'ANUAL'];
  // readonly incomeSources: IncomeSourceOption[] = [
  //   { value: 'auto', label: 'Auto (usar plataforma si existe)' },
  //   { value: 'plataforma', label: 'Solo plataforma (Retenciones)' },
  //   { value: 'cfdi', label: 'Solo CFDI ingreso' },
  //   { value: 'ambos', label: 'Sumar ambos (solo si NO son las mismas ventas)' },
  // ];

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

  onTipoDeclaracionChange(): void {
    if (this.tipoDeclaracion === 'ANUAL') {
      this.month = null;
    }
  }

  get isrIngresosIntermediariosPasajeros(): number {
    return 0;
  }

  get isrIngresosIntermediariosEntrega(): number {
    return this.summary?.plat_ing_siva ?? 0;
  }

  get isrIngresosDirectosPasajeros(): number {
    return 0;
  }

  get isrIngresosDirectosEntrega(): number {
    return this.summary?.ingresos_base ?? 0;
  }

  get isrIngresosTotalesMes(): number {
    return this.summary?.ingresos_total_sin_iva ?? 0;
  }

  get isrTasa(): number {
    const ingresos = this.isrIngresosTotalesMes;
    const retenido = this.summary?.isr_retenido ?? 0;
    if (ingresos <= 0 || retenido <= 0) return 0;
    return this.round2((retenido / ingresos) * 100);
  }

  get isrCausado(): number {
    return this.summary?.isr_retenido ?? 0;
  }

  get isrRetencionesPlataformas(): number {
    return this.summary?.isr_retenido ?? 0;
  }

  get isrCargo(): number {
    return Math.max(this.round2(this.isrCausado - this.isrRetencionesPlataformas), 0);
  }

  get ivaIngresosIntermediarios(): number {
    return this.summary?.plat_ing_siva ?? 0;
  }

  get ivaIngresosDirectos(): number {
    return this.summary?.ingresos_base ?? 0;
  }

  get ivaIngresosTotalesMes(): number {
    return this.summary?.ingresos_total_sin_iva ?? 0;
  }

  get ivaTasa(): number {
    return 16;
  }

  get ivaACargoTasa16(): number {
    return this.summary?.iva_trasladado_total ?? 0;
  }

  get ivaAcreditable(): number {
    return this.summary?.iva_acreditable ?? 0;
  }

  get ivaRetenido(): number {
    return this.summary?.iva_retenido ?? 0;
  }

  get ivaResultado(): number {
    return this.round2(this.ivaACargoTasa16 - this.ivaAcreditable - this.ivaRetenido);
  }

  get ivaImpuestoCargo(): number {
    return this.ivaResultado > 0 ? this.ivaResultado : 0;
  }

  get ivaSaldoFavor(): number {
    return this.ivaResultado < 0 ? Math.abs(this.ivaResultado) : 0;
  }

  get totalPagar(): number {
    return this.round2(this.isrCargo + this.ivaImpuestoCargo);
  }

  get okChecksCount(): number {
    return this.summary?.checks.filter((check) => check.level === 'ok').length ?? 0;
  }

  get warnChecksCount(): number {
    return this.summary?.checks.filter((check) => check.level === 'warn').length ?? 0;
  }

  get errorChecksCount(): number {
    return this.summary?.checks.filter((check) => check.level === 'error').length ?? 0;
  }

  get infoChecksCount(): number {
    return this.summary?.checks.filter((check) => check.level === 'info').length ?? 0;
  }

  get highlightChecks(): DeclaracionCheck[] {
    return (this.summary?.checks ?? []).slice(0, 4);
  }

  get highlightAcuseChecks() {
    return (this.summary?.acuse_checks ?? []).slice(0, 4);
  }

  get validationSteps(): Array<{ label: string; status: 'ok' | 'warn' | 'error' | 'info' }> {
    if (!this.summary) return [];

    const checklistStatus: 'ok' | 'warn' | 'error' | 'info' =
      this.errorChecksCount > 0 ? 'error' : this.warnChecksCount > 0 ? 'warn' : this.infoChecksCount > 0 ? 'info' : 'ok';

    const acuseItems = this.summary.acuse_checks ?? [];
    const acuseStatus: 'ok' | 'warn' | 'error' | 'info' =
      acuseItems.some((item) => item.status === 'error')
        ? 'error'
        : acuseItems.some((item) => item.status === 'warn')
          ? 'warn'
          : this.summary.acuse_payload
            ? 'ok'
            : 'info';

    const pdfStatus: 'ok' | 'warn' | 'error' | 'info' = this.summary.declaracion_pdf ? 'ok' : 'info';

    return [
      { label: 'Datos calculados', status: 'ok' },
      { label: 'Checklist automatico', status: checklistStatus },
      { label: 'Conciliacion SAT', status: acuseStatus },
      { label: 'Declaracion presentada', status: pdfStatus },
    ];
  }

  setPresentationView(view: PresentationView): void {
    this.presentationView = view;
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

  openPdf(pdf: DeclaracionPdf): void {
    this.facade.openPdf(pdf);
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

  private periodLabelFromInputs(): string {
    const year = Number(this.year);
    const month = Number(this.month);
    const safeYear = Number.isFinite(year) ? year : new Date().getFullYear();
    const safeMonth = Number.isFinite(month) && month > 0 ? month : 1;
    return `${safeYear}-${String(safeMonth).padStart(2, '0')}`;
  }

  private round2(value: number): number {
    return Math.round((value + Number.EPSILON) * 100) / 100;
  }
}
