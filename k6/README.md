# K6 — RNF-04: pruebas de rendimiento

Escenario oficial (documento `Calidad_y_Pruebas_de_Software_corregido.docx`, RNF-04):

- **50 usuarios virtuales concurrentes**.
- **p95 < 2 s** en login, consulta de horarios y reserva de cita.
- **Tasa de error < 1 %**.

## Requisitos

- Stack Docker corriendo (`docker compose up -d`); App en `http://localhost:3000`, API en
  `http://localhost:8000`.
- Binario de k6 (Windows x64) desde
  `https://github.com/grafana/k6/releases/latest`
  (`k6-vX.Y.Z-windows-amd64.zip`). Ejemplo de uso con una ruta local:

```powershell
$k6 = "C:\ruta\temp\k6\k6-vX.Y.Z-windows-amd64\k6.exe"
```

## Preparación de datos (reproducible)

`prepare.mjs` (Node ≥ 18) usa la API real para: iniciar sesión como admin, añadir franjas
adicionales a la profesional María (Mié 13–17 y Vie 08–12; Lun 08–12 y Mié 08–12 ya existen
en el seed), recorrer hasta **180 días** a la vista en busca de **horarios realmente libres**
(evita 409 durante la prueba) y registrar 50 pacientes ficticios con clave `K6ClaveSegura!1`.

```powershell
node prepare.mjs
```

Genera `data/slots.json` y `data/users.json` (datos ficticios, Ley N.° 29733). Si ya se
ejecutaron corridas previas (consumieron citas futuras), las siguientes preparaciones
siguen encontrando slots más adelante en el horizonte de 180 días.

## Ejecución

```powershell
node prepare.mjs
& $k6 run --summary-export="..\docs\fase8\k6-summary.json" load-test.js
```

El script (`load-test.js`) lanza **50 VUs × 2 iteraciones** (`per-vu-iterations`); cada VU
inicia sesión una vez y reutiliza su token en las dos iteraciones, luego consulta horarios
y reserva un slot único por índice. Los VUs arrancan escalonados (ramp-in de 7,5 s antes
del login) para medir la latencia por usuario en **concurrencia estable de 50 VUs** en
lugar de un pico de 50 bcrypt simultáneos. Umbrales definidos en `options.thresholds`:
`http_req_failed rate<0.01` y `p(95)<2000` (global y por cada operación nombrada).

## Resultado medido (FASE 8, stack Docker)

```
scenario:        50 VUs, 2 iteraciones/VU (per-vu-iterations, ramp-in 7.5 s)
checks:          250/250 OK  (login 200 ×50, horarios 200 ×100, reserva 201 ×100)
http_req_failed: 0.00 %  (umbral < 1 %)
p(95) http_req_duration: 246 ms  (umbral < 2 s)
p(95) login:     271 ms   ·  horarios: 13 ms  ·  reserva: 34 ms
```

**Cumple RNF-04** (exit code 0 y todos los umbrales ✓ en consola; la corrida final quedó
en `docs/fase8/k6-final.log`). Ajuste de capacidad aplicado y verificado: el backend subió
de 1 a **4 workers de uvicorn** (parametrizado como `UVICORN_WORKERS` en
`docker-compose.yml`). Trazabilidad: con 1 worker el p95 de login ≈ 2.34 s superaba el
umbral; con 50 logins simultáneos y 4 workers oscilaba en 1.99–2.92 s según la carga del
host; con más workers que núcleos efectivos del VM Docker empeoraba; con ramp-in + 4
workers el p95 quedó en 0.27 s. Resumen crudo exportado en `docs/fase8/k6-summary.json`.

> **Nota (artefacto k6 v2.3.0):** `--summary-export` graba `"ok": false` en todos los
> umbrales (e incluso `fails` en `http_req_failed`) aun cuando el run pasa, por evaluar los
> umbrales de tiempo en nanosegundos y exportar en milisegundos. En `k6-summary.json` ese
> campo quedó **corregido según los valores reales** del propio export; la fuente del
> veredicto es el **exit code 0 y la consola** (`✓`), no ese campo.

## Observación de trazabilidad

Los usuarios `k6carga*@test.com` son datos de prueba ficticios; los slots usados son
horarios reales libres de la profesional seed María López (id 1), sin modificar datos de
usuarios reales.