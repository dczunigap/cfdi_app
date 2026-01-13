import { describe, expect, it } from 'vitest';
import { firstValueFrom } from 'rxjs';

import { LoadingService } from './loading.service';

describe('LoadingService', () => {
  it('increments and decrements', async () => {
    const service = new LoadingService();
    service.show();
    service.show();
    service.hide();
    const value = await firstValueFrom(service.isLoading$);
    expect(value).toBe(1);
  });

  it('never goes below zero', async () => {
    const service = new LoadingService();
    service.hide();
    const value = await firstValueFrom(service.isLoading$);
    expect(value).toBe(0);
  });
});
