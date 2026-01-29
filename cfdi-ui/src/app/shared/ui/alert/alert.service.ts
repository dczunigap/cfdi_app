import { Injectable, inject } from '@angular/core';
import { ToastService } from './toast.service';

export type AlertAppearance = 'info' | 'positive' | 'negative' | 'warning';

@Injectable({ providedIn: 'root' })
export class AppAlertService {
  private readonly toasts = inject(ToastService);

  info(message: string, title = 'Info'): void {
    this.show(message, 'info', title);
  }

  success(message: string, title = 'Exito'): void {
    this.show(message, 'positive', title);
  }

  warning(message: string, title = 'Atencion'): void {
    this.show(message, 'warning', title);
  }

  error(message: string, title = 'Error'): void {
    this.show(message, 'negative', title);
  }

  private show(message: string, appearance: AlertAppearance, title: string): void {
    this.toasts.show({
      appearance,
      title,
      message,
      dismissible: true,
      durationMs: 4000,
    });
  }
}
