import { Component, OnInit, inject } from '@angular/core';
import { AsyncPipe, NgClass } from '@angular/common';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { lucideCheck, lucidePencil, lucideSave, lucideTrash2, lucideX } from '@ng-icons/lucide';
import { FormsModule } from '@angular/forms';

import { SatCredentialsRepository } from '../data/sat-credentials.repository';
import { satCredentials$ } from '../data/sat-credentials.queries';
import { RfcPhonesRepository } from '../data/rfc-phones.repository';
import { rfcPhones$ } from '../data/rfc-phones.queries';
import { UserRfcsRepository } from '../data/user-rfcs.repository';
import { userRfcs$ } from '../data/user-rfcs.queries';
import { AdminUsersRepository } from '../data/users.repository';
import { adminUsers$ } from '../data/users.queries';
import { RfcService } from '../../../core/rfc/rfc.service';

type UploadMode = 'pfx' | 'cerkey';

@Component({
  selector: 'app-admin-sat-page',
  standalone: true,
  imports: [AsyncPipe, FormsModule, NgClass, NgIcon],
  providers: [provideIcons({ lucideCheck, lucidePencil, lucideSave, lucideTrash2, lucideX })],
  templateUrl: './admin-sat-page.component.html',
  styleUrl: './admin-sat-page.component.css',
})
export class AdminSatPageComponent implements OnInit {
  private readonly repo = inject(SatCredentialsRepository);
  private readonly rfcPhonesRepo = inject(RfcPhonesRepository);
  private readonly userRfcsRepo = inject(UserRfcsRepository);
  private readonly usersRepo = inject(AdminUsersRepository);
  private readonly rfcService = inject(RfcService);

  readonly credentials$ = satCredentials$;
  readonly rfcPhones$ = rfcPhones$;
  readonly userRfcs$ = userRfcs$;
  readonly users$ = adminUsers$;

  mode: UploadMode = 'pfx';
  rfc = '';
  keyPassword = '';
  pfxFile: File | null = null;
  certFile: File | null = null;
  keyFile: File | null = null;
  saving = false;
  deletingRfc: string | null = null;
  error: string | null = null;

  phone = '';
  phoneRfc = '';
  phoneSaving = false;
  deletingPhoneId: number | null = null;
  phoneError: string | null = null;
  showPhoneForm = false;
  editingPhoneId: number | null = null;
  editingPhone = '';
  editingRfc = '';

  selectedUserId: number | null = null;
  userRfc = '';
  userRfcError: string | null = null;
  userRfcSaving = false;
  deletingUserRfcKey: string | null = null;

  ngOnInit(): void {
    this.repo.fetch();
    this.rfcPhonesRepo.fetch();
    this.usersRepo.fetch().subscribe();
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

  savePhone(): void {
    const phoneValue = this.normalizePhone(this.phone);
    const rfcValue = this.phoneRfc.trim().toUpperCase();
    this.phone = phoneValue;
    this.phoneRfc = rfcValue;
    if (!phoneValue) {
      this.phoneError = 'Telefono requerido.';
      return;
    }
    if (!this.isValidPhone(phoneValue)) {
      this.phoneError = 'Telefono invalido.';
      return;
    }
    if (!rfcValue) {
      this.phoneError = 'RFC requerido.';
      return;
    }
    if (!this.isValidRfc(rfcValue)) {
      this.phoneError = 'RFC invalido.';
      return;
    }

    this.phoneError = null;
    this.phoneSaving = true;
    this.rfcPhonesRepo.upsert({ phone: phoneValue, rfc: rfcValue }).subscribe({
      next: () => {
        this.phoneSaving = false;
        this.phone = '';
        this.phoneRfc = '';
      },
      error: () => {
        this.phoneSaving = false;
        this.phoneError = 'No se pudo guardar el telefono.';
      },
    });
  }

  removePhone(id: number): void {
    if (!confirm('Eliminar telefono asociado?')) return;
    this.deletingPhoneId = id;
    this.rfcPhonesRepo.delete(id).subscribe({
      next: () => {
        this.deletingPhoneId = null;
      },
      error: () => {
        this.deletingPhoneId = null;
        this.phoneError = 'No se pudo eliminar.';
      },
    });
  }

  togglePhoneForm(): void {
    this.showPhoneForm = !this.showPhoneForm;
  }

  startEditPhone(row: { id: number; phone: string; rfc: string }): void {
    this.editingPhoneId = row.id;
    this.editingPhone = row.phone;
    this.editingRfc = row.rfc;
    this.phoneError = null;
  }

  cancelEditPhone(): void {
    this.editingPhoneId = null;
    this.editingPhone = '';
    this.editingRfc = '';
  }

  saveEditPhone(): void {
    const phoneValue = this.normalizePhone(this.editingPhone);
    const rfcValue = this.editingRfc.trim().toUpperCase();
    if (!phoneValue) {
      this.phoneError = 'Telefono requerido.';
      return;
    }
    if (!this.isValidPhone(phoneValue)) {
      this.phoneError = 'Telefono invalido.';
      return;
    }
    if (!rfcValue) {
      this.phoneError = 'RFC requerido.';
      return;
    }
    if (!this.isValidRfc(rfcValue)) {
      this.phoneError = 'RFC invalido.';
      return;
    }

    this.phoneError = null;
    this.phoneSaving = true;
    this.rfcPhonesRepo.upsert({ phone: phoneValue, rfc: rfcValue }).subscribe({
      next: () => {
        this.phoneSaving = false;
        this.cancelEditPhone();
      },
      error: () => {
        this.phoneSaving = false;
        this.phoneError = 'No se pudo guardar el telefono.';
      },
    });
  }

  onUserChange(value: string) {
    const userId = Number(value);
    if (!userId || Number.isNaN(userId)) {
      this.selectedUserId = null;
      this.userRfcsRepo.clear();
      return;
    }
    this.selectedUserId = userId;
    this.userRfcsRepo.fetch(userId).subscribe();
  }

  addUserRfc(): void {
    if (!this.selectedUserId) {
      this.userRfcError = 'Selecciona un usuario.';
      return;
    }
    const rfcValue = this.userRfc.trim().toUpperCase();
    if (!rfcValue) {
      this.userRfcError = 'RFC requerido.';
      return;
    }
    if (!this.isValidRfc(rfcValue)) {
      this.userRfcError = 'RFC invalido.';
      return;
    }
    this.userRfcError = null;
    this.userRfcSaving = true;
    this.userRfcsRepo.add(this.selectedUserId, rfcValue).subscribe({
      next: () => {
        this.userRfcSaving = false;
        this.userRfc = '';
      },
      error: () => {
        this.userRfcSaving = false;
        this.userRfcError = 'No se pudo asociar el RFC.';
      },
    });
  }

  removeUserRfc(rfc: string): void {
    if (!this.selectedUserId) return;
    if (!confirm(`Eliminar RFC ${rfc} del usuario?`)) return;
    const key = `${this.selectedUserId}:${rfc}`;
    this.deletingUserRfcKey = key;
    this.userRfcsRepo.remove(this.selectedUserId, rfc).subscribe({
      next: () => {
        this.deletingUserRfcKey = null;
      },
      error: () => {
        this.deletingUserRfcKey = null;
        this.userRfcError = 'No se pudo eliminar el RFC.';
      },
    });
  }

  private isValidRfc(value: string) {
    return /^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$/.test(value);
  }

  private hasExtension(file: File, ext: string) {
    return file.name.toLowerCase().endsWith(ext);
  }

  private normalizePhone(value: string) {
    return (value || '').replace(/\D+/g, '');
  }

  private isValidPhone(value: string) {
    return /^\d{8,15}$/.test(value);
  }
}
