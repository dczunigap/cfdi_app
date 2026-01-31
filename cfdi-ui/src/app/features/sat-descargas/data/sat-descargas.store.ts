import { createStore } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { SatDescarga } from './sat-descargas.model';

export const satDescargasStore = createStore(
  { name: 'sat-descargas' },
  withEntities<SatDescarga>()
);
