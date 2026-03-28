import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

export default function ACFChart({ data }) {
  if (!data || !data.lags || !data.values) {
    return (
      <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--atlas-text-secondary)", padding: 8 }}>
        Aguardando dados...
      </div>
    );
  }

  const chartData = data.lags.map((lag, i) => ({
    lag,
    value: data.values[i] ?? 0
  }));

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11 }}>
      ACF
      <BarChart width={400} height={120} data={chartData}>
        <Bar dataKey="value" fill="var(--atlas-amber)" />
        <XAxis dataKey="lag" />
        <YAxis />
        <Tooltip />
      </BarChart>
    </div>
  );
}