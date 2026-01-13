import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { AuthUser } from './auth.model';

const STORAGE_KEY = 'cfdi.auth.user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly userSubject = new BehaviorSubject<AuthUser | null>(null);
  readonly user$ = this.userSubject.asObservable();

  constructor() {
    this.restore();
  }

  loginMock(name = 'Demo', role = 'admin'): void {
    this.setUser({
      id: 'mock-user',
      name,
      role,
    });
  }

  logout(): void {
    this.setUser(null);
  }

  private restore(): void {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      this.userSubject.next(JSON.parse(raw));
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  private setUser(user: AuthUser | null): void {
    this.userSubject.next(user);
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }
}
