import { useEffect, useState, useCallback } from "react";
import { Layout } from "../Components/Layout";
import { useAuth } from "../Services/Context/AuthContext";
import { OcrReview } from "../Components/OcrReview";
import {
  uploadOcrDocument,
  getOcrDocuments,
  getJournalEntries,
  validateOcrDocument,
  rejectOcrDocument,
} from "../Services/api";
import type { OCRDocument, OcrLine, JournalEntry } from "../Services/api";

const statusBadge = (status: string) =>
  status === "validated"
    ? "badge-success"
    : status === "rejected"
    ? "badge-critical"
    : "badge-warning";

const statusLabel = (status: string) =>
  status === "validated" ? "Validé" : status === "rejected" ? "Rejeté" : "À vérifier";

const engineLabel = (e: string) =>
  e === "structured" ? "Structuré" : e === "transparent" ? "Simple" : e === "tesseract" ? "Tesseract" : e === "paddle" ? "PaddleOCR" : e;

export const DocumentsOCR = () => {
  const { isManager } = useAuth();
  const [docs, setDocs] = useState<OCRDocument[]>([]);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [reviewDoc, setReviewDoc] = useState<OCRDocument | null>(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    getOcrDocuments().then((res) => setDocs(res.data)).catch(() => {});
    getJournalEntries().then((res) => setEntries(res.data)).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleUpload = (file: File) => {
    setUploading(true);
    setError("");
    uploadOcrDocument(file)
      .then(() => load())
      .catch((err) => setError(err?.response?.data?.detail || "Échec de l'extraction"))
      .finally(() => setUploading(false));
  };

  const handleValidate = (docId: string, lines: OcrLine[]) => {
    setSaving(true);
    validateOcrDocument(docId, lines)
      .then(() => {
        setReviewDoc(null);
        load();
      })
      .catch((err) => setError(err?.response?.data?.detail || "Échec de la validation"))
      .finally(() => setSaving(false));
  };

  const handleReject = (docId: string) => {
    setSaving(true);
    rejectOcrDocument(docId)
      .then(() => {
        setReviewDoc(null);
        load();
      })
      .catch((err) => setError(err?.response?.data?.detail || "Échec du rejet"))
      .finally(() => setSaving(false));
  };

  const pendingCount = docs.filter((d) => d.status === "pending").length;
  const validatedCount = docs.filter((d) => d.status === "validated").length;

  return (
    <Layout>
      <div className="mb-8 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="page-title">OCR intelligent</h1>
          <p className="text-gray-500 text-sm mt-1">
            Extrayez les écritures des factures et justificatifs, puis validez-les avant intégration.
          </p>
        </div>
      </div>

      {error && <p className="text-danger text-sm mb-4 bg-danger/10 border border-danger/25 p-3 rounded-xl">{error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="card p-6 col-span-2">
          <h3 className="section-title mb-4">Importer un document</h3>
          <label
            className={`card rounded-2xl p-8 sm:p-10 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
              uploading
                ? "border-gray-600 opacity-50"
                : "border-cyan-500/20 hover:border-cyan-400/60 hover:shadow-glow"
            }`}
          >
            <input
              type="file"
              className="hidden"
              disabled={uploading}
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
                e.target.value = "";
              }}
              accept=".csv,.txt,.pdf,.png,.jpg,.jpeg,.xlsx,.xls,.json"
            />
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
              </svg>
            </div>
            <p className="text-base font-semibold text-white">
              {uploading ? "Extraction en cours..." : "Déposer une facture ou un relevé"}
            </p>
            <p className="text-gray-400 text-sm mt-2">CSV, XLSX, JSON, PDF, image (JPG/PNG)</p>
          </label>
        </div>

        <div className="space-y-4">
          <div className="card p-6">
            <p className="text-3xl font-extrabold text-warning">{pendingCount}</p>
            <p className="text-sm text-gray-500 mt-1">Documents à vérifier</p>
          </div>
          <div className="card p-6">
            <p className="text-3xl font-extrabold text-success">{validatedCount}</p>
            <p className="text-sm text-gray-500 mt-1">Documents validés</p>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="section-title mb-4">Documents ({docs.length})</h2>
        {docs.length === 0 ? (
          <div className="card p-6"><p className="text-gray-500 text-sm">Aucun document pour le moment.</p></div>
        ) : (
          <div className="space-y-3">
            {docs.map((d) => (
              <div key={d.id} className="card p-5 flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-cyan-400">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-white truncate">{d.filename}</p>
                    <p className="text-xs text-gray-500">
                      {d.lines.length} ligne(s) · Moteur {engineLabel(d.engine)} · {d.created_at ? new Date(d.created_at).toLocaleDateString() : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`badge ${statusBadge(d.status)}`}>{statusLabel(d.status)}</span>
                  {d.status === "pending" && isManager && (
                    <button
                      onClick={() => { setReviewDoc(d); setError(""); }}
                      className="btn-primary !py-1.5 !px-4 text-xs"
                      disabled={busy}
                    >
                      Vérifier
                    </button>
                  )}
                  {!isManager && d.status === "pending" && (
                    <span className="text-xs text-gray-600">Réservé au manager+</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="section-title mb-4">Écritures comptables (issues du rapprochement OCR)</h2>
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Référence</th>
                  <th>Date</th>
                  <th>Libellé</th>
                  <th className="num">Montant</th>
                  <th>Source</th>
                  <th className="num">Confiance</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e) => (
                  <tr key={e.id}>
                    <td className="font-mono text-xs text-cyan-400">{e.entry_ref}</td>
                    <td>{e.date || "-"}</td>
                    <td>{e.lines?.[0]?.label || "-"}</td>
                    <td className="num">
                      {(e.lines?.[0]?.amount ?? 0).toLocaleString("fr-FR", { minimumFractionDigits: 2 })} CDF
                    </td>
                    <td><span className="badge badge-info">{e.source}</span></td>
                    <td className="num text-gray-400">{(e.confidence * 100).toFixed(0)}%</td>
                  </tr>
                ))}
                {entries.length === 0 && (
                  <tr><td colSpan={6} className="text-center text-gray-500">Aucune écriture pour le moment.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {reviewDoc && isManager && (
        <OcrReview
          docId={reviewDoc.id}
          filename={reviewDoc.filename}
          initialLines={reviewDoc.lines}
          saving={saving}
          onSave={(lines) => handleValidate(reviewDoc.id, lines)}
          onReject={() => handleReject(reviewDoc.id)}
          onClose={() => setReviewDoc(null)}
        />
      )}
    </Layout>
  );
};
