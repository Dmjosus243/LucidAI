import { useEffect, useState } from "react";
import { Layout } from "../Components/Layout";
import { useAuth } from "../Services/Context/AuthContext";
import { importStatement, getStatements } from "../Services/api";
import type { ReconImportResponse, ReconResult, BankStatementItem } from "../Services/api";

const statusBadge = (s: string) =>
  s === "auto" ? "badge-success" : s === "matched" ? "badge-info" : "badge-critical";

const statusLabel = (s: string) =>
  s === "auto" ? "Auto" : s === "matched" ? "Suggesté" : "Non rapproché";

const fmt = (v?: number | null) =>
  v == null ? "—" : v.toLocaleString("fr-FR", { minimumFractionDigits: 2 });

export const Reconciliation = () => {
  const { isManager } = useAuth();
  const [statements, setStatements] = useState<BankStatementItem[]>([]);
  const [result, setResult] = useState<ReconImportResponse | null>(null);
  const [results, setResults] = useState<ReconResult[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    getStatements().then((res) => setStatements(res.data)).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const handleUpload = (file: File) => {
    setUploading(true);
    setError("");
    setResult(null);
    importStatement(file)
      .then((res) => {
        setResult(res.data);
        setResults(res.data.results);
        load();
      })
      .catch((err) => setError(err?.response?.data?.detail || "Échec de l'import du relevé"))
      .finally(() => setUploading(false));
  };

  const matchedCount = results.filter((r) => r.status !== "unmatched").length;

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="page-title">Rapprochement bancaire</h1>
        <p className="text-gray-500 text-sm mt-1">
          Pointez automatiquement vos écritures avec les lignes de votre relevé bancaire.
        </p>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}

      {!isManager ? (
        <div className="card p-6"><p className="text-gray-500 text-sm">Réservé au manager ou au-dessus.</p></div>
      ) : (
        <>
          <div className="card p-6 mb-8">
            <h3 className="section-title mb-4">Importer un relevé bancaire</h3>
            <label
              className={`card rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
                uploading ? "border-gray-600 opacity-50" : "border-cyan-500/20 hover:border-cyan-400/60 hover:shadow-glow"
              }`}
            >
              <input
                type="file"
                className="hidden"
                disabled={uploading}
                accept=".csv,.xlsx,.xls,.json"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleUpload(f);
                  e.target.value = "";
                }}
              />
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
                </svg>
              </div>
              <p className="text-base font-semibold text-white">
                {uploading ? "Rapprochement en cours..." : "Déposer votre relevé bancaire"}
              </p>
              <p className="text-gray-400 text-sm mt-2">CSV, XLSX, JSON — colonnes montant / date / libellé</p>
            </label>
          </div>

          {result && (
            <div className="mb-8">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <div className="card p-6">
                  <p className="text-3xl font-extrabold text-cyan-400">{(result.automation_rate * 100).toFixed(0)}%</p>
                  <p className="text-sm text-gray-500 mt-1">Taux d'automatisation</p>
                </div>
                <div className="card p-6">
                  <p className="text-3xl font-extrabold text-success">{matchedCount}</p>
                  <p className="text-sm text-gray-500 mt-1">Lignes rapprochées</p>
                </div>
                <div className="card p-6">
                  <p className="text-3xl font-extrabold text-white">{result.lines_count}</p>
                  <p className="text-sm text-gray-500 mt-1">Lignes du relevé</p>
                </div>
              </div>

              <h3 className="section-title mb-4">Détail des pointages</h3>
              <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs text-gray-500 border-b border-white/10">
                        <th className="p-3 font-medium">Relevé (libellé)</th>
                        <th className="p-3 font-medium text-right">Montant</th>
                        <th className="p-3 font-medium">Statut</th>
                        <th className="p-3 font-medium text-right">Confiance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((r, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
                          <td className="p-3 text-gray-300 max-w-[280px] truncate">
                            {r.statement_line?.description || "—"}
                          </td>
                          <td className="p-3 text-right font-mono">
                            {fmt(r.statement_line?.amount)} CDF
                          </td>
                          <td className="p-3">
                            <span className={`badge ${statusBadge(r.status)}`}>{statusLabel(r.status)}</span>
                          </td>
                          <td className="p-3 text-right">
                            <span className={`font-mono ${r.confidence >= 0.7 ? "text-success" : r.confidence >= 0.4 ? "text-warning" : "text-danger"}`}>
                              {(r.confidence * 100).toFixed(0)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                      {results.length === 0 && (
                        <tr><td colSpan={4} className="p-6 text-center text-gray-500">Importez un relevé pour voir les pointages.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          <div className="mb-8">
            <h2 className="section-title mb-4">Relevés importés ({statements.length})</h2>
            {statements.length === 0 ? (
              <div className="card p-6"><p className="text-gray-500 text-sm">Aucun relevé importé.</p></div>
            ) : (
              <div className="space-y-2">
                {statements.map((s) => (
                  <div key={s.id} className="card p-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-white">{s.date_range || "Relevé bancaire"}</p>
                      <p className="text-xs text-gray-500">{s.lines_count} ligne(s) · {s.source}</p>
                    </div>
                    <span className="badge badge-info">{s.created_at ? new Date(s.created_at).toLocaleDateString() : ""}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </Layout>
  );
};
