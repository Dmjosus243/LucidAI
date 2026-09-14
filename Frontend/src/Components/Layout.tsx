import { useState } from "react";
import type { ReactNode } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import { useAuth } from "../Services/Context/AuthContext";
import { Logo } from "./Logo";

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  end?: boolean;
}

const icon = (d: string) => (
  <svg className="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round">
    <path strokeLinecap="round" strokeLinejoin="round" d={d} />
  </svg>
);

export const Layout = ({ children }: { children: ReactNode }) => {
  const { user, logout, isOrgAdmin, isSuperAdmin } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const initials = (user?.full_name || user?.email || "?")
    .split(" ")
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const NAV: NavItem[] = [
    { to: "/", label: "Audit", icon: icon("M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"), end: true },
    { to: "/ocr", label: "Documents (OCR)", icon: icon("M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z") },
    { to: "/rapprochement", label: "Rapprochement", icon: icon("M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5") },
    { to: "/assistant", label: "Assistant", icon: icon("M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z") },
    { to: "/banque", label: "Banque", icon: icon("M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z") },
    { to: "/organisation", label: "Organisation", icon: icon("M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21") },
    ...(isOrgAdmin || isSuperAdmin ? [{ to: "/equipe", label: "Équipe", icon: icon("M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z") }] : []),
    ...(isSuperAdmin ? [{ to: "/admin", label: "Administration", icon: icon("M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.623 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z") }] : []),
  ];

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors border-l-2 ${
      isActive
        ? "bg-cyan-500/10 text-cyan-300 border-l-cyan-400"
        : "text-gray-400 hover:text-white hover:bg-white/5 border-l-transparent"
    }`;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen lg:flex">
      {/* Voile mobile */}
      {open && <div className="fixed inset-0 z-40 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 shrink-0 flex flex-col bg-dark2 border-r border-white/5 transform transition-transform duration-200
          lg:sticky lg:top-0 lg:h-screen lg:transform-none lg:z-auto ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <NavLink to="/" onClick={() => setOpen(false)}>
            <Logo size={34} />
          </NavLink>
          <button onClick={() => setOpen(false)} className="lg:hidden text-gray-400 hover:text-white" title="Fermer le menu">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={linkClass}
              onClick={() => setOpen(false)}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-white/5 space-y-1">
          <p className="text-[11px] text-gray-500 font-medium">Comptabilité & Audit</p>
          <p className="text-[10px] text-gray-600">Logiciel professionnel v2</p>
        </div>
      </aside>

      {/* Zone principale */}
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-30 bg-dark/85 backdrop-blur border-b border-white/5">
          <div className="flex items-center justify-between px-4 md:px-6 py-3 gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <button onClick={() => setOpen(true)} className="lg:hidden btn-ghost !p-2" title="Ouvrir le menu">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
              </button>
              <span className="text-xs text-gray-500 truncate">
                {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500/80 to-blue-600/80 flex items-center justify-center text-sm font-bold text-white">
                  {initials}
                </div>
                <div className="text-right leading-tight">
                  <p className="text-sm font-medium text-white">{user?.full_name || user?.email}</p>
                  <p className="text-[11px] text-cyan-400/80 capitalize">{user?.role?.replace("_", " ")}</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
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

        <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-8 py-6 md:py-8">
          <div className="animate-fadeIn">{children}</div>
        </main>

        <footer className="px-6 pb-6 text-center text-xs text-gray-600">
          LucidAI — Plateforme d'audit financier intelligent
        </footer>
      </div>
    </div>
  );
};