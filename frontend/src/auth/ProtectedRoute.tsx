import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import type { Role } from "../types/auth";

/**
 * Protege una ruta: requiere sesión activa (RF-19 / HU-12) y, opcionalmente,
 * un rol específico (CA-12.2 / CA-12.3). La seguridad real la garantiza la API.
 */
export function ProtectedRoute({
  children,
  roles,
}: {
  children: JSX.Element;
  roles?: Role[];
}): JSX.Element {
  const { status, user } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <main className="content" role="main">
        <p role="status" aria-live="polite">
          Cargando sesión…
        </p>
      </main>
    );
  }

  if (status !== "authenticated" || user === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (roles !== undefined && !roles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
}