import { describe, expect, it, beforeEach } from 'vitest';
import { firstValueFrom } from 'rxjs';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), AuthService],
    });
  });

  it('starts with null user', async () => {
    const service = TestBed.inject(AuthService);
    const value = await firstValueFrom(service.user$);
    expect(value).toBeNull();
  });

  it('logs out and clears storage', async () => {
    const service = TestBed.inject(AuthService);
    await firstValueFrom(service.logout());
    const value = await firstValueFrom(service.user$);
    expect(value).toBeNull();
    expect(localStorage.getItem('cfdi.auth.user')).toBeNull();
  });
});
