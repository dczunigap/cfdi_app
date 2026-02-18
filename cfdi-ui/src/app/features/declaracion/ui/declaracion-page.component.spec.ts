import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { DeclaracionFacade } from '../data/declaracion.facade';
import { DeclaracionSummary } from '../data/declaracion.model';
import { DeclaracionPageComponent } from './declaracion-page.component';

const declaracionSample: DeclaracionSummary = {
  tipo_declaracion: 'MENSUAL',
  year: 2025,
  month: 7,
  income_source: 'cfdi',
  effective_income_source: 'cfdi',
  mi_rfc: 'AAA010101AAA',
  ingresos_total_sin_iva: 100,
  plat_ing_siva: 0,
  ingresos_base: 100,
  isr_retenido: 0,
  iva_retenido: 0,
  iva_acreditable: 8,
  iva_trasladado_total: 16,
  iva_trasladado_seleccion: 16,
  saldo_a_favor_anterior: 0,
  saldo_a_pagar_anterior: 0,
  checks: [],
  acuse_payload: null,
  acuse_checks: [],
  declaracion_pdf: null,
  retenciones_count: 0,
  docs_count: 1,
  pagos_count: 0,
};

describe('DeclaracionPageComponent', () => {
  const facadeMock = {
    loadDeclaracion: vi.fn(),
    csvUrl: vi.fn(),
    hojaUrl: vi.fn(),
    pdfUrl: vi.fn(),
    downloadFile: vi.fn(),
    openPdf: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    TestBed.configureTestingModule({
      imports: [DeclaracionPageComponent],
      providers: [provideRouter([]), { provide: DeclaracionFacade, useValue: facadeMock }],
    });
  });

  it('loads declaracion with selected filters', () => {
    facadeMock.loadDeclaracion.mockReturnValue(of(declaracionSample));
    const fixture = TestBed.createComponent(DeclaracionPageComponent);
    fixture.componentInstance.year = 2025;
    fixture.componentInstance.month = 7;
    fixture.componentInstance.tipoDeclaracion = 'MENSUAL';
    fixture.componentInstance.incomeSource = 'cfdi';

    fixture.componentInstance.load();

    expect(facadeMock.loadDeclaracion).toHaveBeenCalledWith('MENSUAL', 2025, 7, 'cfdi');
    expect(fixture.componentInstance.summary?.year).toBe(2025);
  });

  it('clears summary when facade returns null', () => {
    facadeMock.loadDeclaracion.mockReturnValue(of(null));
    const fixture = TestBed.createComponent(DeclaracionPageComponent);
    fixture.componentInstance.summary = { ...declaracionSample };

    fixture.componentInstance.load();

    expect(fixture.componentInstance.summary).toBeNull();
    expect(fixture.componentInstance.loading).toBe(false);
  });

  it('delegates download and open actions to facade', () => {
    facadeMock.loadDeclaracion.mockReturnValue(of(declaracionSample));
    facadeMock.csvUrl.mockReturnValue('/api/v1/sat_report.csv?year=2025&month=7&income_source=cfdi');
    facadeMock.hojaUrl.mockReturnValue('/api/v1/sat_hoja.txt?year=2025&month=7&income_source=cfdi');
    facadeMock.pdfUrl.mockReturnValue('/api/v1/declaraciones/1/archivo/demo.pdf');
    const fixture = TestBed.createComponent(DeclaracionPageComponent);
    fixture.componentInstance.year = 2025;
    fixture.componentInstance.month = 7;

    fixture.componentInstance.downloadCsv();
    fixture.componentInstance.downloadHoja();
    fixture.componentInstance.openPdf({
      id: 1,
      rfc: null,
      folio: null,
      fecha_presentacion: null,
      filename: 'demo.pdf',
      original_name: null,
      text_excerpt: null,
    });

    expect(facadeMock.downloadFile).toHaveBeenNthCalledWith(
      1,
      '/api/v1/sat_report.csv?year=2025&month=7&income_source=cfdi',
      'sat_report_2025-07.csv',
      'No se pudo descargar el CSV SAT.',
    );
    expect(facadeMock.downloadFile).toHaveBeenNthCalledWith(
      2,
      '/api/v1/sat_hoja.txt?year=2025&month=7&income_source=cfdi',
      'hoja_sat_2025-07.txt',
      'No se pudo generar la hoja SAT.',
    );
    expect(facadeMock.openPdf).toHaveBeenCalledOnce();
  });
});
