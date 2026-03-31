import { useEffect, useState } from "react";

export default function OfflineBanner() {
  const [backendDown, setBackendDown] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("http://localhost:8000/mode", {
          signal: AbortSignal.timeout(2000)
        });
        setBackendDown(!res.ok);
      } catch {
        setBackendDown(true);
      }
    };

    check();
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!backendDown) return null;

  return (
    <div style={{
      background: "var(--atlas-red)",
      color: "#fff",
      padding: "6px 16px",
      textAlign: "center",
      fontFamily: "monospace",
      fontSize: 11,
      letterSpacing: 1,
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      zIndex: 9999,
      borderBottom: "2px solid var(--atlas-red)",
      boxShadow: "0 2px 8px rgba(0,0,0,0.3)"
    }}>
      ⚠️ BACKEND OFFLINE — Verifique se o servidor em localhost:8000 está ativo
    </div>
  );
}