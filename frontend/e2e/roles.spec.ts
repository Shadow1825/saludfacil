import { expect, test } from "@playwright/test";

import { ADMIN, PROFESIONAL, crearCitaConTriajeApi, ingresarPorUi } from "./helpers";

test.describe("Rol profesional", () => {
  test("consulta el triaje de la cita asignada (RF-16)", async ({ page, request }) => {
    const setup = await crearCitaConTriajeApi(request);

    await ingresarPorUi(page, PROFESIONAL.email, PROFESIONAL.password);
    await page.goto("/profesional/triajes");
    const fila = page.getByRole("row").filter({ hasText: `${setup.slot.fecha} ${setup.slot.hora}` });
    await expect(fila).toContainText("tos");
    await expect(fila).toContainText("Pendiente de revisión");
  });

  test("consulta sus citas asignadas (HU-08 / RF-14)", async ({ page, request }) => {
    const setup = await crearCitaConTriajeApi(request);

    await ingresarPorUi(page, PROFESIONAL.email, PROFESIONAL.password);
    await page.goto("/profesional/citas");
    const fila = page
      .getByRole("row")
      .filter({ hasText: setup.slot.fecha })
      .filter({ hasText: setup.slot.hora })
      .first();
    await expect(fila).toContainText("Reservada");
  });
});

test.describe("Rol administrador (RF-17 / FASE 6)", () => {
  test("marca como revisado un triaje pendiente", async ({ page, request }) => {
    const setup = await crearCitaConTriajeApi(request);

    await ingresarPorUi(page, ADMIN.email, ADMIN.password);
    await page.goto("/admin/triajes");
    const fila = page.getByRole("row").filter({ hasText: `${setup.slot.fecha} ${setup.slot.hora}` });
    await expect(fila).toContainText("Pendiente de revisión");
    await fila.getByRole("button", { name: "Revisado" }).click();
    await expect(page.locator("p.notice")).toContainText(/revisado/i);
    await expect(
      page.getByRole("row").filter({ hasText: `${setup.slot.fecha} ${setup.slot.hora}` }),
    ).toContainText("Revisado");
  });
});