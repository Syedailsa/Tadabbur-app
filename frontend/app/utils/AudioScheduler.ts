export class AudioScheduler {
  private audioContext: AudioContext | null = null;
  private nextStartTime: number = 0;
  private isBuffering: boolean = true;
  private chunkBuffer: Uint8Array[] = []; 
  
  private minStartChunks = 5; 
  private minPlayThreshold = 4000; 

  constructor() {
  }

  public reset() {
    this.isBuffering = true;
    this.chunkBuffer = [];
    
    if (this.audioContext) {
      this.nextStartTime = this.audioContext.currentTime + 0.1;
    }
  }

  public async scheduleChunk(base64Audio: string) {
    try {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = this.audioContext;

      if (ctx.state === "suspended") {
        await ctx.resume();
      }

      const binaryString = window.atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      this.chunkBuffer.push(bytes);

      const totalBufferedSize = this.chunkBuffer.reduce((acc, chunk) => acc + chunk.length, 0);

      if (this.isBuffering) {
        if (this.chunkBuffer.length < this.minStartChunks) {
          return; 
        }
        this.isBuffering = false;
        await this.processBuffer(true); 
        return;
      }

      if (totalBufferedSize > this.minPlayThreshold) {
        await this.processBuffer(false);
      }

    } catch (e) {
      console.error("Audio Scheduler Error:", e);
    }
  }

  public async flush() {
      if (this.chunkBuffer.length > 0) {
          await this.processBuffer(false);
      }
  }

  private async processBuffer(isStart: boolean) {
    if (!this.audioContext) return;
    const ctx = this.audioContext;

    // Stitch all buffered chunks into one big array
    const totalSize = this.chunkBuffer.reduce((acc, chunk) => acc + chunk.length, 0);
    const combined = new Uint8Array(totalSize);
    let offset = 0;
    for (const chunk of this.chunkBuffer) {
      combined.set(chunk, offset);
      offset += chunk.length;
    }

    this.chunkBuffer = [];

    try {
        const audioBuffer = await ctx.decodeAudioData(combined.buffer as ArrayBuffer);
        
        const source = ctx.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(ctx.destination);

        const now = ctx.currentTime;
        
        if (this.nextStartTime < now) {
            this.nextStartTime = now;
        }

        if (isStart) {
            this.nextStartTime += 0.25; 
        }

        source.start(this.nextStartTime);
        this.nextStartTime += audioBuffer.duration;

    } catch (err) {
        console.warn("Audio decode warning (minor frame drop):", err);
    }
  }
}

export const audioScheduler = new AudioScheduler();