import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./Services/Context/AuthContext";
import { AnalysisProvider } from "./Services/Context/AnalyseCont";
import { Dashboard } from "./Pages/Dashboard";
import { Landing } from "./Pages/Landing";
import { Login } from "./Pages/Login";
import { Register } from "./Pages/Register";
import { ForgotPassword } from "./Pages/ForgotPassword";
import { TeamManagement } from "./Pages/TeamManagement";
import { OrgDashboard } from "./Pages/OrgDashboard";
import { AdminDashboard } from "./Pages/AdminDashboard";
import { Subscription } from "./Pages/Subscription";
import { DocumentsOCR } from "./Pages/DocumentsOCR";
import { Reconciliation } from "./Pages/Reconciliation";
import { Assistant } from "./Pages/Assistant";
import { Banking } from "./Pages/Banking";
import type { ReactNode } from "react";

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen bg-dark flex items-center justify-center text-gray-400">Chargement...</div>;
  if (!user) return <Navigate to="/" />;
  return <>{children}</>;
};

const RoleRoute = ({ children, allowed }: { children: ReactNode; allowed: (role: string) => boolean }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen bg-dark flex items-center justify-center text-gray-400">Chargement...</div>;
  if (!user) return <Navigate to="/" />;
  if (!allowed(user.role)) return <Navigate to="/" />;
  return <>{children}</>;
};

// Page d'accueil : landing publique si déconnecté, Dashboard si connecté
const IndexRoute = () => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen bg-dark flex items-center justify-center text-gray-400">Chargement...</div>;
  if (!user) return <Landing />;
  return (
    <AnalysisProvider>
      <Dashboard />
    </AnalysisProvider>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<IndexRoute />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
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
          <Route
            path="/abonnement"
            element={
              <ProtectedRoute>
                <Subscription />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ocr"
            element={
              <ProtectedRoute>
                <DocumentsOCR />
              </ProtectedRoute>
            }
          />
          <Route
            path="/rapprochement"
            element={
              <ProtectedRoute>
                <Reconciliation />
              </ProtectedRoute>
            }
          />
          <Route
            path="/assistant"
            element={
              <ProtectedRoute>
                <Assistant />
              </ProtectedRoute>
            }
          />
          <Route
            path="/banque"
            element={
              <ProtectedRoute>
                <Banking />
              </ProtectedRoute>
            }
          />
          <Route path="/*" element={<IndexRoute />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
