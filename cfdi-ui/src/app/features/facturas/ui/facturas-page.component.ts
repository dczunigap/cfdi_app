import { Component, OnInit } from '@angular/core';
import { AsyncPipe, DatePipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { facturas$, facturasCount$ } from '../data/facturas.queries';
import { FacturasRepository } from '../data/facturas.repository';
import { XmlImportComponent } from '../../../shared/ui/imports/xml-import.component';
import { API_BASE_URL } from '../../../core/api/api-client';

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
  deletingId: number | null = null;
  error: string | null = null;

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

  deleteFactura(id: number): void {
    if (!confirm('Eliminar CFDI?')) return;
    this.deletingId = id;
    this.error = null;
    this.repo.delete(id).subscribe({
      next: () => {
        this.deletingId = null;
      },
      error: () => {
        this.error = 'No se pudo eliminar el CFDI.';
        this.deletingId = null;
      },
    });
  }

  downloadCsv(): void {
    window.location.href = this.csvUrl;
  }

  get csvUrl(): string {
    const params = new URLSearchParams();
    if (this.year) params.set('year', String(this.year));
    if (this.month) params.set('month', String(this.month));
    if (this.tipo) params.set('tipo', this.tipo);
    if (this.naturaleza) params.set('naturaleza', this.naturaleza);
    const query = params.toString();
    return `${API_BASE_URL}/facturas/export.csv${query ? `?${query}` : ''}`;
  }

  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }
}
