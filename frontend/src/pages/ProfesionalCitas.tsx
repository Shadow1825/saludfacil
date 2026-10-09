import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { ESTADO_LABEL, listAppointments } from "../api/appointments";
import type { Cita } from "../api/appointments";

export function ProfesionalCitasPage(): JSX.Element {
  const [citas, setCitas] = useState<Cita[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const proximas = citas.filter((c) => c.estado === "reservada");
  const historial = citas.filter((c) => c.estado !== "reservada");

  return (
    <>
      <section aria-labelledby="titulo-profesional-citas">
        <h2 id="titulo-profesional-citas">Mis citas</h2>
        <p>Citas asignadas a su atención. Revise el triaje de cada una en «Triaje de citas».</p>
        {error && <p className="error" role="alert">{error}</p>}

        {loading ? (
          <p>Cargando citas…</p>
        ) : (
          <>
            <h3>Citas próximas</h3>
            {proximas.length === 0 ? (
              <p>No tiene citas próximas asignadas.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Fecha</th>
                      <th scope="col">Paciente</th>
                      <th scope="col">Especialidad</th>
                      <th scope="col">Hora</th>
                      <th scope="col">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {proximas.map((c) => (
                      <tr key={c.id}>
                        <td>{c.fecha}</td>
                        <td>{c.paciente}</td>
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

            <h3>Historial</h3>
            {historial.length === 0 ? (
              <p>Aún no tiene citas en su historial.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Fecha</th>
                      <th scope="col">Paciente</th>
                      <th scope="col">Especialidad</th>
                      <th scope="col">Hora</th>
                      <th scope="col">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historial.map((c) => (
                      <tr key={c.id}>
                        <td>{c.fecha}</td>
                        <td>{c.paciente}</td>
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