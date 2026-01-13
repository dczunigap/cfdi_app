import { Injectable, Injector } from '@angular/core';
import { TuiDialogService } from '@taiga-ui/core';
import { PolymorpheusComponent } from '@taiga-ui/polymorpheus';

import { XmlImportComponent } from './xml-import.component';
import { PdfImportComponent } from './pdf-import.component';

@Injectable({ providedIn: 'root' })
export class ImportDialogService {
  constructor(
    private readonly dialogs: TuiDialogService,
    private readonly injector: Injector,
  ) {}

  openXml(): void {
    this.dialogs
      .open(new PolymorpheusComponent(XmlImportComponent, this.injector), {
        label: 'Importar XML',
        size: 'l',
        closeable: true,
        dismissible: false,
        data: { showCard: false },
      })
      .subscribe();
  }

  openPdf(): void {
    this.dialogs
      .open(new PolymorpheusComponent(PdfImportComponent, this.injector), {
        label: 'Importar PDF',
        size: 'l',
        closeable: true,
        dismissible: false,
        data: { showCard: false },
      })
      .subscribe();
  }
}
