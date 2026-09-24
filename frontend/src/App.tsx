import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import { GuestRoute } from "./auth/GuestRoute";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AdminUsersPage } from "./pages/AdminUsers";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { DashboardHome, DashboardLayout } from "./pages/Dashboard";
import { HomePage } from "./pages/Home";

export default function App(): JSX.Element {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardHome />} />
            <Route
              path="admin/usuarios"
              element={
                <ProtectedRoute roles={["administrador"]}>
                  <AdminUsersPage />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/registro"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />
          <Route
            path="/inicio"
            element={
              <GuestRoute>
                <HomePage />
              </GuestRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}