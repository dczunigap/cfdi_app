export interface AuthUser {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}
