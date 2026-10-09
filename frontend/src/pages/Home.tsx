import { useCallback, useEffect, useState } from "react";

import { fetchHealth, HealthResponse } from "../api/client";
import { SkipLink } from "../components/SkipLink";
import { ServiceIcon } from "../components/ServiceIcon";

type StatusState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

const SERVICIOS = [
  {
    titulo: "Reserva de citas en línea",
    descripcion:
      "Consulte la disponibilidad de nuestros especialistas y reserve su atención sin llamadas ni filas.",
    icono: "calendar-check" as const,
  },
  {
    titulo: "Triaje inicial orientativo",
    descripcion:
      "Registre sus síntomas y obtenga una clasificación inicial que orienta el orden de atención.",
    icono: "activity" as const,
  },
  {
    titulo: "Atención por roles",
    descripcion:
      "Pacientes, profesionales y administración acceden a procesos diseñados para cada función.",
    icono: "users" as const,
  },
];

export function HomePage(): JSX.Element {
  const [status, setStatus] = useState<StatusState>({ kind: "loading" });

  const load = useCallback(async () => {
    setStatus({ kind: "loading" });
    try {
      const data = await fetchHealth();
      setStatus({ kind: "ok", data });
    } catch (error) {
      setStatus({
        kind: "error",
        message: error instanceof Error ? error.message : "Error desconocido",
      });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="shell">
      <SkipLink />
      <header role="banner">
        <div className="site-header">
          <div className="site-header__row">
            <div className="site-header__brand">
              <ServiceIcon name="home" size={34} />
              <div>
                <p className="brand-title">
                  <a href="/inicio">SaludFácil</a>
                </p>
                <p className="brand-subtitle">Citas médicas y triaje en línea</p>
              </div>
            </div>
            <div className="site-header__actions">
              <a className="button button--secondary" href="/login">
                Iniciar sesión
              </a>
              <a className="button button--primary" href="/registro">
                Crear cuenta
              </a>
            </div>
          </div>
        </div>
        <div className="banner">
          <p className="banner__eyebrow">Clínica Comunitaria del Norte S.A.C.</p>
          <h1>SaludFácil</h1>
          <p className="banner__subtitle">
            Gestión de citas médicas y triaje para su centro de salud
          </p>
        </div>
      </header>

      <main id="main" className="content" role="main" tabIndex={-1}>
        <section aria-labelledby="titulo-bienvenida" className="card">
          <h2 id="titulo-bienvenida">Bienvenido al portal</h2>
          <p>
            SaludFácil es la plataforma institucional que permite programar citas médicas,
            consultar la disponibilidad de los especialistas y realizar la clasificación inicial
            de sus síntomas de forma segura y ordenada.
          </p>
          <div className="actions-row">
            <a className="button button--primary" href="/login">
              Iniciar sesión
            </a>
            <a className="button button--secondary" href="/registro">
              Crear cuenta
            </a>
          </div>
        </section>

        <section aria-labelledby="titulo-servicios">
          <h2 id="titulo-servicios">Servicios del portal</h2>
          <div className="services" aria-label="Servicios del portal">
            {SERVICIOS.map((servicio) => (
              <article className="service-card" key={servicio.titulo}>
                <div className="service-card__icon">
                  <ServiceIcon name={servicio.icono} />
                </div>
                <h3 className="service-card__title">{servicio.titulo}</h3>
                <p className="service-card__text">{servicio.descripcion}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="card" aria-labelledby="titulo-estado">
          <h2 id="titulo-estado">Estado del sistema</h2>

          {status.kind === "loading" && (
            <p role="status" aria-live="polite">
              Comprobando conexión con el servidor…
            </p>
          )}

          {status.kind === "ok" && (
            <dl className="health" aria-live="polite">
              <div>
                <dt>Servicio</dt>
                <dd>{status.data.status === "ok" ? "Operativo" : status.data.status}</dd>
              </div>
              <div>
                <dt>API</dt>
                <dd>{status.data.service}</dd>
              </div>
              <div>
                <dt>Base de datos</dt>
                <dd>{status.data.database === "ok" ? "Conectada" : "No conectada"}</dd>
              </div>
            </dl>
          )}

          {status.kind === "error" && (
            <p className="error" role="alert">
              No se pudo contactar el servidor: {status.message}. Intente nuevamente en unos
              momentos.
            </p>
          )}
        </section>
      </main>

      <footer className="site-footer" role="contentinfo">
        <div className="site-footer__cols">
          <div>
            <p className="site-footer__title">SaludFácil</p>
            <p>Sistema de gestión de citas médicas, agenda profesional y triaje inicial orientativo.</p>
            <p>Plataforma de demostración con fines institucionales.</p>
          </div>
          <div>
            <p className="site-footer__title">Atención</p>
            <p>Lunes a viernes: 7:00 a. m. – 7:00 p. m.</p>
            <p>Sábados y domingos: 7:00 a. m. – 1:00 p. m.</p>
          </div>
          <div>
            <p className="site-footer__title">Contacto</p>
            <p>Clínica Comunitaria del Norte S.A.C.</p>
            <p>Av. Los Eucaliptos 245 · Lima · Perú</p>
            <p>
              Central: <a href="tel:+51905987665">(01) 598-7665</a>
            </p>
          </div>
        </div>
        <div className="site-footer__bottom">
          © 2026 SaludFácil · Clínica Comunitaria del Norte S.A.C. · Todos los derechos reservados.
        </div>
      </footer>
    </div>
  );
}