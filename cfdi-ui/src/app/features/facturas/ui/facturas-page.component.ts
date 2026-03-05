import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AsyncPipe, DatePipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideFileText, lucideTrash2 } from '@ng-icons/lucide';
import { combineLatest, map } from 'rxjs';
import { facturas$, facturasCount$ } from '../data/facturas.queries';
import { FacturasRepository } from '../data/facturas.repository';
import { XmlImportComponent } from '../../../shared/ui/imports/xml-import.component';
import { RfcService } from '../../../core/rfc/rfc.service';

@Component({
  selector: 'app-facturas-page',
  standalone: true,
  imports: [
    AsyncPipe,
    DatePipe,
    DecimalPipe,
    FormsModule,
    RouterLink,
    XmlImportComponent,
    NgIcon
],
  providers: [provideIcons({ lucideFileText, lucideTrash2 })],
  templateUrl: './facturas-page.component.html',
  styleUrl: './facturas-page.component.css',
})
export class FacturasPageComponent implements OnInit {
  private readonly repo = inject(FacturasRepository);
  private readonly rfcService = inject(RfcService);
  private readonly destroyRef = inject(DestroyRef);

  readonly facturas$ = facturas$;
  readonly facturasCount$ = facturasCount$;
  readonly subtotalTotal$ = this.facturas$.pipe(
    map((items) => items.reduce((acc, item) => acc + Number(item.total ?? 0), 0))
  );
  readonly subtotalTotalTrasladados$ = this.facturas$.pipe(
    map((items) =>
      items.reduce((acc, item) => acc + Number(item.total_trasladados ?? 0), 0)
    )
  );
  
  readonly years = this.buildYears();
  readonly months = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly naturalezas = ['ingreso', 'gasto', 'cobro', 'pago', 'otro'];
  readonly receptorScopes = [
    { value: 'all', label: 'Todos' },
    { value: 'mine', label: 'Mi RFC' },
    { value: 'others', label: 'Otros RFC' },
  ] as const;
  
  subtotales$ = combineLatest([this.subtotalTotal$, this.subtotalTotalTrasladados$])
    .pipe(
      map(([total, total_trasladados]) => ({ total, total_trasladados }))
    );
  filtersCollapsed = false;
  showXmlImport = false;
  deletingId: number | null = null;
  error: string | null = null;

  year: number | null = null;
  month: number | null = null;
  naturaleza: string | null = null;
  usoCfdi: string | null = null;
  receptorScope: 'all' | 'mine' | 'others' = 'all';

  ngOnInit(): void {
    this.rfcService.refreshOptions();
    this.loadFacturas();
  }

  applyFilters(): void {
    const miRfc = this.rfcService.selectedRfc();
    this.repo.setFilters({
      year: this.year,
      month: this.month,
      naturaleza: this.naturaleza,
      uso_cfdi: this.usoCfdi,
      receptor_scope: this.receptorScope,
      mi_rfc: miRfc,
    });
  }

  resetFilters(): void {
    this.year = null;
    this.month = null;
    this.naturaleza = null;
    this.usoCfdi = null;
    this.receptorScope = 'all';
    this.repo.setFilters({
      year: null,
      month: null,
      tipo: null,
      naturaleza: null,
      uso_cfdi: null,
      receptor_scope: 'all',
      mi_rfc: this.rfcService.selectedRfc(),
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
      this.loadFacturas();
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
    this.error = null;
    this.repo
      .exportCsv({
        year: this.year ?? undefined,
        month: this.month ?? undefined,
        naturaleza: this.naturaleza ?? undefined,
        uso_cfdi: this.usoCfdi ?? undefined,
      })
      .subscribe({
        next: (resp) => {
          const blob = resp.body;
          if (!blob) {
            this.error = 'No se pudo descargar el CSV.';
            return;
          }
          const filename =
            this.getFilename(resp.headers.get('content-disposition')) ||
            this.buildCsvFilename();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          link.click();
          window.URL.revokeObjectURL(url);
        },
        error: () => {
          this.error = 'No se pudo descargar el CSV.';
        },
      });
  }

  private buildYears(): number[] {
    const current = new Date().getFullYear();
    return Array.from({ length: 6 }, (_, i) => current - i);
  }

  private getFilename(contentDisposition: string | null): string | null {
    if (!contentDisposition) return null;
    const match = /filename=([^;]+)/i.exec(contentDisposition);
    if (!match) return null;
    return match[1].replace(/"/g, '').trim() || null;
  }

  private buildCsvFilename(): string {
    if (this.year && this.month) {
      return `facturas_${this.year}_${String(this.month).padStart(2, '0')}.csv`;
    }
    return 'facturas.csv';
  }

  private loadFacturas(): void {
    this.error = null;
    this.repo
      .fetch()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        error: () => {
          this.error = 'No se pudieron cargar los CFDI.';
        },
      });
  }
}
