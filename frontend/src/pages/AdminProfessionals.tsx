import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import {
  createProfessional,
  listProfessionals,
  listSpecialties,
  updateProfessional,
} from "../api/medical";
import type { Especialidad, Profesional } from "../api/medical";

const FORM_VACIO = {
  first_name: "",
  last_name: "",
  dni: "",
  email: "",
  phone: "",
  password: "",
  specialty_id: "",
};

export function AdminProfessionalsPage(): JSX.Element {
  const [professionals, setProfessionals] = useState<Profesional[]>([]);
  const [specialties, setSpecialties] = useState<Especialidad[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [form, setForm] = useState(FORM_VACIO);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [prof, esp] = await Promise.all([listProfessionals(), listSpecialties()]);
      setProfessionals(prof);
      setSpecialties(esp);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los profesionales.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function setField<K extends keyof typeof FORM_VACIO>(field: K, value: string): void {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleCreate(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    setNotice(null);
    const vacios = Object.values(form).some((v) => !v.trim() && v !== form.password);
    if (vacios || !form.password) {
      setError("Complete todos los campos del formulario.");
      return;
    }
    setBusy(true);
    try {
      await createProfessional({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        dni: form.dni.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
        specialty_id: Number(form.specialty_id),
      });
      setForm(FORM_VACIO);
      setNotice("Profesional registrado.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar el profesional.");
    } finally {
      setBusy(false);
    }
  }

  async function changeSpecialty(profesional: Profesional, specialtyId: number): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      await updateProfessional(profesional.id, { specialty_id: specialtyId });
      setNotice("Especialidad del profesional actualizada.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el profesional.");
    }
  }

  async function toggleActive(profesional: Profesional): Promise<void> {
    setError(null);
    setNotice(null);
    try {
      await updateProfessional(profesional.id, { is_active: !profesional.is_active });
      setNotice(profesional.is_active ? "Profesional desactivado." : "Profesional activado.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el profesional.");
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-profesionales">
        <h2 id="titulo-profesionales">Profesionales de salud</h2>
        <p>Registre profesionales, asigne su especialidad o desactívelos.</p>
        {error && <p className="error" role="alert">{error}</p>}
        {notice && <p className="notice">{notice}</p>}

        <form className="card" onSubmit={(event) => void handleCreate(event)}>
          <div className="field">
            <label htmlFor="first_name">Nombres</label>
            <input id="first_name" type="text" value={form.first_name} onChange={(e) => setField("first_name", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="last_name">Apellidos</label>
            <input id="last_name" type="text" value={form.last_name} onChange={(e) => setField("last_name", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="dni">DNI (8 dígitos)</label>
            <input id="dni" type="text" inputMode="numeric" maxLength={8} value={form.dni} onChange={(e) => setField("dni", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="email">Correo electrónico</label>
            <input id="email" type="email" value={form.email} onChange={(e) => setField("email", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="phone">Teléfono</label>
            <input id="phone" type="tel" value={form.phone} onChange={(e) => setField("phone", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Contraseña (mínimo 8 caracteres)</label>
            <input id="password" type="password" minLength={8} value={form.password} onChange={(e) => setField("password", e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="specialty_id">Especialidad</label>
            <select id="specialty_id" value={form.specialty_id} onChange={(e) => setField("specialty_id", e.target.value)} required>
              <option value="">Seleccione…</option>
              {specialties.filter((s) => s.is_active).map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="button button--primary" disabled={busy}>
            {busy ? "Registrando…" : "Registrar profesional"}
          </button>
        </form>

        {loading ? (
          <p>Cargando profesionales…</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Profesional</th>
                  <th scope="col">Especialidad</th>
                  <th scope="col">Estado</th>
                  <th scope="col">
                    <span className="visually-hidden">Acciones</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {professionals.map((p) => (
                  <tr key={p.id}>
                    <td>
                      {p.first_name} {p.last_name}
                      <br />
                      <small>{p.email}</small>
                    </td>
                    <td>
                      <select
                        aria-label={`Especialidad de ${p.first_name} ${p.last_name}`}
                        value={p.specialty_id}
                        onChange={(e) => void changeSpecialty(p, Number(e.target.value))}
                      >
                        {specialties.filter((s) => s.is_active).map((s) => (
                          <option key={s.id} value={s.id}>{s.nombre}</option>
                        ))}
                      </select>
                    </td>
                    <td>{p.is_active ? "Activo" : "Inactivo"}</td>
                    <td>
                      <button
                        type="button"
                        className="button button--small"
                        onClick={() => void toggleActive(p)}
                      >
                        {p.is_active ? "Desactivar" : "Activar"}
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