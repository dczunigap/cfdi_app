import { Component, signal } from '@angular/core';

import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { LoadingOverlayComponent } from './shared/ui/loading/loading-overlay.component';
import { RfcService } from './core/rfc/rfc.service';

@Component({
  selector: 'app-root',
  imports: [
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    LoadingOverlayComponent
],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('cfdi-ui');
  protected readonly sidebarCollapsed = signal(false);
  protected readonly rfcService: RfcService;

  constructor(rfcService: RfcService) {
    this.rfcService = rfcService;
    this.rfcService.refreshOptions();
  }

  toggleSidebar(): void {
    this.sidebarCollapsed.update((current) => !current);
  }

  onRfcChange(event: Event) {
    const value = (event.target as HTMLSelectElement).value;
    this.rfcService.setSelected(value || null);
  }
}
