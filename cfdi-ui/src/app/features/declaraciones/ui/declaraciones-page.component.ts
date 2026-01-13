import { Component, OnInit } from '@angular/core';
import { AsyncPipe, DecimalPipe, NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

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
  imports: [AsyncPipe, DecimalPipe, NgFor, NgIf, FormsModule, RouterLink, PdfImportComponent],
  templateUrl: './declaraciones-page.component.html',
  styleUrl: './declaraciones-page.component.css',
})
export class DeclaracionesPageComponent implements OnInit {
  readonly declaraciones$ = declaraciones$;
  readonly declaracionesCount$ = declaracionesCount$;
  readonly periods$ = declaracionesPeriods$;

  selectedPeriod: string | null = null;
  filtersCollapsed = false;
  showPdfImport = false;

  constructor(private readonly repo: DeclaracionesRepository) {}

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

  formatPeriod(year: number, month: number): string {
    return `${year}-${String(month).padStart(2, '0')}`;
  }
}
