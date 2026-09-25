document.addEventListener('DOMContentLoaded', () => {
  initParticleCanvas();
  init3DTilt();
  initCounters();
  initFormAnimations();
});

/* -------------------------------------------------------------------
 * Live 3D Floating Blood Cell Particle Background Canvas
 * ------------------------------------------------------------------- */
function initParticleCanvas() {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  let mouse = { x: width / 2, y: height / 2 };

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  class Particle {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.radius = Math.random() * 8 + 3;
      this.vx = (Math.random() - 0.5) * 0.8;
      this.vy = (Math.random() - 0.5) * 0.8;
      this.alpha = Math.random() * 0.5 + 0.2;
      this.pulseSpeed = Math.random() * 0.02 + 0.005;
      this.pulse = Math.random() * Math.PI;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.pulse += this.pulseSpeed;

      if (this.x < 0) this.x = width;
      if (this.x > width) this.x = 0;
      if (this.y < 0) this.y = height;
      if (this.y > height) this.y = 0;

      const dx = mouse.x - this.x;
      const dy = mouse.y - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 140) {
        const force = (140 - dist) / 140;
        this.x -= (dx / dist) * force * 1.5;
        this.y -= (dy / dist) * force * 1.5;
      }
    }

    draw() {
      const currentRadius = this.radius + Math.sin(this.pulse) * 1.5;
      ctx.save();
      ctx.beginPath();
      ctx.arc(this.x, this.y, Math.max(1, currentRadius), 0, Math.PI * 2);

      const gradient = ctx.createRadialGradient(
        this.x - currentRadius * 0.3,
        this.y - currentRadius * 0.3,
        1,
        this.x,
        this.y,
        currentRadius
      );
      gradient.addColorStop(0, `rgba(255, 100, 120, ${this.alpha + 0.2})`);
      gradient.addColorStop(0.7, `rgba(217, 4, 41, ${this.alpha})`);
      gradient.addColorStop(1, `rgba(141, 8, 1, 0)`);

      ctx.fillStyle = gradient;
      ctx.shadowColor = 'rgba(217, 4, 41, 0.4)';
      ctx.shadowBlur = 10;
      ctx.fill();
      ctx.restore();
    }
  }

  const particleCount = Math.min(Math.floor(width / 25), 50);
  const particles = Array.from({ length: particleCount }, () => new Particle());

  function animate() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 130) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(217, 4, 41, ${(1 - dist / 130) * 0.15})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    particles.forEach((p) => {
      p.update();
      p.draw();
    });

    requestAnimationFrame(animate);
  }

  animate();
}

/* -------------------------------------------------------------------
 * 3D Card Hover Tilt — ONLY on dashboard module-cards (NOT form cards)
 * Uses gentle rotation only, NO translateY so buttons stay clickable
 * ------------------------------------------------------------------- */
function init3DTilt() {
  // Only apply tilt to the small dashboard module cards, never to form containers
  const tiltElements = document.querySelectorAll('.module-card');

  tiltElements.forEach((el) => {
    el.addEventListener('mousemove', (e) => {
      const rect = el.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      // Gentle rotation only — no translation that would move the card away
      const rotateX = ((centerY - y) / centerY) * 5;
      const rotateY = ((x - centerX) / centerX) * 5;

      el.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    });

    el.addEventListener('mouseleave', () => {
      el.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg)';
    });
  });
}

/* -------------------------------------------------------------------
 * Statistics Number Count-Up Animation
 * ------------------------------------------------------------------- */
function initCounters() {
  const counters = document.querySelectorAll('.stat-number');
  counters.forEach((counter) => {
    const target = +counter.getAttribute('data-target') || 0;
    const duration = 1500;
    const stepTime = 20;
    const totalSteps = duration / stepTime;
    const increment = target / totalSteps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        counter.textContent = target;
        clearInterval(timer);
      } else {
        counter.textContent = Math.ceil(current);
      }
    }, stepTime);
  });
}

/* -------------------------------------------------------------------
 * Smooth Form Control Interactions
 * ------------------------------------------------------------------- */
function initFormAnimations() {
  const inputs = document.querySelectorAll('.field-group input, .field-group select');
  inputs.forEach((input) => {
    input.addEventListener('focus', () => {
      const group = input.closest('.field-group');
      if (group) group.classList.add('active');
    });
    input.addEventListener('blur', () => {
      const group = input.closest('.field-group');
      if (group) group.classList.remove('active');
    });
  });
}
