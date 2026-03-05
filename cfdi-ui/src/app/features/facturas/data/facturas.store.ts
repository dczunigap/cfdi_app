import { createStore, withProps } from '@ngneat/elf';
import { withEntities } from '@ngneat/elf-entities';

import { Deducibilidad, FacturaListItem, TipoDeclaracion } from './facturas.model';

export interface FacturasFilters {
  year: number | null;
  month: number | null;
  tipo: string | null;
  naturaleza: string | null;
  deducibilidad: Deducibilidad;
  tipo_declaracion: TipoDeclaracion;
  deducibles_usos: string[];
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
    deducibilidad: 'TODAS',
    tipo_declaracion: 'MENSUAL',
    deducibles_usos: [],
    receptor_scope: 'all',
    mi_rfc: null,
  })
);
