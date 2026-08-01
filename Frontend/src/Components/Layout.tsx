import type { ReactNode } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { useAuth } from "../Services/Context/AuthContext";
import { Logo } from "./Logo";

export const Layout = ({ children }: { children: ReactNode }) => {
  const { user, logout, isOrgAdmin, isSuperAdmin } = useAuth();
  const navigate = useNavigate();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 rounded-lg text-sm transition-colors ${
      isActive ? "bg-cyan-500/10 text-cyan-400" : "text-gray-400 hover:text-white"
    }`;

  return (
    <div className="min-h-screen p-6 md:p-12">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div className="flex items-center gap-2">
          <Logo />
        </div>

        <nav className="flex flex-wrap items-center gap-1">
          <NavLink to="/" className={linkClass} end>Audit</NavLink>
          <NavLink to="/organisation" className={linkClass}>Organisation</NavLink>
          {(isOrgAdmin || isSuperAdmin) && (
            <NavLink to="/equipe" className={linkClass}>Équipe</NavLink>
          )}
          {isSuperAdmin && (
            <NavLink to="/admin" className={linkClass}>Administration</NavLink>
          )}
        </nav>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-white">{user?.full_name}</p>
            <p className="text-xs text-gray-500">{user?.role}</p>
          </div>
          <button
            onClick={() => { logout(); navigate("/login"); }}
            className="text-sm text-gray-500 hover:text-danger transition-colors"
          >
            Déconnexion
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto">{children}</div>
    </div>
  );
};
