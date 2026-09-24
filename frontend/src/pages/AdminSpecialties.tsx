import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { createSpecialty, listSpecialties, updateSpecialty } from "../api/medical";
import type { Especialidad } from "../api/medical";

export function AdminSpecialtiesPage(): JSX.Element {
  const [specialties, setSpecialties] = useState<Especialidad[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [nombre, setNombre] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSpecialties(await listSpecialties());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar las especialidades.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    setNotice(null);
    if (!nombre.trim()) {
      setError("Ingrese el nombre de la especialidad.");
      return;
    }
    setBusy(true);
    try {
      await createSpecialty(nombre.trim());
      setNombre("");
      setNotice("Especialidad registrada.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar la especialidad.");
    } finally {
      setBusy(false);
    }
  }

  async function toggle(specialty: Especialidad): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      await updateSpecialty(specialty.id, { is_active: !specialty.is_active });
      setNotice(specialty.is_active ? "Especialidad desactivada." : "Especialidad activada.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar la especialidad.");
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-especialidades">
        <h2 id="titulo-especialidades">Especialidades (RF-05)</h2>
        <p>
          Registre, edite o desactive las especialidades médicas ofrecidas por la clínica.
        </p>
        {error && <p className="error" role="alert">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        <form className="card" onSubmit={(event) => void handleCreate(event)}>
          <div className="field">
            <label htmlFor="nombre">Nombre de la especialidad</label>
            <input
              id="nombre"
              type="text"
              value={nombre}
              onChange={(event) => setNombre(event.target.value)}
              required
            />
          </div>
          <button type="submit" className="button button--primary" disabled={busy}>
            {busy ? "Registrando…" : "Registrar especialidad"}
          </button>
        </form>

        {loading ? (
          <p>Cargando especialidades…</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Nombre</th>
                  <th scope="col">Estado</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {specialties.map((s) => (
                  <tr key={s.id}>
                    <td>{s.nombre}</td>
                    <td>{s.is_active ? "Activa" : "Inactiva"}</td>
                    <td>
                      <button
                        type="button"
                        className="button button--small"
                        onClick={() => void toggle(s)}
                      >
                        {s.is_active ? "Desactivar" : "Activar"}
                      </button>
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