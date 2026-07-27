interface Anomaly {
  severity: string;
  description: string;
  type: string;
}

export const AnomalyList = ({ anomalies }: { anomalies: Anomaly[] }) => {
  const severityColors = {
    critical: "bg-danger/20 text-danger",
    high: "bg-orange-500/20 text-orange-400",
    medium: "bg-yellow-500/20 text-yellow-400",
    low: "bg-blue-500/20 text-blue-400",
  };

  return (
    <div className="glass rounded-2xl p-6">
      <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Anomalies ({anomalies.length})</h3>
      <div className="max-h-60 overflow-y-auto space-y-2">
        {anomalies.slice(0, 10).map((a, i) => (
          <div key={i} className="flex items-start gap-3 p-2 bg-dark/30 rounded-lg">
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${severityColors[a.severity]}`}>
              {a.severity.toUpperCase()}
            </span>
            <p className="text-sm text-gray-200">{a.description}</p>
          </div>
        ))}
        {anomalies.length > 10 && (
          <p className="text-xs text-gray-500 text-center">+ {anomalies.length - 10} autres anomalies</p>
        )}
      </div>
    </div>
  );
};