import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { cancelAppointment, ESTADO_LABEL, listAppointments, updateAppointmentEstado } from "../api/appointments";
import type { Cita } from "../api/appointments";

export function AdminCitasPage(): JSX.Element {
  const [citas, setCitas] = useState<Cita[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [filtroEstado, setFiltroEstado] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setCitas(await listAppointments({ estado: filtroEstado || undefined }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar las citas.");
    } finally {
      setLoading(false);
    }
  }, [filtroEstado]);

  useEffect(() => {
    void load();
  }, [load]);

  async function cambiarEstado(cita: Cita, estado: "atendida" | "no_asistio"): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      const result = await updateAppointmentEstado(cita.id, estado);
      setNotice(result.message);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el estado.");
    }
  }

  async function handleCancelarAdmin(cita: Cita): Promise<void> {
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

  return (
    <>
      <section aria-labelledby="titulo-admin-citas">
        <h2 id="titulo-admin-citas">Gestión de citas (RF-21)</h2>
        <p>Vea todas las citas del sistema, cambie su estado o cancélelas.</p>
        {error && <p className="error" role="alert">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        <div className="card">
          <div className="field">
            <label htmlFor="filtro-estado">Filtrar por estado</label>
            <select id="filtro-estado" value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
              <option value="">Todos los estados</option>
              <option value="reservada">Reservadas</option>
              <option value="cancelada">Canceladas</option>
              <option value="atendida">Atendidas</option>
              <option value="no_asistio">No asistió</option>
            </select>
          </div>
        </div>

        {loading ? (
          <p>Cargando citas…</p>
        ) : citas.length === 0 ? (
          <p>No hay citas registradas.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Fecha</th>
                  <th scope="col">Paciente</th>
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
                {citas.map((c) => (
                  <tr key={c.id}>
                    <td>{c.fecha}</td>
                    <td>{c.paciente}</td>
                    <td>{c.profesional}</td>
                    <td>{c.specialty_name}</td>
                    <td>
                      {c.hora_inicio} - {c.hora_fin}
                    </td>
                    <td>{ESTADO_LABEL[c.estado]}</td>
                    <td>
                      {c.estado === "reservada" && (
                        <>
                          <button
                            type="button"
                            className="button button--small"
                            onClick={() => void cambiarEstado(c, "atendida")}
                          >
                            Atendida
                          </button>{" "}
                          <button
                            type="button"
                            className="button button--small"
                            onClick={() => void cambiarEstado(c, "no_asistio")}
                          >
                            No asistió
                          </button>{" "}
                          <button
                            type="button"
                            className="button button--small"
                            onClick={() => void handleCancelarAdmin(c)}
                          >
                            Cancelar
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