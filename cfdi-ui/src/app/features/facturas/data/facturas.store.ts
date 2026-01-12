import { createStore, withProps } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { FacturaListItem } from './facturas.model';

export interface FacturasFilters {
  year: number | null;
  month: number | null;
  tipo: string | null;
  naturaleza: string | null;
}

export const facturasStore = createStore(
  { name: 'facturas' },
  withEntities<FacturaListItem>(),
  withProps<FacturasFilters>({
    year: null,
    month: null,
    tipo: null,
    naturaleza: null,
  })
);
