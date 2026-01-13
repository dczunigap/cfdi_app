import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.css',
})
export class LoginPageComponent {
  constructor(
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

  login(): void {
    this.auth.loginMock();
    this.router.navigateByUrl('/summary');
  }
}
