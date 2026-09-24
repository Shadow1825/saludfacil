import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { createAppointment, directorioSlots } from "../api/appointments";
import type { Slot } from "../api/appointments";
import { directorioProfessionals, directorioSpecialties } from "../api/medical";
import type { Especialidad, Profesional } from "../api/medical";

export function ReservarCitaPage(): JSX.Element {
  const [specialties, setSpecialties] = useState<Especialidad[]>([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState("");
  const [professionals, setProfessionals] = useState<Profesional[]>([]);
  const [selectedProfessional, setSelectedProfessional] = useState("");
  const [fecha, setFecha] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmacion, setConfirmacion] = useState<string | null>(null);

  useEffect(() => {
    directorioSpecialties()
      .then(setSpecialties)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudieron cargar las especialidades."));
  }, []);

  const loadSlots = useCallback(async (professionalId: number, dia: string) => {
    setError(null);
    setConfirmacion(null);
    try {
      const lista = await directorioSlots(professionalId, dia);
      setSlots(lista);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los horarios.");
      setSlots([]);
    }
  }, []);

  function handleSpecialty(value: string): void {
    setSelectedSpecialty(value);
    setSelectedProfessional("");
    setFecha("");
    setSlots([]);
    if (value) {
      directorioProfessionals(Number(value))
        .then(setProfessionals)
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudieron cargar los profesionales."));
    } else {
      setProfessionals([]);
    }
  }

  function handleProfessional(value: string): void {
    setSelectedProfessional(value);
    setFecha("");
    setSlots([]);
  }

  function handleFecha(value: string): void {
    setFecha(value);
    if (selectedProfessional && value) {
      void loadSlots(Number(selectedProfessional), value);
    } else {
      setSlots([]);
    }
  }

  async function handleReservar(slot: Slot): Promise<void> {
    setError(null);
    setConfirmacion(null);
    setBusy(true);
    try {
      const cita = await createAppointment({
        professional_id: Number(selectedProfessional),
        fecha: slot.fecha,
        hora_inicio: slot.hora_inicio,
      });
      setConfirmacion(
        `Cita reservada: ${cita.profesional} · ${cita.dia} ${cita.fecha} ${cita.hora_inicio}-${cita.hora_fin}.`,
      );
      setSlots((prev) => prev.filter((s) => s.hora_inicio !== slot.hora_inicio));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo reservar la cita.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-reservar">
        <h2 id="titulo-reservar">Reservar cita (RF-09)</h2>
        <p>
          Elija la especialidad, el profesional y la fecha para ver los horarios
          disponibles y reservar su cita.
        </p>
        {error && <p className="error" role="alert">{error}</p>}
        {confirmacion && <p className="notice" role="status">{confirmacion}</p>}

        <form className="card">
          <div className="field">
            <label htmlFor="especialidad">Especialidad</label>
            <select id="especialidad" value={selectedSpecialty} onChange={(e) => handleSpecialty(e.target.value)}>
              <option value="">Seleccione una especialidad…</option>
              {specialties.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>

          {selectedSpecialty && (
            <div className="field">
              <label htmlFor="profesional">Profesional</label>
              <select id="profesional" value={selectedProfessional} onChange={(e) => handleProfessional(e.target.value)}>
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

          {selectedProfessional && (
            <div className="field">
              <label htmlFor="fecha">Fecha de la cita</label>
              <input id="fecha" type="date" value={fecha} onChange={(e) => handleFecha(e.target.value)} />
            </div>
          )}
        </form>

        {fecha &&
          (slots.length === 0 ? (
            <p className="notice">No hay horarios disponibles para la fecha seleccionada.</p>
          ) : (
            <div className="table-wrap">
              <h3>Horarios disponibles (30 min)</h3>
              <table>
                <thead>
                  <tr>
                    <th scope="col">Hora</th>
                    <th scope="col">
                      <span className="visually-hidden">Acción</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {slots.map((s) => (
                    <tr key={s.hora_inicio}>
                      <td>
                        {s.hora_inicio} - {s.hora_fin}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="button button--small"
                          disabled={busy}
                          onClick={() => void handleReservar(s)}
                        >
                          {busy ? "Reservando…" : "Reservar"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
      </section>
    </>
  );
}