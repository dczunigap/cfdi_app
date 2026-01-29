import { Injectable, inject } from '@angular/core';
import { Dialog } from '@angular/cdk/dialog';

import { XmlImportComponent } from './xml-import.component';
import { PdfImportComponent } from './pdf-import.component';

@Injectable({ providedIn: 'root' })
export class ImportDialogService {
  private readonly dialogs = inject(Dialog);

  openXml(): void {
    this.dialogs.open(XmlImportComponent, {
      data: { showCard: false },
      ariaLabel: 'Importar XML',
      width: 'min(720px, 92vw)',
      maxWidth: '92vw',
      disableClose: true,
      panelClass: 'app-dialog-panel',
      backdropClass: 'app-dialog-backdrop',
    });
  }

  openPdf(): void {
    this.dialogs.open(PdfImportComponent, {
      data: { showCard: false },
      ariaLabel: 'Importar PDF',
      width: 'min(720px, 92vw)',
      maxWidth: '92vw',
      disableClose: true,
      panelClass: 'app-dialog-panel',
      backdropClass: 'app-dialog-backdrop',
    });
  }
}
