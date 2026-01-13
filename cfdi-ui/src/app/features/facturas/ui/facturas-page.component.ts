import { Component, OnInit } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { facturas$, facturasCount$ } from '../data/facturas.queries';
import { FacturasRepository } from '../data/facturas.repository';
import { XmlImportComponent } from '../../../shared/ui/imports/xml-import.component';

@Component({
  selector: 'app-facturas-page',
  standalone: true,
  imports: [AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf, FormsModule, RouterLink, XmlImportComponent],
  templateUrl: './facturas-page.component.html',
  styleUrl: './facturas-page.component.css',
})
export class FacturasPageComponent implements OnInit {
  readonly facturas$ = facturas$;
  readonly facturasCount$ = facturasCount$;
  readonly years = this.buildYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly tipos = ['I', 'E', 'P', 'T', 'N'];
  readonly naturalezas = ['ingreso', 'gasto', 'cobro', 'pago', 'otro'];
  filtersCollapsed = false;
  showXmlImport = false;

  year: number | null = null;
  month: number | null = null;
  tipo: string | null = null;
  naturaleza: string | null = null;

  constructor(private readonly repo: FacturasRepository) {}

  ngOnInit(): void {
    this.repo.fetch();
  }

  applyFilters(): void {
    this.repo.setFilters({
      year: this.year,
      month: this.month,
      tipo: this.tipo,
      naturaleza: this.naturaleza,
    });
  }

  resetFilters(): void {
    this.year = null;
    this.month = null;
    this.tipo = null;
    this.naturaleza = null;
    this.repo.setFilters({
      year: null,
      month: null,
      tipo: null,
      naturaleza: null,
    });
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


  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }
}
