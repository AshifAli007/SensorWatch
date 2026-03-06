import { useEffect, useRef } from "react";

export default function useWebSocket(url, onMessage) {
  const callbackRef = useRef(onMessage);
  callbackRef.current = onMessage;

  useEffect(() => {
    let ws;
    let reconnectTimer;
    let alive = true;

    function connect() {
      if (!alive) return;
      ws = new WebSocket(url);

      ws.onopen = () => console.log("[ws] connected");

      ws.onmessage = (e) => {
        try {
          callbackRef.current(JSON.parse(e.data));
        } catch {
          /* ignore malformed frames */
        }
      };

      ws.onclose = () => {
        if (alive) {
          console.log("[ws] disconnected — reconnecting in 2s");
          reconnectTimer = setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      alive = false;
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, [url]);
}
