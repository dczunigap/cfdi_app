import { createStore, withProps } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { RetencionListItem } from './retenciones.model';

export interface RetencionesFilters {
  period: string | null;
}

export const retencionesStore = createStore(
  { name: 'retenciones' },
  withEntities<RetencionListItem>(),
  withProps<RetencionesFilters>({
    period: null,
  })
);
