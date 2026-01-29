import { selectAllEntities } from '@ngneat/elf-entities';

import { rfcPhonesStore } from './rfc-phones.store';

export const rfcPhones$ = rfcPhonesStore.pipe(selectAllEntities());
