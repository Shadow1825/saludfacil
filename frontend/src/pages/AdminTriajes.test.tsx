import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminTriajesPage } from "./AdminTriajes";

function apiResponse(body: unknown, status = 200): { ok: boolean; status: number; json: () => Promise<unknown> } {
  return { ok: status < 400, status, json: () => Promise.resolve(body) };
}

function triaje(id: number, estado_revision: string): Record<string, unknown> {
  return {
    id,
    cita_id: 10,
    paciente_id: 9,
    fecha: "2026-10-05",
    hora_inicio: "08:00",
    paciente: "Luis Quispe",
    profesional: "María López",
    specialty_name: "Medicina General",
    dia: "Lunes",
    clasificacion: "baja",
    resultado: "Baja",
    sintomas: [{ nombre: "tos", severidad: "leve" }],
    es_diagnostico: false,
    mensaje: "Clasificación inicial orientativa.",
    estado_revision,
    estado_revision_label:
      estado_revision === "pendiente"
        ? "Pendiente de revisión"
        : estado_revision === "revisado"
          ? "Revisado"
          : "Descartado",
    revisado_en: null,
    created_at: "2026-09-24T18:00:00",
  };
}

describe("AdminTriajesPage (FASE 6, HU-13 / RF-17)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("lista triajes con su estado de revisión (CA-13.1/CA-13.2)", async () => {
    fetchMock.mockResolvedValueOnce(apiResponse([triaje(1, "pendiente"), triaje(2, "revisado")]));

    render(<AdminTriajesPage />);

    expect(await screen.findByText("Pendiente de revisión")).toBeTruthy();
    expect(screen.getAllByText("Revisado").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Descartar" })).toBeTruthy();
  });

  it("marca un triaje como revisado (PATCH /revision)", async () => {
    fetchMock
      .mockResolvedValueOnce(apiResponse([triaje(1, "pendiente")])) // carga inicial
      .mockResolvedValueOnce(apiResponse(triaje(1, "revisado"))) // PATCH
      .mockResolvedValueOnce(apiResponse([triaje(1, "revisado")])); // recarga

    render(<AdminTriajesPage />);

    const boton = await screen.findByRole("button", { name: "Revisado" });
    fireEvent.click(boton);

    expect(await screen.findByText("Triaje marcado como \"revisado\" (RF-17).")).toBeTruthy();

    const patchCall = fetchMock.mock.calls.find((call) => call[1] && call[1].method === "PATCH");
    expect(patchCall).toBeDefined();
    expect(patchCall![0]).toContain("/api/triage/1/revision");
    expect(patchCall![1].body).toContain('"estado":"revisado"');
  });

  it("usa encabezados de tabla semánticos con scope de columna (RNF-07)", async () => {
    fetchMock.mockResolvedValueOnce(apiResponse([triaje(1, "pendiente")]));

    render(<AdminTriajesPage />);

    await screen.findByText("Pendiente de revisión");
    const headers = screen.getAllByRole("columnheader");
    expect(headers.length).toBeGreaterThan(0);
    for (const th of headers) {
      expect(th).toHaveAttribute("scope", "col");
    }
  });

  it("los triajes ya revisados no ofrecen botones de acción", async () => {
    fetchMock.mockResolvedValueOnce(apiResponse([triaje(1, "revisado"), triaje(2, "descartado")]));

    render(<AdminTriajesPage />);

    expect(await screen.findByText("Revisado")).toBeTruthy();
    expect(screen.getByText("Descartado")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Revisado" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Descartar" })).toBeNull();
  });
});