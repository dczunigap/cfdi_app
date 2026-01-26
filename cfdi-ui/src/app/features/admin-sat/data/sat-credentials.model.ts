export interface SatCredential {
  rfc: string;
  created_at: string;
  updated_at?: string | null;
  has_password: boolean;
  has_pfx: boolean;
}
