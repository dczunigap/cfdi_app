import { selectAllEntities } from '@ngneat/elf-entities';

import { satCredentialsStore } from './sat-credentials.store';

export const satCredentials$ = satCredentialsStore.pipe(selectAllEntities());
