import { get, patch, post } from "./client";

export type Severidad = "leve" | "moderada" | "intensa";
export type Clasificacion = "alta" | "media" | "baja";
export type EstadoRevision = "pendiente" | "revisado" | "descartado";

export interface Sintoma {
  nombre: string;
  severidad: Severidad;
}

export interface Triage {
  id: number;
  cita_id: number;
  paciente_id: number;
  fecha: string;
  hora_inicio: string;
  paciente: string;
  profesional: string;
  specialty_name: string;
  dia: string;
  clasificacion: Clasificacion;
  resultado: string;
  sintomas: Sintoma[];
  es_diagnostico: boolean;
  mensaje: string;
  estado_revision: EstadoRevision;
  estado_revision_label: string;
  revisado_en: string | null;
  created_at: string;
}

export const CLASIFICACION_LABEL: Record<Clasificacion, string> = {
  alta: "Alta",
  media: "Media",
  baja: "Baja",
};

export const ESTADO_REVISION_LABEL: Record<EstadoRevision, string> = {
  pendiente: "Pendiente de revisión",
  revisado: "Revisado",
  descartado: "Descartado",
};

// Síntomas de las reglas R1-R3 (especificación oficial del triaje).
export const SINTOMAS_ALTA_CANONICOS: ReadonlyArray<{ nombre: string; descripcion: string }> = [
  { nombre: "Dificultad respiratoria", descripcion: "Dificultad respiratoria intensa (R1)" },
  { nombre: "Dolor torácico", descripcion: "Dolor torácico intenso (R2)" },
  { nombre: "Pérdida de conciencia", descripcion: "Pérdida de conciencia (R3)" },
];

export function createTriaje(citaId: number, sintomas: Sintoma[]): Promise<Triage> {
  return post<Triage>("/triage", { cita_id: citaId, sintomas });
}

export function listTriajes(): Promise<Triage[]> {
  return get<Triage[]>("/triage");
}

export function updateTriajeRevision(citaId: number, estado: "revisado" | "descartado"): Promise<Triage> {
  return patch<Triage>(`/triage/${citaId}/revision`, { estado });
}