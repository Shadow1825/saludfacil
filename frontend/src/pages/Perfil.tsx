import { useState } from "react";

import { updateProfile } from "../api/auth";
import type { ProfileUpdateData } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function PerfilPage(): JSX.Element {
  const { user, refreshUser } = useAuth();
  const [first_name, setFirstName] = useState(user?.first_name ?? "");
  const [last_name, setLastName] = useState(user?.last_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [current_password, setCurrentPassword] = useState("");
  const [new_password, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function validar(): string | null {
    if (phone.trim() && (!/^\d+$/.test(phone.trim()) || phone.trim().length < 7)) {
      return "El teléfono debe contener al menos 7 dígitos.";
    }
    if (new_password && new_password.length < 8) {
      return "La nueva contraseña debe tener al menos 8 caracteres.";
    }
    if ((current_password && !new_password) || (!current_password && new_password)) {
      return "Para cambiar la contraseña debe indicar la actual y la nueva.";
    }
    return null;
  }

  async function handleSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    setMessage(null);
    const invalido = validar();
    if (invalido !== null) {
      setError(invalido);
      return;
    }
    const data: ProfileUpdateData = {};
    if (first_name.trim() !== user?.first_name) data.first_name = first_name.trim();
    if (last_name.trim() !== user?.last_name) data.last_name = last_name.trim();
    if (phone.trim() !== user?.phone) data.phone = phone.trim();
    if (new_password) {
      data.current_password = current_password;
      data.new_password = new_password;
    }
    if (Object.keys(data).length === 0) {
      setError("No hay datos para actualizar.");
      return;
    }
    setBusy(true);
    try {
      await updateProfile(data);
      await refreshUser();
      setCurrentPassword("");
      setNewPassword("");
      setMessage("Sus datos se actualizaron correctamente (RF-03).");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudieron actualizar sus datos.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section aria-labelledby="titulo-perfil">
        <h2 id="titulo-perfil">Mi perfil (RF-03 / HU-15)</h2>
        <p>
          Actualice sus datos personales. DNI y correo electrónico no pueden
          modificarse desde esta opción.
        </p>

        {error !== null && (
          <p className="error" role="alert">{error}</p>
        )}
        {message !== null && (
          <p className="success" role="status">{message}</p>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="perfil-first">Nombres</label>
            <input
              id="perfil-first"
              autoComplete="given-name"
              value={first_name}
              onChange={(event) => setFirstName(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="perfil-last">Apellidos</label>
            <input
              id="perfil-last"
              autoComplete="family-name"
              value={last_name}
              onChange={(event) => setLastName(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="perfil-phone">Teléfono</label>
            <input
              id="perfil-phone"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="perfil-dni">DNI (no editable)</label>
            <input id="perfil-dni" value={user?.dni ?? ""} disabled />
          </div>

          <div className="field">
            <label htmlFor="perfil-email">Correo electrónico (no editable)</label>
            <input id="perfil-email" value={user?.email ?? ""} disabled />
          </div>

          <hr />

          <p className="form-note">
            Si desea cambiar su contraseña, complete ambos campos. En caso
            contrario, déjelos vacíos.
          </p>

          <div className="field">
            <label htmlFor="perfil-cur">Contraseña actual</label>
            <input
              id="perfil-cur"
              type="password"
              autoComplete="current-password"
              value={current_password}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="perfil-new">Nueva contraseña (mínimo 8 caracteres)</label>
            <input
              id="perfil-new"
              type="password"
              autoComplete="new-password"
              minLength={8}
              value={new_password}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </div>

          <button type="submit" className="button button--primary" disabled={busy}>
            {busy ? "Guardando…" : "Guardar cambios"}
          </button>
        </form>
      </section>
    </>
  );
}