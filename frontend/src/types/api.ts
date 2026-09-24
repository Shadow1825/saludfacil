export type Role = "paciente" | "profesional" | "administrador";

export interface User {
  id: number;
  email: string;
  role: Role;
}