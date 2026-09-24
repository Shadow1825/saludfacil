# Arquitectura de SaludFácil

## Modelo de despliegue

```text
Frontend React (Vite)            nginx (producción) / Vite dev server
      |
      | HTTP/REST — JSON (rutas /api/*)
      v
Backend FastAPI                  uvicorn :8000
      |
      | SQLAlchemy (psycopg)
      v
PostgreSQL 16
```

## Capas del backend

| Capa            | Ubicación                  | Responsabilidad                                  |
|-----------------|----------------------------|--------------------------------------------------|
| Presentación    | `backend/app/main.py`      | Configuración de la app, CORS, middleware        |
| API (rutas)     | `backend/app/api/routes/`  | Endpoints REST por dominio                       |
| Lógica de negocio | `backend/app/services/`  | Reglas del dominio (cancelación, triaje, RBAC)   |
| Persistencia    | `backend/app/db/`          | Sesión y motor SQLAlchemy                        |
| Modelos         | `backend/app/models/`      | Entidades relacionales                           |
| Esquemas        | `backend/app/schemas/`     | Contratos Pydantic de entrada/salida             |
| Autenticación   | `backend/app/core/`        | Configuración, logging, seguridad (JWT desde FASE 2) |

> Las carpetas `models/`, `schemas/` y `services/` se incorporan en las fases 2–6
> junto con sus entidades (usuarios, roles, pacientes, profesionales, especialidades,
> horarios, citas, triajes).

## decisiones

- **Conectividad desacoplada**: el arranque del backend no depende de PostgreSQL; el
  estado real de la base de datos se reporta en `GET /api/health`. Esto permite que las
  pruebas base (FASE 1) se ejecuten sin infraestructura.
- **Configuración por variables de entorno** (`pydantic-settings`), nunca credenciales en
  el código.
- **CORS restringido** mediante `CORS_ORIGINS`.
- **Proxy en desarrollo**: Vite envía `/api/*` al backend en `localhost:8000`.
  En producción, `nginx` en el contenedor del frontend hace el mismo enrutado.
- **Logs seguros** (RNF-06/RNF-11): el módulo de logging no registra datos personales.

## Trazabilidad con el documento

La arquitectura responde a la sección 4 del documento de requisitos (arquitectura
cliente-servidor con separación de presentación, API y persistencia, RNF-08).