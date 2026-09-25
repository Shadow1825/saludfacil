import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MisTriajesPage } from "./MisTriajes";

describe("MisTriajesPage (FASE 5, RU-08 / RF-14)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("muestra solo los triajes de las citas del profesional", async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            id: 1,
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
            estado_revision: "pendiente",
            estado_revision_label: "Pendiente de revisión",
            revisado_en: null,
            created_at: "2026-09-24T18:00:00",
          },
          {
            id: 2,
            cita_id: 11,
            paciente_id: 8,
            fecha: "2026-10-05",
            hora_inicio: "09:00",
            paciente: "Ana Pérez",
            profesional: "María López",
            specialty_name: "Medicina General",
            dia: "Lunes",
            clasificacion: "alta",
            resultado: "Alta",
            sintomas: [{ nombre: "dificultad respiratoria", severidad: "intensa" }],
            es_diagnostico: false,
            mensaje: "Clasificación inicial orientativa.",
            estado_revision: "revisado",
            estado_revision_label: "Revisado",
            revisado_en: null,
            created_at: "2026-09-24T18:05:00",
          },
        ]),
    });

    render(<MisTriajesPage />);

    expect(await screen.findByText("Luis Quispe")).toBeTruthy();
    expect(screen.getByText("Ana Pérez")).toBeTruthy();
    expect(screen.getByText("Baja")).toBeTruthy();
    expect(screen.getByText("Alta")).toBeTruthy();
    expect(screen.getByText("Revisado")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/triage"),
      expect.objectContaining({ method: "GET" }),
    );
  });
});