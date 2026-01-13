import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, take } from 'rxjs';

import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

export const authGuard: CanActivateFn = () => {
  if (!environment.authEnabled) {
    return true;
  }

  const auth = inject(AuthService);
  const router = inject(Router);

  return auth.user$.pipe(
    take(1),
    map((user) => (user ? true : router.parseUrl('/login')))
  );
};
