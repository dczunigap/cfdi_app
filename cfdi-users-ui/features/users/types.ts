import { z } from "zod";

const passwordSchema = z
  .string()
  .optional()
  .transform((value) => (value && value.trim() ? value : undefined));

export const userSchema = z.object({
  username: z.string().min(1, "Username requerido"),
  email: z.string().email("Correo inválido"),
  password: passwordSchema,
  is_active: z.boolean().optional(),
});

export type UserFormValues = z.input<typeof userSchema>;
export type UserFormOutput = z.output<typeof userSchema>;

export type User = {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
};
