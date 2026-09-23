import { Link } from "react-router-dom";

const FEATURES = [
  {
    icon: "M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4",
    title: "Détection multi-moteurs",
    desc: "Règles déterministes, analyses statistiques (z-score) et schémas de fraude combinés pour débusquer les anomalies que les contrôles manuels manquent.",
  },
  {
    icon: "M13 10V3L4 14h7v7l9-11h-7z",
    title: "Résultats en moins de 60 secondes",
    desc: "Importez votre fichier Excel ou CSV. LucidAI analyse l'ensemble des écritures et livre un rapport clair, sans configuration.",
  },
  {
    icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
    title: "Conforme SYSCOHADA / OHADA",
    desc: "Adapté aux normes comptables des pays OHADA et au cadre fiscal congolais, en français — pas un outil importé d'Occident.",
  },
  {
    icon: "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z",
    title: "Paiement Mobile Money",
    desc: "Réglez votre abonnement par Mobile Money (Orange Money, M-Pesa, Airtel) via MaishaPay — pensé pour le marché congolais.",
  },
];

const DETECTED = [
  "Transactions en double",
  "Fournisseurs à risque",
  "Montants hors norme",
  "Fractionnement de seuils",
  "TVA invalide",
  "Écritures négatives suspectes",
];

const POSITIONING = [
  { label: "Prix", us: "Accessible aux cabinets locaux", them: "15 000 – 460 000 €/an" },
  { label: "Normes", us: "SYSCOHADA / OHADA", them: "SOX, IFRS, PCAOB" },
  { label: "Langue", us: "Français + vocabulaire local", them: "Anglais / générique" },
  { label: "Paiement", us: "Mobile Money (MaishaPay)", them: "Virement bancaire" },
  { label: "Déploiement", us: "Zero config, 60 secondes", them: "Implémentation lourde" },
];

export const Landing = () => {
  return (
    <div className="min-h-screen">
      {/* NAV */}
      <header className="sticky top-0 z-30 glass border-b border-white/5">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white to-cyan-400 bg-clip-text text-transparent">
              LucidAI
            </span>
          </div>
          <nav className="flex items-center gap-3">
            <Link to="/login" className="btn-ghost text-sm">Connexion</Link>
            <Link to="/register" className="btn-primary text-sm !py-2">Essai gratuit</Link>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="max-w-6xl mx-auto px-4 pt-20 pb-16 text-center">
        <span className="badge-info badge mb-6">🇨🇩 Pensé pour le Congo & l'Afrique francophone</span>
        <h1 className="page-title !text-4xl md:!text-6xl leading-tight mb-6">
          L'audit financier par IA,<br />fait pour l'Afrique francophone
        </h1>
        <p className="text-gray-400 text-lg md:text-xl max-w-3xl mx-auto mb-8">
          LucidAI détecte en <span className="text-cyan-400 font-semibold">moins de 60 secondes</span> les fraudes et
          anomalies dans vos comptabilités — conforme aux normes <span className="text-cyan-400 font-semibold">SYSCOHADA</span>,
          en français, pour les cabinets comptables congolais.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link to="/register" className="btn-primary text-base px-8 !py-3.5">
            Commencer l'analyse gratuite
          </Link>
          <Link to="/login" className="btn-ghost text-base px-8 !py-3.5">
            J'ai déjà un compte
          </Link>
        </div>
        <p className="text-xs text-gray-500 mt-4">Sans carte bancaire · Résultat en 60 s</p>
      </section>

      {/* DETECTED TAGS */}
      <section className="max-w-6xl mx-auto px-4 pb-16">
        <div className="flex flex-wrap justify-center gap-2">
          {DETECTED.map((d) => (
            <span key={d} className="badge bg-white/5 border border-white/10 text-gray-300">
              ✓ {d}
            </span>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-center section-title !text-base mb-10">Pourquoi LucidAI</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {FEATURES.map((f) => (
            <div key={f.title} className="card card-hover p-6">
              <div className="w-11 h-11 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={f.icon} />
                </svg>
              </div>
              <h3 className="font-bold text-white mb-2">{f.title}</h3>
              <p className="text-sm text-gray-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* DIFFERENTIATION / POSITIONING */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="card p-8 md:p-12">
          <h2 className="page-title !text-2xl md:!text-3xl mb-3">Une alternative locale aux géants</h2>
          <p className="text-gray-400 mb-8">
            Les solutions occidentales sont hors de portée des cabinets et PME d'Afrique francophone.
            LucidAI est la seule plateforme de détection de fraude pensée pour votre réalité.
          </p>
          <div className="hidden sm:grid grid-cols-3 gap-4 md:gap-6 font-semibold text-sm pb-3 border-b border-white/10">
            <div></div>
            <div className="text-cyan-400">LucidAI</div>
            <div className="text-gray-500 text-right">Les géants (MindBridge, Oversight)</div>
          </div>
          <div className="divide-y divide-white/5">
            {POSITIONING.map((row) => (
              <div key={row.label} className="py-3 text-sm">
                <div className="text-gray-400 font-medium mb-1">{row.label}</div>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-6 sm:items-center sm:mt-0">
                  <div className="text-green-400 font-semibold min-w-0">{row.us}</div>
                  <div className="text-gray-600 sm:text-right min-w-0">{row.them}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h2 className="page-title !text-3xl mb-4">Prêt à sécuriser vos comptabilités ?</h2>
        <p className="text-gray-400 mb-8">
          Rejoignez les cabinets qui font confiance à LucidAI pour détecter les fraudes avant qu'elles ne coûtent cher.
        </p>
        <Link to="/register" className="btn-primary text-base px-10 !py-3.5">
          Créer mon compte gratuit
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-white/5 mt-8">
        <div className="max-w-6xl mx-auto px-4 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="font-bold text-sm">LucidAI</span>
          </div>
          <p className="text-xs text-gray-500">© {new Date().getFullYear()} LucidAI — Audit financier par IA</p>
        </div>
      </footer>
    </div>
  );
};
