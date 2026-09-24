import { Link, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { ROLE_LABEL } from "../types/auth";

function DashboardLink({ to, label }: { to: string; label: string }): JSX.Element {
  return <Link to={to}>{label}</Link>;
}

export function DashboardLayout(): JSX.Element {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout(): Promise<void> {
    await logout();
    navigate("/login", { replace: true });
  }

  const perfil = user?.role;

  return (
    <div className="shell">
      <header className="banner banner--compact" role="banner">
        <div className="banner__row">
          <div>
            <h1>SaludFácil</h1>
            <p className="banner__subtitle">
              {user ? `Hola, ${user.first_name}` : "Bienvenido"}
            </p>
          </div>
          <div className="banner__actions">
            {perfil !== undefined && (
              <span className="badge">{ROLE_LABEL[perfil]}</span>
            )}
            <button
              type="button"
              className="button button--ghost"
              onClick={() => void handleLogout()}
            >
              Cerrar sesión
            </button>
          </div>
        </div>
        <nav aria-label="Navegación principal" className="nav">
          {perfil === "paciente" && (
            <>
              <DashboardLink to="/" label="Inicio" />
              <DashboardLink to="/disponibilidad" label="Disponibilidad" />
              <span className="nav__pending">Reservar cita (FASE 4)</span>
              <span className="nav__pending">Mis citas (FASE 4)</span>
              <span className="nav__pending">Triaje (FASE 5)</span>
              <span className="nav__pending">Mi perfil (FASE 6)</span>
            </>
          )}

          {perfil === "profesional" && (
            <>
              <DashboardLink to="/" label="Inicio" />
              <span className="nav__pending">Disponibilidad (FASE 5)</span>
              <span className="nav__pending">Mis citas (FASE 4-6)</span>
              <span className="nav__pending">Resultado de triaje (FASE 5)</span>
            </>
          )}

          {perfil === "administrador" && (
            <>
              <DashboardLink to="/" label="Inicio" />
              <DashboardLink to="/admin/usuarios" label="Usuarios" />
              <DashboardLink to="/admin/profesionales" label="Profesionales" />
              <DashboardLink to="/admin/especialidades" label="Especialidades" />
              <DashboardLink to="/admin/horarios" label="Horarios" />
              <span className="nav__pending">Citas (FASE 4/6)</span>
            </>
          )}
        </nav>
      </header>

      <main id="main" className="content" role="main">
        <Outlet />
      </main>

      <footer className="footer" role="contentinfo">
        <p>
          SaludFácil — Proyecto académico con datos ficticios (Ley N.° 29733).
        </p>
      </footer>
    </div>
  );
}

export function DashboardHome(): JSX.Element {
  const { user } = useAuth();

  const tareasPorRol: Record<string, string[]> = {
    paciente: [
      "Registrarse e iniciar sesión (FASE 2, completado)",
      "Consulta de disponibilidad (FASE 3, completado)",
      "Reserva y cancelación de citas (FASE 4)",
      "Triaje inicial (FASE 5)",
      "Actualización de datos (FASE 6)",
    ],
    profesional: [
      "Consultar citas asignadas (FASE 4-6)",
      "Consultar resultado de triaje (FASE 5)",
      "Actualizar estado de atención (FASE 6)",
    ],
    administrador: [
      "Gestión de cuentas de usuario (FASE 2, completado)",
      "Gestión de profesionales, especialidades y horarios (FASE 3, completado)",
      "Gestión de citas (FASE 4/6)",
    ],
  };

  const listado = user ? (tareasPorRol[user.role] ?? []) : [];

  return (
    <>
      <section aria-labelledby="titulo-inicio">
        <h2 id="titulo-inicio">Inicio</h2>
        <p>
          Su sesión está activa con el rol <strong>{user ? ROLE_LABEL[user.role] : ""}</strong>.
          Las siguientes capacidades se habilitan a medida que avanza el proyecto.
        </p>
        <ul>
          {listado.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </>
  );
}