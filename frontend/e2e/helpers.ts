import { APIRequestContext, Page, expect } from "@playwright/test";

export const API = "http://localhost:8000/api";

export const ADMIN = { email: "admin@saludfacil.com", password: "AdminSaludFacil!1" };
export const PROFESIONAL = { email: "profesional@saludfacil.com", password: "Profesional!1" };

let contador = 0;

export function siguienteCorreo(): string {
  contador += 1;
  const ts = Date.now();
  const dni = String((10000000 + (ts % 90000000)) % 100000000).padStart(8, "0");
  return { email: `e2e${ts}${contador}@test.com`, dni };
}

export async function api(
  request: APIRequestContext,
  method: string,
  path: string,
  body?: unknown,
  token?: string,
): Promise<{ status: number; data: Record<string, any> | null }> {
  const response = await request[method.toLowerCase() as "get" | "post" | "patch"](
    `${API}${path}`,
    {
      data: body,
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    },
  );
  let data: Record<string, any> | null = null;
  try {
    data = (await response.json()) as Record<string, any>;
  } catch {
    // sin cuerpo JSON
  }
  if (!response.ok()) {
    throw new Error(`API ${method} ${path} -> ${response.status()} ${JSON.stringify(data)}`);
  }
  return { status: response.status(), data };
}

export async function login(request: APIRequestContext, email: string, password: string): Promise<string> {
  const { data } = await api(request, "post", "/auth/login", { email, password });
  return data!.access_token as string;
}

export async function registrarPacienteApi(
  request: APIRequestContext,
): Promise<{ email: string; password: string; dni: string }> {
  const { email, dni } = siguienteCorreo();
  const password = "E2eClaveSegura!1";
  await api(request, "post", "/auth/register", {
    first_name: "E2E",
    last_name: "Paciente",
    dni,
    email,
    phone: "999123456",
    password,
  });
  return { email, password, dni };
}

function isoFecha(d: Date): string {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}

export interface SlotSeleccionado {
  fecha: string;
  hora: string;
  profesionalId: number;
  profesionalNombre: string;
}

export async function proximoSlotDisponible(
  request: APIRequestContext,
  token: string,
  preferIndex = 0,
): Promise<SlotSeleccionado> {
  const prof = await api(request, "get", "/directory/professionals", undefined, token);
  const profesionales = [...(prof.data as unknown as Array<Record<string, any>>)].sort(
    () => Math.random() - 0.5,
  );
  expect(profesionales.length).toBeGreaterThan(0);

  const d = new Date();
  for (let i = 2; i <= 45; i += 1) {
    const candidato = new Date(d.getFullYear(), d.getMonth(), d.getDate() + i);
    if (![1, 3, 5].includes(candidato.getDay())) continue;
    for (const p of profesionales) {
      const { data: slots } = await api(
        request,
        "get",
        `/directory/slots?professional_id=${p.id}&fecha=${isoFecha(candidato)}`,
        undefined,
        token,
      );
      const lista = slots as unknown as Array<Record<string, any>>;
      if (lista.length > 0) {
        const s = lista[preferIndex % lista.length];
        return {
          fecha: isoFecha(candidato),
          hora: s.hora_inicio as string,
          profesionalId: p.id as number,
          profesionalNombre: `${p.first_name} ${p.last_name}`,
        };
      }
    }
  }
  throw new Error("No se encontraron slots disponibles.");
}

export async function proximaFechaParaPro(
  request: APIRequestContext,
  token: string,
  profesionalId: number,
  inicio: number,
): Promise<string> {
  const d = new Date();
  for (let i = inicio; i <= 45; i += 1) {
    const candidato = new Date(d.getFullYear(), d.getMonth(), d.getDate() + i);
    if (![1, 3, 5].includes(candidato.getDay())) continue;
    const { data: slots } = await api(
      request,
      "get",
      `/directory/slots?professional_id=${profesionalId}&fecha=${isoFecha(candidato)}`,
      undefined,
      token,
    );
    if ((slots as unknown as Array<Record<string, any>>).length > 0) {
      return isoFecha(candidato);
    }
  }
  throw new Error(`No hay fechas disponibles para el profesional ${profesionalId}.`);
}

export async function crearCitaConTriajeApi(
  request: APIRequestContext,
): Promise<{ citaId: number; triajeId: number; slot: SlotSeleccionado }> {
  const paciente = await registrarPacienteApi(request);
  const token = await login(request, paciente.email, paciente.password);
  const Maria = 1;
  const desfase = 3 + Math.round(Math.random() * 28);

  let citaId: number | null = null;
  let slot: SlotSeleccionado | null = null;
  outer: for (let intento = 0; intento < 15; intento += 1) {
    const fecha = await proximaFechaParaPro(request, token, Maria, desfase + intento * 3);
    const { data: slots } = await api(
      request,
      "get",
      `/directory/slots?professional_id=${Maria}&fecha=${fecha}`,
      undefined,
      token,
    );
    for (const s of slots as unknown as Array<Record<string, any>>) {
      const candidato: SlotSeleccionado = {
        fecha,
        hora: s.hora_inicio as string,
        profesionalId: Maria,
        profesionalNombre: "María López",
      };
      try {
        const citaRes = await api(
          request,
          "post",
          "/appointments",
          { professional_id: candidato.profesionalId, fecha, hora_inicio: candidato.hora },
          token,
        );
        citaId = citaRes.data!.id as number;
        slot = candidato;
        break outer;
      } catch (err) {
        if (!String(err).includes("409")) throw err;
      }
    }
  }
  if (citaId === null || slot === null) {
    throw new Error("No se pudo reservar una cita para la profesional María López.");
  }
  const triajeRes = await api(
    request,
    "post",
    "/triage",
    { cita_id: citaId, sintomas: [{ nombre: "tos", severidad: "leve" }] },
    token,
  );
  return { citaId, triajeId: triajeRes.data!.id as number, slot };
}

export async function ingresarPorUi(page: Page, email: string, password: string): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Inicio" })).toBeVisible();
}