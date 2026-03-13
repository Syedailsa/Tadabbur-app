interface ControlProps {
  wsRef: React.RefObject<WebSocket | null>;
  connectionStatus: "connected" | "disconnected";
}

export type { ControlProps };
