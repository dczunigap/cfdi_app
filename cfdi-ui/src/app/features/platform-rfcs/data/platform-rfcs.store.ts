import { createStore } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { PlatformRfc } from './platform-rfcs.model';

export const platformRfcsStore = createStore(
  { name: 'platform-rfcs' },
  withEntities<PlatformRfc>()
);
