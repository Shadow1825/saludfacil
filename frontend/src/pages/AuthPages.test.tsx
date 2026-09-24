import { fireEvent, render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthContext";
import { LoginPage, RegisterPage } from "./AuthPages";

function renderPage(element: JSX.Element): void {
  render(
    <AuthProvider>
      <BrowserRouter>{element}</BrowserRouter>
    </AuthProvider>,
  );
}

describe("AuthPages (FASE 2)", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("Login muestra los campos de correo y contraseña", () => {
    renderPage(<LoginPage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Iniciar sesión");
    expect(screen.getByLabelText("Correo electrónico")).toBeInTheDocument();
    expect(screen.getByLabelText("Contraseña")).toBeInTheDocument();
  });

  it("Registro valida el DNI de 8 dígitos y muestra error comprensible", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })));
    renderPage(<RegisterPage />);

    fireEvent.change(screen.getByLabelText("Nombres"), { target: { value: "A" } });
    fireEvent.change(screen.getByLabelText("Apellidos"), { target: { value: "B" } });
    fireEvent.change(screen.getByLabelText("DNI (8 dígitos)"), { target: { value: "123" } });
    fireEvent.change(screen.getByLabelText("Correo electrónico"), { target: { value: "a@b.com" } });
    fireEvent.change(screen.getByLabelText("Teléfono"), { target: { value: "987654321" } });
    fireEvent.change(screen.getByLabelText("Contraseña (mínimo 8 caracteres)"), {
      target: { value: "12345678" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Registrarse" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "El DNI debe contener exactamente 8 dígitos.",
    );
  });
});