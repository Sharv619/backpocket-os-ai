import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { StaffAuthProvider, useStaffAuth } from "@/hooks/useStaffAuth";
import { DriverAuthProvider, useDriverAuth } from "@/hooks/useDriverAuth";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import { DashboardLogin } from "@/pages/dashboard/Login";
import { DashboardLayout } from "@/pages/dashboard/Layout";
import { DashboardBoard } from "@/pages/dashboard/Board";
import { DashboardDrivers } from "@/pages/dashboard/Drivers";
import { DashboardHistory } from "@/pages/dashboard/History";
import { DriverLogin } from "@/pages/driver/Login";
import { DriverLayout } from "@/pages/driver/Layout";
import { DriverHome } from "@/pages/driver/Home";
import { DriverHistory } from "@/pages/driver/History";

function DashboardRoutes() {
  const { user, loading } = useStaffAuth();
  return (
    <Routes>
      <Route path="login" element={<DashboardLogin />} />
      <Route
        element={
          <ProtectedRoute isAllowed={Boolean(user)} isLoading={loading} redirectTo="/dashboard/login">
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="board" element={<DashboardBoard />} />
        <Route path="drivers" element={<DashboardDrivers />} />
        <Route path="history" element={<DashboardHistory />} />
        <Route index element={<Navigate to="board" replace />} />
      </Route>
    </Routes>
  );
}

function DriverRoutes() {
  const { driver, loading } = useDriverAuth();
  return (
    <Routes>
      <Route path="login" element={<DriverLogin />} />
      <Route
        element={
          <ProtectedRoute isAllowed={Boolean(driver)} isLoading={loading} redirectTo="/driver/login">
            <DriverLayout />
          </ProtectedRoute>
        }
      >
        <Route path="home" element={<DriverHome />} />
        <Route path="history" element={<DriverHistory />} />
        <Route index element={<Navigate to="home" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <StaffAuthProvider>
        <DriverAuthProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard/*" element={<DashboardRoutes />} />
            <Route path="/driver/*" element={<DriverRoutes />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </DriverAuthProvider>
      </StaffAuthProvider>
    </BrowserRouter>
  );
}
