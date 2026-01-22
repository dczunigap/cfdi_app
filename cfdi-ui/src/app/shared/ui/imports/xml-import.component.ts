import { ChangeDetectorRef, Component, ElementRef, EventEmitter, Output, ViewChild, inject } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogRef, DIALOG_DATA } from '@angular/cdk/dialog';

import {
  ImportacionRepository,
  ImportXmlResult,
} from '../../../features/importacion/data/importacion.repository';
import { AppAlertService } from '../alert/alert.service';

@Component({
  selector: 'app-xml-import',
  standalone: true,
  imports: [FormsModule, NgTemplateOutlet],
  templateUrl: './xml-import.component.html',
  styleUrl: './xml-import.component.css',
})
export class XmlImportComponent {
  @ViewChild('xmlInput') xmlInput?: ElementRef<HTMLInputElement>;
  readonly dialogRef = inject<DialogRef<void> | null>(DialogRef, { optional: true });
  readonly dialogData = inject<{ showCard?: boolean } | null>(DIALOG_DATA, { optional: true });

  showCard = this.dialogData?.showCard ?? true;
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
    this.dialogRef?.close();
  }

  onXmlFilesSelected(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    const files = target?.files ? Array.from(target.files) : [];
    this.xmlFiles = files;
    this.cdr.detectChanges();
  }

  cancelImport(): void {
    this.xmlFiles = [];
    this.xmlResult = null;
    this.xmlLoading = false;
    if (this.xmlInput) {
      this.xmlInput.nativeElement.value = '';
    }
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
      result.cfdi_actualizados > 0 ||
      result.cfdi_duplicados > 0 ||
      result.retenciones_insertadas > 0 ||
      result.retenciones_actualizadas > 0 ||
      result.retenciones_duplicadas > 0 ||
      result.errores > 0
    );
  }

  private finishXmlImport(clearFiles: boolean): void {
    this.xmlLoading = false;
    if (clearFiles) {
      this.xmlFiles = [];
      if (this.xmlInput) {
        this.xmlInput.nativeElement.value = '';
      }
    }
    this.cdr.detectChanges();
    this.completed.emit(clearFiles);
  }

  private notifyXmlResult(result: ImportXmlResult): void {
    if (result.errores > 0) {
      this.alerts.warning('Importacion XML con errores. Revisa los archivos.');
      return;
    }
    if (
      result.cfdi_insertados > 0 ||
      result.retenciones_insertadas > 0 ||
      result.cfdi_actualizados > 0 ||
      result.retenciones_actualizadas > 0
    ) {
      const details = [];
      if (result.cfdi_insertados > 0) details.push(`${result.cfdi_insertados} cfdi insertados`);
      if (result.cfdi_actualizados > 0) details.push(`${result.cfdi_actualizados} cfdi actualizados`);
      if (result.retenciones_insertadas > 0) details.push(`${result.retenciones_insertadas} retenciones insertadas`);
      if (result.retenciones_actualizadas > 0)
        details.push(`${result.retenciones_actualizadas} retenciones actualizadas`);
      this.alerts.success(`Importacion XML completada. ${details.join(', ')}.`);
      return;
    }
    if (result.cfdi_duplicados > 0 || result.retenciones_duplicadas > 0) {
      this.alerts.info('Importacion XML sin nuevos registros (duplicados).');
      return;
    }
    this.alerts.info('Importacion XML sin cambios.');
  }
}
