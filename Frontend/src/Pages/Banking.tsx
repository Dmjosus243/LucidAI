import { useEffect, useState } from "react";
import { Layout } from "../Components/Layout";
import { useAuth } from "../Services/Context/AuthContext";
import {
  getBankAccounts,
  createBankAccount,
  deleteBankAccount,
  getWebhookEvents,
} from "../Services/api";
import type { BankAccountItem, WebhookEventItem } from "../Services/api";

export const Banking = () => {
  const { isManager } = useAuth();
  const [accounts, setAccounts] = useState<BankAccountItem[]>([]);
  const [events, setEvents] = useState<WebhookEventItem[]>([]);
  const [label, setLabel] = useState("");
  const [bankCode, setBankCode] = useState("");
  const [provider, setProvider] = useState("generic");
  const [error, setError] = useState("");

  const load = () => {
    getBankAccounts().then((res) => setAccounts(res.data)).catch(() => {});
    getWebhookEvents().then((res) => setEvents(res.data)).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const handleCreate = () => {
    if (!label.trim()) return;
    setError("");
    createBankAccount({ label, bank_code: bankCode || undefined, provider })
      .then(() => {
        setLabel("");
        setBankCode("");
        load();
      })
      .catch((err) => setError(err?.response?.data?.detail || "Échec de création"));
  };

  const handleDelete = (id: string) => {
    if (!window.confirm("Supprimer ce compte bancaire ?")) return;
    deleteBankAccount(id).then(load).catch((err) => setError(err?.response?.data?.detail || "Échec"));
  };

  const statusBadge = (s: string) =>
    s === "processed" ? "badge-success" : s === "failed" ? "badge-critical" : "badge-warning";

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="page-title">Banque & Webhooks</h1>
        <p className="text-gray-500 text-sm mt-1">
          Connectez vos comptes bancaires et recevez les opérations en temps réel via webhook.
        </p>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}

      {!isManager ? (
        <div className="card p-6"><p className="text-gray-500 text-sm">Réservé au manager ou au-dessus.</p></div>
      ) : (
        <>
          <div className="card p-6 mb-8">
            <h3 className="section-title mb-4">Ajouter un compte bancaire</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
              <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="Libellé (ex. Compte Pro Rawbank)"
                className="input"
              />
              <input
                value={bankCode}
                onChange={(e) => setBankCode(e.target.value)}
                placeholder="Code banque (optionnel)"
                className="input"
              />
              <select value={provider} onChange={(e) => setProvider(e.target.value)} className="input">
                <option value="generic">Générique (import manuel)</option>
                <option value="maishapay">MaishaPay</option>
              </select>
            </div>
            <button onClick={handleCreate} className="btn-primary">Ajouter le compte</button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="card p-6">
              <h3 className="section-title mb-4">Comptes bancaires ({accounts.length})</h3>
              {accounts.length === 0 ? (
                <p className="text-gray-500 text-sm">Aucun compte.</p>
              ) : (
                <div className="space-y-3">
                  {accounts.map((a) => (
                    <div key={a.id} className="row bg-white/[0.02] border border-white/10 rounded-xl p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-white">{a.label}</p>
                          <p className="text-xs text-gray-500">{a.currency} · {a.provider}{a.bank_code ? ` · ${a.bank_code}` : ""}</p>
                        </div>
                        <button onClick={() => handleDelete(a.id)} className="text-danger hover:opacity-80" title="Supprimer">
                          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card p-6">
              <h3 className="section-title mb-4">Événements webhook ({events.length})</h3>
              <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-1">
                {events.length === 0 ? (
                  <p className="text-gray-500 text-sm">Aucun événement reçu. Configurez votre webhook sur :</p>
                ) : (
                  events.map((e) => (
                    <div key={e.id} className="row">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-mono text-cyan-400">{e.provider} · {e.event_type || "événement"}</span>
                        <span className={`badge ${statusBadge(e.status)}`}>{e.status}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {e.received_at ? new Date(e.received_at).toLocaleString() : ""}
                      </p>
                    </div>
                  ))
                )}
                <div className="mt-4 p-3 rounded-lg bg-white/[0.03] border border-white/10">
                  <p className="text-xs text-gray-400 font-mono">
                    POST /api/v1/banking/webhook
                  </p>
                  <p className="text-[11px] text-gray-600 mt-1">
                    URL à enregistrer chez votre fournisseur pour recevoir les opérations
                    (idempotent : un rejeu ne crée pas de doublon).
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
};
