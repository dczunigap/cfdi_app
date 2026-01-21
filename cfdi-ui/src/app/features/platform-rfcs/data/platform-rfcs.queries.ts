import { map } from 'rxjs';
import { selectAllEntities } from '@ngneat/elf-entities';

import { platformRfcsStore } from './platform-rfcs.store';

const platformRfcsEntities$ = platformRfcsStore.pipe(selectAllEntities());

export const platformRfcs$ = platformRfcsEntities$.pipe(
  map((items) => [...items].sort((a, b) => a.rfc.localeCompare(b.rfc)))
);
