import { Component, OnInit, inject } from '@angular/core';
import { AsyncPipe, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideFileText, lucideTrash2 } from '@ng-icons/lucide';

import {
  declaraciones$,
  declaracionesCount$,
  declaracionesPeriods$,
} from '../data/declaraciones.queries';
import { DeclaracionesRepository } from '../data/declaraciones.repository';
import { PdfImportComponent } from '../../../shared/ui/imports/pdf-import.component';

@Component({
  selector: 'app-declaraciones-page',
  standalone: true,
  imports: [AsyncPipe, DecimalPipe, FormsModule, RouterLink, PdfImportComponent, NgIcon],
  providers: [provideIcons({ lucideFileText, lucideTrash2 })],
  templateUrl: './declaraciones-page.component.html',
  styleUrl: './declaraciones-page.component.css',
})
export class DeclaracionesPageComponent implements OnInit {
  private readonly repo = inject(DeclaracionesRepository);

  readonly declaraciones$ = declaraciones$;
  readonly declaracionesCount$ = declaracionesCount$;
  readonly periods$ = declaracionesPeriods$;

  selectedPeriod: string | null = null;
  filtersCollapsed = false;
  showPdfImport = false;
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

  openPdfImport(): void {
    this.showPdfImport = true;
  }

  handlePdfImportCompleted(success: boolean): void {
    this.showPdfImport = false;
    if (success) {
      this.repo.fetch();
    }
  }

  deleteDeclaracion(id: number): void {
    if (!confirm('Eliminar declaracion?')) return;
    this.deletingId = id;
    this.error = null;
    this.repo.delete(id).subscribe({
      next: () => {
        this.deletingId = null;
      },
      error: () => {
        this.error = 'No se pudo eliminar la declaracion.';
        this.deletingId = null;
      },
    });
  }

  formatPeriod(year: number, month: number): string {
    return `${year}-${String(month).padStart(2, '0')}`;
  }
}
