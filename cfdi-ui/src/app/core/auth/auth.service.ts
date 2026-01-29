import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable, of, switchMap, catchError, map, tap } from 'rxjs';

import { AuthUser } from './auth.model';
import { API_BASE_URL } from '../api/api-client';
import { environment } from '../../../environments/environment';

const STORAGE_USER_KEY = 'cfdi.auth.user';
const STORAGE_TOKEN_KEY = 'cfdi.auth.token';

type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly userSubject = new BehaviorSubject<AuthUser | null>(null);
  readonly user$ = this.userSubject.asObservable();

  constructor() {
    this.restore();
  }

  login(email: string, password: string): Observable<AuthUser> {
    return this.http
      .post<AuthTokenResponse>(`${API_BASE_URL}/auth/login`, { email, password })
      .pipe(
        tap((res) => this.setToken(res.access_token)),
        switchMap(() => this.fetchMe()),
        tap((user) => this.setUser(user))
      );
  }

  logout(): Observable<void> {
    return this.http.post<void>(`${API_BASE_URL}/auth/logout`, {}).pipe(
      catchError(() => of(void 0)),
      tap(() => {
        this.setUser(null);
        this.setToken(null);
      })
    );
  }

  clearSession(): void {
    this.setUser(null);
    this.setToken(null);
  }

  ensureAuthenticated(): Observable<boolean> {
    const token = this.getToken();
    if (!token || !this.isTokenValid(token)) {
      this.clearSession();
      return of(false);
    }
    if (environment.authValidationMode === 'local') {
      return of(true);
    }
    if (this.userSubject.value) {
      return of(true);
    }
    return this.fetchMe().pipe(
      tap((user) => this.setUser(user)),
      map(() => true),
      catchError(() => {
        this.clearSession();
        return of(false);
      })
    );
  }

  hasValidSessionLocal(): boolean {
    const token = this.getToken();
    return !!token && this.isTokenValid(token);
  }

  getToken(): string | null {
    return localStorage.getItem(STORAGE_TOKEN_KEY);
  }

  private fetchMe(): Observable<AuthUser> {
    return this.http.get<AuthUser>(`${API_BASE_URL}/auth/me`);
  }

  private restore(): void {
    const token = this.getToken();
    if (token && !this.isTokenValid(token)) {
      this.clearSession();
      return;
    }
    const raw = localStorage.getItem(STORAGE_USER_KEY);
    if (!raw) return;
    try {
      this.userSubject.next(JSON.parse(raw));
    } catch {
      localStorage.removeItem(STORAGE_USER_KEY);
    }
  }

  private setUser(user: AuthUser | null): void {
    this.userSubject.next(user);
    if (user) {
      localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(STORAGE_USER_KEY);
    }
  }

  private setToken(token: string | null): void {
    if (token) {
      localStorage.setItem(STORAGE_TOKEN_KEY, token);
    } else {
      localStorage.removeItem(STORAGE_TOKEN_KEY);
    }
  }

  private isTokenValid(token: string): boolean {
    const payload = this.decodeJwtPayload(token);
    if (!payload || typeof payload.exp !== 'number') {
      return false;
    }
    const now = Math.floor(Date.now() / 1000);
    return payload.exp > now;
  }

  private decodeJwtPayload(token: string): { exp?: number } | null {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    try {
      const payloadPart = parts.length === 2 ? parts[0] : parts[1];
      const payload = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
      const pad = payload.length % 4;
      const normalized = pad ? payload + '='.repeat(4 - pad) : payload;
      const decoded = atob(normalized);
      return JSON.parse(decoded);
    } catch {
      return null;
    }
  }
}
