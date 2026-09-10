import { useState } from "react";
import { Layout } from "../Components/Layout";
import { createCheckoutSession } from "../Services/api";
import { useAuth } from "../Services/Context/AuthContext";

const PLANS = [
  {
    id: "pro",
    name: "Pro",
    monthly: "55 000 CDF",
    annual: "550 000 CDF",
    description: "Pour les cabinets et petites équipes",
    features: ["Analyses illimitées", "Rapports PDF détaillés", "5 membres", "Paiement Mobile Money & carte"],
    current: true,
    highlight: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    monthly: "142 000 CDF",
    annual: "1 420 000 CDF",
    description: "Pour les grandes structures",
    features: ["Tout le plan Pro", "Membres illimités", "API et intégrations", "Support prioritaire", "Accompagnement dédié"],
    current: false,
    highlight: false,
  },
];

const POSITIONING = [
  { label: "Normes comptables", us: "SYSCOHADA / OHADA", them: "SOX, IFRS, PCAOB" },
  { label: "Langue", us: "Français + vocabulaire local", them: "Anglais / générique" },
  { label: "Paiement", us: "Mobile Money (MaishaPay)", them: "Virement bancaire" },
  { label: "Déploiement", us: "Zero config, 60 secondes", them: "Implémentation lourde" },
  { label: "Prix", us: "Accessible aux cabinets locaux", them: "15 000 – 460 000 €/an" },
];

const GUARANTEES = [
  "Conforme SYSCOHADA / OHADA",
  "Résultat en moins de 60 s",
  "Paiement Mobile Money",
  "Données hébergées en toute sécurité",
];

export const Subscription = () => {
  const { isOrgAdmin } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleUpgrade = async (plan: string) => {
    setError("");
    setLoading(plan);
    try {
      const res = await createCheckoutSession(plan);
      window.location.href = res.data.checkout_url;
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Erreur lors du paiement");
      setLoading(null);
    }
  };

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="page-title">Abonnement</h1>
        <p className="text-gray-500 text-sm mt-1">Choisissez le plan adapté à votre organisation</p>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}

      {!isOrgAdmin ? (
        <div className="card p-8 text-center">
          <p className="text-gray-400">Seul un administrateur d'organisation peut gérer l'abonnement.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 max-w-4xl mx-auto">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className={`card p-8 relative ${plan.highlight ? "border-cyan-400/40" : ""}`}
              >
                {plan.highlight && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 badge-info badge">
                    Recommandé
                  </span>
                )}
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <p className="text-sm text-gray-500 mt-1 mb-6">{plan.description}</p>
                <div className="mb-6">
                  <span className="text-3xl font-extrabold text-white">{plan.monthly}</span>
                  <span className="text-gray-500 text-sm"> / mois</span>
                  <p className="text-xs text-gray-500 mt-1">ou {plan.annual} / an</p>
                </div>
                <ul className="space-y-2 mb-6 text-sm">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-gray-300">
                      <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-green-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => handleUpgrade(plan.id)}
                  disabled={loading !== null}
                  className={`w-full btn py-2.5 ${plan.highlight ? "btn-primary" : ""}`}
                >
                  {loading === plan.id ? "Redirection vers le paiement..." : `Passer au plan ${plan.name}`}
                </button>
              </div>
            ))}
          </div>

          <div className="card p-6 max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-white">Paiement sécurisé</h3>
              <p className="text-xs text-gray-500 mt-1">
                Paiement par Mobile Money (Orange Money, M-Pesa, Airtel) ou carte bancaire via MaishaPay.
              </p>
            </div>
            <span className="badge-info badge shrink-0">Sécurisé</span>
          </div>

          {/* Garanties */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8 max-w-4xl mx-auto">
            {GUARANTEES.map((g) => (
              <div key={g} className="card p-4 text-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-green-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <p className="text-xs font-semibold text-white">{g}</p>
              </div>
            ))}
          </div>

          {/* Différenciation */}
          <div className="card p-6 sm:p-8 mt-8 max-w-4xl mx-auto">
            <h2 className="page-title !text-xl md:!text-2xl mb-2">Une alternative locale aux géants</h2>
            <p className="text-gray-400 text-sm mb-6">
              Les solutions occidentales (MindBridge, Oversight…) coûtent 15 000 €/an et plus. LucidAI est pensée
              pour les cabinets et PME d'Afrique francophone.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b border-white/10">
                    <th className="py-2 pr-4 font-semibold text-gray-400"></th>
                    <th className="py-2 pr-4 font-semibold text-cyan-400">LucidAI</th>
                    <th className="py-2 font-semibold text-gray-500">Les géants</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {POSITIONING.map((row) => (
                    <tr key={row.label}>
                      <td className="py-2.5 pr-4 text-gray-400 font-medium">{row.label}</td>
                      <td className="py-2.5 pr-4 text-green-400 font-semibold">{row.us}</td>
                      <td className="py-2.5 text-gray-600">{row.them}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
};
