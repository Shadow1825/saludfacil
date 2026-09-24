import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { directorioProfessionals, directorioSchedules, directorioSpecialties } from "../api/medical";
import type { Especialidad, Horario, Profesional } from "../api/medical";

export function DisponibilidadPage(): JSX.Element {
  const [specialties, setSpecialties] = useState<Especialidad[]>([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState<string>("");
  const [professionals, setProfessionals] = useState<Profesional[]>([]);
  const [selectedProfessional, setSelectedProfessional] = useState<string>("");
  const [schedules, setSchedules] = useState<Horario[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    directorioSpecialties()
      .then(setSpecialties)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudieron cargar las especialidades."));
  }, []);

  const loadProfessionals = useCallback(async (specialtyId: number) => {
    setError(null);
    try {
      const lista = await directorioProfessionals(specialtyId);
      setProfessionals(lista);
      setSelectedProfessional("");
      setSchedules([]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los profesionales.");
    }
  }, []);

  const loadSchedules = useCallback(async (professionalId: number) => {
    setError(null);
    try {
      const lista = await directorioSchedules(professionalId);
      setSchedules(lista);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los horarios.");
      setSchedules([]);
    }
  }, []);

  function handleSpecialty(value: string): void {
    setSelectedSpecialty(value);
    if (value) {
      void loadProfessionals(Number(value));
    } else {
      setProfessionals([]);
      setSchedules([]);
    }
  }

  function handleProfessional(value: string): void {
    setSelectedProfessional(value);
    if (value) {
      void loadSchedules(Number(value));
    } else {
      setSchedules([]);
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-disponibilidad">
        <h2 id="titulo-disponibilidad">Consulta de disponibilidad (RF-07 / RF-08)</h2>
        <p>
          Seleccione una especialidad, elija un profesional y consulte los horarios
          disponibles para su atención.
        </p>
        {error && <p className="error" role="alert">{error}</p>}

        <form className="card">
          <div className="field">
            <label htmlFor="especialidad">Especialidad</label>
            <select
              id="especialidad"
              value={selectedSpecialty}
              onChange={(e) => handleSpecialty(e.target.value)}
            >
              <option value="">Seleccione una especialidad…</option>
              {specialties.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>

          {selectedSpecialty && (
            <div className="field">
              <label htmlFor="profesional">Profesional</label>
              <select
                id="profesional"
                value={selectedProfessional}
                onChange={(e) => handleProfessional(e.target.value)}
                disabled={professionals.length === 0}
              >
                <option value="">
                  {professionals.length === 0 ? "No hay profesionales disponibles" : "Seleccione un profesional…"}
                </option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </form>

        {selectedProfessional &&
          (schedules.length === 0 ? (
            <p className="notice">
              No existen horarios disponibles para el profesional seleccionado.
            </p>
          ) : (
            <div className="table-wrap">
              <h3>Horarios disponibles</h3>
              <table>
                <thead>
                  <tr>
                    <th scope="col">Día</th>
                    <th scope="col">Inicio</th>
                    <th scope="col">Fin</th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((s) => (
                    <tr key={s.id}>
                      <td>{s.day_name}</td>
                      <td>{s.start_time}</td>
                      <td>{s.end_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}

        {!selectedSpecialty && (
          <p className="notice">Seleccione una especialidad para ver sus profesionales activos.</p>
        )}
      </section>
    </>
  );
}