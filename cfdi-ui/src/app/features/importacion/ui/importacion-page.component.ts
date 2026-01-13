import { ChangeDetectorRef, Component } from '@angular/core';
import { NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  ImportacionRepository,
  ImportPdfResult,
  ImportXmlResult,
} from '../data/importacion.repository';
import { TuiInputFiles, TuiInputFilesDirective } from '@taiga-ui/kit';
import { AppAlertService } from '../../../shared/ui/alert/alert.service';

@Component({
  selector: 'app-importacion-page',
  standalone: true,
  imports: [FormsModule, NgIf, TuiInputFiles, TuiInputFilesDirective],
  templateUrl: './importacion-page.component.html',
  styleUrl: './importacion-page.component.css',
})
export class ImportacionPageComponent {
  xmlFiles: readonly File[] = [];
  pdfFiles: readonly File[] = [];

  year: number | null = null;
  month: number | null = null;

  xmlResult: ImportXmlResult | null = null;
  pdfResult: ImportPdfResult | null = null;

  xmlLoading = false;
  pdfLoading = false;

  constructor(
    private readonly repo: ImportacionRepository,
    private readonly cdr: ChangeDetectorRef,
    private readonly alerts: AppAlertService,
  ) {}

  importXml(): void {
    this.xmlResult = null;
    if (!this.xmlFiles.length) {
      this.alerts.error('Selecciona al menos un archivo XML.');
      return;
    }

    this.xmlLoading = true;
    this.repo
      .importXml(Array.from(this.xmlFiles))
      .subscribe({
        next: (result) => {
          this.xmlResult = result;
          this.finishXmlImport(true);
          this.notifyXmlResult(result);
        },
        error: () => {
          this.alerts.error('No se pudo importar XML. Revisa el servidor.');
          this.finishXmlImport(false);
        },
      });
  }

  importPdf(): void {
    this.pdfResult = null;
    if (!this.pdfFiles.length) {
      this.alerts.error('Selecciona al menos un PDF.');
      return;
    }

    this.pdfLoading = true;
    this.repo
      .importPdf(Array.from(this.pdfFiles), this.year, this.month)
      .subscribe({
        next: (result) => {
          this.pdfResult = result;
          this.finishPdfImport(true);
          this.notifyPdfResult(result);
        },
        error: () => {
          this.alerts.error('No se pudo importar PDF. Revisa el servidor.');
          this.finishPdfImport(false);
        },
      });
  }

  hasXmlStats(result: ImportXmlResult | null): boolean {
    if (!result) return false;
    return (
      result.cfdi_insertados > 0 ||
      result.cfdi_duplicados > 0 ||
      result.retenciones_insertadas > 0 ||
      result.retenciones_duplicadas > 0 ||
      result.errores > 0
    );
  }

  hasPdfStats(result: ImportPdfResult | null): boolean {
    if (!result) return false;
    return result.insertados > 0 || result.duplicados > 0 || result.errores > 0;
  }

  private finishXmlImport(clearFiles: boolean): void {
    this.xmlLoading = false;
    if (clearFiles) {
      this.xmlFiles = [];
    }
    this.cdr.detectChanges();
  }

  private finishPdfImport(clearFiles: boolean): void {
    this.pdfLoading = false;
    if (clearFiles) {
      this.pdfFiles = [];
    }
    this.cdr.detectChanges();
  }

  private notifyXmlResult(result: ImportXmlResult): void {
    if (result.errores > 0) {
      this.alerts.warning('Importacion XML con errores. Revisa los archivos.');
      return;
    }
    if (result.cfdi_insertados > 0 || result.retenciones_insertadas > 0) {
      this.alerts.success('Importacion XML completada.');
      return;
    }
    if (result.cfdi_duplicados > 0 || result.retenciones_duplicadas > 0) {
      this.alerts.info('Importacion XML sin nuevos registros (duplicados).');
      return;
    }
    this.alerts.info('Importacion XML sin cambios.');
  }

  private notifyPdfResult(result: ImportPdfResult): void {
    if (result.errores > 0) {
      this.alerts.warning('Importacion PDF con errores. Revisa los archivos.');
      return;
    }
    if (result.insertados > 0) {
      this.alerts.success('Importacion PDF completada.');
      return;
    }
    if (result.duplicados > 0) {
      this.alerts.info('Importacion PDF sin nuevos registros (duplicados).');
      return;
    }
    this.alerts.info('Importacion PDF sin cambios.');
  }
}
