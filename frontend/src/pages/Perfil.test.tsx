import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthContext";
import { PerfilPage } from "./Perfil";

function apiResponse(body: unknown, status = 200): { ok: boolean; status: number; json: () => Promise<unknown> } {
  return { ok: status < 400, status, json: () => Promise.resolve(body) };
}

function renderPage(): void {
  render(
    <AuthProvider>
      <PerfilPage />
    </AuthProvider>,
  );
}

const USUARIO_ACTUALIZADO = {
  id: 9,
  email: "paciente@test.com",
  role: "paciente",
  first_name: "Ana",
  last_name: "Gómez",
  dni: "20000001",
  phone: "987654321",
  is_active: true,
  created_at: "2026-09-24T12:00:00",
};

describe("PerfilPage (FASE 6, HU-15 / RF-03)", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("muestra DNI y correo como no editables", () => {
    renderPage();

    expect(fetchMock).not.toHaveBeenCalled(); // sin token, no hay llamadas de autenticación
    expect(screen.getByRole("heading", { name: /Mi perfil/ })).toBeTruthy();
  });

  it("actualiza datos y muestra confirmación (CA-15.1)", async () => {
    fetchMock.mockResolvedValueOnce(apiResponse(USUARIO_ACTUALIZADO));

    renderPage();

    fireEvent.change(screen.getByLabelText("Nombres"), { target: { value: "Ana" } });
    fireEvent.change(screen.getByLabelText("Apellidos"), { target: { value: "Gómez" } });
    fireEvent.change(screen.getByLabelText("Teléfono"), { target: { value: "987654321" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByText("Sus datos se actualizaron correctamente.")).toBeTruthy();

    const patchCall = fetchMock.mock.calls.find((call) => call[1] && call[1].method === "PATCH");
    expect(patchCall).toBeDefined();
    expect(patchCall![0]).toContain("/api/profile");
    expect(patchCall![1].body).toContain('"phone":"987654321"');
  });

  it("valida teléfono antes de enviar (CA-15.2)", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText("Teléfono"), { target: { value: "123" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "El teléfono debe contener al menos 7 dígitos.",
    );
    expect(fetchMock.mock.calls.some((call) => call[1] && call[1].method === "PATCH")).toBe(false);
  });

  it("exige contraseña actual y nueva juntas para cambiar la clave", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText("Nueva contraseña (mínimo 8 caracteres)"), {
      target: { value: "NuevaClave!1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Para cambiar la contraseña debe indicar la actual y la nueva.",
    );
    expect(fetchMock.mock.calls.some((call) => call[1] && call[1].method === "PATCH")).toBe(false);
  });
});