import type { ReactNode } from "react";
import { Logo } from "./Logo";

export const AuthShell = ({ title, children }: { title: string; children: ReactNode }) => {
  return (
    <div className="relative min-h-screen flex items-center justify-center p-6 overflow-hidden">
      <div className="pointer-events-none absolute -top-32 -right-32 w-[420px] h-[420px] rounded-full bg-cyan-500/10 blur-3xl animate-pulseGlow" />
      <div className="pointer-events-none absolute -bottom-40 -left-32 w-[460px] h-[460px] rounded-full bg-blue-500/10 blur-3xl animate-pulseGlow" style={{ animationDelay: "1.5s" }} />
      <div className="pointer-events-none absolute top-1/3 left-1/4 w-2 h-2 rounded-full bg-cyan-400/40 animate-float" />
      <div className="pointer-events-none absolute top-2/3 right-1/4 w-3 h-3 rounded-full bg-cyan-300/30 animate-float" style={{ animationDelay: "2s" }} />

      <div className="relative w-full max-w-md animate-fadeIn">
        <div className="card p-8 md:p-10">
          <div className="flex flex-col items-center gap-3 mb-8">
            <Logo size={48} />
            <p className="text-[11px] tracking-[0.35em] uppercase text-gray-500">Audit Intelligence</p>
          </div>
          <h2 className="text-xl font-bold text-white mb-1 text-center">{title}</h2>
          {children}
        </div>
      </div>
    </div>
  );
};
