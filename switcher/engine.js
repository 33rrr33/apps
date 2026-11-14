'use strict';
/* ============================================================
   映像エンジン（WebGL2）
   - 入力の正規化（1920x1080 にフィット／フィル／ミラー）
   - 背景トランジション（MIX / DIP / WIPE / DVE）
   - アップストリームキー（ルマ / クロマ / パターン / DVE＝PinP）
   - ダウンストリームキー＋フェードトゥブラック
   - マルチビュー描画
   ============================================================ */

const GLSL_COMMON = `
const float AR = 16.0/9.0;
float pat(vec2 uv, int p, vec2 c){
  vec2 d = uv - c; vec2 a = abs(d);
  if (p==0) return uv.x;                       // 左→右
  if (p==1) return 1.0-uv.y;                   // 上→下
  if (p==2) return a.x*2.0;                    // 縦バーンドア
  if (p==3) return a.y*2.0;                    // 横バーンドア
  if (p==4) return min(a.x,a.y)*2.0;           // クロス
  if (p==5) return max(a.x*AR/AR,a.y)*2.0;     // ボックス
  if (p==6) return a.x+a.y;                    // ダイヤ
  if (p==7) return length(d*vec2(AR,1.0))/length(vec2(AR,1.0)*0.5); // アイリス
  if (p==8) return max(uv.x,1.0-uv.y);         // 左上コーナー
  if (p==9) return max(1.0-uv.x,1.0-uv.y);     // 右上コーナー
  if (p==10) return max(1.0-uv.x,uv.y);        // 右下コーナー
  if (p==11) return max(uv.x,uv.y);            // 左下コーナー
  if (p==12) return (uv.x+1.0-uv.y)*0.5;       // 斜め
  if (p==13) return 1.0-uv.x;                  // 右→左
  return uv.x;
}
bool inside(vec2 u){ return u.x>=0.0 && u.x<=1.0 && u.y>=0.0 && u.y<=1.0; }
`;

const VS = `#version 300 es
in vec2 aPos; out vec2 vUV;
void main(){ vUV = aPos*0.5+0.5; gl_Position = vec4(aPos,0.0,1.0); }`;

const FS_NORM = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uTex; uniform vec2 uScale; uniform float uMirror; uniform float uOutA;
void main(){
  vec2 uv = (vUV-0.5)/uScale + 0.5;
  if (uMirror>0.5) uv.x = 1.0-uv.x;
  if (uv.x<0.0||uv.x>1.0||uv.y<0.0||uv.y>1.0){ o = vec4(0.0,0.0,0.0,uOutA); return; }
  o = texture(uTex, uv);
}`;

const FS_COPY = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uTex; uniform float uGain;
void main(){ vec4 c = texture(uTex, vUV); o = vec4(c.rgb*c.a*uGain, 1.0); }`;

const FS_TRANS = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uA, uB, uDip;
uniform int uMode; uniform float uT;
uniform int uPat; uniform float uSoft, uBorder, uRev; uniform vec3 uBorderCol;
uniform int uDveType; uniform vec2 uDir;
${GLSL_COMMON}
vec4 op(vec4 c){ return vec4(c.rgb*c.a, 1.0); }
void main(){
  vec4 A = op(texture(uA, vUV));
  float t = uT;
  if (uMode==0 || t<=0.0){ o = A; return; }
  vec4 B = op(texture(uB, vUV));
  if (t>=1.0 && uMode!=4){ o = B; return; }
  if (uMode==1){ o = mix(A,B,t); }
  else if (uMode==2){ vec4 D = op(texture(uDip, vUV)); o = t<0.5 ? mix(A,D,t*2.0) : mix(D,B,t*2.0-1.0); }
  else if (uMode==3){
    float v = pat(vUV, uPat, vec2(0.5)); if (uRev>0.5) v = 1.0-v;
    float s = max(uSoft, 1e-4), b = uBorder;
    float tt = t*(1.0+s+b);
    float mI = clamp((tt-b-v)/s, 0.0, 1.0);
    if (b>0.0){ float mO = clamp((tt-v)/s,0.0,1.0); vec4 c = mix(A, vec4(uBorderCol,1.0), mO); o = mix(c,B,mI); }
    else o = mix(A,B,mI);
  } else {
    vec2 d = uDir; vec2 uv = vUV;
    if (uDveType==0){ // プッシュ
      vec2 ua = uv + d*t; vec2 ub = uv - d*(1.0-t);
      if (inside(ub)) o = op(texture(uB,ub)); else if (inside(ua)) o = op(texture(uA,ua)); else o = vec4(0,0,0,1);
    } else if (uDveType==1){ // スクイーズ
      bool ax = abs(d.x)>0.5; bool neg = (d.x+d.y)<0.0;
      float p = ax ? uv.x : uv.y; float u = neg ? 1.0-p : p; float xb = 1.0-t;
      vec2 s = uv;
      if (u<xb){ float q = u/max(xb,1e-4); q = neg?1.0-q:q; if(ax) s.x=q; else s.y=q; o = op(texture(uA,s)); }
      else { float q = (u-xb)/max(t,1e-4); q = neg?1.0-q:q; if(ax) s.x=q; else s.y=q; o = op(texture(uB,s)); }
    } else if (uDveType==2){ // スライド（上に重なる）
      vec2 ub = uv - d*(1.0-t);
      o = inside(ub) ? op(texture(uB,ub)) : A;
    } else { // ズーム
      float sc = max(t,1e-3); vec2 ub = (uv-0.5)/sc+0.5;
      o = inside(ub) ? op(texture(uB,ub)) : A;
    }
  }
}`;

const FS_KEY = `#version 300 es
precision highp float;
in vec2 vUV; out vec4 o;
uniform sampler2D uBase, uFill, uKeyT;
uniform int uType; uniform float uVis, uOutGain;
uniform int uKW; uniform float uKWt; uniform int uKWpat; uniform float uKWsoft, uKWrev;
uniform float uClip, uGain, uInv, uPremul, uUseAlpha;
uniform vec2 uCK; uniform float uSim, uSmooth, uSpill, uFgLift;
uniform int uPat; uniform float uPSize, uPSoft; uniform vec2 uPPos;
uniform vec4 uRect; uniform float uBorderW, uBorderSoft; uniform vec3 uBorderCol; uniform vec4 uCrop;
uniform float uMaskOn; uniform vec4 uMask;
${GLSL_COMMON}
vec3 ycc(vec3 c){ float y=dot(c,vec3(0.2126,0.7152,0.0722)); return vec3(y,(c.b-y)/1.8556,(c.r-y)/1.5748); }
vec3 fromYcc(vec3 p){ float r=p.x+1.5748*p.z; float b=p.x+1.8556*p.y; float g=(p.x-0.2126*r-0.0722*b)/0.7152; return vec3(r,g,b); }
void main(){
  vec3 base = texture(uBase, vUV).rgb;
  float a = 0.0; vec3 F = vec3(0.0);
  if (uVis<=0.0){ o = vec4(base*uOutGain,1.0); return; }
  if (uType==0){ // ルマ / アルファ
    vec4 f = texture(uFill, vUV); F = f.rgb;
    vec4 K = texture(uKeyT, vUV);
    float k = uUseAlpha>0.5 ? K.a : dot(K.rgb, vec3(0.2126,0.7152,0.0722));
    if (uPremul>0.5) a = k;
    else { float w = max(1e-3,(1.0-uGain)*0.5); a = clamp((k-uClip)/w+0.5,0.0,1.0); }
    if (uInv>0.5) a = 1.0-a;
    if (uUseAlpha<0.5) a *= f.a;
  } else if (uType==1){ // クロマ
    vec4 f = texture(uFill, vUV);
    vec3 p = ycc(f.rgb);
    float dist = distance(p.yz, uCK);
    a = smoothstep(uSim, uSim+max(uSmooth,1e-4), dist);
    vec2 kd = normalize(uCK+vec2(1e-6));
    float pr = dot(p.yz, kd);
    if (pr>0.0) p.yz -= kd*pr*uSpill;
    p.x += uFgLift*(1.0-a);
    F = clamp(fromYcc(p),0.0,1.0);
    a *= f.a;
  } else if (uType==2){ // パターン
    vec4 f = texture(uFill, vUV); F = f.rgb;
    float v = pat(vUV, uPat, uPPos);
    a = clamp((uPSize-v)/max(uPSoft,1e-4),0.0,1.0);
    if (uInv>0.5) a = 1.0-a;
    a *= f.a;
  } else { // DVE（ピクチャー・イン・ピクチャー）
    vec2 c = uRect.xy, sz = max(uRect.zw, vec2(1e-4));
    vec2 lo = c - sz*0.5;
    vec2 fu = (vUV-lo)/sz;
    vec2 rlo = lo + sz*vec2(uCrop.x, uCrop.z);
    vec2 rhi = lo + sz*vec2(1.0-uCrop.y, 1.0-uCrop.w);
    vec2 q = max(max(rlo-vUV, vUV-rhi), 0.0) * vec2(1920.0,1080.0);
    float dOut = length(q);
    if (dOut<=0.0){ vec4 f = texture(uFill, fu); F = f.rgb*f.a; a = 1.0; }
    else if (uBorderW>0.0 && dOut<uBorderW){ F = uBorderCol; a = 1.0-smoothstep(max(uBorderW-uBorderSoft,0.0), uBorderW, dOut); }
    else a = 0.0;
  }
  if (uMaskOn>0.5){
    if (vUV.x<uMask.x || vUV.x>1.0-uMask.y || vUV.y<uMask.z || vUV.y>1.0-uMask.w) a = 0.0;
  }
  if (uKW>0){
    float v = pat(vUV, uKWpat, vec2(0.5)); if (uKWrev>0.5) v = 1.0-v;
    float s = max(uKWsoft,1e-4);
    float m = clamp((uKWt*(1.0+s)-v)/s,0.0,1.0);
    a *= (uKW==1) ? m : 1.0-m;
  } else a *= uVis;
  o = vec4(mix(base, F, a)*uOutGain, 1.0);
}`;

class Engine {
  constructor(canvas, W = 1920, H = 1080) {
    this.W = W; this.H = H;
    canvas.width = W; canvas.height = H;
    this.canvas = canvas;
    const gl = canvas.getContext('webgl2', { alpha: false, antialias: false, premultipliedAlpha: false, preserveDrawingBuffer: false, desynchronized: false, powerPreference: 'high-performance' });
    if (!gl) throw new Error('WebGL2 が使えません');
    this.gl = gl;
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    this.vao = gl.createVertexArray();
    gl.bindVertexArray(this.vao);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    this.P = {
      norm: this._prog(FS_NORM), copy: this._prog(FS_COPY),
      trans: this._prog(FS_TRANS), key: this._prog(FS_KEY),
    };
    this.sources = new Map();   // id -> {target, raw, hasAlpha}
    this.black = this.target(); this._clear(this.black, [0, 0, 0, 1]);
    this.empty = this.target(); this._clear(this.empty, [0, 0, 0, 0]);
    this.pgmT = [this.target(), this.target()];
    this.pvwT = [this.target(), this.target()];
  }

  _prog(fs) {
    const gl = this.gl;
    const mk = (type, src) => {
      const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    const p = gl.createProgram();
    gl.attachShader(p, mk(gl.VERTEX_SHADER, VS));
    gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
    gl.bindAttribLocation(p, 0, 'aPos');
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    const u = {};
    const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) { const info = gl.getActiveUniform(p, i); u[info.name] = gl.getUniformLocation(p, info.name); }
    return { p, u };
  }

  _tex() {
    const gl = this.gl, t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return t;
  }

  target() {
    const gl = this.gl, tex = this._tex();
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, this.W, this.H, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    const fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return { fb, tex };
  }

  _clear(t, c) {
    const gl = this.gl;
    gl.bindFramebuffer(gl.FRAMEBUFFER, t.fb);
    gl.viewport(0, 0, this.W, this.H);
    gl.clearColor(c[0], c[1], c[2], c[3]); gl.clear(gl.COLOR_BUFFER_BIT);
  }

  _src(id) {
    let s = this.sources.get(id);
    if (!s) { s = { target: this.target(), raw: null, hasAlpha: false, live: false }; this._clear(s.target, [0, 0, 0, 1]); this.sources.set(id, s); }
    return s;
  }
  texOf(id) { const s = this.sources.get(id); return s ? s.target.tex : this.black.tex; }

  setColor(id, rgb) { const s = this._src(id); s.hasAlpha = false; this._clear(s.target, [rgb[0], rgb[1], rgb[2], 1]); }
  setBlank(id, alpha = 1) { const s = this._src(id); s.hasAlpha = alpha < 1; this._clear(s.target, [0, 0, 0, alpha]); }

  /** 映像／画像を正規化して取り込み。el: video / canvas / ImageBitmap / img */
  upload(id, el, w, h, opt = {}) {
    if (!el || !w || !h) return;
    const gl = this.gl, s = this._src(id);
    if (!s.raw) s.raw = this._tex();
    gl.bindTexture(gl.TEXTURE_2D, s.raw);
    try { gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, el); } catch (e) { return; }
    const sa = w / h, ta = this.W / this.H;
    let sc;
    if ((opt.fit || 'fit') === 'fill') sc = sa > ta ? [sa / ta, 1] : [1, ta / sa];
    else if (opt.fit === 'stretch') sc = [1, 1];
    else sc = sa > ta ? [1, ta / sa] : [sa / ta, 1];
    const P = this.P.norm;
    gl.bindFramebuffer(gl.FRAMEBUFFER, s.target.fb);
    gl.viewport(0, 0, this.W, this.H);
    gl.useProgram(P.p);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, s.raw);
    gl.uniform1i(P.u.uTex, 0);
    gl.uniform2f(P.u.uScale, sc[0], sc[1]);
    gl.uniform1f(P.u.uMirror, opt.mirror ? 1 : 0);
    gl.uniform1f(P.u.uOutA, opt.alpha ? 0 : 1);
    s.hasAlpha = !!opt.alpha;
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  _bindTex(unit, tex, loc) { const gl = this.gl; gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(loc, unit); }

  _bg(spec, out) {
    const gl = this.gl, P = this.P.trans, u = P.u;
    gl.bindFramebuffer(gl.FRAMEBUFFER, out.fb);
    gl.viewport(0, 0, this.W, this.H);
    gl.useProgram(P.p);
    this._bindTex(0, this.texOf(spec.a), u.uA);
    this._bindTex(1, this.texOf(spec.b), u.uB);
    this._bindTex(2, this.texOf(spec.dip ?? 0), u.uDip);
    const modes = { cut: 0, mix: 1, dip: 2, wipe: 3, dve: 4 };
    gl.uniform1i(u.uMode, spec.t > 0 ? (modes[spec.mode] ?? 1) : 0);
    gl.uniform1f(u.uT, spec.t);
    const w = spec.wipe || {};
    gl.uniform1i(u.uPat, w.pattern | 0);
    gl.uniform1f(u.uSoft, w.soft ?? 0);
    gl.uniform1f(u.uBorder, w.border ?? 0);
    gl.uniform1f(u.uRev, w.rev ? 1 : 0);
    gl.uniform3fv(u.uBorderCol, w.borderCol || [1, 1, 1]);
    const dv = spec.dve || {};
    gl.uniform1i(u.uDveType, dv.type | 0);
    gl.uniform2fv(u.uDir, dv.dir || [1, 0]);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  _key(base, k, out, outGain) {
    const gl = this.gl, P = this.P.key, u = P.u;
    gl.bindFramebuffer(gl.FRAMEBUFFER, out.fb);
    gl.viewport(0, 0, this.W, this.H);
    gl.useProgram(P.p);
    this._bindTex(0, base.tex, u.uBase);
    this._bindTex(1, this.texOf(k.fill), u.uFill);
    this._bindTex(2, this.texOf(k.key ?? k.fill), u.uKeyT);
    const types = { luma: 0, chroma: 1, pattern: 2, dve: 3 };
    gl.uniform1i(u.uType, types[k.type] ?? 0);
    gl.uniform1f(u.uVis, k.vis);
    gl.uniform1f(u.uOutGain, outGain);
    gl.uniform1i(u.uKW, k.kw | 0);
    gl.uniform1f(u.uKWt, k.kwt ?? 0);
    gl.uniform1i(u.uKWpat, k.kwpat | 0);
    gl.uniform1f(u.uKWsoft, k.kwsoft ?? 0.02);
    gl.uniform1f(u.uKWrev, k.kwrev ? 1 : 0);
    gl.uniform1f(u.uClip, k.clip ?? 0.5);
    gl.uniform1f(u.uGain, k.gain ?? 0.7);
    gl.uniform1f(u.uInv, k.invert ? 1 : 0);
    gl.uniform1f(u.uPremul, k.premult ? 1 : 0);
    gl.uniform1f(u.uUseAlpha, k.useAlpha ? 1 : 0);
    gl.uniform2fv(u.uCK, k.ck || [-0.2, -0.3]);
    gl.uniform1f(u.uSim, k.sim ?? 0.12);
    gl.uniform1f(u.uSmooth, k.smooth ?? 0.08);
    gl.uniform1f(u.uSpill, k.spill ?? 0.5);
    gl.uniform1f(u.uFgLift, k.lift ?? 0);
    gl.uniform1i(u.uPat, k.pat | 0);
    gl.uniform1f(u.uPSize, k.psize ?? 0.5);
    gl.uniform1f(u.uPSoft, k.psoft ?? 0.02);
    gl.uniform2fv(u.uPPos, k.ppos || [0.5, 0.5]);
    gl.uniform4fv(u.uRect, k.rect || [0.5, 0.5, 0.5, 0.5]);
    gl.uniform1f(u.uBorderW, k.borderW ?? 0);
    gl.uniform1f(u.uBorderSoft, k.borderSoft ?? 0);
    gl.uniform3fv(u.uBorderCol, k.borderCol || [1, 1, 1]);
    gl.uniform4fv(u.uCrop, k.crop || [0, 0, 0, 0]);
    gl.uniform1f(u.uMaskOn, k.maskOn ? 1 : 0);
    gl.uniform4fv(u.uMask, k.mask || [0, 0, 0, 0]);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  /** 背景→USK→DSK＋FTB を合成し結果ターゲットを返す */
  composite(spec, T) {
    this._bg(spec.bg, T[0]);
    let cur = T[0], other = T[1];
    if (spec.usk && (spec.usk.vis > 0 || spec.usk.kw)) { this._key(cur, spec.usk, other, 1); [cur, other] = [other, cur]; }
    const gain = 1 - (spec.ftb || 0);
    if ((spec.dsk && (spec.dsk.vis > 0 || spec.dsk.kw)) || gain < 1) {
      this._key(cur, spec.dsk || { vis: 0 }, other, gain); [cur, other] = [other, cur];
    }
    return cur;
  }

  _blit(tex, x, y, w, h, gain = 1) {
    const gl = this.gl, P = this.P.copy;
    gl.viewport(x, this.H - y - h, w, h);
    gl.useProgram(P.p);
    this._bindTex(0, tex, P.u.uTex);
    gl.uniform1f(P.u.uGain, gain);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  /** 1フレーム描画。tiles: [{id|'pgm'|'pvw', x,y,w,h}]、onMV(canvas): マルチビュー合成直後に呼ばれる */
  frame(pgmSpec, pvwSpec, tiles, onMV) {
    const gl = this.gl;
    const pgm = this.composite(pgmSpec, this.pgmT);
    const pvw = this.composite(pvwSpec, this.pvwT);
    this.lastPgm = pgm; this.lastPvw = pvw;
    if (tiles && onMV) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, this.W, this.H);
      gl.clearColor(0.06, 0.06, 0.07, 1); gl.clear(gl.COLOR_BUFFER_BIT);
      for (const t of tiles) {
        if (t.id == null) continue;
        const tex = t.id === 'pgm' ? pgm.tex : t.id === 'pvw' ? pvw.tex : this.texOf(t.id);
        this._blit(tex, t.x, t.y, t.w, t.h);
      }
      onMV(this.canvas);
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    this._blit(pgm.tex, 0, 0, this.W, this.H);
  }

  /** ソース上の1点の色（0..1 RGB） */
  sample(id, u, v) {
    const gl = this.gl, s = this.sources.get(id);
    if (!s) return [0, 0, 0];
    gl.bindFramebuffer(gl.FRAMEBUFFER, s.target.fb);
    const px = new Uint8Array(4 * 9);
    const x = Math.max(1, Math.min(this.W - 2, Math.round(u * this.W))) - 1;
    const y = Math.max(1, Math.min(this.H - 2, Math.round((1 - v) * this.H))) - 1;
    gl.readPixels(x, y, 3, 3, gl.RGBA, gl.UNSIGNED_BYTE, px);
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < 9; i++) { r += px[i * 4]; g += px[i * 4 + 1]; b += px[i * 4 + 2]; }
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return [r / 9 / 255, g / 9 / 255, b / 9 / 255];
  }
}

function rgbToCbCr(rgb) {
  const y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
  return [(rgb[2] - y) / 1.8556, (rgb[0] - y) / 1.5748];
}
