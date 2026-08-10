interface Anomaly {
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  type: string;
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
            <span className={`badge shrink-0 ${severityBadge[a.severity]}`}>
              {a.severity.toUpperCase()}
            </span>
            <div className="min-w-0">
              {a.type && <p className="text-[11px] text-cyan-400/70 font-medium">{a.type}</p>}
              <p className="text-sm text-gray-200">{a.description}</p>
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
