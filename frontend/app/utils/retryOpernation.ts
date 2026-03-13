export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries: number = 5,
  delayMs: number = 1000,
  useExponentialBackoff: boolean = true
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        console.log(`🔄 Retry Attempt ${attempt + 1}/${maxRetries}...`);
      }
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      // Log the specific error to help debugging
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.warn(`⚠️ Attempt ${attempt + 1} failed: ${errorMessage}`);

      if (attempt < maxRetries - 1) {
        // Calculate delay: base delay * 2^attempt
        const waitTime = useExponentialBackoff 
          ? delayMs * Math.pow(2, attempt) 
          : delayMs;
        
        console.log(`⏳ Waiting ${waitTime}ms before next attempt...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  console.error("❌ Max retries reached. Operation failed.");
  throw lastError!;
}

export const wsSendAsync = <T extends { type?: string }>(
  ws: WebSocket | null,
  payload: T,
  maxRetries: number = 8,
  retryDelay: number = 500
): Promise<void> => {
  return retryOperation(async () => {
    return new Promise((resolve, reject) => {
      if (!ws) {
        return reject(new Error("WebSocket is null"));
      }

      if (ws.readyState === WebSocket.OPEN) {
        try {
          ws.send(JSON.stringify(payload));
          console.log("✅ WebSocket message sent:", payload.type);
          resolve();
        } catch (error) {
          reject(error);
        }
      } else if (ws.readyState === WebSocket.CONNECTING) {
        console.log("⏳ WebSocket connecting, attaching listeners...");
        
        const timeout = setTimeout(() => {
          cleanup();
          reject(new Error("WebSocket connection timeout (5s)"));
        }, 5000);

        const onOpen = () => {
          cleanup();
          try {
            ws.send(JSON.stringify(payload));
            resolve();
          } catch (error) {
            reject(error);
          }
        };

        const onError = (ev: Event) => {
          cleanup();
          reject(new Error("WebSocket connection failed during send"));
        };

        const cleanup = () => {
          clearTimeout(timeout);
          ws.removeEventListener('open', onOpen);
          ws.removeEventListener('error', onError);
        };

        ws.addEventListener('open', onOpen, { once: true });
        ws.addEventListener('error', onError, { once: true });
      } else {
        reject(new Error(`WebSocket not ready (state: ${ws.readyState})`));
      }
    });
  }, maxRetries, retryDelay);
};