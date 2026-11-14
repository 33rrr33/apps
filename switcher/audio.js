'use strict';
/* ============================================================
   オーディオミキサー（Fairlight 風）
   入力ごと: ゲイン → ディレイ → 3バンドEQ → コンプ → パン → フェーダー → ON/OFF/AFV
   マスター: リミッター → フェーダー → 録画/配信 & モニター
   ============================================================ */
const dbToLin = db => (db <= -60 ? 0 : Math.pow(10, db / 20));
const linToDb = v => (v <= 0.000001 ? -Infinity : 20 * Math.log10(v));

class AudioChannel {
  constructor(eng, id, name) {
    const c = eng.ctx;
    this.eng = eng; this.id = id; this.name = name;
    this.p = { gain: 0, delay: 0, eqOn: true, low: 0, mid: 0, high: 0, compOn: false, thresh: -18, ratio: 3, pan: 0, fader: 0, mode: 'on', mute: false };
    this.trim = c.createGain();
    this.delay = c.createDelay(1.0);
    this.low = c.createBiquadFilter(); this.low.type = 'lowshelf'; this.low.frequency.value = 120;
    this.mid = c.createBiquadFilter(); this.mid.type = 'peaking'; this.mid.frequency.value = 1000; this.mid.Q.value = 0.9;
    this.high = c.createBiquadFilter(); this.high.type = 'highshelf'; this.high.frequency.value = 8000;
    this.wet = c.createGain(); this.dry = c.createGain();
    this.comp = c.createDynamicsCompressor(); this.comp.knee.value = 6; this.comp.attack.value = 0.005; this.comp.release.value = 0.15;
    this.makeup = c.createGain();
    this.pan = c.createStereoPanner();
    this.fader = c.createGain();
    this.mix = c.createGain();
    this.analyser = c.createAnalyser(); this.analyser.fftSize = 1024; this.analyser.smoothingTimeConstant = 0;
    this.trim.connect(this.delay); this.delay.connect(this.low); this.low.connect(this.mid); this.mid.connect(this.high);
    this.high.connect(this.dry); this.dry.connect(this.pan);
    this.high.connect(this.wet); this.wet.connect(this.comp); this.comp.connect(this.makeup); this.makeup.connect(this.pan);
    this.pan.connect(this.fader); this.fader.connect(this.mix); this.mix.connect(eng.masterIn);
    this.mix.connect(this.analyser);
    this.buf = new Float32Array(this.analyser.fftSize);
    this.src = null; this.afv = 1; this.peak = -Infinity; this.hold = -Infinity; this.holdT = 0;
    this.apply();
  }
  setSource(node) {
    if (this.src) { try { this.src.disconnect(); } catch (e) {} }
    this.src = node;
    if (node) node.connect(this.trim);
  }
  set(k, v) { this.p[k] = v; this.apply(); }
  apply() {
    const p = this.p, t = this.eng.ctx.currentTime;
    this.trim.gain.setTargetAtTime(dbToLin(p.gain), t, 0.01);
    this.delay.delayTime.setTargetAtTime(Math.max(0, Math.min(1, p.delay / 1000)), t, 0.01);
    this.low.gain.value = p.eqOn ? p.low : 0;
    this.mid.gain.value = p.eqOn ? p.mid : 0;
    this.high.gain.value = p.eqOn ? p.high : 0;
    this.wet.gain.value = p.compOn ? 1 : 0; this.dry.gain.value = p.compOn ? 0 : 1;
    this.comp.threshold.value = p.thresh; this.comp.ratio.value = p.ratio;
    this.makeup.gain.value = dbToLin(Math.max(0, -p.thresh * (1 - 1 / p.ratio) * 0.35));
    this.pan.pan.setTargetAtTime(p.pan, t, 0.01);
    this.fader.gain.setTargetAtTime(dbToLin(p.fader), t, 0.02);
    this.updateMix();
  }
  setAfv(level) { if (Math.abs(level - this.afv) > 0.001) { this.afv = level; this.updateMix(); } }
  updateMix() {
    const p = this.p;
    let g = p.mode === 'off' || p.mute ? 0 : p.mode === 'afv' ? this.afv : 1;
    this.mix.gain.setTargetAtTime(g, this.eng.ctx.currentTime, 0.015);
  }
  meter(now) {
    this.analyser.getFloatTimeDomainData(this.buf);
    let m = 0; for (let i = 0; i < this.buf.length; i++) { const a = Math.abs(this.buf[i]); if (a > m) m = a; }
    const db = linToDb(m);
    this.peak = Math.max(db, (this.peak === -Infinity ? -90 : this.peak) - 1.2);
    if (db > this.hold || now - this.holdT > 1500) { this.hold = db; this.holdT = now; }
    return this.peak;
  }
}

class AudioEngine {
  constructor() {
    const C = window.AudioContext || window.webkitAudioContext;
    this.ctx = new C({ latencyHint: 'interactive', sampleRate: 48000 });
    const c = this.ctx;
    this.masterIn = c.createGain();
    this.limiter = c.createDynamicsCompressor();
    this.limiter.threshold.value = -1; this.limiter.knee.value = 0; this.limiter.ratio.value = 20; this.limiter.attack.value = 0.002; this.limiter.release.value = 0.1;
    this.masterFader = c.createGain();
    this.ftbGain = c.createGain();
    this.masterIn.connect(this.limiter); this.limiter.connect(this.masterFader); this.masterFader.connect(this.ftbGain);
    this.out = c.createMediaStreamDestination();
    this.ftbGain.connect(this.out);
    this.monitor = c.createGain(); this.monitor.gain.value = 0;
    this.ftbGain.connect(this.monitor); this.monitor.connect(c.destination);
    this.split = c.createChannelSplitter(2);
    this.ftbGain.connect(this.split);
    this.anL = c.createAnalyser(); this.anR = c.createAnalyser();
    for (const a of [this.anL, this.anR]) { a.fftSize = 1024; a.smoothingTimeConstant = 0; }
    this.split.connect(this.anL, 0); this.split.connect(this.anR, 1);
    this.bufL = new Float32Array(1024); this.bufR = new Float32Array(1024);
    this.pk = [-90, -90];
    this.channels = new Map();
    this.mp = { fader: 0, limiter: true, monitorOn: false, monitorLevel: -6, ftbFollow: true };
    this.elementSources = new WeakMap();
  }
  add(id, name) { const ch = new AudioChannel(this, id, name); this.channels.set(id, ch); return ch; }
  ch(id) { return this.channels.get(id); }
  fromStream(stream) {
    if (!stream || !stream.getAudioTracks().length) return null;
    return this.ctx.createMediaStreamSource(stream);
  }
  fromElement(el) {
    let n = this.elementSources.get(el);
    if (!n) { n = this.ctx.createMediaElementSource(el); this.elementSources.set(el, n); }
    return n;
  }
  applyMaster() {
    const m = this.mp, t = this.ctx.currentTime;
    this.masterFader.gain.setTargetAtTime(dbToLin(m.fader), t, 0.02);
    this.limiter.threshold.value = m.limiter ? -1 : 0;
    this.limiter.ratio.value = m.limiter ? 20 : 1;
    this.monitor.gain.setTargetAtTime(m.monitorOn ? dbToLin(m.monitorLevel) : 0, t, 0.02);
  }
  setFtb(level) { this.ftbGain.gain.setTargetAtTime(this.mp.ftbFollow ? 1 - level : 1, this.ctx.currentTime, 0.02); }
  masterMeter() {
    const f = (an, buf, i) => {
      an.getFloatTimeDomainData(buf);
      let m = 0; for (let k = 0; k < buf.length; k++) { const a = Math.abs(buf[k]); if (a > m) m = a; }
      const db = linToDb(m);
      this.pk[i] = Math.max(db, this.pk[i] - 1.2);
      return this.pk[i];
    };
    return [f(this.anL, this.bufL, 0), f(this.anR, this.bufR, 1)];
  }
}
