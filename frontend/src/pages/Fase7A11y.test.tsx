import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../auth/AuthContext";
import { SkipLink } from "../components/SkipLink";
import { RegisterPage } from "./AuthPages";

const AQUI = dirname(fileURLToPath(import.meta.url));
const INDEX_CSS = readFileSync(join(AQUI, "..", "styles", "index.css"), "utf8");

function renderWithProviders(element: JSX.Element): void {
  render(
    <AuthProvider>
      <BrowserRouter>{element}</BrowserRouter>
    </AuthProvider>,
  );
}

describe("Accesibilidad y responsive (FASE 7, RNF-07)", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("SkipLink salta al contenido principal con href #main", () => {
    render(<SkipLink />);
    const link = screen.getByRole("link", { name: "Saltar al contenido principal" });
    expect(link).toHaveAttribute("href", "#main");
    expect(link.className).toContain("skip-link");
  });

  it("las páginas de autenticación exponen un main accesible y saltable", () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })));
    renderWithProviders(<RegisterPage />);

    const main = screen.getByRole("main");
    expect(main).toHaveAttribute("id", "main");
    expect(main).toHaveAttribute("tabindex", "-1");
    expect(screen.getByRole("link", { name: "Saltar al contenido principal" })).toHaveAttribute(
      "href",
      "#main",
    );
  });

  it("los formularios asocian cada etiqueta con su campo mediante htmlFor/id (RNF-07)", () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })));
    renderWithProviders(<RegisterPage />);

    for (const name of ["Nombres", "Apellidos", "DNI (8 dígitos)", "Correo electrónico", "Teléfono"]) {
      expect(screen.getByLabelText(name)).toHaveAttribute("id");
    }
    const labels = screen.getAllByLabelText(/Contraseña/);
    expect(labels.some((label) => label.hasAttribute("id"))).toBe(true);
  });

  it("la hoja de estilos define saltos de línea responsive y reduce movimiento (RNF-07)", () => {
    expect(INDEX_CSS).toContain(".skip-link");
    expect(INDEX_CSS).toContain("@media (max-width: 700px)");
    expect(INDEX_CSS).toContain("@media (max-width: 480px)");
    expect(INDEX_CSS).toContain("@media (prefers-reduced-motion: reduce)");
  });
});