import { Component, signal, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { LoadingOverlayComponent } from '../shared/ui/loading/loading-overlay.component';
import { RfcSelectorComponent } from '../shared/ui/rfc-selector/rfc-selector.component';
import { RfcService } from '../core/rfc/rfc.service';
import { AuthService } from '../core/auth/auth.service';

@Component({
  selector: 'app-main-shell',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
    LoadingOverlayComponent,
    RfcSelectorComponent,
    FormsModule,
  ],
  templateUrl: './main-shell.component.html',
  styleUrl: './main-shell.component.css'
})
export class MainShellComponent {
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  protected readonly title = signal('cfdi-ui');
  protected readonly sidebarCollapsed = signal(false);
  protected readonly rfcService: RfcService;
  protected readonly rfcNotice = signal<string | null>(null);

  constructor() {
    const rfcService = inject(RfcService);

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

  logout(): void {
    this.auth.logout().subscribe(() => {
      this.router.navigateByUrl('/login');
    });
  }
}
