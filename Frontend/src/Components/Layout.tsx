import type { ReactNode } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { useAuth } from "../Services/Context/AuthContext";
import { Logo } from "./Logo";

export const Layout = ({ children }: { children: ReactNode }) => {
  const { user, logout, isOrgAdmin, isSuperAdmin } = useAuth();
  const navigate = useNavigate();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 rounded-xl text-sm font-medium transition-all ${
      isActive
        ? "bg-cyan-500/15 text-cyan-300 shadow-glow"
        : "text-gray-400 hover:text-white hover:bg-white/5"
    }`;

  const initials = (user?.full_name || user?.email || "?")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 glass border-x-0 border-t-0 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 md:px-6 py-3 flex flex-wrap items-center justify-between gap-3">
          <NavLink to="/" className="flex items-center gap-2 shrink-0">
            <Logo size={36} />
          </NavLink>

          <nav className="flex flex-wrap items-center gap-1 order-3 md:order-2 w-full md:w-auto">
            <NavLink to="/" className={linkClass} end>Audit</NavLink>
            <NavLink to="/organisation" className={linkClass}>Organisation</NavLink>
            {(isOrgAdmin || isSuperAdmin) && (
              <NavLink to="/equipe" className={linkClass}>Équipe</NavLink>
            )}
            {isSuperAdmin && (
              <NavLink to="/admin" className={linkClass}>Administration</NavLink>
            )}
          </nav>

          <div className="flex items-center gap-3 order-2 md:order-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500/80 to-blue-600/80 flex items-center justify-center text-sm font-bold text-white shadow-glow">
                {initials}
              </div>
              <div className="hidden sm:block text-right leading-tight">
                <p className="text-sm font-medium text-white">{user?.full_name || user?.email}</p>
                <p className="text-[11px] text-cyan-400/80 capitalize">{user?.role?.replace("_", " ")}</p>
              </div>
            </div>
            <button
              onClick={() => { logout(); navigate("/login"); }}
              title="Déconnexion"
              className="btn-ghost !px-3 !py-2 text-gray-400 hover:text-danger"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              <span className="hidden sm:inline">Déconnexion</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-8">
        <div className="animate-fadeIn">{children}</div>
      </main>

      <footer className="max-w-7xl mx-auto px-6 pb-8 text-center text-xs text-gray-600">
        LucidAI — Plateforme d'audit financier intelligent
      </footer>
    </div>
  );
};
