import { createStore, withProps } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { DeclaracionListItem, DeclaracionSummary } from './declaraciones.model';

export interface DeclaracionesFilters {
  period: string | null;
}

export interface DeclaracionesProps extends DeclaracionesFilters {
  summaries: Record<number, DeclaracionSummary>;
}

export const declaracionesStore = createStore(
  { name: 'declaraciones' },
  withEntities<DeclaracionListItem>(),
  withProps<DeclaracionesProps>({
    period: null,
    summaries: {},
  })
);
