

export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries: number = 8,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      console.log(`🔄 Attempt ${attempt + 1}/${maxRetries}`);
      return await operation();
    } catch (error) {
      lastError = error as Error;
      console.error(`❌ Attempt ${attempt + 1} failed:`, error);

      if (attempt < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }
  }

  throw lastError!;
}

export const wsSendAsync = (
  ws: WebSocket | null,
  payload: any,
  maxRetries: number = 8,
  retryDelay: number = 500
): Promise<void> => {
  return retryOperation(async () => {
    return new Promise((resolve, reject) => {
      if (!ws) {
        reject(new Error("WebSocket is null"));
        return;
      }

      if (ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify(payload));
          console.log("✅ WebSocket message sent:", payload.type);
          resolve();
        } catch (error) {
          console.error("❌ WebSocket send error:", error);
          reject(error);
        }
      } else if (ws.readyState === WebSocket.CONNECTING) {
        console.log("⏳ WebSocket connecting, waiting...");
        
        const timeout = setTimeout(() => {
          ws.removeEventListener('open', onOpen);
          ws.removeEventListener('error', onError);
          reject(new Error("WebSocket connection timeout (5s)"));
        }, 5000);

        const onOpen = () => {
          clearTimeout(timeout);
          ws.removeEventListener('error', onError);
          try {
            ws.send(JSON.stringify(payload));
            console.log("✅ WebSocket message sent after connection:", payload.type);
            resolve();
          } catch (error) {
            reject(error);
          }
        };

        const onError = () => {
          clearTimeout(timeout);
          ws.removeEventListener('open', onOpen);
          reject(new Error("WebSocket connection failed"));
        };

        ws.addEventListener('open', onOpen, { once: true });
        ws.addEventListener('error', onError, { once: true });
        
      } else {
        reject(new Error(`WebSocket not ready (state: ${ws.readyState})`));
      }
    });
  }, maxRetries, retryDelay);
};



