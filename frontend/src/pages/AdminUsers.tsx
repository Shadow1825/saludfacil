import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import { createUser, listUsers, updateUser } from "../api/users";
import { ROLE_LABEL } from "../types/auth";
import type { User } from "../types/auth";

const ROLES = ["paciente", "profesional", "administrador"] as const;

const FORM_VACIO = {
  first_name: "",
  last_name: "",
  dni: "",
  email: "",
  phone: "",
  password: "",
  role: "paciente" as User["role"],
};

export function AdminUsersPage(): JSX.Element {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState(FORM_VACIO);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setUsers(await listUsers());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron cargar los usuarios.");
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
    const vacios = !form.first_name.trim() || !form.last_name.trim() || !form.dni.trim() ||
      !form.email.trim() || !form.phone.trim() || !form.password;
    if (vacios) {
      setError("Complete todos los campos del formulario.");
      return;
    }
    setBusy(true);
    try {
      await createUser(form);
      setForm(FORM_VACIO);
      setNotice("Cuenta creada correctamente.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la cuenta.");
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive(user: User): Promise<void> {
    setError(null);
    try {
      const updated = await updateUser(user.id, { is_active: !user.is_active });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setNotice(
        updated.is_active ? "Cuenta reactivada." : "Cuenta desactivada. Su sesión activa se cerró.",
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar la cuenta.");
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-usuarios">
        <h2 id="titulo-usuarios">Usuarios</h2>
        <p>
          Gestión de cuentas (RF-18 / CA-11.5): crear, desactivar o reactivar usuarios del
          sistema.
        </p>

        {notice !== null && (
          <p className="notice" role="status">
            {notice}
          </p>
        )}
        {error !== null && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        {loading ? (
          <p role="status">Cargando usuarios…</p>
        ) : (
          <div className="table-wrap">
            <table>
              <caption className="visually-hidden">Lista de usuarios del sistema</caption>
              <thead>
                <tr>
                  <th scope="col">Nombre</th>
                  <th scope="col">Correo</th>
                  <th scope="col">Rol</th>
                  <th scope="col">Estado</th>
                  <th scope="col"><span className="visually-hidden">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>
                      {user.first_name} {user.last_name}
                    </td>
                    <td>{user.email}</td>
                    <td>{ROLE_LABEL[user.role]}</td>
                    <td>{user.is_active ? "Activo" : "Desactivado"}</td>
                    <td>
                      <button
                        type="button"
                        className="button button--small"
                        onClick={() => void toggleActive(user)}
                      >
                        {user.is_active ? "Desactivar" : "Reactivar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <section className="card" aria-labelledby="titulo-nuevo">
          <h3 id="titulo-nuevo">Crear cuenta de usuario</h3>
          <form onSubmit={handleCreate} noValidate>
            <div className="field">
              <label htmlFor="nu_first_name">Nombres</label>
              <input
                id="nu_first_name"
                required
                value={form.first_name}
                onChange={(event) => setField("first_name", event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="nu_last_name">Apellidos</label>
              <input
                id="nu_last_name"
                required
                value={form.last_name}
                onChange={(event) => setField("last_name", event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="nu_dni">DNI (8 dígitos)</label>
              <input
                id="nu_dni"
                inputMode="numeric"
                maxLength={8}
                required
                value={form.dni}
                onChange={(event) => setField("dni", event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="nu_email">Correo electrónico</label>
              <input
                id="nu_email"
                type="email"
                required
                value={form.email}
                onChange={(event) => setField("email", event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="nu_phone">Teléfono</label>
              <input
                id="nu_phone"
                type="tel"
                required
                value={form.phone}
                onChange={(event) => setField("phone", event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="nu_password">Contraseña (mínimo 8 caracteres)</label>
              <input
                id="nu_password"
                type="password"
                minLength={8}
                required
                value={form.password}
                onChange={(event) => setField("password", event.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="nu_role">Rol</label>
              <select
                id="nu_role"
                value={form.role}
                onChange={(event) => setField("role", event.target.value)}
              >
                {ROLES.map((role) => (
                  <option key={role} value={role}>
                    {ROLE_LABEL[role]}
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" className="button button--primary" disabled={busy}>
              {busy ? "Creando…" : "Crear cuenta"}
            </button>
          </form>
        </section>
      </section>
    </>
  );
}