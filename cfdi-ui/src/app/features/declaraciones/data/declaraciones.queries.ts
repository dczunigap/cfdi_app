import { combineLatest, map } from 'rxjs';
import { selectAllEntities } from '@ngneat/elf-entities';

import { declaracionesStore } from './declaraciones.store';
import { DeclaracionListItem, DeclaracionListView } from './declaraciones.model';

const declaracionesEntities$ = declaracionesStore.pipe(selectAllEntities());
const filters$ = declaracionesStore.pipe(map((state) => ({ period: state.period })));
const summaries$ = declaracionesStore.pipe(map((state) => state.summaries));

const periodKey = (item: DeclaracionListItem): string => {
  const month = String(item.month).padStart(2, '0');
  return `${item.year}-${month}`;
};

export const declaraciones$ = combineLatest([declaracionesEntities$, filters$, summaries$]).pipe(
  map(([items, filters, summaries]) =>
    items
      .filter((item) => {
        if (!filters.period) return true;
        return periodKey(item) === filters.period;
      })
      .map(
        (item): DeclaracionListView => ({
          ...item,
          summary: summaries[item.id],
        })
      )
  )
);

export const declaracionesCount$ = declaraciones$.pipe(map((items) => items.length));

export const declaracionesPeriods$ = declaracionesEntities$.pipe(
  map((items) =>
    Array.from(new Set(items.map(periodKey))).sort((a, b) => b.localeCompare(a))
  )
);
