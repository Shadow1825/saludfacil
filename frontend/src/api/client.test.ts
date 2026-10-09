import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getToken, request, setToken } from "./client";

function respuesta(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

describe("cliente HTTP (api/client)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setToken(null);
  });

  it("lanza ApiError con el detalle en respuestas 401 y limpia el token (regresion pantalla en blanco)", async () => {
    setToken("token-antiguo");
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(respuesta(401, { detail: "Correo electronico o contrasena incorrectos." }))),
    );

    let error: unknown;
    try {
      await request("/auth/login", { method: "POST", body: {} });
    } catch (e) {
      error = e;
    }

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(401);
    expect((error as ApiError).message).toBe("Correo electronico o contrasena incorrectos.");
    expect(getToken()).toBeNull();
  });

  it("devuelve el cuerpo JSON en respuestas correctas", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(respuesta(200, { status: "ok" }))));
    await expect(request("/health")).resolves.toEqual({ status: "ok" });
  });
});
