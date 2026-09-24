import { useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { listTriajes } from "../api/triage";
import type { Triage } from "../api/triage";

export function MisTriajesPage(): JSX.Element {
  const [triajes, setTriajes] = useState<Triage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTriajes()
      .then(setTriajes)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudieron cargar los triajes."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <section aria-labelledby="titulo-triajes-prof">
        <h2 id="titulo-triajes-prof">Triaje de mis citas (RF-14 / HU-08)</h2>
        <p>
          Consulte la clasificación inicial registrada por los pacientes de las
          citas asignadas a usted. Es una clasificación orientativa, no un diagnóstico.
        </p>
        {error && <p className="error" role="alert">{error}</p>}
        {loading ? (
          <p>Cargando triajes…</p>
        ) : triajes.length === 0 ? (
          <p>No hay triajes registrados para sus citas.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Fecha</th>
                  <th scope="col">Paciente</th>
                  <th scope="col">Especialidad</th>
                  <th scope="col">Clasificación inicial</th>
                  <th scope="col">Síntomas</th>
                </tr>
              </thead>
              <tbody>
                {triajes.map((t) => (
                  <tr key={t.id}>
                    <td>
                      {t.fecha} {t.hora_inicio}
                    </td>
                    <td>{t.paciente}</td>
                    <td>{t.specialty_name}</td>
                    <td>{t.resultado}</td>
                    <td>{t.sintomas.map((s) => `${s.nombre} (${s.severidad})`).join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}