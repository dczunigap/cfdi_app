export interface RetencionListItem {
  id: number;
  uuid: string | null;
  fecha_exp: string | null;
  ejercicio: number | null;
  mes_ini: number | null;
  mes_fin: number | null;
  emisor_rfc: string | null;
  emisor_nombre: string | null;
  receptor_rfc: string | null;
  mon_tot_serv_siva: number | null;
  total_iva_trasladado: number | null;
  total_iva_retenido: number | null;
  total_isr_retenido: number | null;
}

export interface RetencionDetail {
  id: number | null;
  uuid: string | null;
  fecha_exp: string | null;
  ejercicio: number | null;
  mes_ini: number | null;
  mes_fin: number | null;
  emisor_rfc: string | null;
  emisor_nombre: string | null;
  receptor_rfc: string | null;
  receptor_nombre: string | null;
  mon_tot_serv_siva: number | null;
  total_iva_trasladado: number | null;
  total_iva_retenido: number | null;
  total_isr_retenido: number | null;
  mon_total_por_uso_plataforma: number | null;
  xml_text: string | null;
}
