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
| 5    | RF-12, RF-13, RF-14, RF-15, RF-16 | ✅ Implementado y probado |
| 6    | RF-03, RF-17 | ✅ Implementado y probado |
| 7    | RNF-06, RNF-07 | ✅ Implementado y probado |

## FASE 5 — trazabilidad verificada

Las reglas de clasificación de esta fase son la **especificación oficial del motor de
triaje** (académica; NO constituyen un protocolo médico ni un diagnóstico).

| Regla | Condición                                                                    | Resultado |
| ----- | ---------------------------------------------------------------------------- | --------- |
| R1    | Dificultad respiratoria intensa                                              | Alta      |
| R2    | Dolor torácico intenso                                                       | Alta      |
| R3    | Pérdida de conciencia                                                        | Alta      |
| R4    | No hay regla de Alta y existen 2 o más síntomas de severidad moderada        | Media     |
| R5    | No hay regla de Alta ni R4 y existe al menos 1 síntoma de severidad moderada | Media     |
| R6    | No se cumple ninguna regla anterior y los síntomas son de severidad leve     | Baja      |

Precedencia: **Alta → Media → Baja**. Mismos datos de entrada → mismo resultado (determinista).

| Requisito | HU  | Criterios        | CP  | Implementación                       | Estado |
|-----------|-----|------------------|-----|--------------------------------------|--------|
| RF-12     | HU-07 | CA-07.1–07.3    | CP-12 | `POST /api/triage` (R1-R6) `services/triage.py` | ✅ pruebas 201/409/422/403 |
| RF-13     | HU-08 | CA-08.1–08.4    | CP-13 | `GET /api/triage` (paciente: solo los suyos) | ✅ pruebas 200/403 |
| RF-14     | HU-08 | CA-08.2–08.4    | CP-14 | `GET /api/triage` y `/{id}` (profesional: solo sus citas) | ✅ pruebas 200/403 |
| RF-15     | HU-09 | CA-09.1, 09.2   | CP-15 | clasificación síncrona en la respuesta (tiempo real) | ✅ pruebas 201 |
| RF-16     | HU-10 | CA-10.1, 10.2   | CP-16 | motor puro y determinista (sin estado externo) | ✅ pruebas R1-R6 + determinismo |

Decisiones técnicas (documentadas, sin alterar requisitos):
- **Síntomas de Alta (R1-R3)**: los tres canónicos de la tabla (dificultad respiratoria,
  dolor torácico, pérdida de conciencia) con severidad **intensa**. Los demás síntomas se
  reportan como **moderada** o **leve**; "intensa" en un síntoma no canónico es un 422.
- **El resultado se asocia al paciente y a la cita reservada que lo motiva**; un triaje por
  cita (unique `cita_id`). El triaje se registra mientras la cita está `reservada` y no venció.
- **Clasificación inicial, no diagnóstico**: la respuesta incluye `es_diagnostico=false` y el
  mensaje oficial de orientación (CA-07.x).
- **Acceso**: el paciente solo ve los suyos; el profesional, solo los de sus citas (vía
  `citas.professional_id == profesionales.user_id`); el administrador tiene acceso de solo
  lectura al sistema completo (la revisión oficial RF-17 corresponde a FASE 6).

## FASE 6 — trazabilidad verificada

**Alcance y base documental.** El documento oficial asigna a la FASE 6 los requisitos
RF-03 y RF-17. El texto exacto de los criterios CA-15.x y CA-13.x no se encontraba
disponible en el contexto de trabajo; **por decisión explícita del usuario se adoptó la
siguiente interpretación documentada** (registrada aquí, sin modificar identificadores ni
demás requisitos): RF-03 = el paciente actualiza sus propios datos; RF-17 = el administrador
revisa los triajes marcándolos como revisado o descartado.

| Requisito | HU  | Criterios        | CP  | Implementación                              | Estado |
|-----------|-----|------------------|-----|---------------------------------------------|--------|
| RF-03     | HU-15 | CA-15.1–15.4    | CP-03 | `api/routes/profile.py: PATCH /api/profile` (solo paciente) | ✅ pruebas 200/422/403/401 |
| RF-17     | HU-13 | CA-13.1–13.3    | CP-17 | `api/routes/triage.py: PATCH /api/triage/{id}/revision` (solo admin) | ✅ pruebas 200/403/404/422 |

Decisiones técnicas (interpretación documentada, aprobada para FASE 6):
- **RF-03 / HU-15 (perfil del paciente)**:
  - Se actualizan nombre, apellido, teléfono y (opcionalmente) la contraseña.
  - CA-15.1: la respuesta devuelve los nuevos valores y confirma la operación (200).
  - CA-15.2: validaciones iguales al registro (RNF-05): teléfono ≥ 7 dígitos numéricos,
    nueva contraseña ≥ 8 caracteres; cambiar la clave exige la contraseña actual correcta
    (422 si es incorrecta o si falta alguno de los dos campos).
  - CA-15.3: DNI y correo son **inmutables por el propio usuario**; el esquema usa
    `extra="forbid"`, por lo que intentar enviarlos produce 422.
  - La sesión activa se mantiene válida tras el cambio de contraseña (no se incrementa
    `token_version`); decisión documentada.
- **RF-17 / HU-13 (revisión administrativa del triaje)**:
  - Cada triaje tiene un `estado_revision` con tres estados: `pendiente` (al nacer),
    `revisado` (el administrador confirma el registro) y `descartado` (datos inconsistentes).
  - Solo el administrador cambia el estado (CA-13.3): paciente o profesional → 403
    (dependencia `require_roles(ADMINISTRADOR)`).
  - El estado es visible para paciente y profesional en sus consultas (columna "Revisión").
  - Triaje inexistente → 404; estado fuera del conjunto → 422.
- **Verificación Docker/PostgreSQL (E2E FASE 6)**: 201/200 en actualización de perfil;
  422 en DNI/email/telefono/clave incorrecta; cambio de contraseña y nuevo login con la
  clave; 403 para admin y profesional editando su perfil; triaje nuevo en `pendiente`;
  403 de paciente y profesional al intentar revisar; `revisado` y `descartado` con 200 por
  el admin; profesional asignado a la cita ve el estado; 404 y 422 en casos inválidos.
- **Persistencia**: se agregó la columna `estado_revision` a `triajes`; al tratarse de un
  cambio de esquema en el desarrollo local se recreó el volumen de PostgreSQL (`down -v`).

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

## FASE 7 — accesibilidad, seguridad de errores y responsive

**Alcance y base documental.** El documento oficial asigna a la FASE 7 los requisitos
RNF-06 y RNF-07. El texto exacto de estos criterios de aceptación no se encontraba
disponible en el contexto de trabajo; **por decisión explícita del usuario se adoptó la
siguiente interpretación documentada** (registrada aquí, sin alterar identificadores ni
otros requisitos): RNF-06 = los errores y los logs no exponen datos personales ni
información interna; RNF-07 = accesibilidad (HTML semántico, landmarks, foco y
responsive) en la interfaz.

| Requisito | Tipo        | Interpretación documentada                          | Implementación                                              | Estado |
|-----------|-------------|-----------------------------------------------------|-------------------------------------------------------------|--------|
| RNF-06    | Seguridad   | Errores y logs sin datos personales ni internos     | `main.py`: handlers 422 (sin `input`) y 500 genérico; logs solo con el tipo | ✅ pruebas y E2E |
| RNF-07    | Accesibilidad | HTML semántico, foco, responsive                  | `SkipLink`, `main#main`, `th scope="col"`, `@media` + `prefers-reduced-motion` | ✅ pruebas y build |

Decisiones técnicas (interpretación documentada, aprobada para FASE 7):
- **RNF-06: los errores y logs no exponen datos personales ni información interna.**
  - El manejador de `RequestValidationError` devuelve 422 con solo `field` y `message`;
    **elimina el campo `input`** que FastAPI incluye por defecto (allí viajaban los valores
    enviados: contraseñas, DNI, correos, teléfonos). Verificado que el cuerpo crudo de un
    422 de registro no contiene el correo ni la contraseña enviados.
  - Las excepciones no controladas devuelven 500 genérico
    `{"detail": "Error interno del servidor. Intente nuevamente."}` sin trazas ni stack.
  - El registro de la excepción solo incluye **el tipo** (`type(exc).__name__`); nunca el
    mensaje ni argumentos (reforzando la política de `core/logging.py`, RNF-11).
  - Cabeceras de seguridad en todas las respuestas (aspecto de seguridad de RNF-07):
    `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
    `Referrer-Policy: strict-origin-when-cross-origin` y
    `Content-Security-Policy: frame-ancestors 'none'`.
- **RNF-07: accesibilidad y responsive.**
  - Enlace **Saltar al contenido principal** (`.skip-link`, visible solo al recibir el
    foco) en Home, autenticación y panel; `main#main` con `role="main"` y `tabIndex={-1}`
    para recibir el foco del salto.
  - HTML semántico: landmarks (`banner`, `main`, `nav aria-label`, `contentinfo`),
    encabezados jerárquicos, tablas con `<th scope="col">`, formularios con `<label htmlFor>`
    asociado, mensajes de estado con `role="status"`/`aria-live` y errores con `role="alert"`.
  - Responsive en `index.css`: punto de quiebre 700px (banner, botones a ancho completo,
    padding) y 480px (navegación en columna, tipografía de formularios), manteniendo el
    desplazamiento horizontal de tablas; `prefers-reduced-motion: reduce` para usuarios con
    movimiento reducido.
- **Verificación Docker/PostgreSQL (E2E FASE 7)**: `/api/health` expone las cuatro
  cabeceras de seguridad; registro con DNI inválido devuelve 422 con
  `{"detail":[{"field":"dni","message":"..."}]}` sin `input` ni valores enviados; login con
  credenciales erróneas devuelve 401 con mensaje genérico.

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