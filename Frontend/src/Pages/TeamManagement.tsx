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
      <h2 className="text-xl font-bold mb-6">Gestion de l'équipe</h2>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 p-3 rounded-xl">{error}</p>}
      {notice && <p className="text-success text-sm mb-4 bg-success/10 p-3 rounded-xl">{notice}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Inviter un membre</h3>
          <form onSubmit={handleInvite} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              required
            />
            <input
              type="text"
              placeholder="Nom complet"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              required
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white focus:outline-none focus:border-cyan-500"
            >
              {ROLES.filter((r) => r !== "super_admin" || isSuperAdmin).map((r) => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
            <button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-dark font-bold py-3 rounded-xl transition-colors">
              Inviter
            </button>
          </form>
          {tempPassword && (
            <div className="mt-4 p-3 bg-success/10 rounded-xl text-sm">
              <p className="text-success mb-1">Membre invité !</p>
              <p className="text-gray-300">Mot de passe temporaire :</p>
              <p className="font-mono text-white select-all">{tempPassword}</p>
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          <div className="glass rounded-2xl p-6">
            <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">
              Membres ({users.length})
            </h3>
            {loading ? (
              <p className="text-gray-500 text-sm">Chargement...</p>
            ) : users.length === 0 ? (
              <p className="text-gray-500 text-sm">Aucun membre</p>
            ) : (
              <div className="space-y-3">
                {users.map((u) => (
                  <div key={u.id} className="p-3 bg-dark/30 rounded-lg flex flex-col md:flex-row md:items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white truncate">{u.full_name || u.email}</p>
                      <p className="text-xs text-gray-500 truncate">{u.email}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <select
                        value={u.role}
                        onChange={(e) => handleRole(u, e.target.value)}
                        disabled={u.id === me?.id}
                        className="p-2 rounded-lg bg-dark-card border border-gray-700 text-xs text-white focus:outline-none focus:border-cyan-500 disabled:opacity-40"
                      >
                        {ROLES.filter((r) => r !== "super_admin" || isSuperAdmin).map((r) => (
                          <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                        ))}
                      </select>
                      {u.id !== me?.id && (
                        <>
                          <button
                            onClick={() => handleToggleActive(u)}
                            className={`px-3 py-2 rounded-lg text-xs font-semibold transition-colors ${
                              u.is_active ? "bg-success/10 text-success hover:bg-success/20" : "bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20"
                            }`}
                          >
                            {u.is_active ? "Actif" : "Désactivé"}
                          </button>
                          <button
                            onClick={() => handleDelete(u)}
                            className="px-3 py-2 rounded-lg text-xs font-semibold bg-danger/10 text-danger hover:bg-danger/20 transition-colors"
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
