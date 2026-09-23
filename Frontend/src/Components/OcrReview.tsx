import { useState } from "react";
import type { OcrLine } from "../Services/api";

interface Props {
  docId: string;
  filename: string;
  initialLines: OcrLine[];
  onSave: (lines: OcrLine[]) => void;
  onReject: () => void;
  onClose: () => void;
  saving: boolean;
}

export const OcrReview = ({ filename, initialLines, onSave, onReject, onClose, saving }: Props) => {
  const [lines, setLines] = useState<OcrLine[]>(
    initialLines.map((l) => ({ ...l }))
  );

  const update = (idx: number, patch: Partial<OcrLine>) => {
    setLines((prev) => prev.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="card w-full max-w-3xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-white/10">
          <div className="min-w-0">
            <h3 className="text-base font-bold text-white truncate">Vérification — {filename}</h3>
            <p className="text-xs text-gray-500 mt-1">
              Corrigez les valeurs avant d'intégrer les écritures comptables.
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white" title="Fermer">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-5 overflow-y-auto flex-1 space-y-3">
          {lines.length === 0 && (
            <p className="text-sm text-gray-500">Aucune ligne extraite — vous pouvez saisir les écritures manuellement ou rejeter le document.</p>
          )}
          {lines.map((line, i) => (
            <div key={i} className="row bg-white/[0.02] border border-white/10 rounded-xl">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-xs font-mono text-gray-500">Ligne {i + 1}</span>
                <span
                  className={`badge ${line.confidence >= 0.8 ? "badge-success" : line.confidence >= 0.5 ? "badge-warning" : "badge-critical"}`}
                >
                  Confiance {(line.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  className="input text-sm col-span-2"
                  value={line.label || ""}
                  placeholder="Libellé / fournisseur"
                  onChange={(e) => update(i, { label: e.target.value })}
                />
                <input
                  className="input text-sm"
                  value={line.date || ""}
                  placeholder="Date"
                  onChange={(e) => update(i, { date: e.target.value })}
                />
                <input
                  className="input text-sm"
                  type="number"
                  step="0.01"
                  value={line.amount === null || line.amount === undefined ? "" : line.amount}
                  placeholder="Montant CDF"
                  onChange={(e) => update(i, { amount: e.target.value === "" ? null : Number(e.target.value) })}
                />
                <input
                  className="input text-sm"
                  type="number"
                  step="0.01"
                  value={line.tax_rate === null || line.tax_rate === undefined ? "" : line.tax_rate}
                  placeholder="TVA %"
                  onChange={(e) => update(i, { tax_rate: e.target.value === "" ? null : Number(e.target.value) })}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between gap-3 p-5 border-t border-white/10">
          <button onClick={onReject} disabled={saving} className="btn-ghost text-danger">
            Rejeter
          </button>
          <div className="flex items-center gap-3">
            <button onClick={onClose} disabled={saving} className="btn-ghost">Annuler</button>
            <button onClick={() => onSave(lines)} disabled={saving} className="btn-primary">
              {saving ? "Intégration..." : "Valider les écritures"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
