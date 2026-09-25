import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { SkipLink } from "../components/SkipLink";
import { useAuth } from "../auth/AuthContext";

export function LoginPage(): JSX.Element {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !password) {
      setError("Ingrese su correo electrónico y contraseña.");
      return;
    }
    setBusy(true);
    try {
      await login({ email: email.trim(), password });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar sesión.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SkipLink />
      <main id="main" className="content auth" role="main" tabIndex={-1}>
        <section className="card card--narrow" aria-labelledby="titulo-login">
        <h1 id="titulo-login">Iniciar sesión</h1>
        <p>
          Acceda a SaludFácil con su correo electrónico y contraseña.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Correo electrónico</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="password">Contraseña</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          {error !== null && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="button button--primary" disabled={busy}>
            {busy ? "Ingresando…" : "Ingresar"}
          </button>
        </form>

        <p className="auth-links">
          ¿No tiene una cuenta? <Link to="/registro">Regístrese aquí</Link>
        </p>
      </section>
      </main>
    </>
  );
}

export function RegisterPage(): JSX.Element {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [values, setValues] = useState({
    first_name: "",
    last_name: "",
    dni: "",
    email: "",
    phone: "",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update(field: keyof typeof values, value: string): void {
    setValues((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    setError(null);
    const vacios = !values.first_name.trim() || !values.last_name.trim() || !values.dni.trim() ||
      !values.email.trim() || !values.phone.trim() || !values.password;
    if (vacios) {
      setError("Todos los campos son obligatorios.");
      return;
    }
    if (!/^\d{8}$/.test(values.dni.trim())) {
      setError("El DNI debe contener exactamente 8 dígitos.");
      return;
    }
    setBusy(true);
    try {
      await register(values);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo completar el registro.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <SkipLink />
      <main id="main" className="content auth" role="main" tabIndex={-1}>
        <section className="card card--narrow" aria-labelledby="titulo-registro">
        <h1 id="titulo-registro">Crear cuenta de paciente</h1>
        <p>Complete el formulario para registrarse en SaludFácil.</p>

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="first_name">Nombres</label>
            <input
              id="first_name"
              autoComplete="given-name"
              required
              value={values.first_name}
              onChange={(event) => update("first_name", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="last_name">Apellidos</label>
            <input
              id="last_name"
              autoComplete="family-name"
              required
              value={values.last_name}
              onChange={(event) => update("last_name", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="dni">DNI (8 dígitos)</label>
            <input
              id="dni"
              inputMode="numeric"
              maxLength={8}
              autoComplete="off"
              required
              value={values.dni}
              onChange={(event) => update("dni", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="email">Correo electrónico</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={values.email}
              onChange={(event) => update("email", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="phone">Teléfono</label>
            <input
              id="phone"
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              required
              value={values.phone}
              onChange={(event) => update("phone", event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="password">Contraseña (mínimo 8 caracteres)</label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={values.password}
              onChange={(event) => update("password", event.target.value)}
            />
          </div>

          {error !== null && (
            <p className="error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="button button--primary" disabled={busy}>
            {busy ? "Registrando…" : "Registrarse"}
          </button>
        </form>

        <p className="auth-links">
          ¿Ya tiene una cuenta? <Link to="/login">Inicie sesión</Link>
        </p>
      </section>
      </main>
    </>
  );
}