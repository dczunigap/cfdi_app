import { createStore } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { SatCredential } from './sat-credentials.model';

export const satCredentialsStore = createStore(
  { name: 'sat-credentials' },
  withEntities<SatCredential, 'rfc'>({ idKey: 'rfc' })
);
