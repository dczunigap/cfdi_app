export type SatCredential = {
  rfc: string;
  created_at: string;
  updated_at: string | null;
  has_pfx: boolean;
  has_password: boolean;
};

export type RfcPhone = {
  id: number;
  phone: string;
  rfc: string;
};

export type UserRfc = {
  user_id: number;
  rfc: string;
  tipo_persona_clave: "PM" | "PF" | "EXT";
  regimen_fiscal_clave: string;
  regimen_fiscal_descripcion: string;
};

export type TipoPersonaCatalog = {
  clave: "PM" | "PF" | "EXT";
  descripcion: string;
};

export type RegimenFiscalCatalog = {
  id: number;
  tipo_persona_clave: "PM" | "PF" | "EXT";
  clave: string;
  descripcion: string;
  activo: boolean;
};

export type UserRfcCatalogs = {
  tipos_persona: TipoPersonaCatalog[];
  regimenes_fiscales: RegimenFiscalCatalog[];
};

export type AdminUser = {
  id: number;
  username?: string | null;
  email?: string | null;
};
