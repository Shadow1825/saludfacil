import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { listTriajes, updateTriajeRevision } from "../api/triage";
import type { Triage } from "../api/triage";

export function AdminTriajesPage(): JSX.Element {
  const [triajes, setTriajes] = useState<Triage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setTriajes(await listTriajes());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los triajes.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function revisar(triaje: Triage, estado: "revisado" | "descartado"): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      await updateTriajeRevision(triaje.id, estado);
      setNotice(`Triaje marcado como "${estado}".`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar la revisión.");
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-admin-triajes">
        <h2 id="titulo-admin-triajes">Revisión de triajes</h2>
        <p>
          Revise las clasificaciones iniciales del sistema. Confirme ("revisado")
          o descarte los registros con datos inconsistentes ("descartado").
        </p>
        {error && <p className="error" role="alert">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        {loading ? (
          <p>Cargando triajes…</p>
        ) : triajes.length === 0 ? (
          <p>No hay triajes registrados.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Fecha</th>
                  <th scope="col">Paciente</th>
                  <th scope="col">Profesional</th>
                  <th scope="col">Clasificación</th>
                  <th scope="col">Síntomas</th>
                  <th scope="col">Revisión</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {triajes.map((t) => (
                  <tr key={t.id}>
                    <td>
                      {t.fecha} {t.hora_inicio}
                    </td>
                    <td>{t.paciente}</td>
                    <td>{t.profesional || "—"}</td>
                    <td>{t.resultado}</td>
                    <td>{t.sintomas.map((s) => `${s.nombre} (${s.severidad})`).join(", ")}</td>
                    <td>{t.estado_revision_label}</td>
                    <td>
                      {t.estado_revision === "pendiente" && (
                        <>
                          <button
                            type="button"
                            className="button button--small"
                            onClick={() => void revisar(t, "revisado")}
                          >
                            Revisado
                          </button>{" "}
                          <button
                            type="button"
                            className="button button--small"
                            onClick={() => void revisar(t, "descartado")}
                          >
                            Descartar
                          </button>
                        </>
                      )}
                    </td>
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