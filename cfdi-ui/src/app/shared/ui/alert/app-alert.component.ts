import { Component, EventEmitter, Input, Output } from '@angular/core';
import { NgClass } from '@angular/common';

export type AlertAppearance = 'info' | 'positive' | 'negative' | 'warning';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [NgClass],
  templateUrl: './app-alert.component.html',
  styleUrl: './app-alert.component.css',
})
export class AppAlertComponent {
  @Input() appearance: AlertAppearance = 'info';
  @Input() title: string | null = null;
  @Input() message = '';
  @Input() dismissible = false;

  @Output() readonly close = new EventEmitter<void>();

  get classes(): Record<string, boolean> {
    return {
      'alert-info': this.appearance === 'info',
      'alert-success': this.appearance === 'positive',
      'alert-warning': this.appearance === 'warning',
      'alert-danger': this.appearance === 'negative',
    };
  }
}
