import { useSystemStore } from "../store/systemStore";
import { useAnalyticsStore } from "../store/analyticsStore";

export default function ExportReportButton() {
  const state = useSystemStore();
  const analytics = useAnalyticsStore();

  async function exportReport() {
    const res = await fetch("/report", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        state,
        analytics,
        staleness: analytics.staleness || 0
      })
    });

    const blob = await res.blob();

    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "atlas_report.md";
    a.click();

    window.URL.revokeObjectURL(url);
  }

  return (
    <button
      onClick={exportReport}
      style={{
        background: "var(--atlas-blue)",
        color: "#fff",
        border: "none",
        padding: "6px 12px",
        fontFamily: "monospace",
        fontSize: 11,
        borderRadius: 2
      }}
    >
      Exportar Relatório
    </button>
  );
}