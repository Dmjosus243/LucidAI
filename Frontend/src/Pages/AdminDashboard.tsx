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

  return (
    <Layout>
      <h2 className="text-xl font-bold mb-6">Administration de la plateforme</h2>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 p-3 rounded-xl">{error}</p>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="glass rounded-2xl p-6">
          <p className="text-3xl font-bold text-white">{stats?.total_users ?? "-"}</p>
          <p className="text-sm text-gray-500">Utilisateurs</p>
        </div>
        <div className="glass rounded-2xl p-6">
          <p className="text-3xl font-bold text-cyan-400">{stats?.total_organizations ?? "-"}</p>
          <p className="text-sm text-gray-500">Organisations</p>
        </div>
        <div className="glass rounded-2xl p-6">
          <p className="text-3xl font-bold text-white">{stats?.total_analyses ?? "-"}</p>
          <p className="text-sm text-gray-500">Analyses</p>
        </div>
        <div className="glass rounded-2xl p-6">
          <p className="text-3xl font-bold text-yellow-400">{stats?.avg_risk_score ?? "-"}</p>
          <p className="text-sm text-gray-500">Score de risque moyen</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Organisations par abonnement</h3>
          <div className="space-y-2">
            {Object.entries(stats?.organizations_by_tier ?? {}).map(([tier, count]) => (
              <div key={tier} className="flex justify-between items-center">
                <span className="text-sm text-gray-300 capitalize">{tier}</span>
                <span className="text-sm font-bold text-white">{count}</span>
              </div>
            ))}
            {(!stats || Object.keys(stats.organizations_by_tier).length === 0) && (
              <p className="text-gray-500 text-sm">Aucune donnée</p>
            )}
          </div>
        </div>
        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Utilisateurs par rôle</h3>
          <div className="space-y-2">
            {Object.entries(stats?.users_by_role ?? {}).map(([role, count]) => (
              <div key={role} className="flex justify-between items-center">
                <span className="text-sm text-gray-300">{ROLE_LABELS[role] ?? role}</span>
                <span className="text-sm font-bold text-white">{count}</span>
              </div>
            ))}
            {(!stats || Object.keys(stats.users_by_role).length === 0) && (
              <p className="text-gray-500 text-sm">Aucune donnée</p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Tous les utilisateurs ({users.length})</h3>
          <div className="space-y-2 max-h-[40vh] overflow-y-auto">
            {users.map((u) => (
              <div key={u.id} className="p-3 bg-dark/30 rounded-lg flex justify-between items-center">
                <div className="min-w-0">
                  <p className="text-sm text-white truncate">{u.full_name || u.email}</p>
                  <p className="text-xs text-gray-500 truncate">{u.email}</p>
                </div>
                <span className="text-xs text-gray-400">{ROLE_LABELS[u.role] ?? u.role}</span>
              </div>
            ))}
            {users.length === 0 && <p className="text-gray-500 text-sm">Aucun utilisateur</p>}
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Journal d'audit</h3>
          <div className="space-y-2 max-h-[40vh] overflow-y-auto">
            {logs.map((l) => (
              <div key={l.id} className="p-3 bg-dark/30 rounded-lg">
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
