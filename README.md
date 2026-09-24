# SaludFácil

**Sistema de Gestión de Citas Médicas y Triaje**

Caso de estudio: *Clínica Comunitaria del Norte S.A.C.*

Proyecto del curso **Calidad y Pruebas de Software (ISOF1401A)** — Ingeniería de Sistemas
Computacionales, ciclo 2026-2.

> El documento de requisitos (con los identificadores RF, RNF, RES, HU, CA y CP) es la
> **fuente de verdad** del sistema. Esta implementación mantiene trazabilidad estricta
> entre requisitos, historias de usuario, criterios de aceptación, código y pruebas.

## Propósito

Organizar digitalmente los procesos de gestión de citas y triaje inicial de la clínica,
con tres roles de acceso (paciente, profesional de salud y administrador), controles de
seguridad por rol y una arquitectura preparada para pruebas de calidad.

> **Importante:** el triaje constituye únicamente una *clasificación inicial orientativa*
> basada en reglas definidas para el proyecto. **No es un diagnóstico médico.**

## Arquitectura

```text
Frontend (React + TypeScript + Vite)
      |
      | HTTP/REST (JSON)
      v
Backend (FastAPI + SQLAlchemy)
      |
      v
PostgreSQL
```

Separación por capas: presentación, API, lógica de negocio, persistencia, modelos,
esquemas y autenticación/autorización.

## Tecnologías

| Capa        | Tecnología                                             |
|-------------|--------------------------------------------------------|
| Frontend    | React, TypeScript, Vite, CSS responsive                |
| Backend     | Python, FastAPI, Pydantic, SQLAlchemy, JWT, RBAC       |
| Base de datos | PostgreSQL                                            |
| Infra       | Docker, Docker Compose, `.env`, Git, GitHub            |
| Pruebas     | Pytest, Playwright, K6, axe, Lighthouse, SonarQube     |
| CI/CD       | GitHub Actions                                         |

## Estado del proyecto

Por fases, conforme al plan del documento de especificación:

- **FASE 1 — ✅ Estructura y base ejecutable** (frontend, backend, PostgreSQL, Docker,
  variables de entorno, configuración base).
- **FASE 2 — ✅ Usuarios, roles, registro, login, JWT, RBAC, logout** (RF-01, RF-02,
  RF-18, RF-19, RF-20; RNF-01, RNF-02, RNF-05).
- **FASE 3 — ✅ Catálogo médico** (especialidades, profesionales, horarios) y consulta
  de disponibilidad del paciente (RF-04 a RF-08, HU-03/HU-11, CA-03.x y CA-11.x).
- **FASE 4 — ✅ Gestión de citas** reserva, consulta, cancelación y administración
  (RF-09 a RF-11, RF-21; RNF-09; HU-04/HU-05/HU-06 y CA-04 a CA-06, CA-11.4).
- **FASE 5 — ✅ Triaje inicial** registro de síntomas, clasificación inicial determinista
  (reglas oficiales R1-R6: Alta/Media/Baja) y consulta por paciente y profesional
  (RF-12 a RF-16; HU-07/HU-08/HU-09/HU-10 y CA-07 a CA-10).
- FASE 3 — Profesionales, especialidades, horarios, disponibilidad.
- FASE 4 — Citas, reserva, concurrencia, consulta, cancelación.
- FASE 5 — Síntomas, triaje, clasificación, resultado, consulta profesional.
- FASE 6 — Estados de atención y administración.
- FASE 7 — Accesibilidad, manejo de errores, seguridad, responsive, logs seguros.
- FASE 8 — Pytest, Playwright, K6, axe, Lighthouse, SonarQube.
- FASE 9 — Docker definitivo, GitHub Actions, CI/CD, reportes.

## Requisitos previos

- Docker Desktop (para ejecución por contenedores).
- Alternativa local: Python 3.12+ y Node.js 20+.

## Configuración

1. Copiar el archivo de ejemplo a `.env`:

   ```bash
   cp .env.example .env
   ```

2. Ajustar credenciales de PostgreSQL y el secreto JWT (nunca subir `.env` real).

## Ejecución con Docker Compose

```bash
docker compose up --build
```

Servicios:

| Servicio  | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:3000        |
| Backend   | http://localhost:8000/docs   |
| PostgreSQL| localhost:5432               |

## Ejecución local (desarrollo)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
# Ajustar DATABASE_URL en .env para apuntar a un PostgreSQL local
uvicorn app.main:app --reload --port 8000
```

Docs interactivas: http://localhost:8000/docs (OpenAPI/Swagger).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

URL: http://localhost:5173 (el proxy de Vite envía `/api/*` al backend).

## Variables de entorno

Ver `.env.example` (documentadas en su interior). Resumen:

- `DATABASE_URL` — conexión del backend a PostgreSQL.
- `SECRET_KEY` — secreto de firma de tokens (usado desde FASE 2).
- `ACCESS_TOKEN_EXPIRE_MINUTES` — 30 para cumplir RNF-01.
- `CORS_ORIGINS` — orígenes permitidos para el frontend.
- `VITE_API_URL` — URL de la API visible por el frontend.

## Usuarios de prueba (datos ficticios, RES-04)

Generados con `python -m app.seed` (dentro del contenedor: `docker compose exec backend python -m app.seed`):

| Rol          | Correo                    | Contraseña           |
|--------------|---------------------------|----------------------|
| Administrador| `admin@saludfacil.com`    | `AdminSaludFacil!1`  |
| Paciente     | `paciente@saludfacil.com` | `PacientePrueba!1`   |
| Profesional  | `profesional@saludfacil.com` | `Profesional!1`    |

Los DNI, teléfonos y demás datos son ficticios (Ley N.° 29733). El seed también crea
6 especialidades, 3 profesionales de salud y sus horarios de atención (FASE 3).

## Ejecución de pruebas

- Backend (pytest): `cd backend && pytest`
- Frontend (vitest): `cd frontend && npm test`
- E2E (Playwright), K6, axe/Lighthouse y SonarQube: **Pendiente de configuración**
  (FASE 8). No se declaran resultados que aún no existen.

## CI/CD

- GitHub Actions: **pendiente de implementación completa** (FASE 9) conforme a la
  especificación (instalación, lint, unitarias, integración, build, análisis y E2E).

## Documentación

- `docs/arquitectura.md` — decisiones de arquitectura.
- `docs/requisitos.md` — registro de requisitos y trazabilidad (en elaboración por fase).

---
*Este proyecto usa exclusivamente datos ficticios o anonimizados para pruebas,
conforme a la Ley N.° 29733. El historial de Git conserva los commits del equipo (RES-01).*