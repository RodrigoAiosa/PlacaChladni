"use strict";
const $ = (id) => document.getElementById(id);
const canvas = $("canvas"), ctx = canvas.getContext("2d");
const PLATE_LABELS = {
  square: "Quadrada (modos m, n)",
  rect: "Retangular (proporção livre)",
  circle: "Circular (Bessel)",
  ring: "Anel (membrana anular)",
  mix: "Superposição de modos",
};
// rótulos dos sliders m / n por tipo de placa
const AXES = {
  square: ["m", "n"], rect: ["m (vertical)", "n (horizontal)"], circle: ["k (anéis)", "n (diâmetros)"],
  ring: ["k (anéis)", "n (diâmetros)"], mix: ["m", "n"],
};

const state = { plate: "square", m: 2, n: 3, sign: 1, aspect: 1.5, mix: 0.5, inner: 0.35, view: "sand", field: null };
let particles = [], raf = null, t0 = 0, audio = null;

// ------------------------------------------------------------------ API
const unpack = (o) => {
  const [h, w] = o.shape;
  const f = new Float32Array(h * w);
  for (let i = 0; i < f.length; i++) f[i] = o.data[i] === -128 ? NaN : o.data[i] / 127;
  return { h, w, f, freq: o.freq };
};
const qs = (extra = {}) => new URLSearchParams({
  plate: state.plate, m: state.m, n: state.n, sign: state.sign, aspect: state.aspect,
  mix: state.mix, inner: state.inner, ...extra,
});

async function loadField() {
  $("loading").hidden = false;
  try {
    const r = await fetch("/api/pattern?" + qs({ res: 200 }));
    const j = await r.json();
    if (j.error) throw new Error(j.error);
    state.field = unpack(j);
    sizeCanvas();
    initParticles();
    $("info").textContent = `frequência relativa ∝ ${j.freq.toFixed(2)}`;
    if (audio) audio.osc.frequency.value = 110 + 60 * Math.sqrt(j.freq);
  } catch (e) {
    $("info").textContent = "erro: " + e.message;
  } finally {
    $("loading").hidden = true;
  }
  draw();
}

// ------------------------------------------------------------------ canvas
function sizeCanvas() {
  const { w, h } = state.field;
  const W = 560;
  canvas.width = W;
  canvas.height = Math.round(W * h / w);
  canvas.parentElement.style.aspectRatio = `${w} / ${h}`;
}

const sample = (F, x, y) => { // amostra bilinear, x,y em [0,1]
  const fx = Math.min(F.w - 1.001, Math.max(0, x * (F.w - 1)));
  const fy = Math.min(F.h - 1.001, Math.max(0, y * (F.h - 1)));
  const x0 = fx | 0, y0 = fy | 0, tx = fx - x0, ty = fy - y0;
  const a = F.f[y0 * F.w + x0], b = F.f[y0 * F.w + x0 + 1], c = F.f[(y0 + 1) * F.w + x0], d = F.f[(y0 + 1) * F.w + x0 + 1];
  return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
};

function initParticles() {
  const F = state.field, N = 14000;
  particles = [];
  while (particles.length < N) {
    const x = Math.random(), y = Math.random();
    if (!Number.isNaN(sample(F, x, y))) particles.push([x, y]);
  }
}

function stepParticles(amp = 1) {
  // passo aleatório proporcional a |w|: onde a placa vibra forte a areia salta,
  // onde |w|≈0 ela fica parada -> acumula nas linhas nodais
  const F = state.field;
  for (const p of particles) {
    const w0 = Math.abs(sample(F, p[0], p[1]));
    const s = 0.05 * amp * (w0 + 0.002);
    let nx = p[0] + (Math.random() - 0.5) * s;
    let ny = p[1] + (Math.random() - 0.5) * s;
    if (nx < 0 || nx > 1 || ny < 0 || ny > 1 || Number.isNaN(sample(F, nx, ny))) continue;
    p[0] = nx; p[1] = ny;
  }
}

function paintField(mode, phase = 1) {
  const F = state.field, W = canvas.width, H = canvas.height;
  const img = ctx.createImageData(W, H);
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const v = sample(F, i / (W - 1), j / (H - 1));
    const o = (j * W + i) * 4;
    if (Number.isNaN(v)) { img.data[o + 3] = 0; continue; }
    let r, g, b;
    if (mode === "lines") { // brilho forte onde |w| ≈ 0
      const k = Math.exp(-Math.pow(Math.abs(v) / 0.045, 2));
      r = 230 * k; g = 201 * k; b = 138 * k;
    } else { // divergente azul ↔ âmbar
      const s = v * phase;
      if (s >= 0) { r = 30 + 225 * s; g = 30 + 150 * s; b = 40; }
      else { r = 30; g = 40 + 110 * -s; b = 60 + 195 * -s; }
    }
    img.data[o] = r; img.data[o + 1] = g; img.data[o + 2] = b; img.data[o + 3] = 255;
  }
  ctx.putImageData(img, 0, 0);
}

function paintSand() {
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = "#0b0d11"; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = "#e6c98a";
  for (const p of particles) ctx.fillRect(p[0] * W, p[1] * H, 1.4, 1.4);
}

function draw(ts = 0) {
  cancelAnimationFrame(raf);
  if (!state.field) return;
  const v = state.view;
  if (v === "sand") {
    for (let k = 0; k < 3; k++) stepParticles();
    paintSand();
    raf = requestAnimationFrame(draw);
  } else if (v === "vibe") {
    paintField("heat", Math.sin(ts / 140));
    raf = requestAnimationFrame(draw);
  } else {
    paintField(v);
  }
}

// ------------------------------------------------------------------ galeria
async function loadGallery() {
  const g = $("gallery");
  g.textContent = "calculando…";
  const r = await fetch("/api/gallery?" + new URLSearchParams({
    plate: state.plate, kmax: $("kmax").value, res: 72, aspect: state.aspect, mix: state.mix, inner: state.inner,
  }));
  const j = await r.json();
  g.textContent = "";
  if (j.error) { g.textContent = j.error; return; }
  for (const it of j.items) {
    const F = unpack({ ...it.w, freq: it.freq });
    const card = document.createElement("div");
    card.className = "card";
    const c = document.createElement("canvas");
    c.width = F.w; c.height = F.h;
    const cx = c.getContext("2d"), img = cx.createImageData(F.w, F.h);
    for (let i = 0; i < F.f.length; i++) {
      const v = F.f[i], o = i * 4;
      if (Number.isNaN(v)) { img.data[o + 3] = 0; continue; }
      const k = Math.exp(-Math.pow(Math.abs(v) / 0.07, 2));
      img.data[o] = 230 * k; img.data[o + 1] = 201 * k; img.data[o + 2] = 138 * k; img.data[o + 3] = 255;
    }
    cx.putImageData(img, 0, 0);
    card.append(c);
    const [a, b] = AXES[state.plate];
    card.append(`${a[0]}=${it.m} ${b[0]}=${it.n}${state.plate === "square" ? (it.sign < 0 ? " −" : " +") : ""}`);
    card.title = `frequência ∝ ${it.freq.toFixed(1)}`;
    card.onclick = () => {
      state.m = it.m; state.n = it.n; state.sign = it.sign;
      syncUI(); loadField();
      scrollTo({ top: 0, behavior: "smooth" });
    };
    g.append(card);
  }
}

// ------------------------------------------------------------------ UI
function syncUI() {
  $("plate").value = state.plate;
  $("m").value = state.m; $("n").value = state.n; $("sign").value = state.sign;
  $("oM").value = state.m; $("oN").value = state.n;
  $("lblM").textContent = AXES[state.plate][0]; $("lblN").textContent = AXES[state.plate][1];
  $("signWrap").hidden = state.plate !== "square";
  $("aspectWrap").hidden = state.plate !== "rect";
  $("mixWrap").hidden = state.plate !== "mix";
  $("innerWrap").hidden = state.plate !== "ring";
  $("m").min = (state.plate === "circle" || state.plate === "ring") ? 1 : 0;
}

let tmr;
const debounce = (fn) => { clearTimeout(tmr); tmr = setTimeout(fn, 150); };

function bind() {
  for (const [id, k] of [["m", "m"], ["n", "n"], ["aspect", "aspect"], ["mix", "mix"], ["inner", "inner"]]) {
    $(id).oninput = (e) => {
      state[k] = +e.target.value;
      const out = { m: "oM", n: "oN", aspect: "oAspect", mix: "oMix", inner: "oInner" }[k];
      $(out).value = state[k];
      debounce(loadField);
      if (["aspect", "mix", "inner"].includes(k)) debounce(loadGallery);
    };
  }
  $("sign").onchange = (e) => { state.sign = +e.target.value; loadField(); };
  $("plate").onchange = (e) => {
    state.plate = e.target.value;
    state.m = state.plate === "circle" || state.plate === "ring" ? 2 : 2;
    state.n = 3; state.sign = 1;
    syncUI(); loadField(); loadGallery();
  };
  $("kmax").oninput = (e) => { $("oK").value = e.target.value; debounce(loadGallery); };
  document.querySelectorAll("input[name=view]").forEach((r) => r.onchange = () => { state.view = r.value; draw(); });
  $("shake").onclick = () => { if (state.field) { initParticles(); if (state.view !== "sand") { state.view = "sand"; document.querySelector("input[value=sand]").checked = true; } draw(); } };
  $("sound").onclick = toggleSound;
}

function toggleSound() {
  const btn = $("sound");
  if (audio) { audio.osc.stop(); audio.ctx.close(); audio = null; btn.classList.remove("on"); return; }
  const ac = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ac.createOscillator(), gain = ac.createGain();
  osc.type = "sine";
  osc.frequency.value = 110 + 60 * Math.sqrt(m2f());
  gain.gain.value = 0.08;
  osc.connect(gain).connect(ac.destination); osc.start();
  audio = { ctx: ac, osc }; btn.classList.add("on");
}
const m2f = () => (state.plate === "square" || state.plate === "mix") ? state.m ** 2 + state.n ** 2 : state.m + state.n * 3;

// ------------------------------------------------------------------ início
(async function init() {
  const sel = $("plate");
  for (const [k, v] of Object.entries(PLATE_LABELS)) sel.append(new Option(v, k));
  bind(); syncUI();
  await loadField();
  loadGallery();
})();
