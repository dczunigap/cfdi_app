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
    deducibilidad: state.deducibilidad,
    deducibles_usos: state.deducibles_usos,
    receptor_scope: state.receptor_scope,
    mi_rfc: state.mi_rfc,
  }))
);

export const facturas$ = combineLatest([facturasEntities$, filters$]).pipe(
  map(([facturas, filters]) =>
    facturas.filter((f) => {
      const receptor = (f.receptor_rfc || '').trim().toUpperCase();
      const miRfc = (filters.mi_rfc || '').trim().toUpperCase();
      const usoCfdi = (f.uso_cfdi || '').trim().toUpperCase();
      const deducibles = new Set((filters.deducibles_usos || []).map((item) => item.trim().toUpperCase()));

      if (filters.year !== null && f.year_emision !== filters.year) return false;
      if (filters.month !== null && f.month_emision !== filters.month) return false;
      if (filters.tipo !== null && f.tipo_comprobante !== filters.tipo) return false;
      if (filters.naturaleza !== null && f.naturaleza !== filters.naturaleza) return false;
      if (filters.deducibilidad === 'DEDUCIBLES' && !deducibles.has(usoCfdi)) return false;
      if (filters.deducibilidad === 'NO_DEDUCIBLES' && usoCfdi && deducibles.has(usoCfdi)) return false;
      if (filters.receptor_scope === 'mine' && miRfc && receptor !== miRfc) return false;
      if (filters.receptor_scope === 'others' && miRfc && receptor === miRfc) return false;
      return true;
    })
  )
);

export const facturasCount$ = facturas$.pipe(map((items) => items.length));
