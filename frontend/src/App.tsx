import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import { GuestRoute } from "./auth/GuestRoute";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { AdminCitasPage } from "./pages/AdminCitas";
import { AdminProfessionalsPage } from "./pages/AdminProfessionals";
import { AdminSchedulesPage } from "./pages/AdminSchedules";
import { AdminSpecialtiesPage } from "./pages/AdminSpecialties";
import { AdminUsersPage } from "./pages/AdminUsers";
import { LoginPage, RegisterPage } from "./pages/AuthPages";
import { DashboardHome, DashboardLayout } from "./pages/Dashboard";
import { DisponibilidadPage } from "./pages/Disponibilidad";
import { HomePage } from "./pages/Home";
import { MisCitasPage } from "./pages/MisCitas";
import { MisTriajesPage } from "./pages/MisTriajes";
import { ReservarCitaPage } from "./pages/ReservarCita";
import { TriajePage } from "./pages/Triaje";

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
              path="disponibilidad"
              element={
                <ProtectedRoute roles={["paciente", "profesional"]}>
                  <DisponibilidadPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="reservar"
              element={
                <ProtectedRoute roles={["paciente"]}>
                  <ReservarCitaPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="mis-citas"
              element={
                <ProtectedRoute roles={["paciente"]}>
                  <MisCitasPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="triaje"
              element={
                <ProtectedRoute roles={["paciente"]}>
                  <TriajePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="profesional/triajes"
              element={
                <ProtectedRoute roles={["profesional"]}>
                  <MisTriajesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/citas"
              element={
                <ProtectedRoute roles={["administrador"]}>
                  <AdminCitasPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/usuarios"
              element={
                <ProtectedRoute roles={["administrador"]}>
                  <AdminUsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/profesionales"
              element={
                <ProtectedRoute roles={["administrador"]}>
                  <AdminProfessionalsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/especialidades"
              element={
                <ProtectedRoute roles={["administrador"]}>
                  <AdminSpecialtiesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/horarios"
              element={
                <ProtectedRoute roles={["administrador"]}>
                  <AdminSchedulesPage />
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