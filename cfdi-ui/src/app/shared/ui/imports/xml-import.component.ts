import { ChangeDetectorRef, Component, EventEmitter, Output, inject } from '@angular/core';
import { NgIf, NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TuiInputFiles, TuiInputFilesDirective } from '@taiga-ui/kit';
import { type TuiDialogContext } from '@taiga-ui/core';
import { POLYMORPHEUS_CONTEXT } from '@taiga-ui/polymorpheus';

import {
  ImportacionRepository,
  ImportXmlResult,
} from '../../../features/importacion/data/importacion.repository';
import { AppAlertService } from '../alert/alert.service';

@Component({
  selector: 'app-xml-import',
  standalone: true,
  imports: [FormsModule, NgIf, NgTemplateOutlet, TuiInputFiles, TuiInputFilesDirective],
  templateUrl: './xml-import.component.html',
  styleUrl: './xml-import.component.css',
})
export class XmlImportComponent {
  readonly dialogContext =
    (inject(POLYMORPHEUS_CONTEXT, { optional: true }) as
      | TuiDialogContext<void, { showCard?: boolean }>
      | null) ?? null;

  showCard = this.dialogContext?.data?.showCard ?? true;
  xmlFiles: readonly File[] = [];
  xmlResult: ImportXmlResult | null = null;
  xmlLoading = false;

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
    this.xmlFiles = [];
    this.xmlResult = null;
    this.xmlLoading = false;
    this.cdr.detectChanges();
    this.completed.emit(false);
  }

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

  private finishXmlImport(clearFiles: boolean): void {
    this.xmlLoading = false;
    if (clearFiles) {
      this.xmlFiles = [];
    }
    this.cdr.detectChanges();
    this.completed.emit(clearFiles);
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
}
