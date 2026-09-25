import { Link, Outlet, useNavigate } from "react-router-dom";

import { SkipLink } from "../components/SkipLink";
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
      <SkipLink />
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
              <DashboardLink to="/reservar" label="Reservar cita" />
              <DashboardLink to="/mis-citas" label="Mis citas" />
              <DashboardLink to="/triaje" label="Triaje" />
              <DashboardLink to="/perfil" label="Mi perfil" />
            </>
          )}

          {perfil === "profesional" && (
            <>
              <DashboardLink to="/" label="Inicio" />
              <DashboardLink to="/disponibilidad" label="Disponibilidad" />
              <DashboardLink to="/profesional/citas" label="Mis citas" />
              <DashboardLink to="/profesional/triajes" label="Triaje de citas" />
            </>
          )}

          {perfil === "administrador" && (
            <>
              <DashboardLink to="/" label="Inicio" />
              <DashboardLink to="/admin/usuarios" label="Usuarios" />
              <DashboardLink to="/admin/profesionales" label="Profesionales" />
              <DashboardLink to="/admin/especialidades" label="Especialidades" />
              <DashboardLink to="/admin/horarios" label="Horarios" />
              <DashboardLink to="/admin/citas" label="Citas" />
              <DashboardLink to="/admin/triajes" label="Triajes" />
            </>
          )}
        </nav>
      </header>

      <main id="main" className="content" role="main" tabIndex={-1}>
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

interface Acceso {
  titulo: string;
  descripcion: string;
  to: string;
}

const ACCESOS_POR_ROL: Record<string, Acceso[]> = {
  paciente: [
    {
      titulo: "Disponibilidad",
      descripcion: "Consulte horarios disponibles de los profesionales por especialidad.",
      to: "/disponibilidad",
    },
    {
      titulo: "Reservar cita",
      descripcion: "Reserve su atención médica eligiendo fecha y horario.",
      to: "/reservar",
    },
    {
      titulo: "Mis citas",
      descripcion: "Revise sus próximas citas y cancele las que no pueda asistir.",
      to: "/mis-citas",
    },
    {
      titulo: "Triaje inicial",
      descripcion: "Registre sus síntomas y obtenga una clasificación inicial orientativa.",
      to: "/triaje",
    },
    {
      titulo: "Mi perfil",
      descripcion: "Actualice sus datos de contacto.",
      to: "/perfil",
    },
  ],
  profesional: [
    {
      titulo: "Disponibilidad",
      descripcion: "Consulte la agenda y los horarios de atención de los profesionales.",
      to: "/disponibilidad",
    },
    {
      titulo: "Mis citas",
      descripcion: "Revise las citas asignadas a su atención.",
      to: "/profesional/citas",
    },
    {
      titulo: "Triaje de citas",
      descripcion: "Consulte la clasificación inicial de sus citas.",
      to: "/profesional/triajes",
    },
  ],
  administrador: [
    {
      titulo: "Usuarios",
      descripcion: "Administre las cuentas de los usuarios del sistema.",
      to: "/admin/usuarios",
    },
    {
      titulo: "Profesionales",
      descripcion: "Administre los profesionales y las especialidades médicas.",
      to: "/admin/profesionales",
    },
    {
      titulo: "Horarios",
      descripcion: "Gestione la agenda de atención de cada profesional.",
      to: "/admin/horarios",
    },
    {
      titulo: "Citas",
      descripcion: "Supervise las citas registradas en el sistema.",
      to: "/admin/citas",
    },
    {
      titulo: "Revisión de triajes",
      descripcion: "Revise o descarte las clasificaciones iniciales registradas.",
      to: "/admin/triajes",
    },
  ],
};

export function DashboardHome(): JSX.Element {
  const { user } = useAuth();
  const accesos = user ? (ACCESOS_POR_ROL[user.role] ?? []) : [];

  return (
    <>
      <section aria-labelledby="titulo-inicio">
        <h2 id="titulo-inicio">Inicio</h2>
        <p>
          Bienvenido/a, <strong>{user ? user.first_name : ""}</strong>. Desde aquí puede
          acceder a los servicios que SaludFácil pone a su disposición como{" "}
          <strong>{user ? ROLE_LABEL[user.role] : ""}</strong>.
        </p>
      </section>

      {accesos.length > 0 && (
        <div className="health" aria-label="Accesos rápidos">
          {accesos.map((item) => (
            <div key={item.titulo}>
              <p className="banner__eyebrow">{item.titulo}</p>
              <p>{item.descripcion}</p>
              <Link className="button button--secondary button--small" to={item.to}>
                Abrir
              </Link>
            </div>
          ))}
        </div>
      )}
    </>
  );
}