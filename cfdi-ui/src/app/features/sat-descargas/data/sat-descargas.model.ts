export interface SatDescarga {
  id: number;
  rfc: string;
  kind: string;
  tipo_solicitud: string;
  anio_filtro?: number | null;
  mes_filtro?: number | null;
  id_solicitud?: string | null;
  estado: string;
  paquetes: string[];
  link_descarga?: string | null;
  zip_path?: string | null;
  attempts: number;
  next_check_at?: string | null;
  last_error?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface SatDescargaCreatePayload {
  kind: 'cfdi' | 'retenciones';
  direccion_solicitud: 'emitidos' | 'recibidos';
  tipo_descarga: 'CFDI' | 'Metadata';
  // Compatibilidad legacy del backend.
  tipo_solicitud?: 'emitidos' | 'recibidos';
  fecha_inicial: string;
  fecha_final: string;
  rfc_emisor?: string | null;
  rfc_receptor?: string | null;
  rfc_a_cuenta_terceros?: string | null;
  tipo_comprobante?: string | null;
  complemento?: string | null;
  estado_comprobante?: string | null;
  folio?: string | null;
  uuid?: string | null;
  rfc_receptores?: string[];
}
