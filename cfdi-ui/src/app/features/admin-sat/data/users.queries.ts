import { selectAllEntities } from '@ngneat/elf-entities';

import { usersStore } from './users.store';

export const adminUsers$ = usersStore.pipe(selectAllEntities());
