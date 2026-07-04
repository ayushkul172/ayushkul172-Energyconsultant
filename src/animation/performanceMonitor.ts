/**
 * Performance Monitor
 *
 * Tracks FPS via requestAnimationFrame timestamps and provides performance
 * state to consumers (PageTurner, ParticleSystem) so they can fall back
 * to simpler animations on low-end devices or when frame rate drops.
 *
 * Requirements: 1.6, 9.2
 */

export interface PerformanceMetrics {
  currentFPS: number;
  isLowPerformance: boolean;
  shouldFallback: boolean;
}

// Number of recent frame times to average over
const ROLLING_WINDOW = 10;

// FPS threshold below which we consider performance low
const LOW_FPS_THRESHOLD = 10;

// Duration (ms) that FPS must stay below threshold before triggering fallback
const FALLBACK_DURATION_MS = 200;

/**
 * Detects whether the current device is low-end based on hardware signals.
 * - navigator.hardwareConcurrency < 4 (fewer than 4 logical cores)
 * - navigator.deviceMemory < 4 (less than 4 GB RAM, Chrome-only API)
 */
function detectLowEndDevice(): boolean {
  if (typeof navigator === 'undefined') return false;

  const cores = navigator.hardwareConcurrency;
  if (cores !== undefined && cores < 4) return true;

  // deviceMemory is a non-standard Chrome API
  const memory = (navigator as unknown as { deviceMemory?: number }).deviceMemory;
  if (memory !== undefined && memory < 4) return true;

  return false;
}

type Listener = (metrics: PerformanceMetrics) => void;

/**
 * Singleton class that monitors animation frame rate and exposes
 * performance metrics for consumers to decide on animation complexity.
 */
export class PerformanceMonitor {
  private static instance: PerformanceMonitor | null = null;

  // State
  private _currentFPS: number = 60;
  private _isLowPerformance: boolean = false;
  private _shouldFallback: boolean = false;

  // Internal tracking
  private frameTimes: number[] = [];
  private lastFrameTime: number = 0;
  private lowFPSStartTime: number | null = null;
  private rafId: number | null = null;
  private running: boolean = false;

  // Subscribers
  private listeners: Set<Listener> = new Set();

  private constructor() {
    // Check for low-end device on construction
    this._isLowPerformance = detectLowEndDevice();
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /** Reset the singleton (useful for testing) */
  static resetInstance(): void {
    if (PerformanceMonitor.instance) {
      PerformanceMonitor.instance.stop();
      PerformanceMonitor.instance = null;
    }
  }

  // --- Public getters ---

  get currentFPS(): number {
    return this._currentFPS;
  }

  get isLowPerformance(): boolean {
    return this._isLowPerformance;
  }

  get shouldFallback(): boolean {
    return this._shouldFallback;
  }

  get metrics(): PerformanceMetrics {
    return {
      currentFPS: this._currentFPS,
      isLowPerformance: this._isLowPerformance,
      shouldFallback: this._shouldFallback,
    };
  }

  // --- Lifecycle ---

  start(): void {
    if (this.running) return;
    this.running = true;
    this.lastFrameTime = 0;
    this.frameTimes = [];
    this.lowFPSStartTime = null;
    this.scheduleFrame();
  }

  stop(): void {
    this.running = false;
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  isRunning(): boolean {
    return this.running;
  }

  // --- Subscription ---

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    // Immediately notify with current state
    listener(this.metrics);
    return () => {
      this.listeners.delete(listener);
    };
  }

  // --- Internal ---

  private scheduleFrame(): void {
    this.rafId = requestAnimationFrame((timestamp) => this.onFrame(timestamp));
  }

  private onFrame(timestamp: number): void {
    if (!this.running) return;

    if (this.lastFrameTime > 0) {
      const delta = timestamp - this.lastFrameTime;
      this.frameTimes.push(delta);

      // Keep only the rolling window
      if (this.frameTimes.length > ROLLING_WINDOW) {
        this.frameTimes.shift();
      }

      // Calculate rolling average FPS
      this.updateMetrics(timestamp);
    }

    this.lastFrameTime = timestamp;
    this.scheduleFrame();
  }

  private updateMetrics(currentTimestamp: number): void {
    if (this.frameTimes.length === 0) return;

    // Calculate average frame time from the rolling window
    const avgFrameTime =
      this.frameTimes.reduce((sum, t) => sum + t, 0) / this.frameTimes.length;

    // Convert to FPS (frame time is in ms)
    this._currentFPS = avgFrameTime > 0 ? Math.round(1000 / avgFrameTime) : 60;

    // Check fallback condition: fps < 10 for > 200ms continuously
    // Once shouldFallback is true, it stays true (no flicker back)
    if (!this._shouldFallback) {
      if (this._currentFPS < LOW_FPS_THRESHOLD) {
        if (this.lowFPSStartTime === null) {
          this.lowFPSStartTime = currentTimestamp;
        } else {
          const lowDuration = currentTimestamp - this.lowFPSStartTime;
          if (lowDuration > FALLBACK_DURATION_MS) {
            this._shouldFallback = true;
          }
        }
      } else {
        // FPS recovered, reset the timer
        this.lowFPSStartTime = null;
      }
    }

    // Update isLowPerformance if FPS is consistently below 30
    if (this._currentFPS < 30) {
      this._isLowPerformance = true;
    }

    this.notifyListeners();
  }

  private notifyListeners(): void {
    const metrics = this.metrics;
    for (const listener of this.listeners) {
      listener(metrics);
    }
  }
}

// Export a convenience reference to the singleton
export const performanceMonitor = PerformanceMonitor.getInstance();
