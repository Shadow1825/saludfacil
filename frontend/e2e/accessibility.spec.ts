import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

import { registrarPacienteApi, login } from "./helpers";

const RX_CRITICAS = (impact: string) => impact === "serious" || impact === "critical";

test.describe("Auditoría de accesibilidad con axe (RNF-07, WCAG 2.2 AA)", () => {
  const resumen: Array<Record<string, unknown>> = [];

  async function escanear(page: import("@playwright/test").Page, url: string, etiqueta: string): Promise<void> {
    await page.goto(url);
    const resultados = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    const criticas = resultados.violations.filter((v) => v.nodes.some((n) => RX_CRITICAS(n.impact ?? "")));
    resumen.push({
      url,
      violaciones: resultados.violations.length,
      ids: resultados.violations.map((v) => v.id),
      criticas_o_serias: criticas.length,
      detalle: criticas.map((v) => ({
        id: v.id,
        impact: v.impact,
        targets: v.nodes.map((n) => n.target),
      })),
    });
    const detalle = criticas
      .map((v) => `${v.id} [${v.nodes.map((n) => `${n.target} (${n.impact})`).join("; ")}]`)
      .join(" | ");
    expect.soft(criticas.length, `${etiqueta}: violaciones serias/críticas (${detalle})`).toBe(0);
  }

  test("páginas públicas sin violaciones serias/críticas de axe", async ({ page }) => {
    await escanear(page, "/inicio", "inicio");
    await escanear(page, "/login", "login");
    await escanear(page, "/registro", "registro");
  });

  test("páginas autenticadas del paciente sin violaciones serias/críticas de axe", async ({ page, request }) => {
    const paciente = await registrarPacienteApi(request);
    const token = await login(request, paciente.email, paciente.password);
    await page.goto("/login");
    await page.evaluate(
      ([t]) => window.localStorage.setItem("sf_token", t),
      [token] as unknown as string[],
    );
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Inicio" })).toBeVisible();

    await escanear(page, "/", "home autenticado");
    await escanear(page, "/disponibilidad", "disponibilidad");
    await escanear(page, "/reservar", "reservar");
    await escanear(page, "/triaje", "triaje");
    await escanear(page, "/perfil", "perfil");
  });

  test.afterAll(async () => {
    const dir = join(process.cwd(), "..", "docs", "fase8");
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "axe-scan.json"), JSON.stringify(resumen, null, 2), "utf8");
  });
});