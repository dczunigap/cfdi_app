import { describe, expect, it, beforeEach } from 'vitest';
import { firstValueFrom } from 'rxjs';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { AuthService } from './auth.service';
import { API_BASE_URL } from '../api/api-client';

describe('AuthService', () => {
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), AuthService],
    });
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('starts with null user', async () => {
    const service = TestBed.inject(AuthService);
    const value = await firstValueFrom(service.user$);
    expect(value).toBeNull();
  });

  it('logs out and clears storage', async () => {
    const service = TestBed.inject(AuthService);
    const logoutPromise = firstValueFrom(service.logout());
    const req = httpMock.expectOne(`${API_BASE_URL}/auth/logout`);
    req.flush(null);
    await logoutPromise;
    const value = await firstValueFrom(service.user$);
    expect(value).toBeNull();
    expect(localStorage.getItem('cfdi.auth.user')).toBeNull();
  });
});
