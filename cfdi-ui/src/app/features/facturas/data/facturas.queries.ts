import { combineLatest, map } from 'rxjs';
import { selectAllEntities } from '@ngneat/elf-entities';
import { facturasStore } from './facturas.store';

const facturasEntities$ = facturasStore.pipe(selectAllEntities());
const filters$ = facturasStore.pipe(
  map((state) => ({
    year: state.year,
    month: state.month,
    tipo: state.tipo,
    naturaleza: state.naturaleza,
  }))
);

export const facturas$ = combineLatest([facturasEntities$, filters$]).pipe(
  map(([facturas, filters]) =>
    facturas.filter((f) => {
      if (filters.year !== null && f.year_emision !== filters.year) return false;
      if (filters.month !== null && f.month_emision !== filters.month) return false;
      if (filters.tipo !== null && f.tipo_comprobante !== filters.tipo) return false;
      if (filters.naturaleza !== null && f.naturaleza !== filters.naturaleza) return false;
      return true;
    })
  )
);

export const facturasCount$ = facturas$.pipe(map((items) => items.length));
