import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./Services/Context/AuthContext";
import { AnalysisProvider } from "./Services/Context/AnalyseCont";
import { Dashboard } from "./Pages/Dashboard";
import { Login } from "./Pages/Login";
import { Register } from "./Pages/Register";
import { TeamManagement } from "./Pages/TeamManagement";
import { OrgDashboard } from "./Pages/OrgDashboard";
import { AdminDashboard } from "./Pages/AdminDashboard";
import type { ReactNode } from "react";

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen bg-dark flex items-center justify-center text-gray-400">Chargement...</div>;
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
};

const RoleRoute = ({ children, allowed }: { children: ReactNode; allowed: (role: string) => boolean }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen bg-dark flex items-center justify-center text-gray-400">Chargement...</div>;
  if (!user) return <Navigate to="/login" />;
  if (!allowed(user.role)) return <Navigate to="/" />;
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AnalysisProvider>
                  <Dashboard />
                </AnalysisProvider>
              </ProtectedRoute>
            }
          />
          <Route
            path="/equipe"
            element={
              <RoleRoute allowed={(r) => ["super_admin", "org_admin", "admin"].includes(r)}>
                <TeamManagement />
              </RoleRoute>
            }
          />
          <Route
            path="/organisation"
            element={
              <ProtectedRoute>
                <OrgDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <RoleRoute allowed={(r) => r === "super_admin"}>
                <AdminDashboard />
              </RoleRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
