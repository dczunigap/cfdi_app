import { Component, computed, signal, inject } from '@angular/core';
import { Router } from '@angular/router';

import { RfcSelectorComponent } from '../../../shared/ui/rfc-selector/rfc-selector.component';
import { RfcService } from '../../../core/rfc/rfc.service';

@Component({
  selector: 'app-welcome-page',
  standalone: true,
  imports: [RfcSelectorComponent],
  templateUrl: './welcome-page.component.html',
  styleUrl: './welcome-page.component.css',
})
export class WelcomePageComponent {
  private readonly router = inject(Router);

  protected readonly rfcService: RfcService;
  protected readonly notice = signal<string | null>(null);
  protected readonly canContinue = computed(() => !!this.rfcService.selectedRfc());

  constructor() {
    const rfcService = inject(RfcService);

    this.rfcService = rfcService;
    this.rfcService.refreshOptions();
  }

  continue(): void {
    if (!this.rfcService.selectedRfc()) {
      this.notice.set('Selecciona un RFC para continuar.');
      return;
    }
    this.notice.set(null);
    this.router.navigateByUrl('/summary');
  }
}
