import { createStore, withProps } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { FacturaListItem } from './facturas.model';

export interface FacturasFilters {
  year: number | null;
  month: number | null;
  tipo: string | null;
  naturaleza: string | null;
  uso_cfdi: string | null;
  receptor_scope: 'all' | 'mine' | 'others';
  mi_rfc: string | null;
}

export const facturasStore = createStore(
  { name: 'facturas' },
  withEntities<FacturaListItem>(),
  withProps<FacturasFilters>({
    year: null,
    month: null,
    tipo: null,
    naturaleza: null,
    uso_cfdi: null,
    receptor_scope: 'all',
    mi_rfc: null,
  })
);
