import { Component, OnInit, inject } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCheck, lucidePackage, lucideTrash2 } from '@ng-icons/lucide';
import { map } from 'rxjs';

import { satDescargas$ } from '../data/sat-descargas.queries';
import { SatDescargasRepository } from '../data/sat-descargas.repository';
import { SatDescargaCreatePayload } from '../data/sat-descargas.model';
import { RfcService } from '../../../core/rfc/rfc.service';

type KindOption = 'cfdi' | 'retenciones';
type TipoSolicitud = 'emitidos' | 'recibidos';
type EstadoFiltro =
  | 'TODOS'
  | 'SOLICITADA'
  | 'EN_PROCESO'
  | 'LISTA'
  | 'DESCARGANDO'
  | 'COMPLETADA'
  | 'SIN_RESULTADOS'
  | 'EXPIRADA'
  | 'ERROR';

@Component({
  selector: 'app-sat-descargas-page',
  standalone: true,
  imports: [AsyncPipe, FormsModule, NgIcon],
  providers: [provideIcons({ lucideCheck, lucidePackage, lucideTrash2 })],
  templateUrl: './sat-descargas-page.component.html',
  styleUrl: './sat-descargas-page.component.css',
})
export class SatDescargasPageComponent implements OnInit {
  private readonly repo = inject(SatDescargasRepository);
  private readonly rfcService = inject(RfcService);

  readonly descargas$ = satDescargas$.pipe(
    map((items) => {
      console.log("🚀 ~ SatDescargasPageComponent ~ items:", items);
      return [...items].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
    }
    )
  );

  readonly estados: EstadoFiltro[] = [
    'TODOS',
    'SOLICITADA',
    'EN_PROCESO',
    'LISTA',
    'DESCARGANDO',
    'COMPLETADA',
    'SIN_RESULTADOS',
    'EXPIRADA',
    'ERROR',
  ];

  kind: KindOption = 'cfdi';
  tipoSolicitud: TipoSolicitud = 'emitidos';
  fechaInicial = this.toDateInput(this.firstDayOfMonth());
  fechaFinal = this.toDateInput(new Date());

  rfcEmisor = '';
  rfcReceptor = '';
  uuid = '';
  rfcReceptores = '';

  lookupId = '';
  loading = false;
  loadingList = false;
  verifyingId: number | null = null;
  processingId: number | null = null;
  deletingId: number | null = null;
  formError: string | null = null;
  lookupError: string | null = null;
  estadoFiltro: EstadoFiltro = 'TODOS';
  page = 0;
  pageSize = 20;
  lastCount = 0;

  ngOnInit(): void {
    this.rfcService.refreshOptions();
    this.loadList();
  }

  selectedRfc() {
    return this.rfcService.selectedRfc();
  }

  submit(): void {
    const start = this.buildDateTime(this.fechaInicial, 'start');
    const end = this.buildDateTime(this.fechaFinal, 'end');
    if (!start || !end) {
      this.formError = 'Selecciona un rango de fechas valido.';
      return;
    }
    if (new Date(start) > new Date(end)) {
      this.formError = 'La fecha inicial no puede ser mayor a la final.';
      return;
    }

    const selectedRfc = this.selectedRfc();
    const payload: SatDescargaCreatePayload = {
      kind: this.kind,
      direccion_solicitud: this.tipoSolicitud,
      tipo_descarga: 'CFDI',
      fecha_inicial: start,
      fecha_final: end,
      estado_comprobante: 'Vigente',
      rfc_emisor:
        this.tipoSolicitud === 'emitidos'
          ? this.normalizeRfc(this.rfcEmisor) || selectedRfc
          : this.normalizeRfc(this.rfcEmisor),
      rfc_receptor:
        this.tipoSolicitud === 'recibidos'
          ? this.normalizeRfc(this.rfcReceptor) || selectedRfc
          : this.normalizeRfc(this.rfcReceptor),
      uuid: this.uuid.trim() || null,
      rfc_receptores: this.parseRfcList(this.rfcReceptores),
    };

    this.formError = null;
    this.loading = true;
    this.repo.create(payload).subscribe({
      next: () => {
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.formError = 'No se pudo crear la solicitud.';
      },
    });
  }

  lookup(): void {
    const id = Number(this.lookupId);
    if (!id || Number.isNaN(id)) {
      this.lookupError = 'Ingresa un id valido.';
      return;
    }
    this.lookupError = null;
    this.repo.fetchById(id).subscribe({
      error: () => {
        this.lookupError = 'No se encontro la descarga.';
      },
    });
  }

  loadList(): void {
    this.loadingList = true;
    const estado = this.estadoFiltro === 'TODOS' ? null : this.estadoFiltro;
    const offset = this.page * this.pageSize;
    this.repo.fetchList({ estado, limit: this.pageSize, offset }).subscribe({
      next: (rows) => {
        this.lastCount = rows.length;
        this.loadingList = false;
      },
      error: () => {
        this.lastCount = 0;
        this.loadingList = false;
      },
    });
  }

  nextPage(): void {
    if (this.lastCount < this.pageSize) return;
    this.page += 1;
    this.loadList();
  }

  prevPage(): void {
    if (this.page <= 0) return;
    this.page -= 1;
    this.loadList();
  }

  verify(id: number): void {
    this.verifyingId = id;
    this.repo.verify(id).subscribe({
      next: () => {
        this.verifyingId = null;
      },
      error: () => {
        this.verifyingId = null;
      },
    });
  }

  process(id: number): void {
    this.processingId = id;
    this.repo.process(id).subscribe({
      next: () => {
        this.processingId = null;
      },
      error: () => {
        this.processingId = null;
      },
    });
  }

  delete(id: number): void {
    if (!confirm('Eliminar solicitud?')) return;
    this.deletingId = id;
    this.repo.delete(id).subscribe({
      next: () => {
        this.deletingId = null;
      },
      error: () => {
        this.deletingId = null;
      },
    });
  }

  private buildDateTime(value: string, mode: 'start' | 'end') {
    if (!value) return '';
    const suffix = mode === 'start' ? 'T00:00:00' : 'T23:59:59';
    return `${value}${suffix}`;
  }

  private normalizeRfc(value: string) {
    const trimmed = value.trim().toUpperCase();
    return trimmed ? trimmed : null;
  }

  private parseRfcList(value: string) {
    const cleaned = value
      .split(',')
      .map((item) => item.trim().toUpperCase())
      .filter(Boolean);
    return cleaned.length ? cleaned : [];
  }

  private toDateInput(value: Date) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, '0');
    const day = String(value.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  private firstDayOfMonth() {
    const today = new Date();
    return new Date(today.getFullYear(), today.getMonth(), 1);
  }
}
