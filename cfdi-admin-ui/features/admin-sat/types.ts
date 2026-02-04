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
};

export type AdminUser = {
  id: number;
  username?: string | null;
  email?: string | null;
};
