export default function Line({ data }) {
  if (data.type === "terminal_error") {
    return (
      <div style={{ color: "var(--atlas-red)" }}>
        <div>{data.error}</div>
        <pre style={{
          whiteSpace: "pre-wrap",
          color: "var(--atlas-red)"
        }}>
          {data.traceback}
        </pre>
      </div>
    );
  }

  const color =
    data.level === "warning"
      ? "var(--atlas-amber)"
      : "var(--atlas-green)";

  return (
    <div style={{ color }}>
      {data.message}
    </div>
  );
}