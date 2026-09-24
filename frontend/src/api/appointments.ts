import { get, patch, post } from "./client";

export type CitaEstado = "reservada" | "cancelada" | "atendida" | "no_asistio";

export interface Cita {
  id: number;
  paciente_id: number;
  professional_id: number;
  specialty_id: number;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  estado: CitaEstado;
  is_active: boolean;
  paciente: string;
  profesional: string;
  profesional_email: string;
  specialty_name: string;
  dia: string;
}

export interface Slot {
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
}

export const ESTADO_LABEL: Record<CitaEstado, string> = {
  reservada: "Reservada",
  cancelada: "Cancelada",
  atendida: "Atendida",
  no_asistio: "No asistió",
};

export function createAppointment(payload: {
  professional_id: number;
  fecha: string;
  hora_inicio: string;
}): Promise<Cita> {
  return post<Cita>("/appointments", payload);
}

export function listAppointments(params: {
  profesional_id?: number;
  especialidad_id?: number;
  estado?: string;
} = {}): Promise<Cita[]> {
  const qs = new URLSearchParams();
  if (params.profesional_id) qs.set("profesional_id", String(params.profesional_id));
  if (params.especialidad_id) qs.set("especialidad_id", String(params.especialidad_id));
  if (params.estado) qs.set("estado", params.estado);
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return get<Cita[]>(`/appointments${query}`);
}

export function cancelAppointment(id: number): Promise<{ message: string; id: number }> {
  return post<{ message: string; id: number }>(`/appointments/${id}/cancel`, {});
}

export function updateAppointmentEstado(id: number, estado: "cancelada" | "atendida" | "no_asistio"): Promise<{
  message: string;
  id: number;
  estado: string;
}> {
  return patch<{ message: string; id: number; estado: string }>(`/appointments/${id}`, { estado });
}

export function directorioSlots(professionalId: number, fecha: string): Promise<Slot[]> {
  return get<Slot[]>(`/directory/slots?professional_id=${professionalId}&fecha=${fecha}`);
}