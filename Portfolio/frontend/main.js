
// ─── Backend URL ─────────────────────────────────────────────────
// Change this to your deployed backend URL (e.g. Render URL) when going live
const BACKEND_URL = "https://prakhar-portfolio-with-voice-agent.onrender.com";

// ─── Cursor Glow ─────────────────────────────────────────────────
const cursorGlow = document.getElementById('cursor-glow');
document.addEventListener('mousemove', (e) => {
  cursorGlow.style.left = e.clientX + 'px';
  cursorGlow.style.top = e.clientY + 'px';
});

// ─── Background Canvas (floating particles) ───────────────────────
const bgCanvas = document.getElementById('bg-canvas');
const bgCtx = bgCanvas.getContext('2d');
let bgParticles = [];

function resizeBgCanvas() {
  bgCanvas.width = window.innerWidth;
  bgCanvas.height = window.innerHeight;
}
resizeBgCanvas();
window.addEventListener('resize', resizeBgCanvas);

function createBgParticle() {
  return {
    x: Math.random() * bgCanvas.width,
    y: Math.random() * bgCanvas.height,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    radius: Math.random() * 1.5 + 0.5,
    alpha: Math.random() * 0.4 + 0.1,
    color: Math.random() > 0.6 ? '#2563eb' : Math.random() > 0.5 ? '#06b6d4' : '#8b5cf6',
  };
}

for (let i = 0; i < 80; i++) bgParticles.push(createBgParticle());

function animateBg() {
  bgCtx.clearRect(0, 0, bgCanvas.width, bgCanvas.height);
  bgParticles.forEach((p) => {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0 || p.x > bgCanvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > bgCanvas.height) p.vy *= -1;
    bgCtx.beginPath();
    bgCtx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    bgCtx.fillStyle = p.color;
    bgCtx.globalAlpha = p.alpha;
    bgCtx.fill();
    bgCtx.globalAlpha = 1;
  });

  bgCtx.globalAlpha = 0.04;
  bgCtx.strokeStyle = '#2563eb';
  bgCtx.lineWidth = 0.5;
  for (let i = 0; i < bgParticles.length; i++) {
    for (let j = i + 1; j < bgParticles.length; j++) {
      const dx = bgParticles[i].x - bgParticles[j].x;
      const dy = bgParticles[i].y - bgParticles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 120) {
        bgCtx.beginPath();
        bgCtx.moveTo(bgParticles[i].x, bgParticles[i].y);
        bgCtx.lineTo(bgParticles[j].x, bgParticles[j].y);
        bgCtx.stroke();
      }
    }
  }
  bgCtx.globalAlpha = 1;
  requestAnimationFrame(animateBg);
}
animateBg();

// ─── Neural Network Canvas ────────────────────────────────────────
const neuralCanvas = document.getElementById('neural-canvas');
if (neuralCanvas) {
  const nc = neuralCanvas.getContext('2d');
  const nodes = [];
  const LAYERS = [4, 6, 6, 4];
  let nw, nh;

  function sizeNeural() {
    nw = neuralCanvas.offsetWidth || 400;
    nh = neuralCanvas.offsetHeight || 400;
    neuralCanvas.width = nw;
    neuralCanvas.height = nh;
    rebuildNodes();
  }

  function rebuildNodes() {
    nodes.length = 0;
    const layerCount = LAYERS.length;
    LAYERS.forEach((count, li) => {
      const x = (nw / (layerCount + 1)) * (li + 1);
      for (let i = 0; i < count; i++) {
        const y = (nh / (count + 1)) * (i + 1);
        nodes.push({ x, y, layer: li, pulse: Math.random() * Math.PI * 2, speed: 0.02 + Math.random() * 0.02 });
      }
    });
  }

  sizeNeural();

  function animateNeural() {
    nc.clearRect(0, 0, nw, nh);
    const layerCount = LAYERS.length;
    for (let li = 0; li < layerCount - 1; li++) {
      const layerA = nodes.filter(n => n.layer === li);
      const layerB = nodes.filter(n => n.layer === li + 1);
      layerA.forEach(a => {
        layerB.forEach(b => {
          const grad = nc.createLinearGradient(a.x, a.y, b.x, b.y);
          grad.addColorStop(0, 'rgba(37,99,235,0.15)');
          grad.addColorStop(1, 'rgba(6,182,212,0.08)');
          nc.beginPath();
          nc.moveTo(a.x, a.y);
          nc.lineTo(b.x, b.y);
          nc.strokeStyle = grad;
          nc.lineWidth = 0.8;
          nc.stroke();
        });
      });
    }
    nodes.forEach(n => {
      n.pulse += n.speed;
      const glow = (Math.sin(n.pulse) + 1) / 2;
      const r = 4 + glow * 2;
      const alpha = 0.5 + glow * 0.5;
      nc.beginPath();
      nc.arc(n.x, n.y, r, 0, Math.PI * 2);
      const color = n.layer === 0 ? `rgba(37,99,235,${alpha})` :
                    n.layer === layerCount - 1 ? `rgba(6,182,212,${alpha})` :
                    `rgba(139,92,246,${alpha})`;
      nc.fillStyle = color;
      nc.shadowBlur = 10;
      nc.shadowColor = color;
      nc.fill();
      nc.shadowBlur = 0;
    });
    requestAnimationFrame(animateNeural);
  }
  animateNeural();
}

// ─── Hero Particles ───────────────────────────────────────────────
const heroParticlesEl = document.getElementById('hero-particles');
if (heroParticlesEl) {
  for (let i = 0; i < 20; i++) {
    const p = document.createElement('div');
    p.style.cssText = `
      position:absolute;width:${Math.random()*3+1}px;height:${Math.random()*3+1}px;
      border-radius:50%;background:${Math.random()>0.5?'#3b82f6':'#06b6d4'};
      left:${Math.random()*100}%;top:${Math.random()*100}%;
      opacity:${Math.random()*0.5+0.1};
      animation:float-particle ${4+Math.random()*6}s ease-in-out infinite;
      animation-delay:${Math.random()*4}s;
    `;
    heroParticlesEl.appendChild(p);
  }
  const styleEl = document.createElement('style');
  styleEl.textContent = `@keyframes float-particle{0%,100%{transform:translateY(0) translateX(0);opacity:0.2;}33%{transform:translateY(-30px) translateX(10px);opacity:0.6;}66%{transform:translateY(-15px) translateX(-8px);opacity:0.4;}}`;
  document.head.appendChild(styleEl);
}

// ─── Nav Scroll ───────────────────────────────────────────────────
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  const scrollY = window.scrollY;
  nav.classList.toggle('scrolled', scrollY > 60);
  const sections = document.querySelectorAll('section[id]');
  let current = '';
  sections.forEach(s => { if (scrollY >= s.offsetTop - 120) current = s.id; });
  document.querySelectorAll('.nav-links a').forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${current}`);
  });
}, { passive: true });

// ─── Nav burger ───────────────────────────────────────────────────
const burger = document.getElementById('nav-burger');
const mobileNav = document.getElementById('nav-mobile');
burger?.addEventListener('click', () => {
  burger.classList.toggle('open');
  mobileNav.classList.toggle('open');
});
mobileNav?.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', () => {
    burger.classList.remove('open');
    mobileNav.classList.remove('open');
  });
});

// ─── Smooth scroll ────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const target = document.querySelector(a.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ─── Reveal on scroll ─────────────────────────────────────────────
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('revealed');
      entry.target.querySelectorAll('.skill-fill').forEach(bar => {
        bar.style.width = bar.dataset.width + '%';
      });
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
document.querySelectorAll('[data-reveal]').forEach(el => revealObserver.observe(el));

const skillObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.skill-fill').forEach(bar => {
        setTimeout(() => { bar.style.width = bar.dataset.width + '%'; }, 200);
      });
      skillObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.2 });
document.querySelectorAll('.skill-category').forEach(el => skillObserver.observe(el));

// ─── Animated counters ────────────────────────────────────────────
function animateCounter(el, target, duration = 1500) {
  let start = null;
  function step(ts) {
    if (!start) start = ts;
    const progress = Math.min((ts - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * target);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const numberEl = entry.target.querySelector('[data-count]');
      if (numberEl && !numberEl.dataset.animated) {
        numberEl.dataset.animated = 'true';
        animateCounter(numberEl, parseInt(numberEl.dataset.count));
      }
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });
document.querySelectorAll('.stat-card, .achieve-card').forEach(el => counterObserver.observe(el));

// ─── 3D Card Tilt ─────────────────────────────────────────────────
document.querySelectorAll('.tilt-card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / (rect.width / 2);
    const dy = (e.clientY - cy) / (rect.height / 2);
    card.style.transform = `perspective(800px) rotateX(${-dy * 4}deg) rotateY(${dx * 4}deg) translateY(-4px)`;
  });
  card.addEventListener('mouseleave', () => {
    card.style.transform = '';
    card.style.transition = 'transform 0.5s ease';
    setTimeout(() => { card.style.transition = ''; }, 500);
  });
});

// ═══════════════════════════════════════════════════════════════════
// VOICE AGENT MODAL — wired to the real Portfolio RAG backend
// ═══════════════════════════════════════════════════════════════════

const voiceFab        = document.getElementById('voice-fab');
const voiceModal      = document.getElementById('voice-modal');
const voiceModalClose = document.getElementById('voice-modal-close');
const voiceListenBtn  = document.getElementById('voice-listen-btn');
const voiceStatus     = document.getElementById('voice-status');
const agentChatBox    = document.getElementById('agent-chat-box');
const agentTextInput  = document.getElementById('agent-text-input');
const agentSendBtn    = document.getElementById('agent-send-btn');
const speakToggle     = document.getElementById('speak-toggle');

// Open / close modal
voiceFab?.addEventListener('click', () => voiceModal.classList.add('open'));
voiceFab?.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); voiceModal.classList.add('open'); } });
voiceModalClose?.addEventListener('click', closeModal);
voiceModal?.addEventListener('click', (e) => { if (e.target === voiceModal) closeModal(); });

function closeModal() {
  if (isRecording) stopRecording();
  voiceModal.classList.remove('open', 'listening');
  setStatus('Ready — tap the mic or type below');
}

// ── Chat helper ──────────────────────────────────────────────────
function addAgentMessage(text, role /* 'user' | 'assistant' | 'system' */) {
  const div = document.createElement('div');
  div.className = `agent-msg agent-msg-${role}`;
  div.textContent = text;
  agentChatBox.appendChild(div);
  agentChatBox.scrollTop = agentChatBox.scrollHeight;
}

function setStatus(msg) {
  if (voiceStatus) voiceStatus.textContent = msg;
}

// ── TTS ───────────────────────────────────────────────────────────
function speak(text) {
  if (!speakToggle?.checked) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.92;
  utterance.pitch = 1;
  const voices = speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith('en') && v.name.includes('Google'))
                 || voices.find(v => v.lang.startsWith('en'));
  if (preferred) utterance.voice = preferred;
  speechSynthesis.speak(utterance);
}
speechSynthesis.addEventListener('voiceschanged', () => speechSynthesis.getVoices());

// ── Send text to backend /chat ────────────────────────────────────
async function sendToAgent(text) {
  if (!text.trim()) return;
  addAgentMessage(text, 'user');
  setStatus('Thinking...');
  voiceModal.classList.add('listening'); // wave animation while waiting

  try {
    const formData = new FormData();
    formData.append('message', text);

    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const data = await res.json();
    const answer = data.answer || 'Sorry, I could not get a response.';

    addAgentMessage(answer, 'assistant');
    speak(answer);
    setStatus('Ready — tap the mic or type below');
  } catch (err) {
    console.error('Agent error:', err);
    addAgentMessage('Error reaching the backend. Make sure the server is running.', 'system');
    setStatus('Error — is the backend running?');
  } finally {
    voiceModal.classList.remove('listening');
  }
}

// Text input send
agentSendBtn?.addEventListener('click', () => {
  const text = agentTextInput.value.trim();
  if (text) {
    agentTextInput.value = '';
    sendToAgent(text);
  }
});
agentTextInput?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    const text = agentTextInput.value.trim();
    if (text) {
      agentTextInput.value = '';
      sendToAgent(text);
    }
  }
});

// ── Voice recording → /transcribe → /chat ────────────────────────
let mediaRecorder = null;
let audioChunks   = [];
let isRecording   = false;

function setListenBtnIdle() {
  voiceListenBtn.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="23"/>
      <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
    Start Listening`;
}

function setListenBtnRecording() {
  voiceListenBtn.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <rect x="6" y="4" width="4" height="16"/>
      <rect x="14" y="4" width="4" height="16"/>
    </svg>
    Stop`;
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(t => t.stop());
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      await transcribeAndChat(audioBlob);
    };

    mediaRecorder.start();
    isRecording = true;
    voiceModal.classList.add('listening');
    setListenBtnRecording();
    setStatus('Listening… tap again to stop');
  } catch (err) {
    console.error('Mic error:', err);
    addAgentMessage('Could not access microphone. Please check permissions.', 'system');
    setStatus('Microphone access denied');
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  isRecording = false;
  voiceModal.classList.remove('listening');
  setListenBtnIdle();
  setStatus('Processing audio…');
}

async function transcribeAndChat(audioBlob) {
  try {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.webm');

    const res = await fetch(`${BACKEND_URL}/transcribe`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error(`Transcription error: ${res.status}`);
    const data = await res.json();

    if (data.text && data.text.trim()) {
      await sendToAgent(data.text.trim());
    } else {
      addAgentMessage('Could not understand audio. Please try again.', 'system');
      setStatus('Ready — tap the mic or type below');
    }
  } catch (err) {
    console.error('Transcription error:', err);
    addAgentMessage('Error transcribing audio. Please try again.', 'system');
    setStatus('Ready — tap the mic or type below');
  }
}

voiceListenBtn?.addEventListener('click', () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// ─── Learning progress bars ──────────────────────────────────────
const learnObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.learn-bar-fill').forEach(bar => {
        setTimeout(() => { bar.style.width = bar.dataset.width + '%'; }, 200);
      });
      learnObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.2 });
document.querySelectorAll('.learn-card').forEach(el => learnObserver.observe(el));

// ─── Keyboard escape ─────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
    mobileNav?.classList.remove('open');
    burger?.classList.remove('open');
  }
});

// ─── Welcome message in agent chat ───────────────────────────────
window.addEventListener('load', () => {
  addAgentMessage("Hi! I'm Prakhar's AI Assistant", 'assistant');
});
