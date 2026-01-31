import { createStore } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { UserRfc } from './user-rfcs.model';

export const userRfcsStore = createStore(
  { name: 'user-rfcs' },
  withEntities<UserRfc, 'key'>({ idKey: 'key' })
);
