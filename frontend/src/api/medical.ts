import { get, patch, post } from "./client";

export interface Especialidad {
  id: number;
  nombre: string;
  is_active: boolean;
}

export interface Profesional {
  id: number;
  user_id: number;
  specialty_id: number;
  specialty_name: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
}

export interface Horario {
  id: number;
  professional_id: number;
  day: number;
  day_name: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface ProfessionalPayload {
  first_name: string;
  last_name: string;
  dni: string;
  email: string;
  phone: string;
  password: string;
  specialty_id: number;
}

export const DIAS_SEMANA: Record<number, string> = {
  1: "Lunes",
  2: "Martes",
  3: "Miércoles",
  4: "Jueves",
  5: "Viernes",
  6: "Sábado",
  7: "Domingo",
};

export function listSpecialties(): Promise<Especialidad[]> {
  return get<Especialidad[]>("/specialties");
}

export function createSpecialty(nombre: string): Promise<Especialidad> {
  return post<Especialidad>("/specialties", { nombre });
}

export function updateSpecialty(id: number, payload: { nombre?: string; is_active?: boolean }): Promise<Especialidad> {
  return patch<Especialidad>(`/specialties/${id}`, payload);
}

export function listProfessionals(): Promise<Profesional[]> {
  return get<Profesional[]>("/professionals");
}

export function createProfessional(payload: ProfessionalPayload): Promise<Profesional> {
  return post<Profesional>("/professionals", payload);
}

export function updateProfessional(
  id: number,
  payload: { specialty_id?: number; is_active?: boolean; first_name?: string; last_name?: string; phone?: string },
): Promise<Profesional> {
  return patch<Profesional>(`/professionals/${id}`, payload);
}

export function listSchedules(professionalId?: number): Promise<Horario[]> {
  const query = professionalId !== undefined ? `?professional_id=${professionalId}` : "";
  return get<Horario[]>(`/schedules${query}`);
}

export function createSchedule(payload: { professional_id: number; day: number; start_time: string; end_time: string }): Promise<Horario> {
  return post<Horario>("/schedules", payload);
}

export function updateSchedule(
  id: number,
  payload: { day?: number; start_time?: string; end_time?: string; is_active?: boolean },
): Promise<Horario> {
  return patch<Horario>(`/schedules/${id}`, payload);
}

export interface DisponibilidadProfesional extends Profesional {}

export function directorioSpecialties(): Promise<Especialidad[]> {
  return get<Especialidad[]>("/directory/specialties");
}

export function directorioProfessionals(specialtyId?: number): Promise<Profesional[]> {
  const query = specialtyId !== undefined ? `?specialty_id=${specialtyId}` : "";
  return get<Profesional[]>(`/directory/professionals${query}`);
}

export function directorioSchedules(professionalId: number): Promise<Horario[]> {
  return get<Horario[]>(`/directory/schedules?professional_id=${professionalId}`);
}