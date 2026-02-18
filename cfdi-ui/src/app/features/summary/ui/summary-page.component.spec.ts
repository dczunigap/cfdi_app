import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { describe, expect, it, vi, beforeEach } from 'vitest';

import { SummaryFacade } from '../data/summary.facade';
import { SummaryData } from '../data/summary.model';
import { SummaryPageComponent } from './summary-page.component';

const summarySample: SummaryData = {
  tipo_declaracion: 'MENSUAL',
  year: 2025,
  month: 7,
  mi_rfc: 'AAA010101AAA',
  ingresos_total: 116,
  ingresos_base: 100,
  ingresos_trasl: 16,
  ingresos_ret: 0,
  gastos_total: 58,
  gastos_trasl: 8,
  gastos_ret: 0,
  p_count: 0,
  cash_in: 0,
  cash_out: 0,
  pagos_count: 0,
  plat_ing_siva: 0,
  plat_iva_tras: 0,
  plat_iva_ret: 0,
  plat_isr_ret: 0,
  plat_comision: 0,
  iva_causado_sugerido: 16,
  iva_acreditable_sugerido: 8,
  iva_retenido_plat: 0,
  iva_neto_sugerido: 8,
  saldo_a_favor_anterior: 0,
  saldo_a_pagar_anterior: 0,
};

describe('SummaryPageComponent', () => {
  const facadeMock = {
    loadSummary: vi.fn(),
    csvUrl: vi.fn(),
    downloadCsv: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    TestBed.configureTestingModule({
      imports: [SummaryPageComponent],
      providers: [provideRouter([]), { provide: SummaryFacade, useValue: facadeMock }],
    });
  });

  it('loads summary on init', () => {
    facadeMock.loadSummary.mockReturnValue(of(summarySample));
    const fixture = TestBed.createComponent(SummaryPageComponent);
    fixture.detectChanges();

    expect(facadeMock.loadSummary).toHaveBeenCalledWith('MENSUAL', null, null);
    expect(fixture.componentInstance.summary?.year).toBe(2025);
  });

  it('clears summary when facade returns null', () => {
    facadeMock.loadSummary.mockReturnValue(of(null));
    const fixture = TestBed.createComponent(SummaryPageComponent);
    fixture.componentInstance.summary = { ...summarySample };

    fixture.componentInstance.fetch();

    expect(fixture.componentInstance.summary).toBeNull();
    expect(fixture.componentInstance.loading).toBe(false);
  });

  it('delegates csv download to facade', () => {
    facadeMock.loadSummary.mockReturnValue(of(summarySample));
    facadeMock.csvUrl.mockReturnValue('/api/v1/sat_report.csv?year=2025&month=7');
    const fixture = TestBed.createComponent(SummaryPageComponent);
    fixture.componentInstance.summary = { ...summarySample };

    fixture.componentInstance.downloadCsv();

    expect(facadeMock.downloadCsv).toHaveBeenCalledWith(
      '/api/v1/sat_report.csv?year=2025&month=7',
      'sat_report_2025-07.csv',
    );
  });
});
