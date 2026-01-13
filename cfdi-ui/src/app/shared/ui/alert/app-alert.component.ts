import { Component, EventEmitter, Input, Output, inject } from '@angular/core';
import { NgIf } from '@angular/common';
import { TuiButton } from '@taiga-ui/core/components/button';
import { TuiNotification } from '@taiga-ui/core/components/notification';
import { TUI_COMMON_ICONS } from '@taiga-ui/core/tokens';

export type AlertAppearance = 'info' | 'positive' | 'negative' | 'warning';

@Component({
  selector: 'app-alert',
  standalone: true,
  imports: [NgIf, TuiButton, TuiNotification],
  templateUrl: './app-alert.component.html',
  styleUrl: './app-alert.component.css',
})
export class AppAlertComponent {
  private readonly icons = inject(TUI_COMMON_ICONS);

  @Input() appearance: AlertAppearance = 'info';
  @Input() title: string | null = null;
  @Input() message = '';
  @Input() dismissible = false;

  @Output() readonly close = new EventEmitter<void>();

  get closeIcon(): string {
    return this.icons.close?.toString?.() ?? '';
  }
}
