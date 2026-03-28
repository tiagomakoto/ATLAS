import { useEffect, useRef } from "react";

export default function useWebSocket(url, onMessage) {
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    let ws;
    let reconnectTimeout;
    let destroyed = false;
    let retryCount = 0;
    const MAX_RETRIES = 5;

    function connect() {
      if (destroyed) return;

      try {
        ws = new WebSocket(url);

        ws.onopen = () => {
          console.log("✓ WS conectado:", url);
          retryCount = 0; // Reset retries on success
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            onMessageRef.current?.(data);
          } catch (e) {
            console.warn("WS parse error:", e);
          }
        };

        ws.onerror = (err) => {
          console.warn("WS error (tentando reconectar):", url);
        };

        ws.onclose = () => {
          if (!destroyed && retryCount < MAX_RETRIES) {
            retryCount++;
            const delay = Math.min(1000 * retryCount, 5000);
            console.log(`🔄 Reconectando em ${delay}ms... (${retryCount}/${MAX_RETRIES})`);
            reconnectTimeout = setTimeout(connect, delay);
          } else if (!destroyed) {
            console.warn("⚠ WS desconectado — máximo de tentativas atingido");
          }
        };
      } catch (e) {
        console.error("WS connection failed:", e);
        if (!destroyed && retryCount < MAX_RETRIES) {
          retryCount++;
          reconnectTimeout = setTimeout(connect, 2000);
        }
      }
    }

    connect();

    return () => {
      destroyed = true;
      clearTimeout(reconnectTimeout);
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close();
      }
    };
  }, [url]);
}