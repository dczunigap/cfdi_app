import { Component, OnInit } from '@angular/core';
import { AsyncPipe, NgClass } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCheck, lucideX, lucideTrash2 } from '@ng-icons/lucide';
import { FormsModule } from '@angular/forms';

import { SatCredentialsRepository } from '../data/sat-credentials.repository';
import { satCredentials$ } from '../data/sat-credentials.queries';
import { RfcService } from '../../../core/rfc/rfc.service';

type UploadMode = 'pfx' | 'cerkey';

@Component({
  selector: 'app-admin-sat-page',
  standalone: true,
  imports: [AsyncPipe, FormsModule, NgClass, NgIcon],
  providers: [provideIcons({ lucideCheck, lucideX, lucideTrash2 })],
  templateUrl: './admin-sat-page.component.html',
  styleUrl: './admin-sat-page.component.css',
})
export class AdminSatPageComponent implements OnInit {
  readonly credentials$ = satCredentials$;

  mode: UploadMode = 'pfx';
  rfc = '';
  keyPassword = '';
  pfxFile: File | null = null;
  certFile: File | null = null;
  keyFile: File | null = null;
  saving = false;
  deletingRfc: string | null = null;
  error: string | null = null;

  constructor(
    private readonly repo: SatCredentialsRepository,
    private readonly rfcService: RfcService
  ) {}

  ngOnInit(): void {
    this.repo.fetch();
  }

  onFileChange(event: Event, kind: 'pfx' | 'cert' | 'key') {
    const input = event.target as HTMLInputElement;
    const file = input.files && input.files.length ? input.files[0] : null;
    if (kind === 'pfx') this.pfxFile = file;
    if (kind === 'cert') this.certFile = file;
    if (kind === 'key') this.keyFile = file;
  }

  save(): void {
    const rfcValue = this.rfc.trim().toUpperCase();
    this.rfc = rfcValue;
    if (!rfcValue) {
      this.error = 'RFC requerido.';
      return;
    }
    if (!this.isValidRfc(rfcValue)) {
      this.error = 'RFC invalido.';
      return;
    }
    if (!this.keyPassword.trim()) {
      this.error = 'Password requerido.';
      return;
    }
    if (this.mode === 'pfx' && !this.pfxFile) {
      this.error = 'Selecciona un archivo PFX.';
      return;
    }
    if (this.mode === 'cerkey' && (!this.certFile || !this.keyFile)) {
      this.error = 'Selecciona .cer y .key.';
      return;
    }
    if (this.mode === 'pfx' && this.pfxFile && !this.hasExtension(this.pfxFile, '.pfx')) {
      this.error = 'El archivo PFX debe tener extension .pfx.';
      return;
    }
    if (this.mode === 'cerkey') {
      if (this.certFile && !this.hasExtension(this.certFile, '.cer')) {
        this.error = 'El archivo .cer debe tener extension .cer.';
        return;
      }
      if (this.keyFile && !this.hasExtension(this.keyFile, '.key')) {
        this.error = 'El archivo .key debe tener extension .key.';
        return;
      }
    }

    const form = new FormData();
    form.append('rfc', rfcValue);
    form.append('key_password', this.keyPassword);
    if (this.mode === 'pfx' && this.pfxFile) {
      form.append('pfx_file', this.pfxFile);
    }
    if (this.mode === 'cerkey') {
      if (this.certFile) form.append('cert_file', this.certFile);
      if (this.keyFile) form.append('key_file', this.keyFile);
    }

    this.error = null;
    this.saving = true;
    this.repo.upsert(form).subscribe({
      next: () => {
        this.saving = false;
        this.rfc = '';
        this.keyPassword = '';
        this.pfxFile = null;
        this.certFile = null;
        this.keyFile = null;
        this.rfcService.refreshOptions();
      },
      error: () => {
        this.saving = false;
        this.error = 'No se pudo guardar las credenciales.';
      },
    });
  }

  onRfcInput() {
    this.rfc = this.rfc.toUpperCase();
  }

  remove(rfc: string): void {
    if (!confirm(`Eliminar credenciales SAT para ${rfc}?`)) return;
    this.deletingRfc = rfc;
    this.repo.delete(rfc).subscribe({
      next: () => {
        this.deletingRfc = null;
        this.rfcService.refreshOptions();
      },
      error: () => {
        this.deletingRfc = null;
        this.error = 'No se pudo eliminar.';
      },
    });
  }

  private isValidRfc(value: string) {
    return /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/.test(value);
  }

  private hasExtension(file: File, ext: string) {
    return file.name.toLowerCase().endsWith(ext);
  }
}
