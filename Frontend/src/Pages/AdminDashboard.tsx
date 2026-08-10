import { useEffect, useState } from "react";
import { Layout } from "../Components/Layout";
import { getAdminStats, getUsers, getAuditLogs } from "../Services/api";
import type { AdminStats, User, AuditLogItem } from "../Services/api";

const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  org_admin: "Admin Orga",
  admin: "Admin",
  manager: "Manager",
  auditor: "Auditeur",
};

const roleBadge = (role: string) =>
  role === "super_admin"
    ? "badge-critical"
    : role === "org_admin" || role === "admin"
    ? "badge-info"
    : role === "manager"
    ? "badge-warning"
    : "badge-low";

export const AdminDashboard = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getAdminStats().then((res) => setStats(res.data)).catch((err) => setError(err?.response?.data?.detail || "Erreur"));
    getUsers().then((res) => setUsers(res.data)).catch(() => {});
    getAuditLogs(100).then((res) => setLogs(res.data)).catch(() => {});
  }, []);

  const statCards = [
    { label: "Utilisateurs", value: stats?.total_users, color: "text-white", icon: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" },
    { label: "Organisations", value: stats?.total_organizations, color: "text-cyan-400", icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14-2h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" },
    { label: "Analyses", value: stats?.total_analyses, color: "text-white", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
    { label: "Score de risque moyen", value: stats?.avg_risk_score, color: "text-yellow-400", icon: "M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" },
  ];

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="page-title">Administration</h1>
        <p className="text-gray-500 text-sm mt-1">Vue d'ensemble de la plateforme</p>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((s) => (
          <div key={s.label} className="card p-6">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className={`w-5 h-5 ${s.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={s.icon} />
                </svg>
              </div>
            </div>
            <p className={`text-3xl font-extrabold ${s.color}`}>{s.value ?? "-"}</p>
            <p className="text-sm text-gray-500 mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="card p-6">
          <h3 className="section-title mb-4">Organisations par abonnement</h3>
          <div className="space-y-2">
            {Object.entries(stats?.organizations_by_tier ?? {}).map(([tier, count]) => (
              <div key={tier} className="flex justify-between items-center">
                <span className="text-sm text-gray-300 capitalize">{tier}</span>
                <span className="badge-info badge">{count}</span>
              </div>
            ))}
            {(!stats || Object.keys(stats.organizations_by_tier).length === 0) && (
              <p className="text-gray-500 text-sm">Aucune donnée</p>
            )}
          </div>
        </div>
        <div className="card p-6">
          <h3 className="section-title mb-4">Utilisateurs par rôle</h3>
          <div className="space-y-2">
            {Object.entries(stats?.users_by_role ?? {}).map(([role, count]) => (
              <div key={role} className="flex justify-between items-center">
                <span className="text-sm text-gray-300">{ROLE_LABELS[role] ?? role}</span>
                <span className={`badge ${roleBadge(role)}`}>{count}</span>
              </div>
            ))}
            {(!stats || Object.keys(stats.users_by_role).length === 0) && (
              <p className="text-gray-500 text-sm">Aucune donnée</p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="section-title mb-4">Tous les utilisateurs ({users.length})</h3>
          <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-1">
            {users.map((u) => (
              <div key={u.id} className="row flex justify-between items-center gap-2">
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{u.full_name || u.email}</p>
                  <p className="text-xs text-gray-500 truncate">{u.email}</p>
                </div>
                <span className={`badge shrink-0 ${roleBadge(u.role)}`}>{ROLE_LABELS[u.role] ?? u.role}</span>
              </div>
            ))}
            {users.length === 0 && <p className="text-gray-500 text-sm">Aucun utilisateur</p>}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="section-title mb-4">Journal d'audit</h3>
          <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-1">
            {logs.map((l) => (
              <div key={l.id} className="row">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono text-cyan-400">{l.action}</span>
                  <span className="text-xs text-gray-500">
                    {l.created_at ? new Date(l.created_at).toLocaleString() : ""}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-1 truncate">
                  {Object.entries(l.details || {}).map(([k, v]) => `${k}: ${v}`).join(" · ")}
                </p>
              </div>
            ))}
            {logs.length === 0 && <p className="text-gray-500 text-sm">Aucune activité</p>}
          </div>
        </div>
      </div>
    </Layout>
  );
};
