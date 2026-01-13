import { ChangeDetectorRef, Component, EventEmitter, Output, inject } from '@angular/core';
import { NgIf, NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TuiInputFiles, TuiInputFilesDirective } from '@taiga-ui/kit';
import { type TuiDialogContext } from '@taiga-ui/core';
import { POLYMORPHEUS_CONTEXT } from '@taiga-ui/polymorpheus';

import {
  ImportacionRepository,
  ImportPdfResult,
} from '../../../features/importacion/data/importacion.repository';
import { AppAlertService } from '../alert/alert.service';

@Component({
  selector: 'app-pdf-import',
  standalone: true,
  imports: [FormsModule, NgIf, NgTemplateOutlet, TuiInputFiles, TuiInputFilesDirective],
  templateUrl: './pdf-import.component.html',
  styleUrl: './pdf-import.component.css',
})
export class PdfImportComponent {
  readonly dialogContext =
    (inject(POLYMORPHEUS_CONTEXT, { optional: true }) as
      | TuiDialogContext<void, { showCard?: boolean }>
      | null) ?? null;

  showCard = this.dialogContext?.data?.showCard ?? true;
  pdfFiles: readonly File[] = [];
  year: number | null = null;
  month: number | null = null;
  pdfResult: ImportPdfResult | null = null;
  pdfLoading = false;

  @Output() completed = new EventEmitter<boolean>();

  constructor(
    private readonly repo: ImportacionRepository,
    private readonly cdr: ChangeDetectorRef,
    private readonly alerts: AppAlertService,
  ) {}

  closeDialog(): void {
    this.dialogContext?.$implicit.complete();
  }

  cancelImport(): void {
    this.pdfFiles = [];
    this.pdfResult = null;
    this.pdfLoading = false;
    this.cdr.detectChanges();
    this.completed.emit(false);
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

  hasPdfStats(result: ImportPdfResult | null): boolean {
    if (!result) return false;
    return result.insertados > 0 || result.duplicados > 0 || result.errores > 0;
  }

  private finishPdfImport(clearFiles: boolean): void {
    this.pdfLoading = false;
    if (clearFiles) {
      this.pdfFiles = [];
    }
    this.cdr.detectChanges();
    this.completed.emit(clearFiles);
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
