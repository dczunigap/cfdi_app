import { Component, inject } from '@angular/core';
import { AsyncPipe, NgIf } from '@angular/common';

import { LoadingService } from './loading.service';

@Component({
  selector: 'app-loading-overlay',
  standalone: true,
  imports: [AsyncPipe, NgIf],
  template: `
    <div
      *ngIf="loading$ | async as count"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-[1px]"
      [class.hidden]="count === 0"
    >
      <div class="flex items-center gap-3 rounded-2xl border border-border bg-surface px-5 py-3 shadow-card">
        <span class="h-3 w-3 animate-pulse rounded-full bg-primary"></span>
        <span class="text-sm text-text">Cargando...</span>
      </div>
    </div>
  `,
})
export class LoadingOverlayComponent {
  private readonly loader = inject(LoadingService);
  readonly loading$ = this.loader.isLoading$;
}
