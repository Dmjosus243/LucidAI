interface Props {
  score: number;
}

export const RiskScoreCard = ({ score }: Props) => {
  const getColor = (s: number) => {
    if (s > 70) return "text-danger";
    if (s > 40) return "text-yellow-400";
    return "text-success";
  };

  return (
    <div className="glass rounded-2xl p-6 text-center">
      <h3 className="text-gray-400 text-sm uppercase tracking-wider">Risk Score</h3>
      <p className={`text-5xl font-bold ${getColor(score)} mt-2`}>{score}</p>
      <p className="text-gray-400 text-xs mt-1">/ 100</p>
    </div>
  );
};