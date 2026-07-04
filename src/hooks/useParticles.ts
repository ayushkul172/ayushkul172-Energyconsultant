/**
 * useParticles Hook
 *
 * Binds a canvas element to the ParticleSystem lifecycle.
 * Handles resizing, mouse tracking, and cleanup.
 *
 * - Desktop: full particle count with mouse attraction
 * - Mobile (<768px): 60% reduction, no mouse interaction
 * - Reduced motion: static dots, no movement
 *
 * Requirements: 3.3, 3.4, 10.3
 */

import { useEffect, useRef, useCallback } from 'react';
import { ParticleSystem, ParticleConfig } from '@/animation/particleSystem';
import { useReducedMotion } from '@/hooks/useReducedMotion';

interface UseParticlesOptions extends Partial<ParticleConfig> {
  /** Whether the particle system should be active */
  enabled?: boolean;
}

export function useParticles(options: UseParticlesOptions = {}) {
  const { enabled = true, ...particleConfig } = options;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const systemRef = useRef<ParticleSystem | null>(null);
  const reducedMotion = useReducedMotion();

  // Handle mouse move on the canvas container
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!systemRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    systemRef.current.setMousePosition(x, y);
  }, []);

  const handleMouseLeave = useCallback(() => {
    if (!systemRef.current) return;
    systemRef.current.clearMousePosition();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !enabled) return;

    const isMobile = window.innerWidth < 768;

    // Create particle system
    const system = new ParticleSystem(canvas, {
      ...particleConfig,
      isMobile,
      reducedMotion,
    });

    systemRef.current = system;

    // Size the canvas to its parent container
    const parent = canvas.parentElement;
    if (parent) {
      const { width, height } = parent.getBoundingClientRect();
      system.resize(width, height);
    }

    // Start the animation loop
    system.start();

    // Mouse tracking (desktop only)
    if (!isMobile && !reducedMotion) {
      canvas.addEventListener('mousemove', handleMouseMove);
      canvas.addEventListener('mouseleave', handleMouseLeave);
    }

    // Resize handler
    const handleResize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        const { width, height } = parent.getBoundingClientRect();
        system.resize(width, height);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      system.destroy();
      systemRef.current = null;
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, reducedMotion]);

  return { canvasRef };
}
