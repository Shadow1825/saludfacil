import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import {
  createSchedule,
  listProfessionals,
  listSchedules,
  updateSchedule,
} from "../api/medical";
import type { Horario, Profesional } from "../api/medical";
import { DIAS_SEMANA } from "../api/medical";

const FORM_VACIO = { day: "", start_time: "", end_time: "" };

export function AdminSchedulesPage(): JSX.Element {
  const [professionals, setProfessionals] = useState<Profesional[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [schedules, setSchedules] = useState<Horario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState(FORM_VACIO);
  const [busy, setBusy] = useState(false);

  const loadProfessionals = useCallback(async () => {
    try {
      const prof = await listProfessionals();
      setProfessionals(prof);
      if (!selected && prof.length > 0) {
        setSelected(String(prof[0].id));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los profesionales.");
    }
  }, [selected]);

  const loadSchedules = useCallback(async () => {
    if (!selected) return;
    setLoading(true);
    try {
      setSchedules(await listSchedules(Number(selected)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los horarios.");
    } finally {
      setLoading(false);
    }
  }, [selected]);

  useEffect(() => {
    void loadProfessionals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    void loadSchedules();
  }, [loadSchedules]);

  function setField<K extends keyof typeof FORM_VACIO>(field: K, value: string): void {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleCreate(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    setNotice(null);
    if (!selected || !form.day || !form.start_time || !form.end_time) {
      setError("Complete el día y las horas del horario.");
      return;
    }
    setBusy(true);
    try {
      await createSchedule({
        professional_id: Number(selected),
        day: Number(form.day),
        start_time: form.start_time,
        end_time: form.end_time,
      });
      setForm(FORM_VACIO);
      setNotice("Horario registrado.");
      await loadSchedules();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar el horario.");
    } finally {
      setBusy(false);
    }
  }

  async function toggle(schedule: Horario): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      await updateSchedule(schedule.id, { is_active: !schedule.is_active });
      setNotice(schedule.is_active ? "Horario desactivado." : "Horario activado.");
      await loadSchedules();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el horario.");
    }
  }

  const profesionalSeleccionado = professionals.find((p) => String(p.id) === selected);

  return (
    <>
      <section aria-labelledby="titulo-horarios">
        <h2 id="titulo-horarios">Horarios de atención (RF-06)</h2>
        <p>Defina los días y horas de atención de cada profesional.</p>
        {error && <p className="error" role="alert">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        <div className="card">
          <div className="field">
            <label htmlFor="profesional">Profesional</label>
            <select
              id="profesional"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} - {p.specialty_name}
                </option>
              ))}
            </select>
          </div>

          <form onSubmit={(event) => void handleCreate(event)}>
            <div className="field">
              <label htmlFor="day">Día</label>
              <select id="day" value={form.day} onChange={(e) => setField("day", e.target.value)}>
                <option value="">Seleccione…</option>
                {Object.entries(DIAS_SEMANA).map(([num, nombre]) => (
                  <option key={num} value={num}>{nombre}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="start_time">Hora de inicio (HH:MM)</label>
              <input id="start_time" type="time" value={form.start_time} onChange={(e) => setField("start_time", e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor="end_time">Hora de fin (HH:MM)</label>
              <input id="end_time" type="time" value={form.end_time} onChange={(e) => setField("end_time", e.target.value)} required />
            </div>
            <button type="submit" className="button button--primary" disabled={busy}>
              {busy ? "Registrando…" : "Agregar horario"}
            </button>
          </form>
        </div>

        {selected && (
          <div className="table-wrap">
            <h3>
              Horarios de {profesionalSeleccionado ? `${profesionalSeleccionado.first_name} ${profesionalSeleccionado.last_name}` : ""}
            </h3>
            {loading ? (
              <p>Cargando horarios…</p>
            ) : schedules.length === 0 ? (
              <p>El profesional aún no tiene horarios registrados.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th scope="col">Día</th>
                    <th scope="col">Inicio</th>
                    <th scope="col">Fin</th>
                    <th scope="col">Estado</th>
                    <th scope="col">
                      <span className="visually-hidden">Acciones</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {schedules.map((s) => (
                    <tr key={s.id}>
                      <td>{s.day_name}</td>
                      <td>{s.start_time}</td>
                      <td>{s.end_time}</td>
                      <td>{s.is_active ? "Activo" : "Inactivo"}</td>
                      <td>
                        <button type="button" className="button button--small" onClick={() => void toggle(s)}>
                          {s.is_active ? "Desactivar" : "Activar"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </section>
    </>
  );
}