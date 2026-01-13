import { Component, signal } from '@angular/core';
import { NgIf } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { TuiRoot } from '@taiga-ui/core';
import { TuiAlerts } from '@taiga-ui/core/components/alert';

@Component({
  selector: 'app-root',
  imports: [NgIf, RouterOutlet, TuiRoot, TuiAlerts],
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
