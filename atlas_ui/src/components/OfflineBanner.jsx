import { useEffect, useState } from "react";

export default function OfflineBanner() {
  const [backendDown, setBackendDown] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("/mode", {
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
      letterSpacing: 1
    }}>
      ⚠ BACKEND OFFLINE — dados podem estar desatualizados
    </div>
  );
}
