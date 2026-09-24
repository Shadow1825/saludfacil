export type Role = "paciente" | "profesional" | "administrador";

export interface User {
  id: number;
  email: string;
  role: Role;
  first_name: string;
  last_name: string;
  dni: string;
  phone: string;
  is_active: boolean;
  created_at: string;
}

export const ROLE_LABEL: Record<Role, string> = {
  paciente: "Paciente",
  profesional: "Profesional de salud",
  administrador: "Administrador",
};