import { ChangeDetectorRef, Component, ElementRef, EventEmitter, Output, ViewChild, inject } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogRef, DIALOG_DATA } from '@angular/cdk/dialog';

import {
  ImportacionRepository,
  ImportPdfResult,
} from '../../../features/importacion/data/importacion.repository';
import { AppAlertService } from '../alert/alert.service';

@Component({
  selector: 'app-pdf-import',
  standalone: true,
  imports: [FormsModule, NgTemplateOutlet],
  templateUrl: './pdf-import.component.html',
  styleUrl: './pdf-import.component.css',
})
export class PdfImportComponent {
  private readonly repo = inject(ImportacionRepository);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly alerts = inject(AppAlertService);

  @ViewChild('pdfInput') pdfInput?: ElementRef<HTMLInputElement>;
  readonly dialogRef = inject<DialogRef<void> | null>(DialogRef, { optional: true });
  readonly dialogData = inject<{ showCard?: boolean } | null>(DIALOG_DATA, { optional: true });

  showCard = this.dialogData?.showCard ?? true;
  pdfFiles: readonly File[] = [];
  year: number | null = null;
  month: number | null = null;
  pdfResult: ImportPdfResult | null = null;
  pdfLoading = false;

  @Output() completed = new EventEmitter<boolean>();

  closeDialog(): void {
    this.dialogRef?.close();
  }

  onPdfFilesSelected(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    const files = target?.files ? Array.from(target.files) : [];
    this.pdfFiles = files;
    this.cdr.detectChanges();
  }

  cancelImport(): void {
    this.pdfFiles = [];
    this.pdfResult = null;
    this.pdfLoading = false;
    if (this.pdfInput) {
      this.pdfInput.nativeElement.value = '';
    }
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
    return (
      result.insertados > 0 ||
      result.actualizados > 0 ||
      result.duplicados > 0 ||
      result.errores > 0
    );
  }

  private finishPdfImport(clearFiles: boolean): void {
    this.pdfLoading = false;
    if (clearFiles) {
      this.pdfFiles = [];
      if (this.pdfInput) {
        this.pdfInput.nativeElement.value = '';
      }
    }
    this.cdr.detectChanges();
    this.completed.emit(clearFiles);
  }

  private notifyPdfResult(result: ImportPdfResult): void {
    if (result.errores > 0) {
      this.alerts.warning('Importacion PDF con errores. Revisa los archivos.');
      return;
    }
    if (result.insertados > 0 || result.actualizados > 0) {
      const details = [];
      if (result.insertados > 0) details.push(`${result.insertados} insertados`);
      if (result.actualizados > 0) details.push(`${result.actualizados} actualizados`);
      this.alerts.success(`Importacion PDF completada. ${details.join(', ')}.`);
      return;
    }
    if (result.duplicados > 0) {
      this.alerts.info('Importacion PDF sin nuevos registros (duplicados).');
      return;
    }
    this.alerts.info('Importacion PDF sin cambios.');
  }
}
