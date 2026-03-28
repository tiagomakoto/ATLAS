import { useEffect, useState, useRef } from "react";
import useWebSocket from "../hooks/useWebSocket";
import Line from "./Line";

export default function Terminal() {
  const [lines, setLines] = useState([]);
  const endRef = useRef();

  function handleEvent(event) {
    if (
      event.type === "terminal_log" ||
      event.type === "terminal_error"
    ) {
      setLines(prev => [...prev.slice(-200), event]);
    }
  }

  useWebSocket("ws://localhost:8000/ws/events", handleEvent);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div style={{
      background: "var(--atlas-bg)",
      color: "var(--atlas-text-primary)",
      padding: 10,
      fontFamily: "monospace",
      fontSize: 11,
      height: 300,
      overflow: "auto",
      border: "1px solid var(--atlas-border)"
    }}>
      {lines.map((l, i) => (
        <Line key={i} data={l} />
      ))}
      <div ref={endRef} />
    </div>
  );
}