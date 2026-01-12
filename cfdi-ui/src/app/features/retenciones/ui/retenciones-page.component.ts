import { Component, OnInit } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { retenciones$, retencionesCount$, retencionesPeriods$ } from '../data/retenciones.queries';
import { RetencionListItem } from '../data/retenciones.model';
import { RetencionesRepository } from '../data/retenciones.repository';

@Component({
  selector: 'app-retenciones-page',
  standalone: true,
  imports: [AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf, FormsModule, RouterLink],
  templateUrl: './retenciones-page.component.html',
  styleUrl: './retenciones-page.component.css',
})
export class RetencionesPageComponent implements OnInit {
  readonly retenciones$ = retenciones$;
  readonly retencionesCount$ = retencionesCount$;
  readonly periods$ = retencionesPeriods$;

  selectedPeriod: string | null = null;
  filtersCollapsed = false;

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

  formatPeriod(item: RetencionListItem): string {
    if (!item.ejercicio || !item.mes_ini) return '-';
    return `${item.ejercicio}-${String(item.mes_ini).padStart(2, '0')}`;
  }
}
