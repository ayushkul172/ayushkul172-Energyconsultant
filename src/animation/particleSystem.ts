/**
 * Canvas-based Particle System
 *
 * Renders animated particles in the hero section background.
 * - Desktop: 50+ particles with mouse attraction within 150px at 2px/frame
 * - Mobile (<768px): 60% particle reduction (20 particles), no mouse interaction
 * - Reduced motion: static dots, no movement
 *
 * Requirements: 3.3, 3.4, 10.3
 */

export interface ParticleConfig {
  /** Number of particles on desktop (50+). Mobile gets Math.floor(count * 0.4). */
  count: number;
  /** Particle color in CSS format */
  color: string;
  /** Maximum drift speed in px/frame */
  maxSpeed: number;
  /** Mouse attraction radius in pixels */
  mouseRadius: number;
  /** Mouse attraction strength in px/frame */
  mouseStrength: number;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  opacity: number;
}

const DEFAULT_CONFIG: ParticleConfig = {
  count: 50,
  color: '6, 182, 212', // cyan RGB values for rgba()
  maxSpeed: 0.5,
  mouseRadius: 150,
  mouseStrength: 2,
};

export class ParticleSystem {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private particles: Particle[] = [];
  private config: ParticleConfig;
  private animationId: number | null = null;
  private mouseX: number = -1000;
  private mouseY: number = -1000;
  private isMobile: boolean;
  private reducedMotion: boolean;
  private running: boolean = false;

  constructor(
    canvas: HTMLCanvasElement,
    options?: Partial<ParticleConfig> & { isMobile?: boolean; reducedMotion?: boolean }
  ) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Could not get 2D canvas context');
    }
    this.ctx = ctx;
    this.config = { ...DEFAULT_CONFIG, ...options };
    this.isMobile = options?.isMobile ?? window.innerWidth < 768;
    this.reducedMotion = options?.reducedMotion ?? false;

    this.initParticles();
  }

  private getParticleCount(): number {
    if (this.isMobile) {
      return Math.floor(this.config.count * 0.4);
    }
    return this.config.count;
  }

  private initParticles(): void {
    const count = this.getParticleCount();
    const { width, height } = this.canvas;

    this.particles = [];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * this.config.maxSpeed * 2,
        vy: (Math.random() - 0.5) * this.config.maxSpeed * 2,
        radius: Math.random() * 2 + 1, // 1-3px radius
        opacity: Math.random() * 0.6 + 0.2, // 0.2–0.8 opacity
      });
    }
  }

  /** Resize the canvas to match its container. Reinitializes particles. */
  resize(width: number, height: number): void {
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = width * dpr;
    this.canvas.height = height * dpr;
    this.canvas.style.width = `${width}px`;
    this.canvas.style.height = `${height}px`;
    this.ctx.scale(dpr, dpr);

    // Reposition particles within new bounds
    this.particles.forEach((p) => {
      p.x = Math.random() * width;
      p.y = Math.random() * height;
    });
  }

  /** Update mouse position for attraction (no-op on mobile) */
  setMousePosition(x: number, y: number): void {
    if (this.isMobile) return;
    this.mouseX = x;
    this.mouseY = y;
  }

  /** Clear mouse position (mouse left the canvas) */
  clearMousePosition(): void {
    this.mouseX = -1000;
    this.mouseY = -1000;
  }

  /** Start the animation loop */
  start(): void {
    if (this.running) return;
    this.running = true;
    this.animate();
  }

  /** Stop the animation loop */
  stop(): void {
    this.running = false;
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /** Whether the system is currently running */
  isRunning(): boolean {
    return this.running;
  }

  private animate = (): void => {
    if (!this.running) return;

    this.update();
    this.draw();
    this.animationId = requestAnimationFrame(this.animate);
  };

  private update(): void {
    // Reduced motion: no movement, just static dots
    if (this.reducedMotion) return;

    const width = this.canvas.width / (window.devicePixelRatio || 1);
    const height = this.canvas.height / (window.devicePixelRatio || 1);

    for (const particle of this.particles) {
      // Apply mouse attraction (desktop only, within 150px radius)
      if (!this.isMobile) {
        const dx = this.mouseX - particle.x;
        const dy = this.mouseY - particle.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance <= this.config.mouseRadius && distance > 0) {
          // Attract at 2px/frame toward cursor
          const angle = Math.atan2(dy, dx);
          particle.vx += Math.cos(angle) * (this.config.mouseStrength / distance) * this.config.mouseStrength;
          particle.vy += Math.sin(angle) * (this.config.mouseStrength / distance) * this.config.mouseStrength;
        }
      }

      // Apply velocity with damping
      particle.x += particle.vx;
      particle.y += particle.vy;

      // Damping to prevent particles from flying off
      particle.vx *= 0.98;
      particle.vy *= 0.98;

      // Add small random drift
      particle.vx += (Math.random() - 0.5) * 0.05;
      particle.vy += (Math.random() - 0.5) * 0.05;

      // Clamp velocity
      const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
      if (speed > this.config.maxSpeed * 3) {
        particle.vx = (particle.vx / speed) * this.config.maxSpeed * 3;
        particle.vy = (particle.vy / speed) * this.config.maxSpeed * 3;
      }

      // Wrap around edges
      if (particle.x < -10) particle.x = width + 10;
      if (particle.x > width + 10) particle.x = -10;
      if (particle.y < -10) particle.y = height + 10;
      if (particle.y > height + 10) particle.y = -10;
    }
  }

  private draw(): void {
    const width = this.canvas.width / (window.devicePixelRatio || 1);
    const height = this.canvas.height / (window.devicePixelRatio || 1);

    // Clear canvas
    this.ctx.clearRect(0, 0, width, height);

    // Draw each particle as a small circle
    for (const particle of this.particles) {
      this.ctx.beginPath();
      this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
      this.ctx.fillStyle = `rgba(${this.config.color}, ${particle.opacity})`;
      this.ctx.fill();
    }
  }

  /** Destroy the system and clean up */
  destroy(): void {
    this.stop();
    this.particles = [];
  }
}
