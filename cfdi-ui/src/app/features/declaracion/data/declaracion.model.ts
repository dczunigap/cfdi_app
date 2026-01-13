export interface DeclaracionCheck {
  level: 'ok' | 'warn' | 'error' | 'info';
  title: string;
  detail: string;
}

export interface DeclaracionPdf {
  id: number;
  rfc: string | null;
  folio: string | null;
  fecha_presentacion: string | null;
  filename: string;
  original_name: string | null;
  text_excerpt: string | null;
}

export interface DeclaracionSummary {
  year: number;
  month: number;
  income_source: string;
  effective_income_source: string;
  mi_rfc: string | null;
  ingresos_total_sin_iva: number;
  plat_ing_siva: number;
  ingresos_base: number;
  isr_retenido: number;
  iva_retenido: number;
  iva_trasladado_total: number;
  iva_trasladado_seleccion: number;
  checks: DeclaracionCheck[];
  acuse_payload: DeclaracionAcusePayload | null;
  acuse_checks: DeclaracionAcuseCheck[];
  declaracion_pdf: DeclaracionPdf | null;
  retenciones_count: number;
  docs_count: number;
  pagos_count: number;
}

export interface DeclaracionAcusePayload {
  periodo: string | null;
  rfc: string | null;
  nombre: string | null;
  tipo_declaracion: string | null;
  periodo_mes: string | null;
  ejercicio: number | null;
  numero_operacion: string | null;
  fecha_presentacion: string | null;
  linea_captura: string | null;
  ingresos_totales_mes: number | null;
  isr_causado: number | null;
  retenciones_plataformas: number | null;
  iva_tasa: number | null;
  iva_a_cargo_16: number | null;
  iva_acreditable: number | null;
  iva_retenido: number | null;
}

export interface DeclaracionAcuseCheck {
  status: 'ok' | 'warn' | 'error' | 'info';
  label: string;
  sat: number | string | null;
  app: number | string | null;
  diff: number | null;
  note: string | null;
}
