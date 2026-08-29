interface Anomaly {
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  type: string;
  confidence?: number;
  summary?: string;
  reason?: string;
  red_flags?: string[];
  suggested_action?: string;
}

const severityBadge: Record<Anomaly["severity"], string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

export const AnomalyList = ({ anomalies }: { anomalies: Anomaly[] }) => {
  return (
    <div className="card card-hover p-6">
      <h3 className="section-title mb-4">Anomalies ({anomalies.length})</h3>
      <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
        {anomalies.slice(0, 10).map((a, i) => (
          <div key={i} className="row flex items-start gap-3 !p-3">
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={`badge shrink-0 ${severityBadge[a.severity]}`}>
                {a.severity.toUpperCase()}
              </span>
              {a.confidence !== undefined && (
                <span className="text-[10px] text-gray-400 bg-white/5 rounded px-1.5 py-0.5">
                  {Math.round(a.confidence * 100)}%
                </span>
              )}
            </div>
            <div className="min-w-0 flex-1">
              {a.type && <p className="text-[11px] text-cyan-400/70 font-medium">{a.type}</p>}
              <p className="text-sm text-gray-200">{a.description}</p>
              {a.summary && <p className="text-xs text-gray-400 mt-1">{a.summary}</p>}
              {a.red_flags && a.red_flags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {a.red_flags.map((f, j) => (
                    <span key={j} className="text-[10px] text-yellow-300/80 bg-yellow-400/10 border border-yellow-400/20 rounded px-1.5 py-0.5">
                      ⚑ {f}
                    </span>
                  ))}
                </div>
              )}
              {a.suggested_action && (
                <p className="text-[11px] text-cyan-300/80 mt-1.5">
                  <span className="font-medium">Action :</span> {a.suggested_action}
                </p>
              )}
            </div>
          </div>
        ))}
        {anomalies.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-6">Aucune anomalie détectée</p>
        )}
        {anomalies.length > 10 && (
          <p className="text-xs text-gray-500 text-center">+ {anomalies.length - 10} autres anomalies</p>
        )}
      </div>
    </div>
  );
};
