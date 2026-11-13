'use strict';
/* ============================================================
   ライブスイッチャー本体
   ============================================================ */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
function h(tag, props, ...kids) {
  const e = document.createElement(tag);
  if (props) for (const [k, v] of Object.entries(props)) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k === 'style') e.style.cssText = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v);
    else if (k in e && typeof v !== 'string') e[k] = v;
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat(3)) if (c != null && c !== false) e.append(c.nodeType ? c : String(c));
  return e;
}
const hex2rgb = hx => { const n = parseInt(hx.slice(1), 16); return [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255]; };
const rgb2hex = c => '#' + c.map(v => Math.round(clamp(v, 0, 1) * 255).toString(16).padStart(2, '0')).join('');
const pad = (n, l = 2) => String(n).padStart(l, '0');
const fmtTime = s => { s = Math.max(0, Math.floor(s)); return `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`; };

/* ---------------- ソースID（ATEM と同じ番号体系） ---------------- */
const BLK = 0, BARS = 1000, COL1 = 2001, COL2 = 2002, MP1 = 3010, MP1K = 3011, MP2 = 3020, MP2K = 3021;
const BUS = [BLK, 1, 2, 3, 4, MP1, MP2, COL1, COL2, BARS];
const keyTexId = id => (id === MP1K ? MP1 : id === MP2K ? MP2 : id);
const isAlphaKey = id => id === MP1K || id === MP2K;

/* ---------------- 既定の状態 ---------------- */
function defaultInput(n) { return { name: `カメラ${n}`, short: `CAM${n}`, type: 'none', deviceId: '', res: '1080', audio: 'auto', screenAudio: true, fit: 'fit', mirror: false, still: 0, loop: true }; }
function defaultAudioCh() { return { gain: 0, delay: 0, eqOn: true, low: 0, mid: 0, high: 0, compOn: false, thresh: -18, ratio: 3, pan: 0, fader: 0, mode: 'on', mute: false, device: '' }; }
function defaultState() {
  return {
    v: 1, fps: 30, mode: 'cutbus', panel: 'hw', hwAuto: false,
    pgm: 1, pvw: 2,
    trans: {
      style: 'mix', rates: { mix: 30, dip: 30, wipe: 30, dve: 30 }, dipSrc: COL1,
      wipe: { pattern: 0, soft: 0.02, border: 0, borderColor: '#ffffff', reverse: false, flipflop: false },
      dve: { type: 0, dir: 0 },
      next: { bkgd: true, key: false }, prevTrans: false,
    },
    usk: {
      onAir: false, type: 'dve', keyType: 'chroma', fill: 2, key: 2,
      luma: { clip: 0.4, gain: 0.7, invert: false, premult: false },
      chroma: { ck: [-0.29, -0.33], color: '#00b140', sim: 0.12, smooth: 0.08, spill: 0.6, lift: 0 },
      pattern: { pat: 7, size: 0.5, soft: 0.03, x: 0.5, y: 0.5, invert: false },
      dve: { x: 0.78, y: 0.74, size: 0.33, borderW: 0, borderColor: '#ffffff', borderSoft: 0, crop: [0, 0, 0, 0] },
      mask: { on: false, l: 0, r: 0, t: 0, b: 0 }, pipPos: 1,
    },
    dsk: { onAir: false, tie: false, rate: 30, fill: MP1, key: MP1K, premult: true, clip: 0.4, gain: 0.7, invert: false, mask: { on: false, l: 0, r: 0, t: 0, b: 0 } },
    ftb: { rate: 30 },
    colors: { c1: '#1f4fa8', c2: '#ffffff' },
    mp: [{ slot: 0 }, { slot: 1 }],
    inputs: [1, 2, 3, 4].map(defaultInput),
    audio: { in1: defaultAudioCh(), in2: defaultAudioCh(), in3: defaultAudioCh(), in4: defaultAudioCh(), mic1: { ...defaultAudioCh(), mode: 'off' }, mic2: { ...defaultAudioCh(), mode: 'off' }, master: { fader: 0, limiter: true, monitorOn: false, monitorLevel: -6, ftbFollow: true } },
    out: { format: 'mp4', vbr: 12000, abr: 192, whipUrl: '', whipToken: '', sbr: 6000, outSrc: 'pgm' },
    mv: { safe: false, labels: true, meters: true },
    ui: { open: { trans: true, usk: true } , audioSel: 'in1' },
  };
}
function merge(def, saved) {
  if (saved == null || typeof def !== 'object' || Array.isArray(def)) return saved ?? def;
  const o = {};
  for (const k of Object.keys(def)) o[k] = k in saved ? merge(def[k], saved[k]) : def[k];
  if (typeof saved === 'object' && !Array.isArray(saved)) for (const k of Object.keys(saved)) if (!(k in o)) o[k] = saved[k];
  return o;
}
let S;
try { S = merge(defaultState(), JSON.parse(localStorage.getItem('lsw.state.v1') || 'null')); } catch (e) { S = defaultState(); }
S.inputs = [0, 1, 2, 3].map(i => merge(defaultInput(i + 1), S.inputs[i]));
let saveT = 0;
function save() { clearTimeout(saveT); saveT = setTimeout(() => { try { localStorage.setItem('lsw.state.v1', JSON.stringify(S)); } catch (e) {} }, 300); }

/* ---------------- 実行時 ---------------- */
const R = {
  t: 0, auto: false, tbarBase: 0, tbarV: 0, dragging: false,
  dskT: S.dsk.onAir ? 1 : 0, dskAuto: false,
  ftbT: 0, ftbAuto: false, ftbOn: false,
  pick: null, last: performance.now(), frames: 0, fpsT: performance.now(), fps: 0,
};
let engine, audio, glCanvas, mvCanvas, mvCtx, pgmStream = null;
const inputs = [];    // InputSource
const pool = [];      // メディアプール {name, img, url}
const POOL_N = 20;

function toast(msg, err) {
  const t = $('#toast'); t.textContent = msg; t.className = 'toast on' + (err ? ' err' : '');
  clearTimeout(toast._t); toast._t = setTimeout(() => t.className = 'toast', err ? 4500 : 2200);
}

function srcLabel(id, short) {
  if (id >= 1 && id <= 4) { const c = S.inputs[id - 1]; return short ? c.short : c.name; }
  const m = { [BLK]: ['BLK', 'ブラック'], [BARS]: ['BARS', 'カラーバー'], [COL1]: ['COL1', 'カラー1'], [COL2]: ['COL2', 'カラー2'], [MP1]: ['MP1', 'メディアプレーヤー1'], [MP1K]: ['MP1K', 'MP1 キー'], [MP2]: ['MP2', 'メディアプレーヤー2'], [MP2K]: ['MP2K', 'MP2 キー'] }[id];
  return m ? m[short ? 0 : 1] : '?';
}
const srcOpts = (keys) => [...BUS, ...(keys ? [MP1K, MP2K] : [])].map(id => [id, srcLabel(id)]);

/* ============================================================
   入力ソース
   ============================================================ */
class InputSource {
  constructor(n) { this.n = n; this.video = null; this.stream = null; this.audioStream = null; this.status = '未設定'; this.live = false; this.kind = 'none'; this.token = 0; }
  newVideo() {
    if (this.video) { this.video.remove(); }
    const v = h('video', { playsInline: true, autoplay: true, muted: true });
    v.setAttribute('playsinline', ''); v.muted = true;
    $('#hiddenMedia').append(v);
    this.video = v; return v;
  }
  stop() {
    for (const s of [this.stream, this.audioStream]) if (s) s.getTracks().forEach(t => t.stop());
    this.stream = this.audioStream = null;
    if (this.video) { this.video.pause(); this.video.srcObject = null; this.video.removeAttribute('src'); this.video.load(); this.video.remove(); this.video = null; }
    if (this.fileUrl) { URL.revokeObjectURL(this.fileUrl); this.fileUrl = null; }
    this.live = false;
    audio && audio.ch('in' + this.n).setSource(null);
    engine && engine.setBlank(this.n, 1);
  }
  async apply(opts = {}) {
    const cfg = S.inputs[this.n - 1];
    const tok = ++this.token;
    this.stop();
    this.kind = cfg.type;
    try {
      if (cfg.type === 'none') { this.status = '未設定'; }
      else if (cfg.type === 'bars') { this.status = 'カラーバー'; this.uploadStatic(barsCanvas()); }
      else if (cfg.type === 'still') { const p = pool[cfg.still]; if (p) { this.uploadStatic(p.img); this.status = `静止画 ${cfg.still + 1}`; } else this.status = '静止画スロットが空です'; }
      else if (cfg.type === 'camera') {
        const res = cfg.res === '720' ? [1280, 720] : cfg.res === '2160' ? [3840, 2160] : [1920, 1080];
        const c = { width: { ideal: res[0] }, height: { ideal: res[1] }, frameRate: { ideal: S.fps } };
        if (cfg.deviceId) c.deviceId = { exact: cfg.deviceId };
        const st = await navigator.mediaDevices.getUserMedia({ video: c, audio: false });
        if (tok !== this.token) { st.getTracks().forEach(t => t.stop()); return; }
        this.stream = st;
        const v = this.newVideo(); v.srcObject = st; await v.play().catch(() => {});
        const tr = st.getVideoTracks()[0];
        if (!cfg.deviceId) { cfg.deviceId = tr.getSettings().deviceId || ''; save(); }
        tr.onended = () => { this.live = false; this.status = '信号が切れました'; syncAll(); };
        this.status = tr.label || 'カメラ';
        await this.applyCamAudio(cfg, tr.label, tok);
      } else if (cfg.type === 'screen') {
        if (!opts.gesture) { this.status = '「画面を選ぶ」を押してください'; syncAll(); return; }
        const st = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: { ideal: S.fps }, width: { ideal: 1920 }, height: { ideal: 1080 } }, audio: !!cfg.screenAudio });
        if (tok !== this.token) { st.getTracks().forEach(t => t.stop()); return; }
        this.stream = st;
        const v = this.newVideo(); v.srcObject = st; await v.play().catch(() => {});
        st.getVideoTracks()[0].onended = () => { this.live = false; this.status = '画面共有が終了しました'; syncAll(); };
        this.status = '画面共有';
        audio.ch('in' + this.n).setSource(audio.fromStream(st));
      } else if (cfg.type === 'file') {
        if (!opts.file) { this.status = '「ファイルを選ぶ」を押してください'; syncAll(); return; }
        const v = this.newVideo();
        this.fileUrl = URL.createObjectURL(opts.file);
        v.src = this.fileUrl; v.loop = !!cfg.loop; v.muted = false;
        audio.ch('in' + this.n).setSource(audio.fromElement(v));
        await v.play().catch(() => {});
        this.status = opts.file.name;
      }
    } catch (e) {
      console.warn(e);
      this.status = 'エラー: ' + (e.name === 'NotAllowedError' ? 'アクセスが許可されていません' : e.name === 'NotFoundError' || e.name === 'OverconstrainedError' ? 'デバイスが見つかりません' : e.message);
    }
    syncAll();
  }
  async applyCamAudio(cfg, label, tok) {
    let devId = null;
    if (cfg.audio === 'none') return;
    if (cfg.audio === 'auto') {
      const devs = await navigator.mediaDevices.enumerateDevices();
      const base = (label || '').replace(/\s*\(.*?\)\s*/g, '').trim().toLowerCase();
      const m = devs.find(d => d.kind === 'audioinput' && base && d.label && (d.label.toLowerCase().includes(base) || base.includes(d.label.replace(/\s*\(.*?\)\s*/g, '').trim().toLowerCase())) && d.deviceId !== 'default');
      if (!m) return;
      devId = m.deviceId;
    } else devId = cfg.audio;
    try {
      const st = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: { exact: devId }, echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 2 } });
      if (tok !== this.token) { st.getTracks().forEach(t => t.stop()); return; }
      this.audioStream = st;
      audio.ch('in' + this.n).setSource(audio.fromStream(st));
    } catch (e) { console.warn('audio', e); }
  }
  uploadStatic(el) {
    const w = el.naturalWidth || el.videoWidth || el.width, hh = el.naturalHeight || el.videoHeight || el.height;
    const cfg = S.inputs[this.n - 1];
    engine.upload(this.n, el, w, hh, { fit: cfg.fit, mirror: cfg.mirror });
    this.live = true; this.staticEl = el;
  }
  restatic() { if ((this.kind === 'bars' || this.kind === 'still') && this.staticEl) this.uploadStatic(this.staticEl); }
  tick() {
    const v = this.video;
    if (!v) return;
    if (v.readyState >= 2 && v.videoWidth) {
      const cfg = S.inputs[this.n - 1];
      engine.upload(this.n, v, v.videoWidth, v.videoHeight, { fit: cfg.fit, mirror: cfg.mirror });
      this.live = true;
      this.res = `${v.videoWidth}×${v.videoHeight}`;
    }
  }
  outStream() {
    if (this.stream && this.stream.getVideoTracks().length) return this.stream;
    if (this.video && this.video.captureStream) { try { return this.video.captureStream(); } catch (e) {} }
    return null;
  }
}

let _bars;
function barsCanvas() {
  if (_bars) return _bars;
  const c = document.createElement('canvas'); c.width = 1920; c.height = 1080;
  const x = c.getContext('2d');
  const top = ['#bfbfbf', '#bfbf00', '#00bfbf', '#00bf00', '#bf00bf', '#bf0000', '#0000bf'];
  const w = 1920 / 7;
  top.forEach((col, i) => { x.fillStyle = col; x.fillRect(Math.round(i * w), 0, Math.ceil(w), 720); });
  const mid = ['#0000bf', '#131313', '#bf00bf', '#131313', '#00bfbf', '#131313', '#bfbfbf'];
  mid.forEach((col, i) => { x.fillStyle = col; x.fillRect(Math.round(i * w), 720, Math.ceil(w), 90); });
  const bw = 1920 / 7 * 5 / 4;
  ['#00214c', '#ffffff', '#32006a', '#131313'].forEach((col, i) => { x.fillStyle = col; x.fillRect(Math.round(i * bw), 810, Math.ceil(bw), 270); });
  x.fillStyle = '#131313'; x.fillRect(Math.round(5 * w), 810, 1920, 270);
  ['#090909', '#131313', '#1d1d1d'].forEach((col, i) => { x.fillStyle = col; x.fillRect(Math.round(5 * w + i * w / 3), 810, Math.ceil(w / 3), 270); });
  return (_bars = c);
}

/* ============================================================
   メディアプール（IndexedDB）
   ============================================================ */
let dbP;
function db() {
  if (!dbP) dbP = new Promise((res, rej) => {
    const r = indexedDB.open('live-switcher', 1);
    r.onupgradeneeded = () => { r.result.createObjectStore('stills'); r.result.createObjectStore('kv'); };
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
  return dbP;
}
async function idb(store, mode, fn) {
  const d = await db();
  return new Promise((res, rej) => { const tx = d.transaction(store, mode); const r = fn(tx.objectStore(store)); tx.oncomplete = () => res(r && r.result); tx.onerror = () => rej(tx.error); });
}
async function loadImg(blob) {
  const url = URL.createObjectURL(blob);
  const img = new Image(); img.src = url;
  await img.decode();
  return { img, url };
}
async function loadPool() {
  for (let i = 0; i < POOL_N; i++) {
    try {
      const rec = await idb('stills', 'readonly', s => s.get(i));
      if (rec && rec.blob) { const { img, url } = await loadImg(rec.blob); pool[i] = { name: rec.name, img, url }; }
    } catch (e) { console.warn(e); }
  }
}
async function setStill(i, blob, name) {
  if (pool[i]) URL.revokeObjectURL(pool[i].url);
  if (!blob) { pool[i] = null; await idb('stills', 'readwrite', s => s.delete(i)); }
  else {
    const { img, url } = await loadImg(blob);
    pool[i] = { name: name || `Still ${i + 1}`, img, url };
    await idb('stills', 'readwrite', s => s.put({ blob, name: pool[i].name }, i));
  }
  updateMP(); inputs.forEach(s => s.kind === 'still' && S.inputs[s.n - 1].still === i && s.apply());
  renderMediaPane(); syncAll();
}
function freeSlot() { for (let i = 0; i < POOL_N; i++) if (!pool[i]) return i; return -1; }
function updateMP() {
  if (!engine) return;
  [MP1, MP2].forEach((id, i) => {
    const p = pool[S.mp[i].slot];
    if (p) engine.upload(id, p.img, p.img.naturalWidth, p.img.naturalHeight, { fit: 'fit', alpha: true });
    else engine.setBlank(id, 0);
  });
}
function updateColors() { if (!engine) return; engine.setColor(COL1, hex2rgb(S.colors.c1)); engine.setColor(COL2, hex2rgb(S.colors.c2)); }

/* ============================================================
   スイッチャーロジック
   ============================================================ */
const STYLES = ['mix', 'dip', 'wipe', 'dve'];
const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const rateOf = () => S.trans.rates[S.trans.style];
const inTrans = () => R.t > 0;

function setPreview(id) { if (R.auto) return; S.pvw = id; changed(); }
function setProgram(id) {
  if (S.pgm === id) return;
  S.pgm = id; if (R.t > 0 && !S.trans.prevTrans) { R.t = 0; R.auto = false; R.tbarV = R.tbarBase; }
  changed();
}
function finishTransition() {
  const n = S.trans.next;
  if (!S.trans.prevTrans) {
    if (n.bkgd) [S.pgm, S.pvw] = [S.pvw, S.pgm];
    if (n.key) S.usk.onAir = !S.usk.onAir;
    if (S.dsk.tie) { S.dsk.onAir = !S.dsk.onAir; R.dskT = S.dsk.onAir ? 1 : 0; }
    if (S.trans.style === 'wipe' && S.trans.wipe.flipflop) S.trans.wipe.reverse = !S.trans.wipe.reverse;
  }
  R.t = 0; R.auto = false;
  changed();
}
function cut() {
  if (R.auto) return;
  R.t = 0; R.tbarV = R.tbarBase; finishTransition();
}
function autoTrans() {
  if (R.auto) return;
  R.auto = true; R.autoBase = R.tbarBase;
  if (R.t <= 0) R.t = 0.00001;
  changed();
}
function tbarSet(v) {
  if (R.auto) return;
  R.tbarV = clamp(v, 0, 1);
  const t = R.tbarBase === 0 ? R.tbarV : 1 - R.tbarV;
  if (t >= 1) { R.tbarBase = R.tbarV >= 0.5 ? 1 : 0; R.tbarV = R.tbarBase; finishTransition(); return; }
  R.t = Math.max(0, t);
}
function keyOnAir(on) { S.usk.onAir = on; changed(); }
function dskOnAir() { R.dskAuto = false; S.dsk.onAir = !S.dsk.onAir; R.dskT = S.dsk.onAir ? 1 : 0; changed(); }
function dskAutoGo() { if (R.dskAuto) return; R.dskAuto = true; R.dskTarget = S.dsk.onAir ? 0 : 1; changed(); }
function ftbGo() { if (R.ftbAuto) return; R.ftbAuto = true; R.ftbTarget = R.ftbOn ? 0 : 1; changed(); }
function setStyle(st) { S.trans.style = st; changed(); }
function pipSet(n) { S.usk.type = 'dve'; S.usk.fill = n; S.usk.key = n; S.usk.onAir = true; changed(); }
const PIP_POS = [[0.22, 0.74], [0.78, 0.74], [0.78, 0.26], [0.22, 0.26], [0.5, 0.5]];
function pipPos(i) { S.usk.pipPos = i % PIP_POS.length; const p = PIP_POS[S.usk.pipPos]; S.usk.dve.x = p[0]; S.usk.dve.y = p[1]; changed(); }

/** 入力ボタン（ハードウェアパネル／キーボード）: モードに応じて動く */
function inputPress(id) {
  if (S.mode === 'pp') { setPreview(id); return; }
  if (S.hwAuto) { if (R.auto || id === S.pgm) return; S.pvw = id; autoTrans(); }
  else { if (R.auto) return; const old = S.pgm; S.pgm = id; if (S.pvw === id) S.pvw = old; R.t = 0; changed(); }
}

function advance(dt) {
  const fps = S.fps;
  if (R.auto) {
    R.t += dt * fps / Math.max(1, rateOf());
    const v = R.autoBase === 0 ? R.t : 1 - R.t;
    R.tbarV = clamp(v, 0, 1);
    if (R.t >= 1) { R.tbarBase = R.autoBase === 0 ? 1 : 0; R.tbarV = R.tbarBase; finishTransition(); }
  }
  if (R.dskAuto) {
    const step = dt * fps / Math.max(1, S.dsk.rate);
    R.dskT += R.dskTarget > R.dskT ? step : -step;
    if ((R.dskTarget === 1 && R.dskT >= 1) || (R.dskTarget === 0 && R.dskT <= 0)) { R.dskT = R.dskTarget; R.dskAuto = false; S.dsk.onAir = R.dskT === 1; changed(); }
  }
  if (R.ftbAuto) {
    const step = dt * fps / Math.max(1, S.ftb.rate);
    R.ftbT += R.ftbTarget > R.ftbT ? step : -step;
    if ((R.ftbTarget === 1 && R.ftbT >= 1) || (R.ftbTarget === 0 && R.ftbT <= 0)) { R.ftbT = R.ftbTarget; R.ftbAuto = false; R.ftbOn = R.ftbT === 1; changed(); }
  }
}

/* ---------- 描画スペック ---------- */
function bgSpec(a, b, t) {
  const tr = S.trans;
  return {
    a, b, t, mode: tr.style, dip: tr.dipSrc,
    wipe: { pattern: tr.wipe.pattern, soft: tr.wipe.soft, border: tr.wipe.border, rev: tr.wipe.reverse, borderCol: hex2rgb(tr.wipe.borderColor) },
    dve: { type: tr.dve.type, dir: DIRS[tr.dve.dir] },
  };
}
function keyVis(onAir, selected, t) {
  if (!selected || t <= 0) return { vis: onAir ? 1 : 0 };
  const tr = S.trans;
  if (tr.style === 'wipe') return { vis: 1, kw: onAir ? 2 : 1, kwt: t, kwpat: tr.wipe.pattern, kwsoft: Math.max(tr.wipe.soft, 0.005), kwrev: tr.wipe.reverse };
  return { vis: onAir ? 1 - t : t };
}
function uskParams() {
  const u = S.usk, k = { type: u.type, fill: u.fill };
  if (u.type === 'luma') Object.assign(k, { key: keyTexId(u.key), useAlpha: isAlphaKey(u.key), clip: u.luma.clip, gain: u.luma.gain, invert: u.luma.invert, premult: u.luma.premult });
  else if (u.type === 'chroma') Object.assign(k, { ck: u.chroma.ck, sim: u.chroma.sim, smooth: u.chroma.smooth, spill: u.chroma.spill, lift: u.chroma.lift });
  else if (u.type === 'pattern') Object.assign(k, { pat: u.pattern.pat, psize: u.pattern.size, psoft: u.pattern.soft, ppos: [u.pattern.x, u.pattern.y], invert: u.pattern.invert });
  else { const d = u.dve; Object.assign(k, { rect: [d.x, d.y, d.size, d.size], borderW: d.borderW, borderSoft: d.borderSoft, borderCol: hex2rgb(d.borderColor), crop: d.crop }); }
  if (u.type !== 'dve' && u.mask.on) Object.assign(k, { maskOn: true, mask: [u.mask.l, u.mask.r, u.mask.b, u.mask.t] });
  return k;
}
function dskParams() {
  const d = S.dsk;
  const k = { type: 'luma', fill: d.fill, key: keyTexId(d.key), useAlpha: isAlphaKey(d.key), clip: d.clip, gain: d.gain, invert: d.invert, premult: d.premult };
  if (d.mask.on) Object.assign(k, { maskOn: true, mask: [d.mask.l, d.mask.r, d.mask.b, d.mask.t] });
  return k;
}
function buildSpecs() {
  const n = S.trans.next, t = R.t;
  const uskP = uskParams(), dskP = dskParams();
  const transSpec = {
    bg: bgSpec(S.pgm, S.pvw, n.bkgd ? t : 0),
    usk: { ...uskP, ...keyVis(S.usk.onAir, n.key, t) },
    dsk: { ...dskP, ...(S.dsk.tie && t > 0 && !R.dskAuto ? keyVis(S.dsk.onAir, true, t) : { vis: R.dskT }) },
    ftb: R.ftbT,
  };
  const staticPgm = {
    bg: bgSpec(S.pgm, S.pvw, 0), usk: { ...uskP, vis: S.usk.onAir ? 1 : 0 }, dsk: { ...dskP, vis: R.dskT }, ftb: R.ftbT,
  };
  const nextPvw = {
    bg: bgSpec(n.bkgd ? S.pvw : S.pgm, S.pvw, 0),
    usk: { ...uskP, vis: (n.key ? !S.usk.onAir : S.usk.onAir) ? 1 : 0 },
    dsk: { ...dskP, vis: S.dsk.tie ? (S.dsk.onAir ? 0 : 1) : R.dskT }, ftb: 0,
  };
  if (S.trans.prevTrans) return { pgm: staticPgm, pvw: t > 0 ? { ...transSpec, ftb: 0 } : nextPvw };
  return { pgm: transSpec, pvw: nextPvw };
}
function specSources(sp) {
  const s = new Set([sp.bg.a]);
  if (sp.bg.t > 0) s.add(sp.bg.b);
  if (sp.usk && (sp.usk.vis > 0 || sp.usk.kw)) s.add(sp.usk.fill);
  if (sp.dsk && (sp.dsk.vis > 0 || sp.dsk.kw)) s.add(sp.dsk.fill);
  return s;
}
function programLevel(n) {
  // AFV 用：入力 n が番組にどれだけ出ているか
  const t = S.trans.prevTrans ? 0 : R.t, bk = S.trans.next.bkgd;
  let lv = 0;
  if (S.pgm === n) lv = Math.max(lv, bk ? 1 - t : 1);
  if (S.pvw === n && bk && t > 0) lv = Math.max(lv, t);
  return lv;
}

/* ============================================================
   マルチビュー
   ============================================================ */
const MV_TILES = [
  { id: 'pvw', x: 0, y: 0, w: 960, h: 540, label: 'プレビュー' },
  { id: 'pgm', x: 960, y: 0, w: 960, h: 540, label: 'プログラム' },
  { id: 1, x: 0, y: 540, w: 480, h: 270 }, { id: 2, x: 480, y: 540, w: 480, h: 270 },
  { id: 3, x: 960, y: 540, w: 480, h: 270 }, { id: 4, x: 1440, y: 540, w: 480, h: 270 },
  { id: MP1, x: 0, y: 810, w: 480, h: 270 },
  { st: 'rec', x: 480, y: 810, w: 480, h: 270 }, { st: 'stream', x: 960, y: 810, w: 480, h: 270 }, { st: 'audio', x: 1440, y: 810, w: 480, h: 270 },
];
const GLTILES = MV_TILES.filter(t => !t.st).map(t => ({ id: t.id, x: t.x + 2, y: t.y + 2, w: t.w - 4, h: t.h - 4 }));
const FONT = '-apple-system, BlinkMacSystemFont, "Hiragino Sans", "Hiragino Kaku Gothic ProN", sans-serif';

function rr(c, x, y, w, hh, r) { c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + hh, r); c.arcTo(x + w, y + hh, x, y + hh, r); c.arcTo(x, y + hh, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath(); }
function dbFrac(db) { return db <= -60 || !isFinite(db) ? 0 : clamp((db + 60) / 60, 0, 1); }
function meterGrad(c, x, y, w, hh) {
  const g = c.createLinearGradient(0, y + hh, 0, y);
  g.addColorStop(0, '#1fc94f'); g.addColorStop(0.7, '#1fc94f'); g.addColorStop(0.82, '#f2d21b'); g.addColorStop(0.95, '#ff3a2e'); g.addColorStop(1, '#ff3a2e');
  return g;
}
function drawMeter(c, x, y, w, hh, db) {
  c.fillStyle = 'rgba(0,0,0,.65)'; c.fillRect(x, y, w, hh);
  const f = dbFrac(db);
  c.fillStyle = meterGrad(c, x, y, w, hh); c.fillRect(x + 1, y + hh * (1 - f), w - 2, hh * f);
}

function drawMV(pgmSet, pvwSet, meters) {
  const c = mvCtx;
  c.drawImage(glCanvas, 0, 0);
  c.textAlign = 'center'; c.textBaseline = 'middle';
  for (const t of MV_TILES) {
    if (t.st) { drawStatusTile(c, t, meters); continue; }
    const big = t.w > 500;
    let label = t.label || srcLabel(t.id);
    if (typeof t.id === 'number' && t.id >= 1 && t.id <= 4) {
      const src = inputs[t.id - 1];
      if (!src || !src.live) {
        c.fillStyle = '#5b5d63'; c.font = `600 22px ${FONT}`;
        c.fillText(S.inputs[t.id - 1].type === 'none' ? '入力なし' : '信号なし', t.x + t.w / 2, t.y + t.h / 2 - 12);
      }
      if (S.mv.meters && meters) {
        const db = meters['in' + t.id];
        drawMeter(c, t.x + 10, t.y + 12, 10, t.h - 70, db);
      }
    }
    if (t.id === MP1 && !pool[S.mp[0].slot]) { c.fillStyle = '#5b5d63'; c.font = `600 22px ${FONT}`; c.fillText('静止画なし', t.x + t.w / 2, t.y + t.h / 2 - 12); }
    if (S.mv.safe && big) {
      c.strokeStyle = 'rgba(255,255,255,.35)'; c.lineWidth = 1.5;
      c.strokeRect(t.x + t.w * 0.05, t.y + t.h * 0.05, t.w * 0.9, t.h * 0.9);
      c.strokeRect(t.x + t.w * 0.1, t.y + t.h * 0.1, t.w * 0.8, t.h * 0.8);
    }
    // タリー
    let tally = null;
    if (t.id === 'pgm') tally = '#ff2d2d'; else if (t.id === 'pvw') tally = '#22d257';
    else if (pgmSet.has(t.id)) tally = '#ff2d2d'; else if (pvwSet.has(t.id)) tally = '#22d257';
    if (tally) { c.strokeStyle = tally; c.lineWidth = big ? 6 : 6; c.strokeRect(t.x + 5, t.y + 5, t.w - 10, t.h - 10); }
    if (S.mv.labels) {
      c.font = `700 ${big ? 26 : 21}px ${FONT}`;
      const tw = c.measureText(label).width + 26, lh = big ? 38 : 32;
      const lx = t.x + t.w / 2 - tw / 2, ly = t.y + t.h - lh - 12;
      c.fillStyle = tally === '#ff2d2d' ? 'rgba(200,20,20,.88)' : tally === '#22d257' ? 'rgba(20,150,60,.88)' : 'rgba(0,0,0,.62)';
      rr(c, lx, ly, tw, lh, 5); c.fill();
      c.fillStyle = '#fff'; c.fillText(label, t.x + t.w / 2, ly + lh / 2 + 1);
    }
    if (t.id === 'pgm') {
      if (R.ftbT > 0) { c.font = `800 22px ${FONT}`; c.fillStyle = '#ff2d2d'; c.textAlign = 'right'; c.fillText(R.ftbOn && !R.ftbAuto ? 'FADE TO BLACK' : 'FTB…', t.x + t.w - 22, t.y + 30); c.textAlign = 'center'; }
      if (Rec.on) { c.fillStyle = '#ff2d2d'; c.beginPath(); c.arc(t.x + 30, t.y + 30, 9, 0, 7); c.fill(); c.font = `700 20px ${FONT}`; c.textAlign = 'left'; c.fillStyle = '#fff'; c.fillText('REC ' + fmtTime((performance.now() - Rec.start) / 1000), t.x + 46, t.y + 31); c.textAlign = 'center'; }
    }
    if (t.id === 'pvw' && R.pick) { c.font = `700 22px ${FONT}`; c.fillStyle = '#ffc21a'; c.fillText('クリックしてキー色を選択', t.x + t.w / 2, t.y + 34); }
  }
  // グリッド線
  c.strokeStyle = 'rgba(255,255,255,.55)'; c.lineWidth = 2;
  c.beginPath();
  c.moveTo(960, 0); c.lineTo(960, 540); c.moveTo(0, 540); c.lineTo(1920, 540); c.moveTo(0, 810); c.lineTo(1920, 810);
  for (const x of [480, 960, 1440]) { c.moveTo(x, 540); c.lineTo(x, 1080); }
  c.stroke();
}
function drawStatusTile(c, t, meters) {
  c.fillStyle = '#121316'; c.fillRect(t.x + 2, t.y + 2, t.w - 4, t.h - 4);
  const cx = t.x + t.w / 2;
  c.textAlign = 'center';
  if (t.st === 'rec') {
    const on = Rec.on;
    c.fillStyle = on ? '#ff2d2d' : '#3a3c42'; c.beginPath(); c.arc(cx - 70, t.y + 80, 14, 0, 7); c.fill();
    c.font = `800 34px ${FONT}`; c.fillStyle = on ? '#fff' : '#8a8c92'; c.textAlign = 'left'; c.fillText('REC', cx - 46, t.y + 82); c.textAlign = 'center';
    c.font = `500 40px ui-monospace, Menlo, monospace`; c.fillStyle = on ? '#fff' : '#5b5d63';
    c.fillText(on ? fmtTime((performance.now() - Rec.start) / 1000) : '00:00:00', cx, t.y + 145);
    c.font = `500 18px ${FONT}`; c.fillStyle = '#8a8c92';
    c.fillText(on ? (Rec.dir ? 'フォルダに保存中' : '停止時にダウンロード') : (Rec.dir ? '保存先: ' + Rec.dir.name : '保存先: ダウンロード'), cx, t.y + 195);
    c.fillText('録画', cx, t.y + 232);
  } else if (t.st === 'stream') {
    const on = Stream.state === 'live', con = Stream.state === 'connecting';
    c.font = `800 34px ${FONT}`; c.fillStyle = on ? '#ff2d2d' : con ? '#ffc21a' : '#8a8c92';
    c.fillText(on ? 'ON AIR' : con ? '接続中…' : 'OFF AIR', cx, t.y + 82);
    c.font = `500 40px ui-monospace, Menlo, monospace`; c.fillStyle = on ? '#fff' : '#5b5d63';
    c.fillText(on ? fmtTime((performance.now() - Stream.start) / 1000) : '00:00:00', cx, t.y + 145);
    c.font = `500 18px ${FONT}`; c.fillStyle = '#8a8c92';
    c.fillText(on ? `${Stream.kbps | 0} kbps` : (S.out.whipUrl ? 'WHIP 配信' : '配信先未設定'), cx, t.y + 195);
    c.fillText('配信', cx, t.y + 232);
  } else if (t.st === 'audio' && meters) {
    const chs = [['in1', '1'], ['in2', '2'], ['in3', '3'], ['in4', '4'], ['mic1', 'M1'], ['mic2', 'M2']];
    const x0 = t.x + 26, top = t.y + 20, mh = t.h - 74;
    chs.forEach(([id, lb], i) => {
      const x = x0 + i * 52;
      drawMeter(c, x, top, 16, mh, meters[id]);
      c.font = `700 16px ${FONT}`; c.fillStyle = '#c6c7cb'; c.fillText(lb, x + 8, top + mh + 20);
    });
    const mx = x0 + 6 * 52 + 22;
    drawMeter(c, mx, top, 16, mh, meters.L); drawMeter(c, mx + 22, top, 16, mh, meters.R);
    c.fillStyle = '#c6c7cb'; c.fillText('PGM', mx + 19, top + mh + 20);
    c.strokeStyle = 'rgba(255,255,255,.2)'; c.lineWidth = 1;
    for (const d of [-6, -18, -30, -42]) { const y = top + mh * (1 - dbFrac(d)); c.beginPath(); c.moveTo(x0 - 6, y); c.lineTo(mx + 44, y); c.stroke(); }
  }
}

function mvHit(e) {
  const r = mvCanvas.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width * 1920, y = (e.clientY - r.top) / r.height * 1080;
  const t = MV_TILES.find(t => x >= t.x && x < t.x + t.w && y >= t.y && y < t.y + t.h);
  return t ? { t, u: (x - t.x) / t.w, v: 1 - (y - t.y) / t.h } : null;
}

/* ============================================================
   メインループ
   ============================================================ */
let lastSig = '';
function tick() {
  const now = performance.now();
  const dt = Math.min(0.2, (now - R.last) / 1000); R.last = now;
  advance(dt);
  for (const s of inputs) s.tick();
  const sp = buildSpecs();
  const pgmSet = specSources(sp.pgm), pvwSet = specSources(sp.pvw);
  // オーディオ
  let meters = null;
  if (audio) {
    for (let n = 1; n <= 4; n++) audio.ch('in' + n).setAfv(programLevel(n));
    audio.setFtb(R.ftbT);
    meters = {};
    for (const [id, ch] of audio.channels) meters[id] = ch.meter(now);
    const [L, Rr] = audio.masterMeter(); meters.L = L; meters.R = Rr;
  }
  engine.frame(sp.pgm, sp.pvw, GLTILES, () => drawMV(pgmSet, pvwSet, meters));
  for (const st of [pgmStream, mvStream]) if (st) { const tr = st.getVideoTracks()[0]; if (tr && tr.requestFrame) tr.requestFrame(); }
  if (R.snap) { const f = R.snap; R.snap = null; const c = document.createElement('canvas'); c.width = 1920; c.height = 1080; c.getContext('2d').drawImage(glCanvas, 0, 0); f(c); }
  updateLights(pgmSet, pvwSet);
  updateMeters(meters);
  // ステータス
  R.frames++;
  if (now - R.fpsT > 1000) { R.fps = R.frames * 1000 / (now - R.fpsT); R.frames = 0; R.fpsT = now; $('#fps').textContent = R.fps.toFixed(1) + ' fps'; }
  const d = new Date();
  $('#clock').textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}:${pad(Math.floor(d.getMilliseconds() / 1000 * S.fps))}`;
  if (Rec.on) $('#recTime').textContent = fmtTime((now - Rec.start) / 1000);
  if (Stream.state === 'live') $('#streamTime').textContent = fmtTime((now - Stream.start) / 1000);
}

/* ============================================================
   UI ユーティリティ（コントロール＋同期）
   ============================================================ */
let curSync = null;
const paneSync = new Map();
function reg(fn) { if (curSync) curSync.push(fn); try { fn(); } catch (e) { console.warn(e); } }
function syncAll() { for (const list of paneSync.values()) for (const f of list) { try { f(); } catch (e) { console.warn(e); } } }
function buildPane(key, root, fn) {
  curSync = []; root.innerHTML = '';
  fn(root);
  paneSync.set(key, curSync); curSync = null;
}
function changed() { save(); syncAll(); }

function slider(label, get, set, min, max, step, fmt = v => v) {
  const inp = h('input', { type: 'range', min, max, step });
  const val = h('span', { class: 'val' });
  inp.addEventListener('input', () => { const v = parseFloat(inp.value); set(v); val.textContent = fmt(v); save(); });
  inp.addEventListener('dblclick', () => { if (slider.defaults.has(inp)) { const v = slider.defaults.get(inp); set(v); inp.value = v; val.textContent = fmt(v); save(); } });
  reg(() => { const v = get(); if (document.activeElement !== inp) inp.value = v; val.textContent = fmt(v); });
  slider.defaults.set(inp, get());
  return h('div', { class: 'row' }, h('label', null, label), inp, val);
}
slider.defaults = new WeakMap();
function select(label, opts, get, set) {
  const s = h('select');
  const fill = () => { const o = typeof opts === 'function' ? opts() : opts; s.innerHTML = ''; o.forEach(([v, t], i) => s.append(h('option', { value: i }, t))); s._o = o; };
  fill();
  s.addEventListener('change', () => { set(s._o[s.value][0]); changed(); });
  reg(() => { if (typeof opts === 'function') fill(); const v = get(); const i = s._o.findIndex(o => o[0] === v); s.value = i < 0 ? '' : i; });
  return label == null ? s : h('div', { class: 'row' }, h('label', null, label), s);
}
function toggle(label, get, set) {
  const c = h('input', { type: 'checkbox' });
  c.addEventListener('change', () => { set(c.checked); changed(); });
  reg(() => { c.checked = !!get(); });
  return h('label', { class: 'row', style: 'cursor:pointer' }, h('span', { class: 'lbl' }, label), h('span', { style: 'flex:1' }, c));
}
function seg(label, opts, get, set) {
  const box = h('div', { class: 'seg' });
  const btns = opts.map(([v, t]) => { const b = h('button', { onclick: () => { set(v); changed(); } }, t); box.append(b); return [v, b]; });
  reg(() => { const g = get(); btns.forEach(([v, b]) => b.classList.toggle('on', v === g)); });
  return label == null ? box : h('div', { class: 'row' }, h('label', null, label), box);
}
function colorPick(label, get, set) {
  const c = h('input', { type: 'color' });
  c.addEventListener('input', () => { set(c.value); save(); });
  reg(() => { c.value = get(); });
  return h('div', { class: 'row' }, h('label', null, label), h('span', null, c));
}
function pal(id, title, tagFn, ...body) {
  const tag = h('span', { class: 'tag' });
  const p = h('div', { class: 'pal' + (S.ui.open[id] ? ' open' : '') },
    h('h3', { onclick: () => { p.classList.toggle('open'); S.ui.open[id] = p.classList.contains('open'); save(); } }, title, tag),
    h('div', { class: 'body' }, ...body));
  if (tagFn) reg(() => { const [txt, cls] = tagFn(); tag.textContent = txt; tag.className = 'tag ' + (cls || ''); tag.style.display = txt ? '' : 'none'; });
  else tag.style.display = 'none';
  return p;
}
const pct = v => Math.round(v * 100) + '%';
const fmtRate = f => `${Math.floor(f / S.fps)}:${pad(Math.round(f % S.fps))}`;
function parseRate(s) {
  s = String(s).trim();
  if (/^\d+:\d+$/.test(s)) { const [a, b] = s.split(':').map(Number); return clamp(a * S.fps + b, 1, 250); }
  const n = parseFloat(s); if (!isNaN(n)) return clamp(Math.round(n * S.fps), 1, 250);
  return null;
}
function rateBox(get, set) {
  const b = h('div', { class: 'ratebox', contentEditable: 'true', spellcheck: false, title: '秒:フレーム（例 1:00）' });
  const commit = () => { const v = parseRate(b.textContent); if (v) { set(v); changed(); } b.textContent = fmtRate(get()); };
  b.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); b.blur(); } });
  b.addEventListener('blur', commit);
  reg(() => { if (document.activeElement !== b) b.textContent = fmtRate(get()); });
  return b;
}

/* ---------- アイコン ---------- */
function patIcon(p) {
  const W = 32, H = 20, w = W / 2, hh = H / 2;
  const shapes = {
    0: `<rect x="0" y="0" width="${w}" height="${H}"/>`,
    1: `<rect x="0" y="0" width="${W}" height="${hh}"/>`,
    2: `<rect x="${W * .3}" y="0" width="${W * .4}" height="${H}"/>`,
    3: `<rect x="0" y="${H * .3}" width="${W}" height="${H * .4}"/>`,
    4: `<rect x="${W * .4}" y="0" width="${W * .2}" height="${H}"/><rect x="0" y="${H * .38}" width="${W}" height="${H * .24}"/>`,
    5: `<rect x="${W * .3}" y="${H * .25}" width="${W * .4}" height="${H * .5}"/>`,
    6: `<polygon points="${w},2 ${W - 7},${hh} ${w},${H - 2} 7,${hh}"/>`,
    7: `<circle cx="${w}" cy="${hh}" r="7"/>`,
    8: `<rect x="0" y="0" width="${W * .55}" height="${H * .55}"/>`,
    9: `<rect x="${W * .45}" y="0" width="${W * .55}" height="${H * .55}"/>`,
    10: `<rect x="${W * .45}" y="${H * .45}" width="${W * .55}" height="${H * .55}"/>`,
    11: `<rect x="0" y="${H * .45}" width="${W * .55}" height="${H * .55}"/>`,
    12: `<polygon points="0,0 ${W * .7},0 0,${H}"/>`,
    13: `<rect x="${w}" y="0" width="${w}" height="${H}"/>`,
  };
  return `<svg viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" fill="#111"/><g fill="currentColor">${shapes[p] || ''}</g></svg>`;
}
const FX_ICONS = {
  mix: `<svg viewBox="0 0 32 20"><defs><linearGradient id="gm"><stop offset="0" stop-color="#111"/><stop offset="1" stop-color="currentColor"/></linearGradient></defs><rect width="32" height="20" fill="url(#gm)"/></svg>`,
  dip: `<svg viewBox="0 0 32 20"><rect width="32" height="20" fill="#111"/><path d="M2 4 L16 16 L30 4" stroke="currentColor" stroke-width="2.5" fill="none"/></svg>`,
  push: `<svg viewBox="0 0 32 20"><rect width="32" height="20" fill="#111"/><rect x="17" y="0" width="15" height="20" fill="currentColor"/><path d="M13 10 H4 M8 6 L4 10 L8 14" stroke="currentColor" stroke-width="2" fill="none"/></svg>`,
  squeeze: `<svg viewBox="0 0 32 20"><rect width="32" height="20" fill="#111"/><rect x="20" y="0" width="12" height="20" fill="currentColor"/><path d="M3 4 L12 10 L3 16" stroke="currentColor" stroke-width="2" fill="none"/></svg>`,
};
const HW_FX = [
  { id: 'mix', label: 'MIX', icon: FX_ICONS.mix, set: () => { S.trans.style = 'mix'; }, is: () => S.trans.style === 'mix' },
  { id: 'dip', label: 'DIP', icon: FX_ICONS.dip, set: () => { S.trans.style = 'dip'; }, is: () => S.trans.style === 'dip' },
  ...[0, 1, 2, 3, 5, 7, 6].map(p => ({ id: 'w' + p, icon: patIcon(p), set: () => { S.trans.style = 'wipe'; S.trans.wipe.pattern = p; }, is: () => S.trans.style === 'wipe' && S.trans.wipe.pattern === p })),
  { id: 'push', icon: FX_ICONS.push, set: () => { S.trans.style = 'dve'; S.trans.dve.type = 0; }, is: () => S.trans.style === 'dve' && S.trans.dve.type === 0 },
  { id: 'sq', icon: FX_ICONS.squeeze, set: () => { S.trans.style = 'dve'; S.trans.dve.type = 1; }, is: () => S.trans.style === 'dve' && S.trans.dve.type === 1 },
];

/* ============================================================
   右ペイン：スイッチャーパレット
   ============================================================ */
function renderSwitcherPane() {
  buildPane('switcher', $('#paneSwitcher'), root => {
    // --- トランジション
    const styleTabs = h('div', { class: 'subtabs' });
    STYLES.forEach(st => { const b = h('button', { onclick: () => setStyle(st) }, { mix: 'ミックス', dip: 'ディップ', wipe: 'ワイプ', dve: 'DVE' }[st]); styleTabs.append(b); reg(() => b.classList.toggle('on', S.trans.style === st)); });
    const boxes = {};
    boxes.mix = h('div', null, h('div', { class: 'row' }, h('label', null, 'レート'), h('span', null, rateBox(() => S.trans.rates.mix, v => S.trans.rates.mix = v))));
    boxes.dip = h('div', null,
      h('div', { class: 'row' }, h('label', null, 'レート'), h('span', null, rateBox(() => S.trans.rates.dip, v => S.trans.rates.dip = v))),
      select('ディップソース', () => srcOpts(false), () => S.trans.dipSrc, v => S.trans.dipSrc = v));
    const pats = h('div', { class: 'icongrid' });
    for (let p = 0; p < 14; p++) { const b = h('button', { html: patIcon(p), title: 'パターン ' + (p + 1), onclick: () => { S.trans.wipe.pattern = p; changed(); } }); pats.append(b); reg(() => b.classList.toggle('on', S.trans.wipe.pattern === p)); }
    boxes.wipe = h('div', null,
      h('div', { class: 'row' }, h('label', null, 'レート'), h('span', null, rateBox(() => S.trans.rates.wipe, v => S.trans.rates.wipe = v))),
      pats,
      slider('ソフトネス', () => S.trans.wipe.soft, v => S.trans.wipe.soft = v, 0, 0.3, 0.005, pct),
      slider('ボーダー幅', () => S.trans.wipe.border, v => S.trans.wipe.border = v, 0, 0.15, 0.002, pct),
      colorPick('ボーダー色', () => S.trans.wipe.borderColor, v => S.trans.wipe.borderColor = v),
      toggle('反転', () => S.trans.wipe.reverse, v => S.trans.wipe.reverse = v),
      toggle('フリップフロップ', () => S.trans.wipe.flipflop, v => S.trans.wipe.flipflop = v));
    boxes.dve = h('div', null,
      h('div', { class: 'row' }, h('label', null, 'レート'), h('span', null, rateBox(() => S.trans.rates.dve, v => S.trans.rates.dve = v))),
      seg('エフェクト', [[0, 'プッシュ'], [1, 'スクイーズ'], [2, 'スライド'], [3, 'ズーム']], () => S.trans.dve.type, v => S.trans.dve.type = v),
      seg('方向', [[0, '← 右から'], [1, '左から →'], [2, '↓ 上から'], [3, '下から ↑']], () => S.trans.dve.dir, v => S.trans.dve.dir = v));
    const boxWrap = h('div');
    Object.entries(boxes).forEach(([k, b]) => { boxWrap.append(b); reg(() => b.style.display = S.trans.style === k ? '' : 'none'); });
    root.append(pal('trans', 'トランジション', () => [R.auto ? '実行中' : S.trans.style.toUpperCase(), R.auto ? 'red' : ''],
      styleTabs, boxWrap, h('div', { class: 'hr' }),
      toggle('プレビュートランジション', () => S.trans.prevTrans, v => S.trans.prevTrans = v)));

    // --- アップストリームキー
    const ktabs = h('div', { class: 'subtabs' });
    [['luma', 'ルマ'], ['chroma', 'クロマ'], ['pattern', 'パターン'], ['dve', 'DVE（PinP）']].forEach(([k, t]) => {
      const b = h('button', { onclick: () => { S.usk.type = k; if (k !== 'dve') S.usk.keyType = k; changed(); } }, t); ktabs.append(b);
      reg(() => b.classList.toggle('on', S.usk.type === k));
    });
    const kb = {};
    kb.luma = h('div', null,
      select('キーソース', () => srcOpts(true), () => S.usk.key, v => S.usk.key = v),
      toggle('プリマルチプライ', () => S.usk.luma.premult, v => S.usk.luma.premult = v),
      slider('クリップ', () => S.usk.luma.clip, v => S.usk.luma.clip = v, 0, 1, 0.005, pct),
      slider('ゲイン', () => S.usk.luma.gain, v => S.usk.luma.gain = v, 0, 1, 0.005, pct),
      toggle('キー反転', () => S.usk.luma.invert, v => S.usk.luma.invert = v));
    const sw = h('span', { class: 'colorsw' });
    reg(() => sw.style.background = S.usk.chroma.color);
    kb.chroma = h('div', null,
      h('div', { class: 'row' }, h('label', null, 'キーカラー'), h('span', { style: 'display:flex;gap:6px;align-items:center' }, sw,
        h('button', { class: 'btn', onclick: () => startPick() }, 'スポイトで選ぶ'),
        h('button', { class: 'btn', onclick: () => { S.usk.chroma.ck = [-0.29, -0.33]; S.usk.chroma.color = '#00b140'; changed(); } }, 'グリーン'),
        h('button', { class: 'btn', onclick: () => { S.usk.chroma.ck = [0.37, -0.24]; S.usk.chroma.color = '#0047bb'; changed(); } }, 'ブルー'))),
      slider('許容範囲', () => S.usk.chroma.sim, v => S.usk.chroma.sim = v, 0, 0.5, 0.002, v => (v * 200).toFixed(0)),
      slider('エッジ', () => S.usk.chroma.smooth, v => S.usk.chroma.smooth = v, 0, 0.3, 0.002, v => (v * 333).toFixed(0)),
      slider('スピル抑制', () => S.usk.chroma.spill, v => S.usk.chroma.spill = v, 0, 1, 0.01, pct),
      slider('前景の明るさ', () => S.usk.chroma.lift, v => S.usk.chroma.lift = v, -0.3, 0.3, 0.005, v => (v * 100).toFixed(0)));
    kb.pattern = h('div', null,
      (() => { const g = h('div', { class: 'icongrid' }); for (let p = 0; p < 14; p++) { const b = h('button', { html: patIcon(p), onclick: () => { S.usk.pattern.pat = p; changed(); } }); g.append(b); reg(() => b.classList.toggle('on', S.usk.pattern.pat === p)); } return g; })(),
      slider('サイズ', () => S.usk.pattern.size, v => S.usk.pattern.size = v, 0, 1.2, 0.005, pct),
      slider('ソフトネス', () => S.usk.pattern.soft, v => S.usk.pattern.soft = v, 0, 0.5, 0.005, pct),
      slider('位置 X', () => S.usk.pattern.x, v => S.usk.pattern.x = v, 0, 1, 0.005, pct),
      slider('位置 Y', () => S.usk.pattern.y, v => S.usk.pattern.y = v, 0, 1, 0.005, pct),
      toggle('反転', () => S.usk.pattern.invert, v => S.usk.pattern.invert = v));
    const posPad = h('div', { class: 'pospad' });
    [[0.22, 0.74], [0.5, 0.74], [0.78, 0.74], [0.22, 0.5], [0.5, 0.5], [0.78, 0.5], [0.22, 0.26], [0.5, 0.26], [0.78, 0.26]].forEach(([x, y]) => posPad.append(h('button', { onclick: () => { S.usk.dve.x = x; S.usk.dve.y = y; changed(); } })));
    kb.dve = h('div', null,
      h('div', { class: 'row' }, h('label', null, '位置プリセット'), h('span', null, posPad)),
      slider('位置 X', () => S.usk.dve.x, v => S.usk.dve.x = v, -0.2, 1.2, 0.002, v => ((v - 0.5) * 32).toFixed(2)),
      slider('位置 Y', () => S.usk.dve.y, v => S.usk.dve.y = v, -0.2, 1.2, 0.002, v => ((v - 0.5) * 18).toFixed(2)),
      slider('サイズ', () => S.usk.dve.size, v => S.usk.dve.size = v, 0.05, 1, 0.005, v => v.toFixed(2)),
      slider('ボーダー幅', () => S.usk.dve.borderW, v => S.usk.dve.borderW = v, 0, 30, 0.5, v => v + 'px'),
      slider('ボーダーぼかし', () => S.usk.dve.borderSoft, v => S.usk.dve.borderSoft = v, 0, 30, 0.5, v => v + 'px'),
      colorPick('ボーダー色', () => S.usk.dve.borderColor, v => S.usk.dve.borderColor = v),
      slider('クロップ 左', () => S.usk.dve.crop[0], v => S.usk.dve.crop[0] = v, 0, 0.5, 0.002, pct),
      slider('クロップ 右', () => S.usk.dve.crop[1], v => S.usk.dve.crop[1] = v, 0, 0.5, 0.002, pct),
      slider('クロップ 上', () => S.usk.dve.crop[3], v => S.usk.dve.crop[3] = v, 0, 0.5, 0.002, pct),
      slider('クロップ 下', () => S.usk.dve.crop[2], v => S.usk.dve.crop[2] = v, 0, 0.5, 0.002, pct));
    const maskBox = h('div', null, h('div', { class: 'hr' }),
      toggle('マスク', () => S.usk.mask.on, v => S.usk.mask.on = v),
      slider('マスク 上', () => S.usk.mask.t, v => S.usk.mask.t = v, 0, 1, 0.005, pct),
      slider('マスク 下', () => S.usk.mask.b, v => S.usk.mask.b = v, 0, 1, 0.005, pct),
      slider('マスク 左', () => S.usk.mask.l, v => S.usk.mask.l = v, 0, 1, 0.005, pct),
      slider('マスク 右', () => S.usk.mask.r, v => S.usk.mask.r = v, 0, 1, 0.005, pct));
    reg(() => maskBox.style.display = S.usk.type === 'dve' ? 'none' : '');
    const kw = h('div');
    Object.entries(kb).forEach(([k, b]) => { kw.append(b); reg(() => b.style.display = S.usk.type === k ? '' : 'none'); });
    root.append(pal('usk', 'アップストリームキー 1', () => [S.usk.onAir ? 'ON AIR' : '', 'red'],
      ktabs,
      select('フィルソース', () => srcOpts(false), () => S.usk.fill, v => S.usk.fill = v),
      kw, maskBox, h('div', { class: 'hr' }),
      h('div', { class: 'row' }, h('button', { class: 'btn full', onclick: () => keyOnAir(!S.usk.onAir) }, 'キー ON AIR 切替（カット）'))));

    // --- ダウンストリームキー
    root.append(pal('dsk', 'ダウンストリームキー 1', () => [S.dsk.onAir || R.dskT > 0 ? 'ON AIR' : '', 'red'],
      select('フィルソース', () => srcOpts(false), () => S.dsk.fill, v => S.dsk.fill = v),
      select('キーソース', () => srcOpts(true), () => S.dsk.key, v => S.dsk.key = v),
      h('div', { class: 'row' }, h('label', null, 'レート'), h('span', null, rateBox(() => S.dsk.rate, v => S.dsk.rate = v))),
      toggle('プリマルチプライ', () => S.dsk.premult, v => S.dsk.premult = v),
      slider('クリップ', () => S.dsk.clip, v => S.dsk.clip = v, 0, 1, 0.005, pct),
      slider('ゲイン', () => S.dsk.gain, v => S.dsk.gain = v, 0, 1, 0.005, pct),
      toggle('キー反転', () => S.dsk.invert, v => S.dsk.invert = v),
      toggle('マスク', () => S.dsk.mask.on, v => S.dsk.mask.on = v),
      slider('マスク 上', () => S.dsk.mask.t, v => S.dsk.mask.t = v, 0, 1, 0.005, pct),
      slider('マスク 下', () => S.dsk.mask.b, v => S.dsk.mask.b = v, 0, 1, 0.005, pct),
      h('div', { class: 'note' }, '静止画（透過PNG）をメディアプレーヤーに入れ、フィル＝MP1・キー＝MP1 キー・プリマルチプライ ON にするとテロップがそのまま乗ります。')));

    // --- FTB
    root.append(pal('ftb', 'フェードトゥブラック', () => [R.ftbOn || R.ftbT > 0 ? 'BLACK' : '', 'red'],
      h('div', { class: 'row' }, h('label', null, 'レート'), h('span', null, rateBox(() => S.ftb.rate, v => S.ftb.rate = v))),
      toggle('音声もフェード', () => S.audio.master.ftbFollow, v => { S.audio.master.ftbFollow = v; audio && (audio.mp.ftbFollow = v); })));

    // --- メディアプレーヤー
    const mpOpts = () => [[-1, '（空）'], ...Array.from({ length: POOL_N }, (_, i) => [i, `${i + 1}: ${pool[i] ? pool[i].name : '—'}`])];
    root.append(pal('mp', 'メディアプレーヤー', null,
      select('MP1', mpOpts, () => S.mp[0].slot, v => { S.mp[0].slot = v; updateMP(); }),
      select('MP2', mpOpts, () => S.mp[1].slot, v => { S.mp[1].slot = v; updateMP(); }),
      h('div', { class: 'sub' }, '静止画の追加は「メディア」タブから。')));

    // --- カラージェネレーター
    root.append(pal('col', 'カラージェネレーター', null,
      colorPick('カラー1', () => S.colors.c1, v => { S.colors.c1 = v; updateColors(); }),
      colorPick('カラー2', () => S.colors.c2, v => { S.colors.c2 = v; updateColors(); })));
  });
}

function startPick() {
  R.pick = 'chroma';
  $('#mvHint').textContent = 'マルチビューの映像をクリックして抜きたい色を選択（Esc で取消）';
  $('#mvHint').classList.add('on');
}
function endPick() { R.pick = null; $('#mvHint').classList.remove('on'); }

/* ============================================================
   右ペイン：メディア
   ============================================================ */
let poolSel = 0;
function renderMediaPane() {
  buildPane('media', $('#paneMedia'), root => {
    const file = h('input', { type: 'file', accept: 'image/*', multiple: true, style: 'display:none' });
    const addFiles = async files => {
      let slot = pool[poolSel] ? freeSlot() : poolSel;
      for (const f of files) {
        if (!f.type.startsWith('image/')) continue;
        if (slot < 0) { toast('メディアプールがいっぱいです', true); break; }
        await setStill(slot, f, f.name.replace(/\.[^.]+$/, ''));
        slot = freeSlot();
      }
    };
    file.addEventListener('change', () => addFiles([...file.files]));
    const drop = h('div', { class: 'drop', onclick: () => file.click() }, '画像をドロップ、またはクリックして追加（PNG の透過も使えます）');
    drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('over'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('over'));
    drop.addEventListener('drop', e => { e.preventDefault(); drop.classList.remove('over'); addFiles([...e.dataTransfer.files]); });
    const grid = h('div', { class: 'pool' });
    for (let i = 0; i < POOL_N; i++) {
      const p = pool[i];
      const mp = h('div', { class: 'mp' });
      if (S.mp[0].slot === i) mp.append(h('span', null, 'MP1'));
      if (S.mp[1].slot === i) mp.append(h('span', null, 'MP2'));
      grid.append(h('div', { class: 'slot' + (poolSel === i ? ' sel' : ''), title: p ? p.name : '空き', onclick: () => { poolSel = i; renderMediaPane(); } },
        p ? h('img', { src: p.url }) : null, h('span', { class: 'n' }, i + 1), mp,
        p ? h('button', { class: 'x', onclick: e => { e.stopPropagation(); if (confirm(`静止画 ${i + 1} を削除しますか？`)) setStill(i, null); } }, '×') : null));
    }
    root.append(h('div', { class: 'pal open' }, h('h3', null, 'メディアプール'),
      h('div', { class: 'body' }, drop, file, grid,
        h('div', { class: 'row', style: 'margin-top:10px' },
          h('button', { class: 'btn', onclick: () => { S.mp[0].slot = poolSel; updateMP(); changed(); renderMediaPane(); } }, `→ MP1 にセット`),
          h('button', { class: 'btn', onclick: () => { S.mp[1].slot = poolSel; updateMP(); changed(); renderMediaPane(); } }, `→ MP2 にセット`)),
        h('div', { class: 'sub' }, `選択中: スロット ${poolSel + 1}${pool[poolSel] ? '（' + pool[poolSel].name + '）' : '（空き）'}`))));

    // テロップ作成
    const T = renderMediaPane.t || (renderMediaPane.t = { l1: '山田 太郎', l2: '株式会社サンプル 代表', style: 'lower', accent: '#d8262c', size: 1 });
    const prev = h('canvas', { width: 480, height: 270, style: 'width:100%;border-radius:5px;background:repeating-conic-gradient(#2a2b2f 0 25%,#222327 0 50%) 0 0/12px 12px' });
    const draw = () => { const c = renderTitle(T); const x = prev.getContext('2d'); x.clearRect(0, 0, 480, 270); x.drawImage(c, 0, 0, 480, 270); };
    const inp = (k, ph) => { const e = h('input', { type: 'text', value: T[k], placeholder: ph }); e.addEventListener('input', () => { T[k] = e.value; draw(); }); e.addEventListener('keydown', ev => ev.stopPropagation()); return e; };
    const styleSel = h('select', null, h('option', { value: 'lower' }, 'ローワーサード（帯）'), h('option', { value: 'simple' }, 'シンプル（影付き文字）'), h('option', { value: 'center' }, '中央タイトル'), h('option', { value: 'corner' }, '右上ラベル'));
    styleSel.value = T.style; styleSel.addEventListener('change', () => { T.style = styleSel.value; draw(); });
    const acc = h('input', { type: 'color', value: T.accent }); acc.addEventListener('input', () => { T.accent = acc.value; draw(); });
    const sz = h('input', { type: 'range', min: 0.6, max: 1.6, step: 0.05, value: T.size }); sz.addEventListener('input', () => { T.size = +sz.value; draw(); });
    root.append(h('div', { class: 'pal open' }, h('h3', null, 'テロップ作成'),
      h('div', { class: 'body' }, prev,
        h('div', { class: 'row' }, h('label', null, '1行目'), inp('l1', '名前・タイトル')),
        h('div', { class: 'row' }, h('label', null, '2行目'), inp('l2', '肩書き・説明')),
        h('div', { class: 'row' }, h('label', null, 'スタイル'), styleSel),
        h('div', { class: 'row' }, h('label', null, 'アクセント色'), h('span', null, acc)),
        h('div', { class: 'row' }, h('label', null, '文字サイズ'), sz),
        h('button', {
          class: 'btn primary full', onclick: () => {
            const slot = pool[poolSel] ? freeSlot() : poolSel;
            if (slot < 0) return toast('メディアプールがいっぱいです', true);
            renderTitle(T).toBlob(b => setStill(slot, b, 'テロップ ' + (T.l1 || '').slice(0, 10)).then(() => toast(`スロット ${slot + 1} に追加しました`)), 'image/png');
          }
        }, 'メディアプールに追加'),
        h('div', { class: 'note' }, '追加したテロップを MP1 にセット → ダウンストリームキー（フィル MP1／キー MP1 キー）→ DSK の AUTO で出し入れできます。'))));
    setTimeout(draw, 0);
  });
}
function renderTitle(T) {
  const c = document.createElement('canvas'); c.width = 1920; c.height = 1080;
  const x = c.getContext('2d'), s = T.size;
  x.textBaseline = 'alphabetic';
  if (T.style === 'lower') {
    const f1 = 64 * s, f2 = 38 * s;
    x.font = `800 ${f1}px ${FONT}`; const w1 = x.measureText(T.l1).width;
    x.font = `600 ${f2}px ${FONT}`; const w2 = x.measureText(T.l2).width;
    const W = Math.max(w1, w2) + 120 * s, y = 1080 - 120 - (f1 + f2 + 70 * s);
    x.fillStyle = 'rgba(12,14,20,.86)'; x.fillRect(110, y, W, f1 + 40 * s);
    x.fillStyle = T.accent; x.fillRect(110, y, 14 * s, f1 + 40 * s + (T.l2 ? f2 + 30 * s : 0));
    if (T.l2) { x.fillStyle = T.accent; x.fillRect(110 + 14 * s, y + f1 + 40 * s, Math.max(w2 + 80 * s, 200), f2 + 30 * s); }
    x.fillStyle = '#fff'; x.font = `800 ${f1}px ${FONT}`; x.fillText(T.l1, 110 + 60 * s, y + f1 + 8 * s);
    if (T.l2) { x.font = `600 ${f2}px ${FONT}`; x.fillText(T.l2, 110 + 60 * s, y + f1 + 40 * s + f2 + 4 * s); }
  } else if (T.style === 'simple') {
    x.shadowColor = 'rgba(0,0,0,.85)'; x.shadowBlur = 14 * s; x.shadowOffsetY = 3;
    x.fillStyle = '#fff'; x.font = `800 ${72 * s}px ${FONT}`; x.fillText(T.l1, 140, 1080 - 150 - (T.l2 ? 56 * s : 0));
    if (T.l2) { x.font = `600 ${42 * s}px ${FONT}`; x.fillStyle = '#f2f2f2'; x.fillText(T.l2, 144, 1080 - 140); }
  } else if (T.style === 'center') {
    x.textAlign = 'center'; x.shadowColor = 'rgba(0,0,0,.8)'; x.shadowBlur = 20 * s;
    x.fillStyle = '#fff'; x.font = `900 ${120 * s}px ${FONT}`; x.fillText(T.l1, 960, 540 + (T.l2 ? 0 : 40 * s));
    if (T.l2) { x.font = `600 ${52 * s}px ${FONT}`; x.fillStyle = T.accent; x.shadowBlur = 10; x.fillText(T.l2, 960, 540 + 90 * s); }
  } else {
    x.font = `800 ${44 * s}px ${FONT}`; const w = x.measureText(T.l1).width;
    x.fillStyle = T.accent; x.fillRect(1920 - 110 - w - 60 * s, 90, w + 60 * s, 76 * s);
    x.fillStyle = '#fff'; x.textAlign = 'right'; x.fillText(T.l1, 1920 - 110 - 30 * s, 90 + 54 * s);
    if (T.l2) { x.font = `600 ${30 * s}px ${FONT}`; x.fillStyle = '#fff'; x.shadowColor = 'rgba(0,0,0,.8)'; x.shadowBlur = 8; x.fillText(T.l2, 1920 - 110, 90 + 76 * s + 44 * s); }
  }
  return c;
}

/* ============================================================
   右ペイン：オーディオ
   ============================================================ */
const ACH = [['in1', 1], ['in2', 2], ['in3', 3], ['in4', 4], ['mic1', 'MIC 1'], ['mic2', 'MIC 2']];
const meterEls = [];
function chName(id) { const n = ACH.find(a => a[0] === id)[1]; return typeof n === 'number' ? S.inputs[n - 1].short : n; }
function applyAudioState() {
  if (!audio) return;
  for (const [id] of ACH) { const ch = audio.ch(id); Object.assign(ch.p, S.audio[id]); ch.apply(); }
  Object.assign(audio.mp, S.audio.master); audio.applyMaster();
}
function setA(id, k, v) { S.audio[id][k] = v; if (audio) audio.ch(id).set(k, v); save(); }
function fmtDb(v) { return v <= -60 ? '-∞' : (v > 0 ? '+' : '') + v.toFixed(1); }
function renderAudioPane() {
  meterEls.length = 0;
  buildPane('audio', $('#paneAudio'), root => {
    const mixer = h('div', { class: 'mixer' });
    for (const [id] of ACH) {
      const a = S.audio[id], isIn = id.startsWith('in');
      const m = h('div', { class: 'vmeter' }, h('i'), h('b'));
      meterEls.push([id, m]);
      const fader = h('input', { type: 'range', class: 'vfader', min: -60, max: 10, step: 0.5, orient: 'vertical' });
      const dbv = h('div', { class: 'dbv' });
      fader.addEventListener('input', () => { setA(id, 'fader', +fader.value); dbv.textContent = fmtDb(+fader.value); });
      fader.addEventListener('dblclick', () => { setA(id, 'fader', 0); syncAll(); });
      reg(() => { fader.value = S.audio[id].fader; dbv.textContent = fmtDb(S.audio[id].fader); });
      const bOn = h('button', { onclick: () => { setA(id, 'mode', S.audio[id].mode === 'on' ? 'off' : 'on'); syncAll(); } }, 'ON');
      const bAfv = isIn ? h('button', { class: 'afv', onclick: () => { setA(id, 'mode', S.audio[id].mode === 'afv' ? 'off' : 'afv'); syncAll(); } }, 'AFV') : null;
      const bMute = h('button', { class: 'mut', onclick: () => { setA(id, 'mute', !S.audio[id].mute); syncAll(); } }, 'MUTE');
      reg(() => { bOn.classList.toggle('on', S.audio[id].mode === 'on'); bAfv && bAfv.classList.toggle('on', S.audio[id].mode === 'afv'); bMute.classList.toggle('on', S.audio[id].mute); });
      const gain = h('input', { type: 'range', min: -20, max: 40, step: 0.5 });
      gain.addEventListener('input', () => setA(id, 'gain', +gain.value));
      reg(() => gain.value = S.audio[id].gain);
      const pan = h('input', { type: 'range', min: -1, max: 1, step: 0.05 });
      pan.addEventListener('input', () => setA(id, 'pan', +pan.value)); pan.addEventListener('dblclick', () => { setA(id, 'pan', 0); pan.value = 0; });
      reg(() => pan.value = S.audio[id].pan);
      const nm = h('div', { class: 'nm', style: 'cursor:pointer', onclick: () => { S.ui.audioSel = id; save(); renderAudioPane(); } });
      reg(() => { nm.textContent = chName(id); nm.style.color = S.ui.audioSel === id ? 'var(--yellow)' : ''; });
      mixer.append(h('div', { class: 'strip' }, nm,
        h('div', { class: 'knob' }, h('label', null, 'GAIN'), gain),
        h('div', { class: 'knob' }, h('label', null, 'PAN'), pan),
        h('div', { class: 'fz' }, m, fader), dbv,
        h('div', { class: 'abtns' }, bOn, bAfv, bMute)));
    }
    // マスター
    const mm = S.audio.master;
    const mL = h('div', { class: 'vmeter' }, h('i'), h('b')), mR = h('div', { class: 'vmeter' }, h('i'), h('b'));
    meterEls.push(['L', mL], ['R', mR]);
    const mf = h('input', { type: 'range', class: 'vfader', min: -60, max: 10, step: 0.5 });
    const mdb = h('div', { class: 'dbv' });
    mf.addEventListener('input', () => { mm.fader = +mf.value; audio && (audio.mp.fader = mm.fader, audio.applyMaster()); mdb.textContent = fmtDb(mm.fader); save(); });
    mf.addEventListener('dblclick', () => { mm.fader = 0; audio && (audio.mp.fader = 0, audio.applyMaster()); syncAll(); save(); });
    reg(() => { mf.value = mm.fader; mdb.textContent = fmtDb(mm.fader); });
    const mon = h('button', { onclick: () => { mm.monitorOn = !mm.monitorOn; audio && (audio.mp.monitorOn = mm.monitorOn, audio.applyMaster()); syncAll(); save(); } }, 'MON');
    const lim = h('button', { onclick: () => { mm.limiter = !mm.limiter; audio && (audio.mp.limiter = mm.limiter, audio.applyMaster()); syncAll(); save(); } }, 'LIMIT');
    reg(() => { mon.classList.toggle('on', mm.monitorOn); lim.classList.toggle('on', mm.limiter); });
    mixer.append(h('div', { class: 'strip master' }, h('div', { class: 'nm' }, 'MASTER'), h('div', { class: 'src' }, 'PGM'),
      h('div', { class: 'fz', style: 'margin-top:auto' }, mL, mR, mf), mdb, h('div', { class: 'abtns' }, lim, mon)));
    root.append(h('div', { class: 'pal open' }, h('h3', null, 'オーディオミキサー'), h('div', { class: 'body', style: 'padding:8px' }, mixer,
      h('div', { class: 'sub', style: 'margin-top:6px' }, 'ON＝常に出す ／ AFV＝その映像が番組に出ている時だけ出す（オーディオ・フォロー・ビデオ）。フェーダーはダブルクリックで 0dB。チャンネル名をクリックすると詳細設定。'))));

    // 詳細（選択チャンネル）
    const id = S.ui.audioSel || 'in1';
    const det = [];
    if (id.startsWith('mic')) {
      det.push(select('入力デバイス', () => [['', '（なし）'], ...devices.audio.map(d => [d.deviceId, d.label || 'マイク'])], () => S.audio[id].device, v => { S.audio[id].device = v; applyMic(id); }));
    } else {
      det.push(h('div', { class: 'sub' }, '入力の音声は「設定」タブの入力ごとの「音声」で選びます。'));
    }
    det.push(
      slider('ゲイン', () => S.audio[id].gain, v => setA(id, 'gain', v), -20, 40, 0.5, v => fmtDb(v) + 'dB'),
      slider('ディレイ', () => S.audio[id].delay, v => setA(id, 'delay', v), 0, 500, 1, v => v + 'ms'),
      h('div', { class: 'hr' }),
      toggle('EQ', () => S.audio[id].eqOn, v => setA(id, 'eqOn', v)),
      slider('低域 120Hz', () => S.audio[id].low, v => setA(id, 'low', v), -15, 15, 0.5, v => v + 'dB'),
      slider('中域 1kHz', () => S.audio[id].mid, v => setA(id, 'mid', v), -15, 15, 0.5, v => v + 'dB'),
      slider('高域 8kHz', () => S.audio[id].high, v => setA(id, 'high', v), -15, 15, 0.5, v => v + 'dB'),
      h('div', { class: 'hr' }),
      toggle('コンプレッサー', () => S.audio[id].compOn, v => setA(id, 'compOn', v)),
      slider('スレッショルド', () => S.audio[id].thresh, v => setA(id, 'thresh', v), -50, 0, 0.5, v => v + 'dB'),
      slider('レシオ', () => S.audio[id].ratio, v => setA(id, 'ratio', v), 1, 20, 0.1, v => v.toFixed(1) + ':1'),
    );
    root.append(h('div', { class: 'pal open' }, h('h3', null, `チャンネル詳細：${chName(id)}`), h('div', { class: 'body' }, ...det)));
    root.append(h('div', { class: 'pal open' }, h('h3', null, 'モニター（ヘッドホン）'), h('div', { class: 'body' },
      slider('モニター音量', () => mm.monitorLevel, v => { mm.monitorLevel = v; audio && (audio.mp.monitorLevel = v, audio.applyMaster()); }, -40, 6, 0.5, v => v + 'dB'),
      h('div', { class: 'note' }, 'MON を押すとプログラム音声を Mac のスピーカー／ヘッドホンから聞けます。マイク使用時はハウリングに注意してヘッドホンで。'))));
  });
}
async function applyMic(id) {
  if (!audio) return;
  const ch = audio.ch(id);
  if (ch._stream) { ch._stream.getTracks().forEach(t => t.stop()); ch._stream = null; }
  ch.setSource(null);
  const dev = S.audio[id].device;
  if (!dev) return;
  try {
    const st = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: { exact: dev }, echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
    ch._stream = st; ch.setSource(audio.fromStream(st));
  } catch (e) { toast(`${id.toUpperCase()}: マイクを開けませんでした`, true); }
}
function updateMeters(meters) {
  if (!meters) return;
  for (const [id, el] of meterEls) {
    if (!el.isConnected) continue;
    const f = dbFrac(meters[id]);
    el.firstChild.style.height = (f * 100).toFixed(1) + '%';
    const ch = audio.ch(id);
    if (ch) el.lastChild.style.bottom = (dbFrac(ch.hold) * 100).toFixed(1) + '%';
  }
  for (const [id, el] of hwMeters) { const f = dbFrac(meters[id]); el.style.height = (f * 100).toFixed(1) + '%'; }
}

/* ============================================================
   録画
   ============================================================ */
const Rec = { on: false, mr: null, chunks: [], writable: null, start: 0, dir: null, files: [], q: Promise.resolve() };
function pickMime(fmt) {
  const c = fmt === 'webm' ? ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm']
    : ['video/mp4;codecs=avc1.640028,mp4a.40.2', 'video/mp4;codecs=avc1.4d0028,mp4a.40.2', 'video/mp4;codecs=avc1,mp4a.40.2', 'video/mp4', 'video/webm;codecs=h264,opus', 'video/webm;codecs=vp9,opus', 'video/webm'];
  return c.find(m => window.MediaRecorder && MediaRecorder.isTypeSupported(m)) || '';
}
function programAV() { return new MediaStream([...pgmStream.getVideoTracks(), ...audio.out.stream.getAudioTracks()]); }
async function pickRecDir() {
  if (!window.showDirectoryPicker) { toast('このブラウザはフォルダ保存に未対応です（停止時にダウンロードされます）', true); return; }
  try { Rec.dir = await showDirectoryPicker({ id: 'lsw-rec', mode: 'readwrite' }); await idb('kv', 'readwrite', s => s.put(Rec.dir, 'recDir')); syncAll(); toast('保存先: ' + Rec.dir.name); } catch (e) {}
}
async function recStart() {
  if (Rec.on) return;
  const mime = pickMime(S.out.format);
  if (!mime) return toast('このブラウザは録画に対応していません', true);
  const ext = mime.includes('mp4') ? 'mp4' : 'webm';
  const d = new Date();
  const name = `Switcher_${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}_${pad(d.getHours())}-${pad(d.getMinutes())}-${pad(d.getSeconds())}.${ext}`;
  Rec.writable = null; Rec.chunks = []; Rec.q = Promise.resolve();
  if (Rec.dir) {
    try {
      let perm = await Rec.dir.queryPermission({ mode: 'readwrite' });
      if (perm !== 'granted') perm = await Rec.dir.requestPermission({ mode: 'readwrite' });
      if (perm === 'granted') { const fh = await Rec.dir.getFileHandle(name, { create: true }); Rec.writable = await fh.createWritable(); }
    } catch (e) { console.warn(e); }
  }
  const mr = new MediaRecorder(programAV(), { mimeType: mime, videoBitsPerSecond: S.out.vbr * 1000, audioBitsPerSecond: S.out.abr * 1000 });
  const w = Rec.writable;
  mr.ondataavailable = e => { if (!e.data.size) return; if (w) Rec.q = Rec.q.then(() => w.write(e.data)); else Rec.chunks.push(e.data); };
  mr.onstop = async () => {
    if (w) { await Rec.q; await w.close(); toast(`保存しました: ${name}`); }
    else {
      const blob = new Blob(Rec.chunks, { type: mime.split(';')[0] });
      const a = h('a', { href: URL.createObjectURL(blob), download: name }); document.body.append(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 60000);
    }
    Rec.files.unshift(`${name}  (${fmtTime((Rec.stopT - Rec.start) / 1000)})`); syncAll();
  };
  mr.start(1000);
  Rec.mr = mr; Rec.on = true; Rec.start = performance.now(); Rec.name = name;
  $('#stRec').classList.add('on'); changed();
}
function recStop() {
  if (!Rec.on) return;
  Rec.stopT = performance.now(); Rec.mr.stop(); Rec.on = false;
  $('#stRec').classList.remove('on'); $('#recTime').textContent = '--:--:--'; changed();
}

/* ============================================================
   配信（WHIP / WebRTC）
   ============================================================ */
const Stream = { state: 'off', pc: null, start: 0, kbps: 0, resource: null, lastBytes: 0, lastT: 0 };
async function streamStart() {
  if (Stream.state !== 'off') return;
  const url = S.out.whipUrl.trim();
  if (!url) { toast('配信先の WHIP URL を「出力」タブで設定してください', true); return; }
  Stream.state = 'connecting'; syncAll(); $('#stStream').classList.add('on');
  try {
    const pc = new RTCPeerConnection({ bundlePolicy: 'max-bundle' });
    Stream.pc = pc;
    const av = programAV();
    const vt = av.getVideoTracks()[0]; vt.contentHint = 'motion';
    pc.addTransceiver(vt, { direction: 'sendonly', sendEncodings: [{ maxBitrate: S.out.sbr * 1000, maxFramerate: S.fps }] });
    const at = av.getAudioTracks()[0]; if (at) pc.addTransceiver(at, { direction: 'sendonly' });
    const offer = await pc.createOffer(); await pc.setLocalDescription(offer);
    await new Promise(res => { if (pc.iceGatheringState === 'complete') return res(); const t = setTimeout(res, 2500); pc.addEventListener('icegatheringstatechange', () => { if (pc.iceGatheringState === 'complete') { clearTimeout(t); res(); } }); });
    const headers = { 'Content-Type': 'application/sdp' };
    if (S.out.whipToken) headers.Authorization = 'Bearer ' + S.out.whipToken.trim();
    const r = await fetch(url, { method: 'POST', headers, body: pc.localDescription.sdp });
    if (!r.ok) throw new Error('サーバー応答 ' + r.status);
    const loc = r.headers.get('Location'); Stream.resource = loc ? new URL(loc, url).href : null;
    await pc.setRemoteDescription({ type: 'answer', sdp: await r.text() });
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === 'connected') { if (Stream.state !== 'live') { Stream.state = 'live'; Stream.start = performance.now(); toast('配信を開始しました'); syncAll(); } }
      else if (['failed', 'closed'].includes(pc.connectionState)) { toast('配信が切断されました', true); streamStop(true); }
    };
    Stream.statT = setInterval(async () => {
      if (!Stream.pc) return;
      const st = await Stream.pc.getStats(); let bytes = 0;
      st.forEach(s => { if (s.type === 'outbound-rtp') bytes += s.bytesSent; });
      const now = performance.now();
      if (Stream.lastT) Stream.kbps = (bytes - Stream.lastBytes) * 8 / (now - Stream.lastT);
      Stream.lastBytes = bytes; Stream.lastT = now;
    }, 1000);
  } catch (e) {
    console.warn(e); toast('配信を開始できませんでした: ' + e.message, true); streamStop(true);
  }
}
async function streamStop(silent) {
  if (Stream.state === 'off' && !Stream.pc) return;
  clearInterval(Stream.statT);
  if (Stream.pc) { try { Stream.pc.close(); } catch (e) {} }
  if (Stream.resource) { const headers = {}; if (S.out.whipToken) headers.Authorization = 'Bearer ' + S.out.whipToken.trim(); fetch(Stream.resource, { method: 'DELETE', headers }).catch(() => {}); }
  Object.assign(Stream, { state: 'off', pc: null, resource: null, kbps: 0, lastBytes: 0, lastT: 0 });
  $('#stStream').classList.remove('on'); $('#streamTime').textContent = '--:--:--';
  if (!silent) toast('配信を停止しました');
  syncAll();
}

/* ============================================================
   外部出力ウィンドウ（HDMI OUT 相当）
   ============================================================ */
let outWin = null, mvStream = null;
function outStreamFor(src) {
  if (src === 'pgm') return pgmStream;
  if (src === 'mv') return mvStream || (mvStream = mvCanvas.captureStream(0));
  const n = +src.slice(2); const s = inputs[n - 1] && inputs[n - 1].outStream();
  return s || null;
}
function setOutput(src) {
  S.out.outSrc = src; save();
  if (!outWin || outWin.closed) {
    outWin = window.open('', 'lsw_output', 'popup,width=960,height=540');
    if (!outWin) { toast('ポップアップがブロックされました。アドレスバー右のアイコンから許可してください', true); return; }
    outWin.document.open();
    outWin.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>出力 - ライブスイッチャー</title><style>html,body{margin:0;height:100%;background:#000;overflow:hidden}video{width:100%;height:100%;object-fit:contain;display:block}.h{position:fixed;left:50%;top:14px;transform:translateX(-50%);background:rgba(0,0,0,.7);color:#fff;font:600 13px -apple-system,sans-serif;padding:7px 14px;border-radius:7px;transition:opacity 1s}body.f .h{opacity:0}body.f{cursor:none}</style></head><body><video autoplay muted playsinline></video><div class="h">ダブルクリック（または F キー）でフルスクリーン。2台目のディスプレイにドラッグしてから使えます。</div><script>const t=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();document.addEventListener('dblclick',t);document.addEventListener('keydown',e=>{if(e.key==='f'||e.key==='F')t()});setTimeout(()=>document.body.classList.add('f'),4000);<\/script></body></html>`);
    outWin.document.close();
  }
  const v = outWin.document.querySelector('video');
  const st = outStreamFor(src);
  if (!st) { toast('この入力は外部出力できません（映像がありません）', true); }
  if (v) { v.srcObject = st; v.play().catch(() => {}); }
  outWin.document.title = '出力: ' + ({ pgm: 'プログラム', mv: 'マルチビュー' }[src] || srcLabel(+src.slice(2)));
  syncAll();
}

/* ============================================================
   右ペイン：出力
   ============================================================ */
function renderOutputPane() {
  buildPane('output', $('#paneOutput'), root => {
    const recBtn = h('button', { class: 'btn full', onclick: () => Rec.on ? recStop() : recStart() });
    reg(() => { recBtn.textContent = Rec.on ? '■ 録画停止' : '● 録画開始'; recBtn.className = 'btn full ' + (Rec.on ? 'red' : 'primary'); });
    const dirLbl = h('span', { class: 'sub' });
    reg(() => dirLbl.textContent = Rec.dir ? Rec.dir.name : '未選択（停止時にダウンロード）');
    const list = h('div', { class: 'reclist' });
    reg(() => { list.innerHTML = ''; Rec.files.forEach(f => list.append(h('div', null, f))); if (!Rec.files.length) list.append(h('div', null, 'まだ録画はありません')); });
    root.append(h('div', { class: 'pal open' }, h('h3', null, '録画'), h('div', { class: 'body' },
      h('div', { class: 'row' }, h('label', null, '保存先'), dirLbl, h('button', { class: 'btn', style: 'flex:none', onclick: pickRecDir }, '選択')),
      select('形式', [['mp4', 'MP4（H.264 / AAC）'], ['webm', 'WebM（VP9 / Opus）']], () => S.out.format, v => S.out.format = v),
      select('映像ビットレート', [[6000, '6 Mbps'], [12000, '12 Mbps'], [20000, '20 Mbps'], [35000, '35 Mbps'], [50000, '50 Mbps']], () => S.out.vbr, v => S.out.vbr = v),
      select('音声ビットレート', [[128, '128 kbps'], [192, '192 kbps'], [320, '320 kbps']], () => S.out.abr, v => S.out.abr = v),
      recBtn, h('div', { class: 'sub', style: 'margin:8px 0 4px' }, 'このセッションの録画'), list)));

    const urlIn = h('input', { type: 'url', placeholder: 'https://…/whip/…' });
    urlIn.addEventListener('input', () => { S.out.whipUrl = urlIn.value; save(); }); urlIn.addEventListener('keydown', e => e.stopPropagation());
    reg(() => { if (document.activeElement !== urlIn) urlIn.value = S.out.whipUrl; });
    const tokIn = h('input', { type: 'password', placeholder: '（必要な場合）' });
    tokIn.addEventListener('input', () => { S.out.whipToken = tokIn.value; save(); }); tokIn.addEventListener('keydown', e => e.stopPropagation());
    reg(() => { if (document.activeElement !== tokIn) tokIn.value = S.out.whipToken; });
    const stBtn = h('button', { class: 'btn full', onclick: () => Stream.state === 'off' ? streamStart() : streamStop() });
    reg(() => { stBtn.textContent = Stream.state === 'off' ? '配信開始（ON AIR）' : Stream.state === 'connecting' ? '接続中…（押すと中止）' : '配信停止'; stBtn.className = 'btn full ' + (Stream.state === 'off' ? 'primary' : 'red'); });
    root.append(h('div', { class: 'pal open' }, h('h3', null, '配信（WHIP）'), h('div', { class: 'body' },
      h('div', { class: 'row' }, h('label', null, 'WHIP URL'), urlIn),
      h('div', { class: 'row' }, h('label', null, 'ストリームキー'), tokIn),
      select('ビットレート', [[2500, '2.5 Mbps'], [4500, '4.5 Mbps'], [6000, '6 Mbps'], [9000, '9 Mbps'], [12000, '12 Mbps']], () => S.out.sbr, v => S.out.sbr = v),
      stBtn,
      h('div', { class: 'note', html: 'ブラウザから直接配信できる <b>WHIP</b> 方式です（Cloudflare Stream、OvenMediaEngine、MediaMTX、Dolby.io、OBS 30+ の WHIP 受信 など）。<br>YouTube などへ RTMP で配信したい場合は、下の外部出力ウィンドウ（プログラム）を OBS でキャプチャして配信してください。' }))));

    const outs = h('div', { class: 'seg' });
    [['in1', '1'], ['in2', '2'], ['in3', '3'], ['in4', '4'], ['mv', 'M/V'], ['pgm', 'PGM']].forEach(([v, t]) => {
      const b = h('button', { onclick: () => setOutput(v) }, t); outs.append(b);
      reg(() => b.classList.toggle('on', S.out.outSrc === v && outWin && !outWin.closed));
    });
    root.append(h('div', { class: 'pal open' }, h('h3', null, '外部出力（HDMI OUT 相当）'), h('div', { class: 'body' },
      h('div', { class: 'row' }, h('label', null, '出力'), outs),
      h('div', { class: 'note' }, 'ボタンを押すと出力ウィンドウが開きます。プロジェクターや2台目のモニターにドラッグして、ダブルクリックでフルスクリーン。Zoom などに「ウェブカメラ」として出したい時は、このウィンドウを OBS の仮想カメラで取り込んでください。'))));

    root.append(h('div', { class: 'pal open' }, h('h3', null, '静止画キャプチャ'), h('div', { class: 'body' },
      h('div', { class: 'row' },
        h('button', { class: 'btn', onclick: () => snapshot(true) }, 'プログラムをメディアプールへ'),
        h('button', { class: 'btn', onclick: () => snapshot(false) }, 'PNG で保存')))));
  });
}
function snapshot(toPool) {
  R.snap = c => {
    c.toBlob(b => {
      if (toPool) { const s = freeSlot(); if (s < 0) return toast('メディアプールがいっぱいです', true); setStill(s, b, 'キャプチャ ' + new Date().toLocaleTimeString()).then(() => toast(`スロット ${s + 1} に取り込みました`)); }
      else { const a = h('a', { href: URL.createObjectURL(b), download: `Still_${Date.now()}.png` }); document.body.append(a); a.click(); a.remove(); }
    }, 'image/png');
  };
}

/* ============================================================
   右ペイン：設定
   ============================================================ */
const devices = { video: [], audio: [] };
async function refreshDevices() {
  try {
    const d = await navigator.mediaDevices.enumerateDevices();
    devices.video = d.filter(x => x.kind === 'videoinput');
    devices.audio = d.filter(x => x.kind === 'audioinput' && x.deviceId !== 'default' && x.deviceId !== 'communications');
  } catch (e) {}
  syncAll();
}
async function askPermission() {
  try {
    const st = await navigator.mediaDevices.getUserMedia({ video: true, audio: true }).catch(() => navigator.mediaDevices.getUserMedia({ video: true }));
    st.getTracks().forEach(t => t.stop());
    await refreshDevices();
    toast('カメラ・マイクへのアクセスが許可されました');
    return true;
  } catch (e) { toast('カメラ・マイクへのアクセスが拒否されました。アドレスバー左の設定から許可してください', true); return false; }
}
function renderSettingsPane() {
  buildPane('settings', $('#paneSettings'), root => {
    root.append(h('div', { class: 'row' },
      h('button', { class: 'btn primary', onclick: askPermission }, 'カメラ・マイクへのアクセスを許可'),
      h('button', { class: 'btn', style: 'flex:none', onclick: refreshDevices }, '再検出')));
    for (let i = 0; i < 4; i++) {
      const n = i + 1, cfg = S.inputs[i], src = inputs[i];
      const chip = h('span', { class: 'chip' });
      reg(() => { chip.textContent = src.live ? (src.res || 'LIVE') : (cfg.type === 'none' ? 'なし' : '信号なし'); chip.style.background = src.live ? '#1d5a2d' : ''; chip.style.color = src.live ? '#bff5cc' : ''; });
      const status = h('div', { class: 'sub' });
      reg(() => status.textContent = src.status);
      const nameIn = h('input', { type: 'text', value: cfg.name, maxLength: 20 });
      nameIn.addEventListener('change', () => { cfg.name = nameIn.value || `カメラ${n}`; changed(); rebuildPanels(); });
      const shortIn = h('input', { type: 'text', value: cfg.short, maxLength: 5, style: 'flex:none;width:70px' });
      shortIn.addEventListener('change', () => { cfg.short = (shortIn.value || `CAM${n}`).toUpperCase(); shortIn.value = cfg.short; changed(); rebuildPanels(); renderAudioPane(); });
      [nameIn, shortIn].forEach(e => e.addEventListener('keydown', ev => ev.stopPropagation()));
      const typeSel = select('ソース', [['none', 'なし'], ['camera', 'カメラ / キャプチャー'], ['screen', '画面共有'], ['file', '動画ファイル'], ['still', '静止画（メディアプール）'], ['bars', 'カラーバー']], () => cfg.type, v => { cfg.type = v; src.apply(); renderSettingsPane(); });
      const box = h('div', { class: 'inputcard' }, h('h4', null, `入力 ${n}`, chip),
        h('div', { class: 'row' }, h('label', null, '名前'), nameIn, shortIn), typeSel);
      if (cfg.type === 'camera') {
        box.append(
          select('デバイス', () => [['', '（自動）'], ...devices.video.map(d => [d.deviceId, d.label || 'カメラ'])], () => cfg.deviceId, v => { cfg.deviceId = v; src.apply(); }),
          select('解像度', [['1080', '1920×1080'], ['720', '1280×720'], ['2160', '3840×2160']], () => cfg.res, v => { cfg.res = v; src.apply(); }),
          select('音声', () => [['auto', '自動（同じ機器の音声）'], ['none', 'なし'], ...devices.audio.map(d => [d.deviceId, d.label || 'マイク'])], () => cfg.audio, v => { cfg.audio = v; src.apply(); }));
      } else if (cfg.type === 'screen') {
        box.append(toggle('音声も取り込む', () => cfg.screenAudio, v => cfg.screenAudio = v),
          h('div', { class: 'row' }, h('button', { class: 'btn', onclick: () => src.apply({ gesture: true }) }, '画面を選ぶ')));
      } else if (cfg.type === 'file') {
        const f = h('input', { type: 'file', accept: 'video/*,audio/*', style: 'display:none' });
        f.addEventListener('change', () => f.files[0] && src.apply({ file: f.files[0] }));
        box.append(f, h('div', { class: 'row' },
          h('button', { class: 'btn', onclick: () => f.click() }, 'ファイルを選ぶ'),
          h('button', { class: 'btn', onclick: () => { if (src.video) { src.video.currentTime = 0; src.video.play(); } } }, '⏮ 頭出し'),
          h('button', { class: 'btn', onclick: () => { const v = src.video; if (v) v.paused ? v.play() : v.pause(); } }, '⏯ 再生/停止')),
          toggle('ループ再生', () => cfg.loop, v => { cfg.loop = v; if (src.video) src.video.loop = v; }));
      } else if (cfg.type === 'still') {
        box.append(select('スロット', () => Array.from({ length: POOL_N }, (_, k) => [k, `${k + 1}: ${pool[k] ? pool[k].name : '—'}`]), () => cfg.still, v => { cfg.still = v; src.apply(); }));
      }
      if (cfg.type !== 'none') box.append(
        seg('表示', [['fit', 'フィット'], ['fill', 'フィル'], ['stretch', 'ストレッチ']], () => cfg.fit, v => { cfg.fit = v; src.restatic(); }),
        toggle('左右反転', () => cfg.mirror, v => { cfg.mirror = v; src.restatic(); }));
      box.append(status);
      root.append(box);
    }
    root.append(h('div', { class: 'pal open' }, h('h3', null, 'スイッチャー'), h('div', { class: 'body' },
      seg('スイッチャーモード', [['cutbus', 'カットバス'], ['pp', 'プログラム／プレビュー']], () => S.mode, v => { S.mode = v; }),
      h('div', { class: 'sub' }, 'カットバス：入力ボタンを押すとすぐ番組が切り替わる（AUTO 点灯時はトランジション）。プログラム／プレビュー：入力ボタンでプレビューを選び、CUT / AUTO で本番へ。'),
      select('ビデオフォーマット', [[24, '1080p 24'], [25, '1080p 25'], [30, '1080p 30'], [50, '1080p 50'], [60, '1080p 60']], () => S.fps, v => setFps(v)),
      h('div', { class: 'hr' }),
      toggle('マルチビュー：ラベル', () => S.mv.labels, v => S.mv.labels = v),
      toggle('マルチビュー：オーディオメーター', () => S.mv.meters, v => S.mv.meters = v),
      toggle('マルチビュー：セーフエリア', () => S.mv.safe, v => S.mv.safe = v))));
    root.append(h('div', { class: 'pal open' }, h('h3', null, 'キーボードショートカット'), h('div', { class: 'body' },
      h('div', { class: 'kbd' }, ...[
        ['1〜4', '入力（モードに従う）'], ['Shift+1〜4', 'プログラムに直接'], ['5 / 6', 'MP1 / MP2 をプレビュー'], ['7 / 8 / 9 / 0', 'カラー1 / カラー2 / バー / ブラック'],
        ['Space', 'CUT'], ['Enter', 'AUTO'], ['M / I / W / V', 'ミックス / ディップ / ワイプ / DVE'], ['K', 'キー ON / OFF'], ['P', 'PinP ON / OFF'],
        ['D', 'DSK AUTO'], ['T', 'DSK TIE'], ['F', 'フェードトゥブラック'], ['R', '録画 開始 / 停止'], ['Esc', 'スポイト取消'],
      ].flatMap(([k, d]) => [h('kbd', null, k), h('span', null, d)])))));
    const imp = h('input', { type: 'file', accept: 'application/json', style: 'display:none' });
    imp.addEventListener('change', async () => {
      try { const j = JSON.parse(await imp.files[0].text()); localStorage.setItem('lsw.state.v1', JSON.stringify(merge(defaultState(), j))); location.reload(); }
      catch (e) { toast('読み込めませんでした', true); }
    });
    root.append(h('div', { class: 'pal open' }, h('h3', null, '設定の保存・読み込み'), h('div', { class: 'body' }, imp,
      h('div', { class: 'row' },
        h('button', { class: 'btn', onclick: () => { const a = h('a', { href: URL.createObjectURL(new Blob([JSON.stringify(S, null, 2)], { type: 'application/json' })), download: 'switcher-settings.json' }); a.click(); } }, '書き出し'),
        h('button', { class: 'btn', onclick: () => imp.click() }, '読み込み'),
        h('button', { class: 'btn', onclick: () => { if (confirm('すべての設定を初期状態に戻しますか？（メディアプールは残ります）')) { localStorage.removeItem('lsw.state.v1'); location.reload(); } } }, '初期化')))));
  });
}
function setFps(v) {
  S.fps = v; save();
  if (Rec.on || Stream.state !== 'off') toast('録画・配信中のためフォーマット変更は停止後に反映されます');
  else makeStreams();
  ticker.postMessage(1000 / S.fps);
}
function makeStreams() {
  if (pgmStream) pgmStream.getTracks().forEach(t => t.stop());
  pgmStream = glCanvas.captureStream(0);
  if (mvStream) { mvStream.getTracks().forEach(t => t.stop()); mvStream = null; }
  if (outWin && !outWin.closed) setOutput(S.out.outSrc);
}

/* ============================================================
   下部パネル：ハードウェア風
   ============================================================ */
const hwMeters = [];
const lights = [];   // [el, fn → className]
function K(label, cls, onclick, lightFn, title) {
  const b = h('button', { class: 'k ' + (cls || ''), onclick, title });
  if (typeof label === 'string') b.innerHTML = label; else b.append(label);
  b._base = 'k ' + (cls || '');
  if (lightFn) lights.push([b, lightFn]);
  return b;
}
function sec(label, ...kids) { return h('div', { class: 'sec' }, h('div', { class: 'sl' }, label), ...kids); }
function rebuildPanels() { lights.length = 0; hwMeters.length = 0; paneSync.set('panel', []); buildHW(); buildSW(); fitPanel(); }

function buildHW() {
  const root = $('#hw'); root.innerHTML = '';
  // オーディオ
  const acols = h('div', { style: 'display:flex;gap:4px' });
  for (const [id, nm] of [['mic1', 'MIC 1'], ['mic2', 'MIC 2'], ['in1', '1'], ['in2', '2'], ['in3', '3'], ['in4', '4']]) {
    const isIn = id.startsWith('in');
    const mi = h('i'); hwMeters.push([id, mi]);
    const lvl = d => () => { setA(id, 'fader', clamp(Math.round((S.audio[id].fader + d) * 2) / 2, -60, 10)); syncAll(); toast(`${chName(id)} レベル ${fmtDb(S.audio[id].fader)} dB`); };
    acols.append(h('div', { class: 'acol' }, h('span', { class: 'an' }, nm), h('div', { class: 'minimeter', style: 'height:52px' }, mi),
      h('div', { style: 'display:flex;gap:3px' }, K('▼', 'xs', lvl(-2)), K('▲', 'xs', lvl(+2))),
      h('div', { style: 'display:flex;gap:3px' },
        K('ON', 'xs', () => { setA(id, 'mode', S.audio[id].mode === 'on' ? 'off' : 'on'); syncAll(); }, () => S.audio[id].mode === 'on' ? 'lit' : ''),
        isIn ? K('AFV', 'xs', () => { setA(id, 'mode', S.audio[id].mode === 'afv' ? 'off' : 'afv'); syncAll(); }, () => S.audio[id].mode === 'afv' ? 'amb' : '')
          : K('OFF', 'xs', () => { setA(id, 'mode', 'off'); syncAll(); }, () => S.audio[id].mode === 'off' ? 'lit' : ''))));
  }
  root.append(sec('AUDIO', acols));
  // 入力
  const vin = h('div', { style: 'display:flex;gap:7px;align-items:flex-start;padding-top:14px' });
  for (let n = 1; n <= 4; n++) {
    vin.append(K(`${n}<span class="sub">${S.inputs[n - 1].short}</span>`, 'big', () => inputPress(n), (pg, pv) => {
      if (S.pgm === n || (R.t > 0 && S.trans.next.bkgd && S.pvw === n && !S.trans.prevTrans)) return 'red';
      if (S.mode === 'pp' && S.pvw === n) return 'green';
      return '';
    }));
  }
  root.append(sec('VIDEO INPUTS', vin));
  // PinP
  const pip = h('div', { class: 'grid', style: 'grid-template-columns:repeat(4,auto)' });
  for (let n = 1; n <= 4; n++) pip.append(K(String(n), 's', () => pipSet(n), () => S.usk.onAir && S.usk.type === 'dve' && S.usk.fill === n ? 'red' : ''));
  pip.append(K('OFF', 's', () => { if (S.usk.type === 'dve') keyOnAir(false); }, () => !(S.usk.onAir && S.usk.type === 'dve') ? 'lit' : ''));
  pip.append(h('span'));
  const posB = K('POS', 's', () => pipPos(S.usk.pipPos + 1), null, 'PinP の位置を切り替え');
  posB.style.gridColumn = 'span 2'; pip.append(posB);
  pip.children[4].style.gridColumn = 'span 2'; pip.children[5].remove();
  root.append(sec('PICTURE IN PICTURE', pip));
  // キー
  root.append(sec('KEY', h('div', { class: 'grid' },
    K('ON', 's', () => { S.usk.type = S.usk.keyType; keyOnAir(true); }, () => S.usk.onAir && S.usk.type !== 'dve' ? 'red' : '', '設定済みのキー（クロマ等）をオン'),
    K('OFF', 's', () => { if (S.usk.type !== 'dve') keyOnAir(false); }, () => !(S.usk.onAir && S.usk.type !== 'dve') ? 'lit' : ''))));
  // トランジション
  const fx = h('div', { class: 'grid', style: 'grid-template-columns:repeat(6,auto)' });
  HW_FX.forEach(f => fx.append(K(f.label ? `<span style="font-size:10px">${f.label}</span>` : f.icon, 's', () => { f.set(); changed(); }, () => f.is() ? 'lit' : '')));
  const ca = h('div', { class: 'grid' },
    K('CUT', '', () => { if (S.mode === 'cutbus') { S.hwAuto = false; changed(); } else cut(); }, () => S.mode === 'cutbus' ? (!S.hwAuto ? 'lit' : '') : ''),
    K('AUTO', '', () => { if (S.mode === 'cutbus') { S.hwAuto = true; changed(); } else autoTrans(); }, () => R.auto ? 'red' : S.mode === 'cutbus' && S.hwAuto ? 'lit' : ''));
  root.append(sec('TRANSITION', h('div', { style: 'display:flex;gap:8px;align-items:flex-start' }, ca, fx),
    h('div', { style: 'display:flex;gap:6px;align-items:center;margin-top:6px' }, h('span', { class: 'sl', style: 'margin:0' }, 'RATE'), rateBoxLive())));
  // FTB
  root.append(sec('FADE TO BLACK', K('FTB', 'big', ftbGo, () => R.ftbAuto ? 'red' : R.ftbOn ? 'red flash' : '')));
  // 出力
  const vo = h('div', { class: 'grid', style: 'grid-template-columns:repeat(3,auto)' });
  [['in1', '1'], ['in2', '2'], ['in3', '3'], ['in4', '4'], ['mv', 'M/V'], ['pgm', 'PGM']].forEach(([v, t]) => vo.append(K(t, 's', () => setOutput(v), () => S.out.outSrc === v && outWin && !outWin.closed ? 'lit' : '')));
  root.append(sec('VIDEO OUT', vo));
  // 録画・配信
  root.append(sec('RECORD / STREAM', h('div', { class: 'grid', style: 'grid-template-columns:auto auto' },
    K('REC', 's', recStart, () => Rec.on ? 'red' : ''), K('STOP', 's', recStop, () => !Rec.on ? 'lit' : ''),
    K('ON AIR', 's', streamStart, () => Stream.state === 'live' ? 'red' : Stream.state === 'connecting' ? 'red flash' : ''), K('OFF', 's', () => streamStop(), () => Stream.state === 'off' ? 'lit' : ''))));
}
function rateBoxLive() {
  const b = h('div', { class: 'ratebox', contentEditable: 'true', spellcheck: false });
  const commit = () => { const v = parseRate(b.textContent); if (v) { S.trans.rates[S.trans.style] = v; changed(); } b.textContent = fmtRate(rateOf()); };
  b.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); b.blur(); } });
  b.addEventListener('blur', commit);
  const list = paneSync.get('panel') || []; paneSync.set('panel', list);
  list.push(() => { if (document.activeElement !== b) b.textContent = fmtRate(rateOf()); });
  b.textContent = fmtRate(rateOf());
  return b;
}

/* ============================================================
   下部パネル：ソフトウェアコントロール風（M/E）
   ============================================================ */
let tbarEl;
function buildSW() {
  const root = $('#sw'); root.innerHTML = '';
  const rows = h('div');
  const pr = h('div', { class: 'busrow' }, h('span', { class: 'buslbl r' }, 'PROGRAM'));
  const pv = h('div', { class: 'busrow' }, h('span', { class: 'buslbl g' }, 'PREVIEW'));
  for (const id of BUS) {
    pr.append(K(srcLabel(id, true), 's', () => setProgram(id), () => S.pgm === id ? 'red' : ''));
    pv.append(K(srcLabel(id, true), 's', () => setPreview(id), () => S.pvw === id ? 'green' : ''));
  }
  rows.append(pr, pv);
  root.append(sec('M/E 1', rows));
  root.append(sec('NEXT TRANSITION', h('div', { class: 'grid', style: 'grid-template-columns:auto auto' },
    h('span'), K('ON AIR', 'xs', () => keyOnAir(!S.usk.onAir), () => S.usk.onAir ? 'red' : ''),
    K('BKGD', 's', () => { S.trans.next.bkgd = !S.trans.next.bkgd; if (!S.trans.next.bkgd && !S.trans.next.key) S.trans.next.bkgd = true; changed(); }, () => S.trans.next.bkgd ? 'yel' : ''),
    K('KEY 1', 's', () => { S.trans.next.key = !S.trans.next.key; if (!S.trans.next.bkgd && !S.trans.next.key) S.trans.next.key = true; changed(); }, () => S.trans.next.key ? 'yel' : ''))));
  root.append(sec('TRANSITION STYLE', h('div', { class: 'grid', style: 'grid-template-columns:auto auto' },
    ...STYLES.map(st => K(st.toUpperCase(), 's', () => setStyle(st), () => S.trans.style === st ? 'yel' : '')),
    K('PREV<br>TRANS', 's', () => { S.trans.prevTrans = !S.trans.prevTrans; changed(); }, () => S.trans.prevTrans ? 'red' : ''),
    h('div', { style: 'display:flex;align-items:center' }, rateBoxLive()))));
  tbarEl = h('div', { class: 'tbar' }, h('div', { class: 'rail' }), h('div', { class: 'fill' }), h('div', { class: 'h' }));
  const tb = e => { const r = tbarEl.getBoundingClientRect(); tbarSet(clamp((e.clientY - r.top - 8) / (r.height - 16), 0, 1)); };
  tbarEl.addEventListener('pointerdown', e => { if (R.auto) return; R.dragging = true; tbarEl.setPointerCapture(e.pointerId); tb(e); });
  tbarEl.addEventListener('pointermove', e => R.dragging && tb(e));
  tbarEl.addEventListener('pointerup', () => R.dragging = false);
  root.append(sec('TRANSITION', h('div', { style: 'display:flex;gap:10px;flex:1' },
    h('div', { class: 'grid', style: 'align-content:start' }, K('CUT', '', cut), K('AUTO', '', autoTrans, () => R.auto ? 'red' : '')),
    tbarEl)));
  const dskRate = h('div', { class: 'ratebox', contentEditable: 'true', spellcheck: false });
  dskRate.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); dskRate.blur(); } });
  dskRate.addEventListener('blur', () => { const v = parseRate(dskRate.textContent); if (v) { S.dsk.rate = v; changed(); } dskRate.textContent = fmtRate(S.dsk.rate); });
  paneSync.get('panel').push(() => { if (document.activeElement !== dskRate) dskRate.textContent = fmtRate(S.dsk.rate); });
  dskRate.textContent = fmtRate(S.dsk.rate);
  root.append(sec('DOWNSTREAM KEY 1', h('div', { class: 'grid', style: 'grid-template-columns:auto' },
    K('TIE', 's', () => { S.dsk.tie = !S.dsk.tie; changed(); }, () => S.dsk.tie ? 'yel' : ''),
    dskRate,
    K('ON AIR', 's', dskOnAir, () => S.dsk.onAir && !R.dskAuto ? 'red' : ''),
    K('AUTO', 's', dskAutoGo, () => R.dskAuto ? 'red' : ''))));
  const ftbRate = h('div', { class: 'ratebox', contentEditable: 'true', spellcheck: false });
  ftbRate.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter') { e.preventDefault(); ftbRate.blur(); } });
  ftbRate.addEventListener('blur', () => { const v = parseRate(ftbRate.textContent); if (v) { S.ftb.rate = v; changed(); } ftbRate.textContent = fmtRate(S.ftb.rate); });
  paneSync.get('panel').push(() => { if (document.activeElement !== ftbRate) ftbRate.textContent = fmtRate(S.ftb.rate); });
  ftbRate.textContent = fmtRate(S.ftb.rate);
  root.append(sec('FADE TO BLACK', h('div', { class: 'grid' }, ftbRate, K('FTB', 'big', ftbGo, () => R.ftbAuto ? 'red' : R.ftbOn ? 'red flash' : ''))));
}

function updateLights(pg, pv) {
  for (const [b, fn] of lights) {
    const c = b._base + ' ' + (fn(pg, pv) || '');
    if (b.className !== c) b.className = c;
  }
  if (tbarEl && tbarEl.isConnected) {
    const v = R.tbarV, hgt = tbarEl.clientHeight - 16;
    const hd = tbarEl.lastChild, fill = tbarEl.children[1];
    hd.style.top = (8 + v * hgt) + 'px';
    const tt = R.t;
    if (tt > 0) { const a = R.tbarBase === 0 ? 0 : 1; const y0 = Math.min(a, v), y1 = Math.max(a, v); fill.style.top = (8 + y0 * hgt) + 'px'; fill.style.height = ((y1 - y0) * hgt) + 'px'; }
    else fill.style.height = '0';
  }
  const ftb = $('#stFtb');
  const on = R.ftbT > 0; if (ftb.classList.contains('warn') !== on) ftb.classList.toggle('warn', on);
  const mi = S.mode === 'cutbus' ? 'モード: カットバス' + (S.hwAuto ? '（AUTO）' : '（CUT）') : 'モード: プログラム／プレビュー';
  const modeInfo = $('#modeInfo'); if (modeInfo.textContent !== mi) modeInfo.textContent = mi;
}

/* ============================================================
   キーボード
   ============================================================ */
document.addEventListener('keydown', e => {
  if (!engine) return;
  const tg = e.target;
  if (tg && (tg.tagName === 'INPUT' && !['range', 'checkbox', 'color'].includes(tg.type) || tg.tagName === 'TEXTAREA' || tg.isContentEditable)) return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key;
  const dm = { Digit1: 1, Digit2: 2, Digit3: 3, Digit4: 4 };
  if (dm[e.code]) { e.preventDefault(); e.shiftKey ? setProgram(dm[e.code]) : inputPress(dm[e.code]); return; }
  const pm = { Digit5: MP1, Digit6: MP2, Digit7: COL1, Digit8: COL2, Digit9: BARS, Digit0: BLK };
  if (pm[e.code] != null) { e.preventDefault(); e.shiftKey ? setProgram(pm[e.code]) : (S.mode === 'pp' ? setPreview(pm[e.code]) : inputPress(pm[e.code])); return; }
  if (k === ' ') { e.preventDefault(); cut(); }
  else if (k === 'Enter') { e.preventDefault(); autoTrans(); }
  else if (k === 'Escape') endPick();
  else {
    const l = k.toLowerCase();
    if (l === 'm') setStyle('mix'); else if (l === 'i') setStyle('dip'); else if (l === 'w') setStyle('wipe'); else if (l === 'v') setStyle('dve');
    else if (l === 'k') { if (!S.usk.onAir) S.usk.type = S.usk.keyType; keyOnAir(!S.usk.onAir); }
    else if (l === 'p') { if (S.usk.onAir && S.usk.type === 'dve') keyOnAir(false); else pipSet(S.usk.fill >= 1 && S.usk.fill <= 4 ? S.usk.fill : 2); }
    else if (l === 'd') dskAutoGo(); else if (l === 't') { S.dsk.tie = !S.dsk.tie; changed(); }
    else if (l === 'f') ftbGo(); else if (l === 'r') Rec.on ? recStop() : recStart();
  }
});

/* ============================================================
   起動
   ============================================================ */
const ticker = new Worker(URL.createObjectURL(new Blob(['let iv;onmessage=e=>{clearInterval(iv);iv=setInterval(()=>postMessage(0),e.data)}'], { type: 'text/javascript' })));
let busy = false;
ticker.onmessage = () => { if (busy || !engine) return; busy = true; try { tick(); } catch (e) { console.error(e); } busy = false; };

async function boot() {
  $('#boot').classList.add('hide');
  glCanvas = document.createElement('canvas');
  glCanvas.style.cssText = 'width:2px;height:2px'; $('#hiddenMedia').append(glCanvas);
  try { engine = new Engine(glCanvas); } catch (e) { alert('WebGL2 を初期化できませんでした: ' + e.message); return; }
  mvCanvas = $('#mv'); mvCtx = mvCanvas.getContext('2d', { alpha: false });
  audio = new AudioEngine();
  audio.ctx.resume();
  for (const [id] of ACH) audio.add(id, id);
  applyAudioState();
  updateColors();
  engine.setColor(BARS, [0, 0, 0]); engine.upload(BARS, barsCanvas(), 1920, 1080, {});
  for (let n = 1; n <= 4; n++) { inputs.push(new InputSource(n)); engine.setBlank(n, 1); }
  await loadPool();
  updateMP();
  try { Rec.dir = await idb('kv', 'readonly', s => s.get('recDir')) || null; } catch (e) {}
  makeStreams();
  renderSwitcherPane(); renderMediaPane(); renderAudioPane(); renderOutputPane(); renderSettingsPane();
  rebuildPanels(); setPanel(S.panel); setTimeout(fitMV, 50);
  ticker.postMessage(1000 / S.fps);
  // デバイス
  if (navigator.mediaDevices) {
    navigator.mediaDevices.addEventListener('devicechange', refreshDevices);
    await refreshDevices();
    const hasLabels = devices.video.some(d => d.label);
    const fresh = S.inputs.every(c => c.type === 'none');
    if (fresh && devices.video.length) {
      if (!hasLabels) await askPermission();
      devices.video.slice(0, 4).forEach((d, i) => { S.inputs[i].type = 'camera'; S.inputs[i].deviceId = d.deviceId; S.inputs[i].name = (d.label || `カメラ${i + 1}`).replace(/\s*\(.*?\)\s*$/, '').slice(0, 20) || `カメラ${i + 1}`; });
      save(); rebuildPanels();
    }
    for (const s of inputs) s.apply();
    for (const id of ['mic1', 'mic2']) if (S.audio[id].device) applyMic(id);
    renderSettingsPane(); renderAudioPane();
  }
  // マルチビュークリック
  mvCanvas.addEventListener('click', e => {
    const hit = mvHit(e); if (!hit) return;
    const { t, u, v } = hit;
    if (R.pick) {
      const src = t.id === 'pgm' || t.id === 'pvw' ? S.usk.fill : t.id;
      if (typeof src !== 'number') return;
      const rgb = engine.sample(src, u, v);
      S.usk.chroma.ck = rgbToCbCr(rgb); S.usk.chroma.color = rgb2hex(rgb);
      endPick(); changed(); toast('キーカラーを設定しました');
      return;
    }
    if (typeof t.id === 'number') inputPress(t.id);
  });
  window.addEventListener('beforeunload', e => { if (Rec.on || Stream.state !== 'off') { e.preventDefault(); e.returnValue = ''; } });
}
function fitMV() {
  const L = $('.left'), b = $('#mvbox');
  const W = L.clientWidth - 16, H = L.clientHeight - 16;
  const w = Math.min(W, H * 16 / 9);
  b.style.width = Math.floor(w) + 'px'; b.style.height = Math.floor(w * 9 / 16) + 'px';
  fitPanel();
}
function fitPanel() {
  for (const el of [$('#hw'), $('#sw')]) {
    if (el.classList.contains('hide')) continue;
    el.style.zoom = 1;
    const sw = el.scrollWidth, cw = el.clientWidth;
    if (sw > cw + 1) el.style.zoom = Math.max(0.6, cw / sw).toFixed(3);
  }
}
window.addEventListener('resize', fitMV); fitMV();
function setPanel(p) {
  S.panel = p; save();
  $('#hw').classList.toggle('hide', p !== 'hw'); $('#sw').classList.toggle('hide', p !== 'sw');
  fitPanel();
  $$('#panelSel button').forEach(b => b.classList.toggle('on', b.dataset.p === p));
}
$$('#panelSel button').forEach(b => b.addEventListener('click', () => setPanel(b.dataset.p)));
$$('#tabs button').forEach(b => b.addEventListener('click', () => {
  $$('#tabs button').forEach(x => x.classList.toggle('on', x === b));
  $$('.pane').forEach(p => p.classList.toggle('on', p.dataset.pane === b.dataset.tab));
}));
$('#bootGo').addEventListener('click', boot);
