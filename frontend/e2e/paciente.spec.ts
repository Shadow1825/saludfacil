import { expect, test } from "@playwright/test";

import { proximaFechaParaPro, siguienteCorreo } from "./helpers";

test.describe("Flujo crítico del paciente (RF-01/07/09/10/12/13/03)", () => {
  test("registro → disponibilidad → reserva → mis citas → triaje → mi perfil", async ({ page, request }) => {
    const { email, dni, password } = siguienteCorreo();
    const pass = "E2eClaveSegura!1";

    // RF-01 / HU-01: registro por formulario (CA-01.1, CA-01.4)
    await page.goto("/registro");
    await page.getByLabel("Nombres").fill("E2E");
    await page.getByLabel("Apellidos").fill("Paciente");
    await page.getByLabel("DNI (8 dígitos)").fill(dni);
    await page.getByLabel("Correo electrónico").fill(email);
    await page.getByLabel("Teléfono").fill("999654321");
    await page.getByLabel("Contraseña (mínimo 8 caracteres)").fill(pass);
    await page.getByRole("button", { name: "Registrarse" }).click();
    await expect(page.getByRole("heading", { name: "Inicio" })).toBeVisible();

    // RF-07 / HU-03: disponibilidad (CA-03.1 a CA-03.3)
    await page.goto("/disponibilidad");
    await expect(page.getByRole("heading", { name: /disponibilidad/i })).toBeVisible();
    const especialidades = page.getByRole("combobox").first().locator("option");
    await expect(especialidades.filter({ hasText: "Medicina General" })).toHaveCount(1);
    expect(await especialidades.count()).toBeGreaterThan(1);

    // Login real (CA-02.x) para preparar datos y resolver un slot disponible
    const loginRes = await request.post("http://localhost:8000/api/auth/login", {
      data: { email, password: pass },
    });
    expect(loginRes.ok()).toBe(true);
    const accessToken = ((await loginRes.json()) as { access_token: string }).access_token;
    const Maria = 1; // profesional seed "María López" (Medicina General)
    const fecha = await proximaFechaParaPro(
      request,
      accessToken,
      Maria,
      2 + Math.round(Math.random() * 38),
    );

    await page.goto("/reservar");
    await page.getByLabel("Especialidad").selectOption({ label: "Medicina General" });
    await page.getByLabel("Profesional").selectOption(String(Maria));
    await page.getByLabel("Fecha de la cita").fill(fecha);
    await expect(page.getByRole("heading", { name: "Horarios disponibles" })).toBeVisible();
    await page.getByRole("button", { name: "Reservar" }).first().click();
      await page.getByRole("button", { name: "Confirmar reserva" }).click();
    await expect(page.getByRole("status")).toContainText("Cita reservada");

    // RF-10 / HU-05: consulta de citas (CA-05.x)
    await page.goto("/mis-citas");
    await expect(page.getByRole("row").filter({ hasText: fecha })).toContainText(/reservada/i);

    // RF-12/13 / HU-07/08: triaje (CA-07.x, CA-08.x)
    await page.goto("/triaje");
    await page.getByLabel("Cita para el triaje").selectOption({ index: 1 });
    await page.getByLabel("Síntoma adicional").fill("tos");
    await page.getByRole("button", { name: "Obtener clasificación inicial" }).click();
    await expect(page.getByRole("heading", { name: /Resultado:/ })).toBeVisible();
    await expect(page.getByRole("status").last()).toContainText(/Alta|Media|Baja/);

    // RF-03 / HU-15: actualización del perfil
    await page.goto("/perfil");
    await page.getByLabel("Teléfono").fill("999888777");
    await page.getByRole("button", { name: /Guardar/ }).click();
    await expect(page.getByRole("status").filter({ hasText: /actualizaron correctamente/ })).toBeVisible();
  });
});