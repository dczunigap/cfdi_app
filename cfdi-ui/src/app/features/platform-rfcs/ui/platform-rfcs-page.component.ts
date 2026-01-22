import { Component, OnInit } from '@angular/core';
import { AsyncPipe, NgFor, NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideTrash2 } from '@ng-icons/lucide';

import { platformRfcs$ } from '../data/platform-rfcs.queries';
import { PlatformRfcsRepository } from '../data/platform-rfcs.repository';

@Component({
  selector: 'app-platform-rfcs-page',
  standalone: true,
  imports: [AsyncPipe, NgFor, NgIf, FormsModule, NgIcon],
  providers: [provideIcons({ lucideTrash2 })],
  templateUrl: './platform-rfcs-page.component.html',
  styleUrl: './platform-rfcs-page.component.css',
})
export class PlatformRfcsPageComponent implements OnInit {
  readonly platformRfcs$ = platformRfcs$;

  newRfc = '';
  newNombre = '';
  saving = false;
  deletingId: number | null = null;
  error: string | null = null;

  constructor(private readonly repo: PlatformRfcsRepository) {}

  ngOnInit(): void {
    this.repo.fetch();
  }

  addRfc(): void {
    const rfc = this.newRfc.trim().toUpperCase();
    const nombre = this.newNombre.trim();
    if (!rfc) {
      this.error = 'RFC requerido.';
      return;
    }
    this.error = null;
    this.saving = true;
    this.repo
      .add({ rfc, nombre: nombre || null })
      .subscribe({
        next: () => {
          this.newRfc = '';
          this.newNombre = '';
          this.saving = false;
        },
        error: () => {
          this.error = 'No se pudo guardar el RFC.';
          this.saving = false;
        },
      });
  }

  deleteRfc(id: number): void {
    if (!confirm('Eliminar RFC de plataforma?')) return;
    this.deletingId = id;
    this.repo.delete(id).subscribe({
      next: () => {
        this.deletingId = null;
      },
      error: () => {
        this.error = 'No se pudo eliminar el RFC.';
        this.deletingId = null;
      },
    });
  }
}
