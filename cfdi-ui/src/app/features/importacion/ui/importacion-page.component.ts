import { Component } from '@angular/core';
import { XmlImportComponent } from '../../../shared/ui/imports/xml-import.component';
import { PdfImportComponent } from '../../../shared/ui/imports/pdf-import.component';

@Component({
  selector: 'app-importacion-page',
  standalone: true,
  imports: [XmlImportComponent, PdfImportComponent],
  templateUrl: './importacion-page.component.html',
  styleUrl: './importacion-page.component.css',
})
export class ImportacionPageComponent {
}
