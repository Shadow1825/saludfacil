# Registro de requisitos y trazabilidad

> Fuente de verdad: documento oficial del proyecto (sección 4: requisitos, historias de
> usuario, criterios de aceptación y matriz de trazabilidad).

## Estado por fase

| Fase | Requisitos cubiertos | Estado                |
|------|----------------------|-----------------------|
| 1    | Infraestructura      | ✅ Implementado       |
| 2    | RF-01, RF-02, RF-18, RF-19, RF-20; RNF-01, RNF-02, RNF-05 | ✅ Implementado y probado |
| 3    | RF-04, RF-05, RF-06, RF-07, RF-08 | ✅ Implementado y probado |
| 4    | RF-09, RF-10, RF-11, RF-21; RNF-09 | ✅ Implementado y probado |
| 5    | RF-12, RF-13, RF-14, RF-15, RF-16 | Pendiente |
| 6    | RF-03, RF-17 | Pendiente |
| 7    | RNF-06, RNF-07 | Pendiente |

## FASE 4 — trazabilidad verificada

| Requisito | HU  | Criterios        | CP  | Implementación                              | Estado |
|-----------|-----|------------------|-----|---------------------------------------------|--------|
| RF-09     | HU-04 | CA-04.1–04.4    | CP-09 | `api/routes/appointments.py: POST /appointments` (reserva y bloquea) | ✅ pruebas 201/409/422/403 |
| RF-10     | HU-05 | CA-05.1–05.3    | CP-10 | `GET /appointments` (solo las propias)       | ✅ pruebas 200 |
| RF-11     | HU-06 | CA-06.1–06.4    | CP-11 | `POST /appointments/{id}/cancel` (libera horario) | ✅ pruebas 200/403/409/201 |
| RF-21     | HU-11 | CA-11.4         | CP-21 | `GET/PATCH /appointments` admin (estado, cancelación) | ✅ pruebas 200/409 |
| RNF-09    | HU-04/HU-06 | CA-04.2, CA-06.3 | CP-NF-09 | fechas pasadas (422), horario ocupado (409), parcial único activo | ✅ |

Decisiones técnicas (documentadas, sin alterar requisitos):
- **Duración de cita = 30 minutos**; la disponibilidad fragmenta los horarios de
  atención (RF-06) en tramos de 30 min no reservados.
- **Bloqueo real del horario**: índice único parcial `(profesional, fecha, hora_inicio)`
  sobre citas activas; al cancelar, la cita pasa a inactiva y el tramo queda libre.
- **Cancelación**: solo el paciente dueño o el administrador; no se permite cancelar
  citas ya iniciadas o pasadas (CA-06.x / RNF-09).
- **Un paciente solo ve sus citas** (RF-10); el administrador ve el sistema completo (RF-21).

## FASE 3 — trazabilidad verificada

| Requisito | HU  | Criterios        | CP  | Implementación                          | Estado |
|-----------|-----|------------------|-----|-----------------------------------------|--------|
| RF-04     | HU-11 | CA-11.1         | CP-04 | `models/medical.py` + `api/routes/medical.py: /professionals` | ✅ pruebas 201/409/200 |
| RF-05     | HU-11 | CA-11.2         | CP-05 | `/specialties` (create/update/deactivate) | ✅ pruebas 201/409 |
| RF-06     | HU-11 | CA-11.3         | CP-06 | `/schedules` (día, inicio, fin, activo)   | ✅ pruebas 201/409/422 |
| RF-07     | HU-03 | CA-03.1, 03.2   | CP-07 | `/directory/specialties`, `/directory/professionals` | ✅ pruebas 200/401 |
| RF-08     | HU-03 | CA-03.3, 03.4   | CP-08 | `/directory/schedules` (solo disponibles) | ✅ pruebas 200/404 |
| RNF-02    | HU-12 | CA-12.4         | CP-NF-02 | endpoints admin protegidos con `require_roles(ADMINISTRADOR)` | ✅ verificado en Docker |

Decisiones técnicas (documentadas, sin alterar requisitos):
- **Un profesional pertenece a una especialidad** (`profesionales.specialty_id`); la
  disponibilidad se filtra por especialidad y profesional activos (RF-07/RF-08).
- **Disponibilidad en FASE 3**: un horario activo está disponible; las citas ya tomadas
  se descontarán en FASE 4 con el módulo de citas (mismo endpoint de disponibilidad).
- **Día del horario**: `1=Lunes … 7=Domingo` con nombres traducidos para la interfaz.
- **Horarios únicos** por (profesional, día, hora de inicio).

## FASE 2 — trazabilidad verificada

| Requisito | HU  | Criterios            | CP  | Implementación                          | Estado |
|-----------|-----|----------------------|-----|-----------------------------------------|--------|
| RF-01     | HU-01 | CA-01.1–01.4        | CP-01 | `api/routes/auth.py: register`          | ✅ pruebas 201/409/422 |
| RF-02     | HU-02 | CA-02.1–02.4        | CP-02 | `api/routes/auth.py: login`             | ✅ pruebas 200/401/403 |
| RF-18     | HU-11 | CA-11.5             | CP-18 | `api/routes/users.py` (admin)           | ✅ pruebas 201/200/409 |
| RF-19     | HU-12 | CA-12.1–12.4        | CP-19 | `services/security.py: require_roles`   | ✅ pruebas 401/403 |
| RF-20     | HU-14 | CA-14.1–14.3        | CP-20 | `api/routes/auth.py: logout` (token_version) | ✅ pruebas 200/401 |
| RNF-01    | HU-02 | CA-02.3             | CP-NF-01 | bcrypt + JWT expiración 30 min        | ✅ |
| RNF-02    | HU-12 | CA-12.4             | CP-NF-02 | 403 en API para rutas de admin         | ✅ verificado en Docker |
| RNF-05    | HU-01/HU-07 | CA-01.2, CA-07.2 | CP-NF-05 | Pydantic: DNI 8 dígitos, email, obligatorios | ✅ `^[0-9]{8}$` |

Decisiones técnicas (documentadas, sin alterar requisitos):
- **Sesión de 30 minutos**: se implementa como expiración del JWT (`ACCESS_TOKEN_EXPIRE_MINUTES=30`).
- **Cierre de sesión**: `token_version` por usuario; cada login expide un token con la versión
  vigente; al hacer logout se incrementa, invalidando los tokens anteriores (RF-20).
- **Hash**: bcrypt con sal (RNF-01).
- **Validaciones**: en la capa de esquemas Pydantic (RNF-05).

## Matriz funcional planificada (oficial)

| Requisito | HU  | Criterios            | CP  | Código | Estado |
|-----------|-----|----------------------|-----|--------|--------|
| RF-01     | HU-01 | CA-01.1–01.4        | CP-01 | | Pendiente |
| RF-02     | HU-02 | CA-02.1–02.4        | CP-02 | | Pendiente |
| RF-03     | HU-15 | CA-15.1–15.4        | CP-03 | | Pendiente |
| RF-04     | HU-11 | CA-11.1             | CP-04 | | Pendiente |
| RF-05     | HU-11 | CA-11.2             | CP-05 | | Pendiente |
| RF-06     | HU-11 | CA-11.3             | CP-06 | | Pendiente |
| RF-07     | HU-03 | CA-03.1, 03.2       | CP-07 | | Pendiente |
| RF-08     | HU-03 | CA-03.3, 03.4       | CP-08 | | Pendiente |
| RF-09     | HU-04 | CA-04.1–04.4        | CP-09 | | Pendiente |
| RF-10     | HU-05 | CA-05.1–05.3        | CP-10 | | Pendiente |
| RF-11     | HU-06 | CA-06.1–06.4        | CP-11 | | Pendiente |
| RF-12     | HU-07 | CA-07.1–07.3        | CP-12 | | Pendiente |
| RF-13     | HU-08 | CA-08.1–08.4        | CP-13 | | Pendiente |
| RF-14     | HU-08 | CA-08.2–08.4        | CP-14 | | Pendiente |
| RF-15     | HU-09 | CA-09.1, 09.2       | CP-15 | | Pendiente |
| RF-16     | HU-10 | CA-10.1, 10.2       | CP-16 | | Pendiente |
| RF-17     | HU-13 | CA-13.1–13.3        | CP-17 | | Pendiente |
| RF-18     | HU-11 | CA-11.5             | CP-18 | | Pendiente |
| RF-19     | HU-12 | CA-12.1–12.4        | CP-19 | | Pendiente |
| RF-20     | HU-14 | CA-14.1–14.3        | CP-20 | | Pendiente |
| RF-21     | HU-11 | CA-11.4             | CP-21 | | Pendiente |

La columna *Código* se completará cuando cada funcionalidad tenga implementación; la
columna *Estado* cambiará a "✅" mediante casos de prueba reales. No se registran
resultados que no existan (regla contra la invención).