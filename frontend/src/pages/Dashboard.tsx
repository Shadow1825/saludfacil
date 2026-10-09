import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { SkipLink } from "../components/SkipLink";
import { ServiceIcon } from "../components/ServiceIcon";
import type { ServiceIconName } from "../components/ServiceIcon";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABEL } from "../types/auth";

interface Acceso {
  titulo: string;
  descripcion: string;
  to: string;
  icono: ServiceIconName;
}

const ACCESOS_POR_ROL: Record<string, Acceso[]> = {
  paciente: [
    {
      titulo: "Disponibilidad",
      descripcion: "Consulte los horarios disponibles de los profesionales por especialidad.",
      to: "/disponibilidad",
      icono: "clock",
    },
    {
      titulo: "Reservar cita",
      descripcion: "Reserve su atención médica eligiendo especialidad, profesional, fecha y horario.",
      to: "/reservar",
      icono: "calendar-plus",
    },
    {
      titulo: "Mis citas",
      descripcion: "Revise sus próximas citas y cancele las que no pueda asistir.",
      to: "/mis-citas",
      icono: "calendar-check",
    },
    {
      titulo: "Triaje inicial",
      descripcion: "Registre sus síntomas y obtenga una clasificación inicial orientativa.",
      to: "/triaje",
      icono: "activity",
    },
    {
      titulo: "Mi perfil",
      descripcion: "Actualice sus datos de contacto.",
      to: "/perfil",
      icono: "user",
    },
  ],
  profesional: [
    {
      titulo: "Disponibilidad",
      descripcion: "Consulte la agenda y los horarios de atención de los profesionales.",
      to: "/disponibilidad",
      icono: "clock",
    },
    {
      titulo: "Mis citas",
      descripcion: "Revise las citas asignadas a su atención.",
      to: "/profesional/citas",
      icono: "calendar-check",
    },
    {
      titulo: "Triaje de citas",
      descripcion: "Consulte la clasificación inicial de sus citas.",
      to: "/profesional/triajes",
      icono: "file-text",
    },
  ],
  administrador: [
    {
      titulo: "Usuarios",
      descripcion: "Administre las cuentas de los usuarios del sistema.",
      to: "/admin/usuarios",
      icono: "users",
    },
    {
      titulo: "Profesionales",
      descripcion: "Administre los profesionales y las especialidades médicas.",
      to: "/admin/profesionales",
      icono: "user-check",
    },
    {
      titulo: "Especialidades",
      descripcion: "Gestione el catálogo de especialidades médicas.",
      to: "/admin/especialidades",
      icono: "grid",
    },
    {
      titulo: "Horarios",
      descripcion: "Gestione la agenda de atención de cada profesional.",
      to: "/admin/horarios",
      icono: "clock",
    },
    {
      titulo: "Citas",
      descripcion: "Supervise las citas registradas en el sistema.",
      to: "/admin/citas",
      icono: "calendar",
    },
    {
      titulo: "Revisión de triajes",
      descripcion: "Revise o descarte las clasificaciones iniciales registradas.",
      to: "/admin/triajes",
      icono: "file-text",
    },
  ],
};

const NAV_POR_ROL: Record<string, { to: string; label: string; icono: ServiceIconName; end?: boolean }[]> = {
  paciente: [
    { to: "/", label: "Inicio", icono: "home", end: true },
    { to: "/disponibilidad", label: "Disponibilidad", icono: "clock" },
    { to: "/reservar", label: "Reservar cita", icono: "calendar-plus" },
    { to: "/mis-citas", label: "Mis citas", icono: "calendar-check" },
    { to: "/triaje", label: "Triaje", icono: "activity" },
    { to: "/perfil", label: "Mi perfil", icono: "user" },
  ],
  profesional: [
    { to: "/", label: "Inicio", icono: "home", end: true },
    { to: "/disponibilidad", label: "Disponibilidad", icono: "clock" },
    { to: "/profesional/citas", label: "Mis citas", icono: "calendar-check" },
    { to: "/profesional/triajes", label: "Triaje de citas", icono: "file-text" },
  ],
  administrador: [
    { to: "/", label: "Inicio", icono: "home", end: true },
    { to: "/admin/usuarios", label: "Usuarios", icono: "users" },
    { to: "/admin/profesionales", label: "Profesionales", icono: "user-check" },
    { to: "/admin/especialidades", label: "Especialidades", icono: "grid" },
    { to: "/admin/horarios", label: "Horarios", icono: "clock" },
    { to: "/admin/citas", label: "Citas", icono: "calendar" },
    { to: "/admin/triajes", label: "Triajes", icono: "file-text" },
  ],
};

export function DashboardLayout(): JSX.Element {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout(): Promise<void> {
    await logout();
    navigate("/login", { replace: true });
  }

  const perfil = user?.role;
  const enlaces = user ? (NAV_POR_ROL[user.role] ?? []) : [];

  return (
    <div className="shell">
      <SkipLink />
      <header role="banner">
        <div className="site-header">
          <div className="site-header__row">
            <div className="site-header__brand">
              <ServiceIcon name="home" size={34} />
              <div>
                <p className="brand-title">
                  <Link to="/">SaludFácil</Link>
                </p>
                <p className="brand-subtitle">Citas médicas y triaje en línea</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar" aria-label="Panel de navegación">
          {user && (
            <div className="sidebar__profile">
              <span className="sidebar__avatar" aria-hidden="true">
                {(user.first_name ?? "").charAt(0).toUpperCase()}
              </span>
              <div>
                <p className="sidebar__name">
                  {user.first_name} {user.last_name}
                </p>
                <p className="sidebar__role">{perfil ? ROLE_LABEL[perfil] : ""}</p>
              </div>
            </div>
          )}

          <nav aria-label="Navegación principal" className="sidebar__nav">
            {enlaces.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? "active" : undefined)}
              >
                <ServiceIcon name={item.icono} size={19} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>

          <button
            type="button"
            className="button button--secondary sidebar__logout"
            onClick={() => void handleLogout()}
          >
            Cerrar sesión
          </button>
        </aside>

        <main id="main" className="content layout__main" role="main" tabIndex={-1}>
          <Outlet />
        </main>
      </div>

      <footer className="site-footer" role="contentinfo">
        <div className="site-footer__cols">
          <div>
            <p className="site-footer__title">SaludFácil</p>
            <p>Sistema de gestión de citas médicas, agenda profesional y triaje inicial orientativo.</p>
            <p>Plataforma de demostración con fines institucionales.</p>
          </div>
          <div>
            <p className="site-footer__title">Atención</p>
            <p>Lunes a viernes: 7:00 a. m. – 7:00 p. m.</p>
            <p>Sábados y domingos: 7:00 a. m. – 1:00 p. m.</p>
          </div>
          <div>
            <p className="site-footer__title">Contacto</p>
            <p>Clínica Comunitaria del Norte S.A.C.</p>
            <p>Av. Los Eucaliptos 245 · Lima · Perú</p>
          </div>
        </div>
        <div className="site-footer__bottom">
          © 2026 SaludFácil · Clínica Comunitaria del Norte S.A.C. · Todos los derechos reservados.
        </div>
      </footer>
    </div>
  );
}

export function DashboardHome(): JSX.Element {
  const { user } = useAuth();
  const accesos = user ? (ACCESOS_POR_ROL[user.role] ?? []) : [];

  return (
    <>
      <section aria-labelledby="titulo-inicio">
        <h2 id="titulo-inicio">Inicio</h2>
        <p>
          Bienvenido/a, <strong>{user ? user.first_name : ""}</strong>. Desde aquí puede acceder a
          los servicios que SaludFácil pone a su disposición como{" "}
          <strong>{user ? ROLE_LABEL[user.role] : ""}</strong>.
        </p>
      </section>

      {accesos.length > 0 && (
        <div className="services" aria-label="Accesos rápidos">
          {accesos.map((item) => (
            <article className="service-card" key={item.titulo}>
              <div className="service-card__icon">
                <ServiceIcon name={item.icono} />
              </div>
              <h3 className="service-card__title">{item.titulo}</h3>
              <p className="service-card__text">{item.descripcion}</p>
              <Link className="button button--secondary button--small service-card__action" to={item.to}>
                Abrir
              </Link>
            </article>
          ))}
        </div>
      )}
    </>
  );
}