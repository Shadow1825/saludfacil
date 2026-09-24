import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

/**
 * Impide acceder a Login/Registro si ya existe una sesión activa.
 */
export function GuestRoute({ children }: { children: JSX.Element }): JSX.Element {
  const { status } = useAuth();
  if (status === "loading") {
    return (
      <main className="content" role="main">
        <p role="status" aria-live="polite">
          Cargando sesión…
        </p>
      </main>
    );
  }
  if (status === "authenticated") {
    return <Navigate to="/" replace />;
  }
  return children;
}