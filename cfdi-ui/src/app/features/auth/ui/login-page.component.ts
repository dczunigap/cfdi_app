import { Component, OnInit, signal, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.css',
})
export class LoginPageComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly email = signal('');
  protected readonly password = signal('');
  protected readonly error = signal<string | null>(null);
  protected readonly loading = signal(false);

  ngOnInit(): void {
    this.auth.ensureAuthenticated().subscribe((ok) => {
      if (ok) {
        this.router.navigateByUrl('/welcome');
      }
    });
  }

  login(): void {
    this.error.set(null);
    const email = this.email().trim();
    const password = this.password();
    if (!email || !password) {
      this.error.set('Ingresa correo y password para continuar.');
      return;
    }
    this.loading.set(true);
    this.auth.login(email, password).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigateByUrl('/welcome');
      },
      error: (err) => {
        this.loading.set(false);
        if (err?.status === 401) {
          this.error.set('Usuario no existe o credenciales invalidas.');
        } else {
          this.error.set('No se pudo iniciar sesion. Intenta de nuevo.');
        }
      },
    });
  }
}
