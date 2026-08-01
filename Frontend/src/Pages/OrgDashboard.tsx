import { useEffect, useState } from "react";
import { Layout } from "../Components/Layout";
import { getOrganization, updateOrganization, getOrgAnalyses } from "../Services/api";
import type { OrganizationInfo, OrgAnalysis } from "../Services/api";
import { useAuth } from "../Services/Context/AuthContext";

const TIERS = ["free", "pro", "enterprise"];
const TIER_LABELS: Record<string, string> = { free: "Gratuit", pro: "Pro", enterprise: "Entreprise" };

export const OrgDashboard = () => {
  const { isOrgAdmin, isManager } = useAuth();
  const [org, setOrg] = useState<OrganizationInfo | null>(null);
  const [analyses, setAnalyses] = useState<OrgAnalysis[]>([]);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [name, setName] = useState("");
  const [tier, setTier] = useState("free");

  useEffect(() => {
    getOrganization()
      .then((res) => {
        setOrg(res.data);
        if (res.data) {
          setName(res.data.name);
          setTier(res.data.subscription_tier);
        }
      })
      .catch(() => setError("Impossible de charger l'organisation"));
    if (isManager || isOrgAdmin) {
      getOrgAnalyses().then((res) => setAnalyses(res.data)).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaved("");
    try {
      const res = await updateOrganization({ name, subscription_tier: tier });
      setOrg(res.data);
      setSaved("Organisation mise à jour");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur lors de la mise à jour");
    }
  };

  const statusLabel = (s: string) =>
    s === "done" ? "Terminé" : s === "error" ? "Erreur" : "En cours";
  const statusClass = (s: string) =>
    s === "done" ? "text-success" : s === "error" ? "text-danger" : "text-yellow-400";

  return (
    <Layout>
      <h2 className="text-xl font-bold mb-6">Mon organisation</h2>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 p-3 rounded-xl">{error}</p>}
      {saved && <p className="text-success text-sm mb-4 bg-success/10 p-3 rounded-xl">{saved}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Informations</h3>
          {!org ? (
            <p className="text-gray-500 text-sm">Aucune organisation</p>
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Nom</label>
                <input
                  type="text"
                  value={name}
                  disabled={!isOrgAdmin}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white focus:outline-none focus:border-cyan-500 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Abonnement</label>
                <select
                  value={tier}
                  disabled={!isOrgAdmin}
                  onChange={(e) => setTier(e.target.value)}
                  className="w-full p-3 rounded-xl bg-dark-card border border-gray-700 text-white focus:outline-none focus:border-cyan-500 disabled:opacity-50"
                >
                  {TIERS.map((t) => (
                    <option key={t} value={t}>{TIER_LABELS[t]}</option>
                  ))}
                </select>
              </div>
              {isOrgAdmin && (
                <button type="submit" className="w-full bg-cyan-500 hover:bg-cyan-600 text-dark font-bold py-3 rounded-xl transition-colors">
                  Enregistrer
                </button>
              )}
            </form>
          )}
        </div>

        <div className="glass rounded-2xl p-6">
          <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Vue d'ensemble</h3>
          <div className="space-y-4">
            <div>
              <p className="text-3xl font-bold text-white">{org?.member_count ?? "-"}</p>
              <p className="text-sm text-gray-500">Membres</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-cyan-400">{TIER_LABELS[tier] ?? tier}</p>
              <p className="text-sm text-gray-500">Niveau d'abonnement</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{analyses.length}</p>
              <p className="text-sm text-gray-500">Analyses de l'équipe</p>
            </div>
          </div>
        </div>

        {(isManager || isOrgAdmin) && (
          <div className="glass rounded-2xl p-6 lg:col-span-1">
            <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Analyses de l'équipe</h3>
            {analyses.length === 0 ? (
              <p className="text-gray-500 text-sm">Aucune analyse</p>
            ) : (
              <div className="space-y-3 max-h-[40vh] overflow-y-auto">
                {analyses.map((a) => (
                  <div key={a.id} className="p-3 bg-dark/30 rounded-lg">
                    <p className="text-sm text-gray-200 truncate">{a.filename}</p>
                    <div className="flex justify-between items-center mt-1">
                      <span className={`text-xs ${statusClass(a.status)}`}>{statusLabel(a.status)}</span>
                      {a.status === "done" && (
                        <span className="text-xs text-gray-400">Score: {a.risk_score}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};
