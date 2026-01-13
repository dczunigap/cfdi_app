import { Component, OnInit } from '@angular/core';
import { AsyncPipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { retenciones$, retencionesCount$, retencionesPeriods$ } from '../data/retenciones.queries';
import { RetencionListItem } from '../data/retenciones.model';
import { RetencionesRepository } from '../data/retenciones.repository';
import { XmlImportComponent } from '../../../shared/ui/imports/xml-import.component';

@Component({
  selector: 'app-retenciones-page',
  standalone: true,
  imports: [AsyncPipe, DecimalPipe, NgFor, NgIf, FormsModule, RouterLink, XmlImportComponent],
  templateUrl: './retenciones-page.component.html',
  styleUrl: './retenciones-page.component.css',
})
export class RetencionesPageComponent implements OnInit {
  readonly retenciones$ = retenciones$;
  readonly retencionesCount$ = retencionesCount$;
  readonly periods$ = retencionesPeriods$;

  selectedPeriod: string | null = null;
  filtersCollapsed = false;
  showXmlImport = false;

  constructor(private readonly repo: RetencionesRepository) {}

  ngOnInit(): void {
    this.repo.fetch();
  }

  applyFilters(): void {
    this.repo.setFilters({ period: this.selectedPeriod });
  }

  resetFilters(): void {
    this.selectedPeriod = null;
    this.repo.setFilters({ period: null });
  }

  toggleFilters(): void {
    this.filtersCollapsed = !this.filtersCollapsed;
  }

  openXmlImport(): void {
    this.showXmlImport = true;
  }

  handleXmlImportCompleted(success: boolean): void {
    this.showXmlImport = false;
    if (success) {
      this.repo.fetch();
    }
  }

  formatPeriod(item: RetencionListItem): string {
    if (!item.ejercicio || !item.mes_ini) return '-';
    return `${item.ejercicio}-${String(item.mes_ini).padStart(2, '0')}`;
  }
}
