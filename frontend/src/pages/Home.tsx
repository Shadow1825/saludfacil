import { useCallback, useEffect, useState } from "react";

import { fetchHealth, HealthResponse } from "../api/client";

type StatusState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

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
      <header className="banner" role="banner">
        <p className="banner__eyebrow">Clínica Comunitaria del Norte S.A.C.</p>
        <h1>SaludFácil</h1>
        <p className="banner__subtitle">Sistema de Gestión de Citas Médicas y Triaje</p>
      </header>

      <main id="main" className="content" role="main">
        <p>
          Bienvenido. Este proyecto se construye por fases para garantizar la trazabilidad con
          los requisitos del curso <strong>Calidad y Pruebas de Software (ISOF1401A)</strong>.
        </p>

        <section className="card" aria-labelledby="titulo-estado">
          <h2 id="titulo-estado">Estado de conexión (FASE 1)</h2>
          <p>
            Permitirá verificar el enlace <em>frontend → backend → PostgreSQL</em> durante la
            configuración inicial.
          </p>

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
              No se pudo contactar la API: {status.message}. Verifica que el backend esté en
              ejecución.
            </p>
          )}
        </section>
      </main>

      <footer className="footer" role="contentinfo">
        <p>
          Curso Calidad y Pruebas de Software — Proyecto académico con datos ficticios (Ley N.°
          29733).
        </p>
      </footer>
    </div>
  );
}