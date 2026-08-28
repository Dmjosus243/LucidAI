import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../Components/Layout";
import { getOrganization, getOrgAnalyses } from "../Services/api";
import type { OrganizationInfo, OrgAnalysis } from "../Services/api";
import { useAuth } from "../Services/Context/AuthContext";

const TIER_LABELS: Record<string, string> = { free: "Gratuit", pro: "Pro", enterprise: "Entreprise" };

export const OrgDashboard = () => {
  const { isOrgAdmin, isManager } = useAuth();
  const [org, setOrg] = useState<OrganizationInfo | null>(null);
  const [analyses, setAnalyses] = useState<OrgAnalysis[]>([]);
  const [error, setError] = useState("");
  const [tier, setTier] = useState("free");

  useEffect(() => {
    getOrganization()
      .then((res) => {
        setOrg(res.data);
        if (res.data) {
          setTier(res.data.subscription_tier);
        }
      })
      .catch(() => setError("Impossible de charger l'organisation"));
    if (isManager || isOrgAdmin) {
      getOrgAnalyses().then((res) => setAnalyses(res.data)).catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const statusLabel = (s: string) =>
    s === "done" ? "Terminé" : s === "error" ? "Erreur" : "En cours";
  const statusBadge = (s: string) =>
    s === "done" ? "badge-success" : s === "error" ? "badge-critical" : "badge-warning";

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="page-title">Mon organisation</h1>
        <p className="text-gray-500 text-sm mt-1">Informations et activité de votre organisation</p>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-6 h-fit">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/15 border border-cyan-500/25 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14-2h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h3 className="section-title">Informations</h3>
          </div>
          {!org ? (
            <p className="text-gray-500 text-sm">Aucune organisation</p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2 p-4 bg-white/[0.02] border border-white/5 rounded-xl">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Nom de l'organisation</p>
                  <p className="text-sm font-medium text-white">{org.name}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 p-4 bg-white/[0.02] border border-white/5 rounded-xl">
                <div className="flex-1">
                  <p className="text-xs text-gray-500 mb-1">Abonnement</p>
                  <p className="text-sm font-medium text-white">{TIER_LABELS[tier] ?? tier}</p>
                </div>
              </div>
              <Link to="/abonnement" className="btn-primary w-full items-center justify-center flex">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Gérer l'abonnement
              </Link>
            </div>
          )}
        </div>

        <div className="card p-6">
          <h3 className="section-title mb-5">Vue d'ensemble</h3>
          <div className="space-y-5">
            <div className="flex items-center gap-4 p-4 bg-dark-card/50 border border-white/5 rounded-xl">
              <div className="w-11 h-11 rounded-lg bg-cyan-500/15 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-extrabold text-white">{org?.member_count ?? "-"}</p>
                <p className="text-sm text-gray-500">Membres</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 bg-dark-card/50 border border-white/5 rounded-xl">
              <div className="w-11 h-11 rounded-lg bg-yellow-500/15 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-extrabold text-yellow-400">{TIER_LABELS[tier] ?? tier}</p>
                <p className="text-sm text-gray-500">Niveau d'abonnement</p>
              </div>
            </div>
            <div className="flex items-center gap-4 p-4 bg-dark-card/50 border border-white/5 rounded-xl">
              <div className="w-11 h-11 rounded-lg bg-success/15 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p className="text-2xl font-extrabold text-white">{analyses.length}</p>
                <p className="text-sm text-gray-500">Analyses de l'équipe</p>
              </div>
            </div>
          </div>
        </div>

        {(isManager || isOrgAdmin) && (
          <div className="card p-6 lg:col-span-1">
            <h3 className="section-title mb-5">Analyses de l'équipe</h3>
            {analyses.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">Aucune analyse</p>
            ) : (
              <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-1">
                {analyses.map((a) => (
                  <div key={a.id} className="row">
                    <p className="text-sm text-gray-200 truncate font-medium">{a.filename}</p>
                    <div className="flex justify-between items-center mt-2">
                      <span className={`badge ${statusBadge(a.status)}`}>{statusLabel(a.status)}</span>
                      {a.status === "done" && (
                        <span className="text-xs font-semibold text-cyan-400">Score: {a.risk_score}</span>
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
