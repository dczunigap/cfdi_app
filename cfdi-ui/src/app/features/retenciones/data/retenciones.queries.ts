import { combineLatest, map } from 'rxjs';
import { selectAllEntities } from '@ngneat/elf-entities';

import { retencionesStore } from './retenciones.store';
import { RetencionListItem } from './retenciones.model';

const retencionesEntities$ = retencionesStore.pipe(selectAllEntities());
const filters$ = retencionesStore.pipe(map((state) => ({ period: state.period })));

const periodKey = (item: RetencionListItem): string | null => {
  if (!item.ejercicio || !item.mes_ini) return null;
  const month = String(item.mes_ini).padStart(2, '0');
  return `${item.ejercicio}-${month}`;
};

export const retencionesAll$ = retencionesEntities$;

export const retenciones$ = combineLatest([retencionesEntities$, filters$]).pipe(
  map(([items, filters]) =>
    items.filter((item) => {
      if (!filters.period) return true;
      return periodKey(item) === filters.period;
    })
  )
);

export const retencionesCount$ = retenciones$.pipe(map((items) => items.length));

export const retencionesPeriods$ = retencionesEntities$.pipe(
  map((items) =>
    Array.from(
      new Set(items.map(periodKey).filter((period): period is string => Boolean(period)))
    ).sort((a, b) => b.localeCompare(a))
  )
);
