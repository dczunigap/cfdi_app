import { createStore } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { RfcPhone } from './rfc-phones.model';

export const rfcPhonesStore = createStore(
  { name: 'rfc-phones' },
  withEntities<RfcPhone, 'id'>({ idKey: 'id' })
);
