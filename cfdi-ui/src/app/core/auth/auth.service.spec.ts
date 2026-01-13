import { describe, expect, it, beforeEach } from 'vitest';
import { firstValueFrom } from 'rxjs';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts with null user', async () => {
    const service = new AuthService();
    const value = await firstValueFrom(service.user$);
    expect(value).toBeNull();
  });

  it('logs in with mock and persists', async () => {
    const service = new AuthService();
    service.loginMock('User', 'admin');
    const value = await firstValueFrom(service.user$);
    expect(value?.name).toBe('User');
    expect(localStorage.getItem('cfdi.auth.user')).toContain('User');
  });

  it('logs out and clears storage', async () => {
    const service = new AuthService();
    service.loginMock();
    service.logout();
    const value = await firstValueFrom(service.user$);
    expect(value).toBeNull();
    expect(localStorage.getItem('cfdi.auth.user')).toBeNull();
  });
});
