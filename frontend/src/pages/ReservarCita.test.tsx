import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReservarCitaPage } from "./ReservarCita";

type JsonHandler = () => Promise<unknown>;

function apiResponse(body: unknown, status = 200): { ok: boolean; status: number; json: JsonHandler } {
  return { ok: status < 400, status, json: () => Promise.resolve(body) };
}

const SPECIALTIES = [{ id: 1, nombre: "Medicina General", is_active: true }];

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

const SLOTS = [
  { fecha: "2026-10-05", hora_inicio: "08:00", hora_fin: "08:30" },
  { fecha: "2026-10-05", hora_inicio: "08:30", hora_fin: "09:00" },
];

const CITA_CREADA = {
  id: 1,
  paciente_id: 9,
  professional_id: 10,
  specialty_id: 1,
  fecha: "2026-10-05",
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

describe("ReservarCitaPage (FASE 4, HU-04 / RF-09)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("reserva una cita a partir de especialidad, profesional y fecha (CA-04.x)", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse(SPECIALTIES))
      .mockResolvedValueOnce(apiResponse(PROFESSIONALS))
      .mockResolvedValueOnce(apiResponse(SLOTS))
      .mockResolvedValueOnce(apiResponse(CITA_CREADA, 201));

    render(<ReservarCitaPage />);

    const especialidad = await screen.findByLabelText("Especialidad");
    fireEvent.change(especialidad, { target: { value: "1" } });

    const profesional = await screen.findByLabelText("Profesional");
    fireEvent.change(profesional, { target: { value: "10" } });

    const fecha = await screen.findByLabelText("Fecha de la cita");
    fireEvent.change(fecha, { target: { value: "2026-10-05" } });

    const boton = (await screen.findAllByRole("button", { name: "Reservar" }))[0];
    fireEvent.click(boton);

    expect(await screen.findByRole("status")).toHaveTextContent("Cita reservada:");
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/appointments"),
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining('"hora_inicio":"08:00"'),
      }),
    );
  });

  it("reporta un horario ya reservado (409) de forma comprensible", async () => {
    const errorDetail = { detail: "Ese horario ya fue reservado por otro paciente (RNF-09)." };
    fetchMock
      .mockResolvedValueOnce(apiResponse(SPECIALTIES))
      .mockResolvedValueOnce(apiResponse(PROFESSIONALS))
      .mockResolvedValueOnce(apiResponse(SLOTS))
      .mockResolvedValueOnce(apiResponse(errorDetail, 409));

    render(<ReservarCitaPage />);

    const especialidad = await screen.findByLabelText("Especialidad");
    fireEvent.change(especialidad, { target: { value: "1" } });

    const profesional = await screen.findByLabelText("Profesional");
    fireEvent.change(profesional, { target: { value: "10" } });

    const fecha = await screen.findByLabelText("Fecha de la cita");
    fireEvent.change(fecha, { target: { value: "2026-10-05" } });

    const boton = (await screen.findAllByRole("button", { name: "Reservar" }))[0];
    fireEvent.click(boton);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ese horario ya fue reservado por otro paciente",
    );
  });
});