export interface SummaryData {
  year: number;
  month: number;
  ingresos_total: number;
  ingresos_base: number;
  ingresos_trasl: number;
  ingresos_ret: number;
  gastos_total: number;
  gastos_trasl: number;
  gastos_ret: number;
  p_count: number;
  cash_in: number;
  cash_out: number;
  pagos_count: number;
  plat_ing_siva: number;
  plat_iva_tras: number;
  plat_iva_ret: number;
  plat_isr_ret: number;
  plat_comision: number;
  iva_causado_sugerido: number;
  iva_acreditable_sugerido: number;
  iva_retenido_plat: number;
  iva_neto_sugerido: number;
}

export interface SummaryDocItem {
  id: number;
  fecha_emision: string | null;
  tipo_comprobante: string | null;
  naturaleza: string | null;
  uuid: string | null;
  emisor_rfc: string | null;
  receptor_rfc: string | null;
  uso_cfdi: string | null;
  total: number | null;
  moneda: string | null;
}

export interface SummaryPagoItem {
  factura_id: number;
  fecha_pago: string | null;
  monto: number | null;
  moneda_p: string | null;
  forma_pago_p: string | null;
  naturaleza: string | null;
}

export interface SummaryDetails {
  docs: SummaryDocItem[];
  pagos: SummaryPagoItem[];
}
