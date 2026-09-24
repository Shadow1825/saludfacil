import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DisponibilidadPage } from "./Disponibilidad";

type JsonHandler = () => Promise<unknown>;

function apiResponse(body: unknown, status = 200): { ok: boolean; status: number; json: JsonHandler } {
  return { ok: status < 400, status, json: () => Promise.resolve(body) };
}

const SPECIALTIES = [
  { id: 1, nombre: "Medicina General", is_active: true },
  { id: 2, nombre: "Cardiología", is_active: true },
];

const PROFESSIONALS = [
  {
    id: 10,
    user_id: 3,
    specialty_id: 1,
    specialty_name: "Medicina General",
    first_name: "María",
    last_name: "López",
    email: "maria@prof.com",
    is_active: true,
  },
];

const SCHEDULES = [
  { id: 1, professional_id: 10, day: 1, day_name: "Lunes", start_time: "08:00", end_time: "12:00", is_active: true },
  { id: 2, professional_id: 10, day: 3, day_name: "Miércoles", start_time: "08:00", end_time: "12:00", is_active: true },
];

describe("DisponibilidadPage (FASE 3, HU-03 / RF-07 / RF-08)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("muestra horarios disponibles según la selección del usuario (CA-03.1 a CA-03.3)", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse(SPECIALTIES))
      .mockResolvedValueOnce(apiResponse(PROFESSIONALS))
      .mockResolvedValueOnce(apiResponse(SCHEDULES));

    render(<DisponibilidadPage />);

    const especialidad = await screen.findByLabelText("Especialidad");
    fireEvent.change(especialidad, { target: { value: "1" } });

    const profesional = await screen.findByLabelText("Profesional");
    fireEvent.change(profesional, { target: { value: "10" } });

    expect(await screen.findByText("Lunes")).toBeInTheDocument();
    expect(screen.getByText("Miércoles")).toBeInTheDocument();
    expect(screen.getAllByText("08:00")).toHaveLength(2);
    expect(screen.getAllByText("12:00")).toHaveLength(2);
  });

  it("informa cuando no existen horarios disponibles (CA-03.4)", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse(SPECIALTIES))
      .mockResolvedValueOnce(apiResponse(PROFESSIONALS))
      .mockResolvedValueOnce(apiResponse([]));

    render(<DisponibilidadPage />);

    const especialidad = await screen.findByLabelText("Especialidad");
    fireEvent.change(especialidad, { target: { value: "1" } });

    const profesional = await screen.findByLabelText("Profesional");
    fireEvent.change(profesional, { target: { value: "10" } });

    expect(
      await screen.findByText("No existen horarios disponibles para el profesional seleccionado."),
    ).toBeInTheDocument();
  });
});