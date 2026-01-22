import { Component } from '@angular/core';
import { AsyncPipe, NgFor } from '@angular/common';

import { AppAlertComponent } from './app-alert.component';
import { ToastService } from './toast.service';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  imports: [AsyncPipe, NgFor, AppAlertComponent],
  templateUrl: './toast-container.component.html',
  styleUrl: './toast-container.component.css',
})
export class ToastContainerComponent {
  constructor(private readonly toastService: ToastService) {}

  get toasts$() {
    return this.toastService.stream;
  }

  dismiss(id: number): void {
    this.toastService.dismiss(id);
  }
}
