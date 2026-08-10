import { useEffect, useState } from "react";
import { Layout } from "../Components/Layout";
import { getUsers, inviteUser, updateUser, deleteUser } from "../Services/api";
import type { User } from "../Services/api";
import { useAuth } from "../Services/Context/AuthContext";

const ROLES = ["super_admin", "org_admin", "manager", "auditor"];

const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  org_admin: "Admin Organisation",
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

export const TeamManagement = () => {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("auditor");
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  const load = () => {
    getUsers()
      .then((res) => setUsers(res.data))
      .catch(() => setError("Impossible de charger les membres"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setNotice("");
    try {
      const res = await inviteUser({ email, full_name: fullName, role });
      setTempPassword(res.data.temporary_password || null);
      setEmail("");
      setFullName("");
      setRole("auditor");
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur lors de l'invitation");
    }
  };

  const handleRole = async (u: User, newRole: string) => {
    setError("");
    try {
      await updateUser(u.id, { role: newRole });
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur");
    }
  };

  const handleToggleActive = async (u: User) => {
    setError("");
    try {
      await updateUser(u.id, { is_active: !u.is_active });
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur");
    }
  };

  const handleDelete = async (u: User) => {
    setError("");
    setNotice("");
    if (!window.confirm(`Désactiver le compte de ${u.email} ?`)) return;
    try {
      await deleteUser(u.id);
      load();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur");
    }
  };

  const isSuperAdmin = me?.role === "super_admin";

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="page-title">Gestion de l'équipe</h1>
        <p className="text-gray-500 text-sm mt-1">Invitez des membres et gérez leurs accès</p>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}
      {notice && <p className="text-success text-sm mb-4 bg-success/10 border border-success/25 p-3 rounded-xl">{notice}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6 h-fit">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/15 border border-cyan-500/25 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <h3 className="section-title">Inviter un membre</h3>
          </div>
          <form onSubmit={handleInvite} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
            />
            <input
              type="text"
              placeholder="Nom complet"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input"
              required
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="input"
            >
              {ROLES.filter((r) => r !== "super_admin" || isSuperAdmin).map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
            <button type="submit" className="btn-primary w-full">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Inviter
            </button>
          </form>
          {tempPassword && (
            <div className="mt-4 p-4 bg-success/10 border border-success/25 rounded-xl text-sm animate-fadeIn">
              <p className="text-success font-semibold mb-1">Membre invité !</p>
              <p className="text-gray-300">Mot de passe temporaire :</p>
              <p className="font-mono text-white select-all mt-1 p-2 bg-dark/50 rounded-lg">{tempPassword}</p>
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="section-title">Membres</h3>
              <span className="badge-info badge">{users.length}</span>
            </div>
            {loading ? (
              <p className="text-gray-500 text-sm text-center py-8">Chargement...</p>
            ) : users.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">Aucun membre</p>
            ) : (
              <div className="space-y-3">
                {users.map((u) => (
                  <div key={u.id} className="row flex flex-col md:flex-row md:items-center gap-3">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500/60 to-blue-600/60 flex items-center justify-center text-sm font-bold text-white shrink-0">
                        {(u.full_name || u.email).slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm text-white font-medium truncate">{u.full_name || u.email}</p>
                        <p className="text-xs text-gray-500 truncate">{u.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`badge ${roleBadge(u.role)} hidden md:inline-flex`}>{ROLE_LABELS[u.role] ?? u.role}</span>
                      <select
                        value={u.role}
                        onChange={(e) => handleRole(u, e.target.value)}
                        disabled={u.id === me?.id}
                        className="p-2 rounded-lg bg-dark-card border border-white/10 text-xs text-white focus:outline-none focus:border-cyan-500 disabled:opacity-40"
                      >
                        {ROLES.filter((r) => r !== "super_admin" || isSuperAdmin).map((r) => (
                          <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                        ))}
                      </select>
                      {u.id !== me?.id && (
                        <>
                          <button
                            onClick={() => handleToggleActive(u)}
                            className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors border ${
                              u.is_active
                                ? "bg-success/10 text-green-400 border-success/25 hover:bg-success/20"
                                : "bg-yellow-500/10 text-yellow-400 border-yellow-500/25 hover:bg-yellow-500/20"
                            }`}
                          >
                            {u.is_active ? "Actif" : "Désactivé"}
                          </button>
                          <button
                            onClick={() => handleDelete(u)}
                            className="px-3 py-2 rounded-lg text-xs font-semibold bg-danger/10 text-danger border border-danger/25 hover:bg-danger/20 transition-colors"
                          >
                            Désactiver
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};
