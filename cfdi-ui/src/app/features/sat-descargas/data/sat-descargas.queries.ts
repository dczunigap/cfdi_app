import { selectAllEntities } from '@ngneat/elf-entities';

import { satDescargasStore } from './sat-descargas.store';

export const satDescargas$ = satDescargasStore.pipe(selectAllEntities());
