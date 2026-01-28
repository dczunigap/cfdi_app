import { ApplicationConfig, importProvidersFrom, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter } from '@angular/router';
import { DialogModule } from '@angular/cdk/dialog';

import { routes } from './app.routes';
import { httpErrorInterceptor } from './core/api/http-error.interceptor';
import { rfcInterceptor } from './core/api/rfc.interceptor';
import { loadingInterceptor } from './shared/ui/loading/loading.interceptor';
import { authInterceptor } from './core/auth/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideHttpClient(withInterceptors([loadingInterceptor, authInterceptor, rfcInterceptor, httpErrorInterceptor])),
    provideRouter(routes),
    provideAnimations(),
    importProvidersFrom(DialogModule),
  ]
};
