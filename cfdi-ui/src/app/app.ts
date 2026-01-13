import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { TuiRoot } from '@taiga-ui/core';
import { TuiAlerts } from '@taiga-ui/core/components/alert';
import { TuiDialogs } from '@taiga-ui/core/components/dialog';

import { LoadingOverlayComponent } from './shared/ui/loading/loading-overlay.component';

@Component({
  selector: 'app-root',
  imports: [
    NgIf,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    TuiRoot,
    TuiAlerts,
    TuiDialogs,
    LoadingOverlayComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('cfdi-ui');
  protected readonly sidebarCollapsed = signal(false);

  toggleSidebar(): void {
    this.sidebarCollapsed.update((current) => !current);
  }
}
