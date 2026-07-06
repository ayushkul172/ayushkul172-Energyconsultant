import { useState, useEffect } from 'react';
import {
  PerformanceMonitor,
  type PerformanceMetrics,
} from '@/animation/performanceMonitor';

/**
 * React hook that subscribes to the PerformanceMonitor singleton
 * and returns reactive performance metrics.
 *
 * Automatically starts the monitor on mount (if not already running)
 * and stops it when no subscribers remain.
 */
export function usePerformanceMonitor(): PerformanceMetrics {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    currentFPS: 60,
    isLowPerformance: false,
    shouldFallback: false,
  });

  useEffect(() => {
    const monitor = PerformanceMonitor.getInstance();

    // Start monitoring if not already running
    if (!monitor.isRunning()) {
      monitor.start();
    }

    const unsubscribe = monitor.subscribe((newMetrics) => {
      setMetrics(newMetrics);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  return metrics;
}
