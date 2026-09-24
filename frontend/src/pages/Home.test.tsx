import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { HomePage } from "./Home";

const okResponse = (overrides: Partial<{ status: string; service: string; database: string }> = {}) => ({
  ok: true,
  status: 200,
  json: () =>
    Promise.resolve({
      status: "ok",
      service: "saludfacil-api",
      database: "ok",
      ...overrides,
    }),
});

describe("HomePage", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("muestra el título del sistema", () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(okResponse())));
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("SaludFácil");
  });

  it("reporta el estado de la conexión cuando la API responde", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(okResponse())));
    render(<HomePage />);
    expect(await screen.findByText("Operativo")).toBeInTheDocument();
    expect(await screen.findByText("Conectada")).toBeInTheDocument();
  });

  it("muestra error comprensible cuando la API no responde", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })),
    );
    render(<HomePage />);
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});