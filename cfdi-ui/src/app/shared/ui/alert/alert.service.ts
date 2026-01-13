import { Injectable } from '@angular/core';
import { TuiAlertService } from '@taiga-ui/core/components/alert';

export type AlertAppearance = 'info' | 'positive' | 'negative' | 'warning';

@Injectable({ providedIn: 'root' })
export class AppAlertService {
  constructor(private readonly alerts: TuiAlertService) {}

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
    this.alerts
      .open(message, {
        appearance,
        label: title,
        autoClose: 4000,
        closeable: true,
      })
      .subscribe();
  }
}
