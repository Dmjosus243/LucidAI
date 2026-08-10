interface Props {
  score: number;
}

export const RiskScoreCard = ({ score }: Props) => {
  const clamped = Math.max(0, Math.min(100, score));
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  const getColor = (s: number) => {
    if (s > 70) return { stroke: "#FF4D4D", text: "text-danger", label: "Risque élevé" };
    if (s > 40) return { stroke: "#FBBF24", text: "text-yellow-400", label: "Risque modéré" };
    return { stroke: "#00C853", text: "text-success", label: "Risque faible" };
  };

  const c = getColor(clamped);

  return (
    <div className="card card-hover p-6 text-center flex flex-col items-center">
      <h3 className="section-title">Risk Score</h3>
      <div className="relative mt-4">
        <svg width="140" height="140" viewBox="0 0 140 140" className="-rotate-90">
          <circle cx="70" cy="70" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke={c.stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1s ease-out" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <p className={`text-4xl font-extrabold ${c.text}`}>{clamped}</p>
          <p className="text-[10px] text-gray-500 uppercase tracking-wider">/ 100</p>
        </div>
      </div>
      <p className={`text-sm font-semibold mt-3 ${c.text}`}>{c.label}</p>
    </div>
  );
};
