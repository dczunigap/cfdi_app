import { Component, OnInit, inject } from '@angular/core';
import { AsyncPipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideFileText, lucideTrash2 } from '@ng-icons/lucide';

import { retenciones$, retencionesCount$, retencionesPeriods$ } from '../data/retenciones.queries';
import { RetencionListItem } from '../data/retenciones.model';
import { RetencionesRepository } from '../data/retenciones.repository';
import { XmlImportComponent } from '../../../shared/ui/imports/xml-import.component';

@Component({
  selector: 'app-retenciones-page',
  standalone: true,
  imports: [AsyncPipe, DecimalPipe, FormsModule, RouterLink, XmlImportComponent, NgIcon],
  providers: [provideIcons({ lucideFileText, lucideTrash2 })],
  templateUrl: './retenciones-page.component.html',
  styleUrl: './retenciones-page.component.css',
})
export class RetencionesPageComponent implements OnInit {
  private readonly repo = inject(RetencionesRepository);

  readonly retenciones$ = retenciones$;
  readonly retencionesCount$ = retencionesCount$;
  readonly periods$ = retencionesPeriods$;

  selectedPeriod: string | null = null;
  filtersCollapsed = false;
  showXmlImport = false;
  deletingId: number | null = null;
  error: string | null = null;

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

  deleteRetencion(id: number): void {
    if (!confirm('Eliminar retencion?')) return;
    this.deletingId = id;
    this.error = null;
    this.repo.delete(id).subscribe({
      next: () => {
        this.deletingId = null;
      },
      error: () => {
        this.error = 'No se pudo eliminar la retencion.';
        this.deletingId = null;
      },
    });
  }

  formatPeriod(item: RetencionListItem): string {
    if (!item.ejercicio || !item.mes_ini) return '-';
    return `${item.ejercicio}-${String(item.mes_ini).padStart(2, '0')}`;
  }
}
