import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export const Heatmap = ({ data }: { data: any[] }) => {
  const chartData = data.length > 0 ? data : [{ category: "Aucune donnée", risk_level: 0 }];

  return (
    <div className="glass rounded-2xl p-6">
      <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-4">Risk Distribution</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData}>
          <XAxis dataKey="category" stroke="#6B7280" fontSize={10} />
          <YAxis stroke="#6B7280" fontSize={10} />
          <Tooltip contentStyle={{ backgroundColor: "#111F33", border: "none" }} />
          <Bar dataKey="risk_level" fill="#00D4FF" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};