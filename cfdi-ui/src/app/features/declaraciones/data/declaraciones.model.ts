export interface DeclaracionListItem {
  id: number;
  year: number;
  month: number;
  rfc: string | null;
  folio: string | null;
  fecha_presentacion: string | null;
  filename: string | null;
  original_name: string | null;
  num_pages: number | null;
  sha256: string | null;
}

export interface DeclaracionDetail extends DeclaracionListItem {
  text_excerpt: string | null;
}

export interface DeclaracionSummary {
  periodo?: string | null;
  rfc?: string | null;
  nombre?: string | null;
  numero_operacion?: string | null;
  ingresos_totales_mes?: number | null;
  iva_a_cargo_16?: number | null;
  iva_retenido?: number | null;
  retenciones_plataformas?: number | null;
  fecha_presentacion?: string | null;
}

export interface DeclaracionListView extends DeclaracionListItem {
  summary?: DeclaracionSummary;
}
