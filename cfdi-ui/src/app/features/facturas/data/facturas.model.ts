export interface FacturaListItem {
  id: number;
  uuid: string | null;
  fecha_emision: string | null;
  tipo_comprobante: string | null;
  year_emision: number | null;
  month_emision: number | null;
  emisor_rfc: string | null;
  emisor_nombre: string | null;
  receptor_rfc: string | null;
  receptor_nombre: string | null;
  uso_cfdi: string | null;
  moneda: string | null;
  subtotal: number | null;
  descuento: number | null;
  total: number | null;
  total_trasladados: number | null;
  total_retenidos: number | null;
  naturaleza: string | null;
}

export interface ConceptoItem {
  id: number | null;
  factura_id: number;
  clave_prod_serv: string | null;
  cantidad: number | null;
  clave_unidad: string | null;
  descripcion: string | null;
  valor_unitario: number | null;
  importe: number | null;
  objeto_imp: string | null;
}

export interface PagoItem {
  id: number | null;
  factura_id: number;
  fecha_pago: string | null;
  year_pago: number | null;
  month_pago: number | null;
  monto: number | null;
  moneda_p: string | null;
  forma_pago_p: string | null;
}

export interface FacturaDetail {
  factura: FacturaListItem;
  conceptos: ConceptoItem[];
  pagos: PagoItem[];
}
