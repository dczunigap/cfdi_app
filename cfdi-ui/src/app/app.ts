import { Component, signal } from '@angular/core';

import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { LoadingOverlayComponent } from './shared/ui/loading/loading-overlay.component';
import { RfcService } from './core/rfc/rfc.service';

@Component({
  selector: 'app-root',
  imports: [
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    LoadingOverlayComponent,
    FormsModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('cfdi-ui');
  protected readonly sidebarCollapsed = signal(false);
  protected readonly rfcService: RfcService;
  protected readonly rfcNotice = signal<string | null>(null);

  constructor(rfcService: RfcService) {
    this.rfcService = rfcService;
    this.rfcService.refreshOptions();
  }

  toggleSidebar(): void {
    this.sidebarCollapsed.update((current) => !current);
  }

  onNavClick(event: Event) {
    if (!this.rfcService.selectedRfc()) {
      event.preventDefault();
      event.stopPropagation();
      this.rfcNotice.set('Selecciona un RFC para entrar a los módulos.');
    } else {
      this.rfcNotice.set(null);
    }
  }

  closeRfcNotice() {
    this.rfcNotice.set(null);
  }
}
