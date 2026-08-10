import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface HeatmapDatum {
  category: string;
  risk_level: number;
}

const COLORS = ["#00D4FF", "#38E1FF", "#00C853", "#FBBF24", "#FF8A00", "#FF4D4D"];

export const Heatmap = ({ data }: { data: HeatmapDatum[] }) => {
  const chartData = data.length > 0 ? data : [{ category: "Aucune donnée", risk_level: 0 }];

  return (
    <div className="card card-hover p-6">
      <h3 className="section-title mb-4">Répartition des risques</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <XAxis
            dataKey="category"
            stroke="#6B7280"
            fontSize={10}
            interval={0}
            tickFormatter={(v: string) => (v.length > 12 ? `${v.slice(0, 11)}…` : v)}
          />
          <YAxis stroke="#6B7280" fontSize={10} allowDecimals={false} />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.05)" }}
            contentStyle={{ backgroundColor: "#0D1B33", border: "1px solid rgba(0,212,255,0.2)", borderRadius: 12, color: "#fff", fontSize: 12 }}
            labelStyle={{ color: "#9CA3AF" }}
          />
          <Bar dataKey="risk_level" name="Risques" radius={[6, 6, 0, 0]}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
