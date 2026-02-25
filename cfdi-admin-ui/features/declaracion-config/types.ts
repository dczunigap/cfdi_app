export type TipoDeclaracionClave = "MENSUAL" | "ANUAL";

export type DeclaracionTipoCatalog = {
  clave: TipoDeclaracionClave;
  descripcion: string;
  activo: boolean;
};

export type DeclaracionRegimenCatalog = {
  id: number;
  tipo_persona_clave: "PM" | "PF" | "EXT";
  clave: string;
  descripcion: string;
  activo: boolean;
};

export type DeclaracionUsoCatalog = {
  clave: string;
  descripcion: string;
  tipo_declaracion_clave: TipoDeclaracionClave;
  activo: boolean;
};

export type DeclaracionConfigCatalogs = {
  tipos_declaracion: DeclaracionTipoCatalog[];
  regimenes_fiscales: DeclaracionRegimenCatalog[];
  usos_cfdi_deduccion: DeclaracionUsoCatalog[];
};

export type DeclaracionConfigUso = {
  clave: string;
  descripcion: string;
  orden: number;
};

export type DeclaracionConfigGet = {
  regimen_fiscal: {
    id: number;
    clave: string;
    descripcion: string | null;
    tipo_persona_clave: string;
  };
  tipo_declaracion_clave: TipoDeclaracionClave;
  activo: boolean;
  incluir_acumulado_mensual_en_anual: boolean;
  usos_cfdi: DeclaracionConfigUso[];
};

export type DeclaracionConfigUpsertPayload = {
  regimen_fiscal_clave: string;
  tipo_declaracion_clave: TipoDeclaracionClave;
  activo: boolean;
  incluir_acumulado_mensual_en_anual: boolean;
  usos_cfdi: Array<{
    clave: string;
    orden: number;
  }>;
};

export type DeclaracionConfigUpsertResponse = {
  ok: boolean;
  config_id: number;
};
