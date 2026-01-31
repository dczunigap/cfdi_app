import { createStore } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { AdminUser } from './users.model';

export const usersStore = createStore(
  { name: 'admin-users' },
  withEntities<AdminUser>()
);
