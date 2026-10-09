import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MisCitasPage } from "./MisCitas";

type JsonHandler = () => Promise<unknown>;

function apiResponse(body: unknown, status = 200): { ok: boolean; status: number; json: JsonHandler } {
  return { ok: status < 400, status, json: () => Promise.resolve(body) };
}

const CITAS = [
  {
    id: 41,
    paciente_id: 9,
    professional_id: 1,
    specialty_id: 1,
    fecha: "2026-10-06",
    hora_inicio: "09:00",
    hora_fin: "09:30",
    estado: "reservada",
    is_active: true,
    paciente: "Luis Quispe",
    profesional: "María López",
    profesional_email: "maria@prof.com",
    specialty_name: "Medicina General",
    dia: "Martes",
  },
];

describe("MisCitasPage (HU-06 / CA-06.2)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("solicita confirmación antes de cancelar (CA-06.2)", async () => {
    fetchMock.mockResolvedValueOnce(apiResponse(CITAS));

    render(<MisCitasPage />);

    const botonCancelar = await screen.findByRole("button", { name: "Cancelar" });
    fireEvent.click(botonCancelar);

    const dialogo = await screen.findByRole("dialog", { name: /Cancelar cita/i });
    expect(dialogo).toBeInTheDocument();
    expect(dialogo).toHaveTextContent("¿Desea cancelar la cita del 2026-10-06");

    const llamadasCancelacion = fetchMock.mock.calls.filter(
      (call) =>
        (call[1] as { method?: string } | undefined)?.method === "POST" &&
        String(call[0]).includes("/cancel"),
    );
    expect(llamadasCancelacion.length).toBe(0);
  });

  it("cancela solo después de confirmar en el diálogo (CA-06.2/CA-06.3)", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse(CITAS))
      .mockResolvedValue(apiResponse({ message: "Cita cancelada correctamente." }));

    render(<MisCitasPage />);

    const botonCancelar = await screen.findByRole("button", { name: "Cancelar" });
    fireEvent.click(botonCancelar);

    const cancelarDefinitivo = await screen.findByRole("button", { name: "Confirmar cancelación" });
    fireEvent.click(cancelarDefinitivo);

    const patchCall = fetchMock.mock.calls.find(
      (call) =>
        (call[1] as { method?: string } | undefined)?.method === "POST" &&
        String(call[0]).includes("/cancel"),
    );
    expect(patchCall).toBeDefined();
    expect(String(patchCall![0])).toContain("/api/appointments/41/cancel");
  });

  it("mantiene la cita si se elige cancelar el diálogo", async () => {
    fetchMock.mockResolvedValueOnce(apiResponse(CITAS));

    render(<MisCitasPage />);

    const botonCancelar = await screen.findByRole("button", { name: "Cancelar" });
    fireEvent.click(botonCancelar);

    const mantener = await screen.findByRole("button", { name: "Mantener cita" });
    fireEvent.click(mantener);

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    const llamadasCancelacion = fetchMock.mock.calls.filter(
      (call) =>
        (call[1] as { method?: string } | undefined)?.method === "POST" &&
        String(call[0]).includes("/cancel"),
    );
    expect(llamadasCancelacion.length).toBe(0);
  });
});