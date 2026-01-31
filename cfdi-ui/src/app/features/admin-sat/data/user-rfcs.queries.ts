import { selectAllEntities } from '@ngneat/elf-entities';

import { userRfcsStore } from './user-rfcs.store';

export const userRfcs$ = userRfcsStore.pipe(selectAllEntities());
