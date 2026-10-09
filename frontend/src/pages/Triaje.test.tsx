import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TriajePage } from "./Triaje";

function apiResponse(body: unknown, status = 200): { ok: boolean; status: number; json: () => Promise<unknown> } {
  return { ok: status < 400, status, json: () => Promise.resolve(body) };
}

function fechaFuturaISO(diasAdelante = 7): string {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() + diasAdelante);
  return fecha.toISOString().slice(0, 10);
}

const FECHA_CITA = fechaFuturaISO();

const CITA = {
  id: 55,
  paciente_id: 9,
  professional_id: 1,
  specialty_id: 1,
  fecha: FECHA_CITA,
  hora_inicio: "08:00",
  hora_fin: "08:30",
  estado: "reservada",
  is_active: true,
  paciente: "Luis Quispe",
  profesional: "María López",
  profesional_email: "maria@prof.com",
  specialty_name: "Medicina General",
  dia: "Lunes",
};

const TRIAGE_ALTA = {
  id: 1,
  cita_id: 55,
  paciente_id: 9,
  fecha: FECHA_CITA,
  hora_inicio: "08:00",
  paciente: "Luis Quispe",
  profesional: "María López",
  specialty_name: "Medicina General",
  dia: "Lunes",
  clasificacion: "alta",
  resultado: "Alta",
  sintomas: [{ nombre: "pérdida de conciencia", severidad: "intensa" }],
  es_diagnostico: false,
  mensaje: "Clasificación inicial orientativa. Esta clasificación no constituye un diagnóstico médico.",
  created_at: "2026-09-24T18:00:00",
};

describe("TriajePage (FASE 5, HU-07 / RF-12)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("registra síntomas y muestra la clasificación inicial como no-diagnóstico", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse([CITA])) // citas iniciales
      .mockResolvedValueOnce(apiResponse([])) // historial inicial
      .mockResolvedValueOnce(apiResponse(TRIAGE_ALTA, 201)) // POST /triage
      .mockResolvedValueOnce(apiResponse([CITA])) // recarga citas
      .mockResolvedValueOnce(apiResponse([TRIAGE_ALTA])); // recarga historial

    render(<TriajePage />);

    const selectCita = await screen.findByLabelText("Cita para el triaje");
    fireEvent.change(selectCita, { target: { value: "55" } });

    const checkbox = screen.getByRole("checkbox", { name: /Pérdida de conciencia/ });
    fireEvent.click(checkbox);

    fireEvent.click(screen.getByRole("button", { name: "Obtener clasificación inicial" }));

    const status = await screen.findByRole("status");
    expect(status).toHaveTextContent("Alta");
    expect(status).toHaveTextContent("no constituye un diagnóstico médico");

    const postCall = fetchMock.mock.calls.find(
      (call) => call[1] && call[1].method === "POST",
    );
    expect(postCall).toBeDefined();
    expect(postCall![1].body).toContain('"cita_id":55');
    expect(postCall![1].body).toContain('"nombre":"pérdida de conciencia"');
    expect(postCall![1].body).toContain('"severidad":"intensa"');

    // El historial se recargó y muestra el nuevo triaje.
    expect(await screen.findByText("Clasificación inicial")).toBeTruthy();
  });

  it("exige al menos un síntoma (CA-07.3)", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse([CITA]))
      .mockResolvedValueOnce(apiResponse([]))
      .mockResolvedValueOnce(apiResponse([]))
      .mockResolvedValueOnce(apiResponse([]));

    render(<TriajePage />);

    const selectCita = await screen.findByLabelText("Cita para el triaje");
    fireEvent.change(selectCita, { target: { value: "55" } });

    fireEvent.click(screen.getByRole("button", { name: "Obtener clasificación inicial" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("al menos un síntoma");
    expect(fetchMock.mock.calls.some((call) => call[1] && call[1].method === "POST")).toBe(false);
  });
});