import ConfigEditor from "../components/ConfigEditor";
import ExportReportButton from "../components/ExportReportButton";

export default function ActionPanel({ activeTicker, onTickerChange }) {
  return (
    <div style={{ border: "1px solid var(--atlas-border)", background: "var(--atlas-surface)", padding: 10 }}>
      <h4 style={{ fontFamily: "monospace", fontSize: 12, marginBottom: 8 }}>Ações</h4>
      <ConfigEditor activeTicker={activeTicker} onTickerChange={onTickerChange} />
      <div style={{ marginTop: 10 }}>
        <ExportReportButton />
      </div>
    </div>
  );
}