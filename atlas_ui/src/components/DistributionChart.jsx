import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

export default function DistributionChart({ data }) {
  if (!data || !data.histogram || !data.bins || !data.n) {
    return (
      <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--atlas-text-secondary)", padding: 8 }}>
        Aguardando dados...
      </div>
    );
  }

  const chartData = data.histogram.map((v, i) => ({
    bin: data.bins[i]?.toFixed(3) ?? "",
    count: v,
    pct: ((v / data.n) * 100).toFixed(1)
  }));

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11 }}>
      N={data.n}
      <BarChart width={400} height={160} data={chartData}>
        <Bar dataKey="count" fill="var(--atlas-blue)" />
        <XAxis dataKey="bin" />
        <YAxis />
        <Tooltip />
      </BarChart>
    </div>
  );
}