import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { cancelAppointment, ESTADO_LABEL, listAppointments } from "../api/appointments";
import type { Cita } from "../api/appointments";

function esFutura(cita: Cita): boolean {
  return cita.estado === "reservada";
}

export function MisCitasPage(): JSX.Element {
  const [citas, setCitas] = useState<Cita[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCitas(await listAppointments());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar sus citas.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCancelar(cita: Cita): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      const result = await cancelAppointment(cita.id);
      setNotice(result.message);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cancelar la cita.");
    }
  }

  const proximas = citas.filter(esFutura);
  const historial = citas.filter((c) => !esFutura(c));

  return (
    <>
      <section aria-labelledby="titulo-mis-citas">
        <h2 id="titulo-mis-citas">Mis citas (RF-10 / RF-11)</h2>
        <p>Consulte sus citas reservadas y cancele las que no podrá asistir.</p>
        {error && <p className="error" role="alert">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        {loading ? (
          <p>Cargando citas…</p>
        ) : (
          <>
            <h3>Citas próximas</h3>
            {proximas.length === 0 ? (
              <p>No tiene citas reservadas próximamente.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Fecha</th>
                      <th scope="col">Profesional</th>
                      <th scope="col">Especialidad</th>
                      <th scope="col">Hora</th>
                      <th scope="col">Estado</th>
                      <th scope="col">
                        <span className="visually-hidden">Acciones</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {proximas.map((c) => (
                      <tr key={c.id}>
                        <td>{c.fecha}</td>
                        <td>{c.profesional}</td>
                        <td>{c.specialty_name}</td>
                        <td>
                          {c.hora_inicio} - {c.hora_fin}
                        </td>
                        <td>{ESTADO_LABEL[c.estado]}</td>
                        <td>
                          <button
                            type="button"
                            className="button button--small"
                            onClick={() => void handleCancelar(c)}
                          >
                            Cancelar (RF-11)
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <h3>Historial</h3>
            {historial.length === 0 ? (
              <p>Aún no tiene citas en su historial.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Fecha</th>
                      <th scope="col">Profesional</th>
                      <th scope="col">Especialidad</th>
                      <th scope="col">Hora</th>
                      <th scope="col">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historial.map((c) => (
                      <tr key={c.id}>
                        <td>{c.fecha}</td>
                        <td>{c.profesional}</td>
                        <td>{c.specialty_name}</td>
                        <td>
                          {c.hora_inicio} - {c.hora_fin}
                        </td>
                        <td>{ESTADO_LABEL[c.estado]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}