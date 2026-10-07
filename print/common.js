/* 印刷ステーション 共通部品
   - GitHub API（先生の非公開リポジトリを「保管庫」として使う）
   - 暗号化（児童のPDFは先生のパスワードでしか開けない）
   保管庫の中身:
     config.json            … 公開鍵と、パスワードで暗号化した秘密鍵
     inbox/<id>.bin         … 暗号化したPDF
     inbox/<id>.json        … 暗号化した情報（年・組・番・ファイル名など）
*/
var PS = (function(){
  var API = "https://api.github.com";

  /* ---------- base64 ---------- */
  function bufToB64(buf){
    var bytes = new Uint8Array(buf), bin = "";
    for (var i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(bin);
  }
  function b64ToBuf(b64){
    var bin = atob(b64), u = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    return u.buffer;
  }
  function toUrl64(s){ return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
  function fromUrl64(s){ s = s.replace(/-/g, "+").replace(/_/g, "/"); while (s.length % 4) s += "="; return s; }
  function encLink(obj){ return toUrl64(btoa(unescape(encodeURIComponent(JSON.stringify(obj))))); }
  function decLink(s){ return JSON.parse(decodeURIComponent(escape(atob(fromUrl64(s))))); }
  var enc = new TextEncoder(), dec = new TextDecoder();

  /* ---------- GitHub API ---------- */
  function sleep(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
  function pathUrl(cfg, path){
    return API + "/repos/" + cfg.o + "/" + cfg.r + "/contents/" + path.split("/").map(encodeURIComponent).join("/");
  }
  function headers(cfg, accept, json){
    var h = { "Authorization": "Bearer " + cfg.t, "Accept": accept || "application/vnd.github+json" };
    if (json) h["Content-Type"] = "application/json";
    return h;
  }
  function apiError(r, what){
    var e = new Error(what + "（" + r.status + "）"); e.status = r.status; return e;
  }
  async function getJSON(cfg, url){
    var r = await fetch(url, { headers: headers(cfg), cache: "no-store" });
    if (!r.ok) throw apiError(r, "GitHubにつながりませんでした");
    return r.json();
  }
  async function listDir(cfg, dir){
    var r = await fetch(pathUrl(cfg, dir) + "?t=" + Date.now(), { headers: headers(cfg), cache: "no-store" });
    if (r.status === 404) return [];
    if (!r.ok) throw apiError(r, "一覧を読めませんでした");
    var a = await r.json();
    return Array.isArray(a) ? a : [];
  }
  async function getRaw(cfg, path){
    var r = await fetch(pathUrl(cfg, path) + "?t=" + Date.now(), { headers: headers(cfg, "application/vnd.github.raw"), cache: "no-store" });
    if (r.status === 404) return null;
    if (!r.ok) throw apiError(r, "ファイルを読めませんでした");
    return r.arrayBuffer();
  }
  // 同時にたくさん送られると衝突することがあるので、少し待ってやり直す
  async function putFile(cfg, path, b64, message, sha){
    for (var i = 0; i < 7; i++){
      var body = { message: message, content: b64 };
      if (sha) body.sha = sha;
      var r = await fetch(pathUrl(cfg, path), { method: "PUT", headers: headers(cfg, null, true), body: JSON.stringify(body) });
      if (r.ok) return r.json();
      if ([409, 422, 500, 502, 503].indexOf(r.status) < 0 || i === 6) throw apiError(r, "送れませんでした");
      await sleep(400 + Math.random() * 1200 * (i + 1));
    }
  }
  async function deleteFile(cfg, path, sha){
    for (var i = 0; i < 6; i++){
      var r = await fetch(pathUrl(cfg, path), { method: "DELETE", headers: headers(cfg, null, true), body: JSON.stringify({ message: "delete", sha: sha }) });
      if (r.ok || r.status === 404) return;
      if ([409, 422, 500, 502, 503].indexOf(r.status) < 0 || i === 5) throw apiError(r, "消せませんでした");
      await sleep(300 + Math.random() * 900 * (i + 1));
    }
  }
  // トークンで使えるリポジトリ（非公開のもの）
  async function privateRepos(t){
    var a = await getJSON({ t: t }, API + "/user/repos?per_page=100&sort=created&t=" + Date.now());
    return a.filter(function(x){ return x.private && x.permissions && x.permissions.push; });
  }

  /* ---------- 暗号化 ---------- */
  var S = crypto.subtle;
  function rand(n){ return crypto.getRandomValues(new Uint8Array(n)); }
  async function pwKey(pw, salt, iter){
    var base = await S.importKey("raw", enc.encode(pw), "PBKDF2", false, ["deriveKey"]);
    return S.deriveKey({ name: "PBKDF2", salt: salt, iterations: iter, hash: "SHA-256" }, base, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  }
  async function fingerprint(spkiB64){
    var h = await S.digest("SHA-256", b64ToBuf(spkiB64));
    return toUrl64(bufToB64(h)).slice(0, 16);
  }
  // 先生：鍵を作り、秘密鍵をパスワードで守った config を返す
  async function makeConfig(pw){
    var kp = await S.generateKey({ name: "RSA-OAEP", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["encrypt", "decrypt"]);
    var spki = bufToB64(await S.exportKey("spki", kp.publicKey));
    var pkcs8 = await S.exportKey("pkcs8", kp.privateKey);
    var salt = rand(16), iv = rand(12), iter = 210000;
    var k = await pwKey(pw, salt, iter);
    var data = await S.encrypt({ name: "AES-GCM", iv: iv }, k, pkcs8);
    return { config: { v: 1, app: "print-station", pub: spki, priv: { salt: bufToB64(salt), iv: bufToB64(iv), iter: iter, data: bufToB64(data) }, created: new Date().toISOString() },
             privateKey: kp.privateKey, pkcs8: bufToB64(pkcs8) };
  }
  async function unlock(config, pw){
    var p = config.priv;
    var k = await pwKey(pw, new Uint8Array(b64ToBuf(p.salt)), p.iter);
    var pkcs8;
    try { pkcs8 = await S.decrypt({ name: "AES-GCM", iv: new Uint8Array(b64ToBuf(p.iv)) }, k, b64ToBuf(p.data)); }
    catch (e) { var er = new Error("パスワードがちがいます"); er.badPassword = true; throw er; }
    return { privateKey: await importPriv(bufToB64(pkcs8)), pkcs8: bufToB64(pkcs8) };
  }
  function importPriv(b64){ return S.importKey("pkcs8", b64ToBuf(b64), { name: "RSA-OAEP", hash: "SHA-256" }, false, ["decrypt"]); }
  function importPub(b64){ return S.importKey("spki", b64ToBuf(b64), { name: "RSA-OAEP", hash: "SHA-256" }, false, ["encrypt"]); }

  // 児童：PDFと情報を暗号化
  async function seal(pub, bytes, meta){
    var key = await S.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt"]);
    var raw = await S.exportKey("raw", key);
    var iv = rand(12), miv = rand(12);
    var ct = await S.encrypt({ name: "AES-GCM", iv: iv }, key, bytes);
    var mct = await S.encrypt({ name: "AES-GCM", iv: miv }, key, enc.encode(JSON.stringify(meta)));
    var wk = await S.encrypt({ name: "RSA-OAEP" }, pub, raw);
    return { bin: ct, head: { v: 1, k: bufToB64(wk), iv: bufToB64(iv), miv: bufToB64(miv), m: bufToB64(mct) } };
  }
  // 先生：情報を開く（AESの鍵も返す）
  async function openHead(priv, head){
    var raw = await S.decrypt({ name: "RSA-OAEP" }, priv, b64ToBuf(head.k));
    var key = await S.importKey("raw", raw, "AES-GCM", false, ["decrypt"]);
    var m = await S.decrypt({ name: "AES-GCM", iv: new Uint8Array(b64ToBuf(head.miv)) }, key, b64ToBuf(head.m));
    return { meta: JSON.parse(dec.decode(m)), key: key };
  }
  function openBin(key, head, buf){ return S.decrypt({ name: "AES-GCM", iv: new Uint8Array(b64ToBuf(head.iv)) }, key, buf); }

  /* ---------- 画像・PDFを1つのPDFに ---------- */
  function loadImage(file){
    return new Promise(function(res, rej){
      var url = URL.createObjectURL(file), img = new Image();
      img.onload = function(){ res({ img: img, url: url }); };
      img.onerror = function(){ URL.revokeObjectURL(url); rej(new Error("画像を読めませんでした")); };
      img.src = url;
    });
  }
  // 写真は大きすぎるので縮めてJPEGに（向きはブラウザが直してくれる）
  async function imageToJpeg(file){
    var o = await loadImage(file), img = o.img, max = 2000;
    var w = img.naturalWidth, h = img.naturalHeight, s = Math.min(1, max / Math.max(w, h));
    var c = document.createElement("canvas"); c.width = Math.round(w * s); c.height = Math.round(h * s);
    var g = c.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, c.width, c.height); g.drawImage(img, 0, 0, c.width, c.height);
    URL.revokeObjectURL(o.url);
    var blob = await new Promise(function(r){ c.toBlob(r, "image/jpeg", 0.85); });
    return { bytes: await blob.arrayBuffer(), w: c.width, h: c.height };
  }
  async function filesToPdf(files){
    var lib = window.PDFLib, out = await lib.PDFDocument.create(), A4 = [595.28, 841.89];
    for (var i = 0; i < files.length; i++){
      var f = files[i];
      if (f.type === "application/pdf" || /\.pdf$/i.test(f.name)){
        var src = await lib.PDFDocument.load(await f.arrayBuffer(), { ignoreEncryption: true });
        var pages = await out.copyPages(src, src.getPageIndices());
        pages.forEach(function(p){ out.addPage(p); });
      } else {
        var j = await imageToJpeg(f), img = await out.embedJpg(j.bytes);
        var land = j.w > j.h, pw = land ? A4[1] : A4[0], ph = land ? A4[0] : A4[1], m = 20;
        var sc = Math.min((pw - m * 2) / j.w, (ph - m * 2) / j.h);
        var page = out.addPage([pw, ph]);
        page.drawImage(img, { x: (pw - j.w * sc) / 2, y: (ph - j.h * sc) / 2, width: j.w * sc, height: j.h * sc });
      }
    }
    return { bytes: await out.save(), pages: out.getPageCount() };
  }
  async function mergePdfs(list){
    var lib = window.PDFLib, out = await lib.PDFDocument.create();
    for (var i = 0; i < list.length; i++){
      var src = await lib.PDFDocument.load(list[i], { ignoreEncryption: true });
      (await out.copyPages(src, src.getPageIndices())).forEach(function(p){ out.addPage(p); });
    }
    return out.save();
  }

  /* ---------- そのほか ---------- */
  function lsGet(k){ try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function lsSet(k, v){ try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  function lsDel(k){ try { localStorage.removeItem(k); } catch (e) {} }
  function qrSvg(text, cell){
    var q = qrcode(0, "M"); q.addData(text); q.make();
    return q.createSvgTag({ cellSize: cell || 4, margin: 2, scalable: true });
  }
  function appBase(){ return location.href.replace(/[#?].*$/, "").replace(/[^/]*$/, ""); }

  /* ---------- GitHubなしモード：児童のiPad → 先生のiPad に直接送る ---------- */
  // つなぎ役（シグナリング）はPeerJSの無料サーバー。PDFの中身は通らず、端末どうしで直接送る
  function peerOpts(){
    var o = { debug: 0, config: { iceServers: [{ urls: "stun:stun.l.google.com:19302" }, { urls: "stun:stun1.l.google.com:19302" }] } };
    var h = lsGet("ps-peer-host"); if (h) for (var k in h) o[k] = h[k];   // テスト用
    return o;
  }
  function newPeerId(){ var a = rand(12), s = ""; for (var i = 0; i < a.length; i++) s += "abcdefghijkmnpqrstuvwxyz23456789"[a[i] % 32]; return "printstation-" + s; }
  // 先生のiPadの中にPDFをしまっておく（IndexedDB）
  function idb(){
    return new Promise(function(res, rej){
      var r = indexedDB.open("print-station", 1);
      r.onupgradeneeded = function(){ r.result.createObjectStore("items", { keyPath: "id" }); };
      r.onsuccess = function(){ res(r.result); }; r.onerror = function(){ rej(r.error); };
    });
  }
  async function idbDo(mode, fn){
    var db = await idb();
    return new Promise(function(res, rej){
      var tx = db.transaction("items", mode), st = tx.objectStore("items"), out = fn(st);
      tx.oncomplete = function(){ res(out && out.result !== undefined ? out.result : out); db.close(); };
      tx.onerror = function(){ rej(tx.error); db.close(); };
    });
  }
  function idbPut(item){ return idbDo("readwrite", function(s){ s.put(item); }); }
  function idbAll(){ return idbDo("readonly", function(s){ return s.getAll(); }); }
  function idbGet(id){ return idbDo("readonly", function(s){ return s.get(id); }); }
  function idbDel(id){ return idbDo("readwrite", function(s){ s.delete(id); }); }

  /* ---------- ほかのアプリから先生へPDFを送る（算数プリント×印刷ステーション用） ---------- */
  // cfg: 児童用リンクの中身（{p} = GitHubなし、{o,r,t,f} = GitHub）
  function sendDirectTo(cfg, meta, bytes, prog){
    return new Promise(function(resolve, reject){
      var done = false, peer = new Peer(peerOpts()), conn = null;
      function fail(msg){ if (done) return; done = true; try{ peer.destroy(); }catch(e){} reject(new Error(msg)); }
      var t1 = setTimeout(function(){ fail("せんせいの がめんが ひらいて いないみたい。せんせいに いってね"); }, 15000);
      peer.on("error", function(e){ fail(e && e.type === "peer-unavailable" ? "せんせいの がめんが ひらいて いないみたい。せんせいに いってね" : "つながりませんでした"); });
      peer.on("open", function(){
        conn = peer.connect(cfg.p, { reliable: true });
        conn.on("open", function(){
          clearTimeout(t1); if (prog) prog("おくっています…", 75);
          conn.send({ type: "file", meta: meta, bytes: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) });
          setTimeout(function(){ fail("とどいたか わかりませんでした。もういちど おくってね"); }, 90000);
        });
        conn.on("data", function(d){ if (d && d.type === "ok" && !done){ done = true; setTimeout(function(){ try{ peer.destroy(); }catch(e){} }, 300); resolve(); } });
        conn.on("error", function(){ fail("とちゅうで きれました。もういちど おくってね"); });
      });
    });
  }
  async function sendToTeacher(cfg, meta, bytes, prog){
    if (cfg.p) return sendDirectTo(cfg, meta, bytes, prog);
    var raw = await getRaw(cfg, "config.json");
    if (!raw) throw new Error("せんせいの じゅんびが まだです");
    var conf = JSON.parse(dec.decode(raw));
    if (await fingerprint(conf.pub) !== cfg.f) throw new Error("リンクが ちがいます。せんせいに きいてね");
    var pub = await importPub(conf.pub);
    if (prog) prog("かぎを かけています…", 60);
    var s = await seal(pub, bytes, meta), id = Date.now() + "-" + Math.random().toString(36).slice(2, 8);
    if (prog) prog("おくっています…", 75);
    await putFile(cfg, "inbox/" + id + ".bin", bufToB64(s.bin), "pdf");
    await putFile(cfg, "inbox/" + id + ".json", bufToB64(enc.encode(JSON.stringify(s.head))), "info");
  }

  // 受付コード：どの先生につながっているかを、先生と児童の画面で見くらべるための4文字
  function codeOf(cfg){
    if (!cfg) return "";
    var src = cfg.p ? cfg.p : (cfg.o + "/" + cfg.r), h = 0;
    for (var i = 0; i < src.length; i++) h = (h * 31 + src.charCodeAt(i)) >>> 0;
    var a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789", out = "";
    for (var k = 0; k < 4; k++){ out += a[h % 32]; h = Math.floor(h / 32); }
    return out;
  }
  return { codeOf: codeOf, sendToTeacher: sendToTeacher, peerOpts: peerOpts, newPeerId: newPeerId, idbPut: idbPut, idbAll: idbAll, idbGet: idbGet, idbDel: idbDel,
    bufToB64: bufToB64, b64ToBuf: b64ToBuf, encLink: encLink, decLink: decLink, enc: enc,
    listDir: listDir, getRaw: getRaw, putFile: putFile, deleteFile: deleteFile, privateRepos: privateRepos,
    makeConfig: makeConfig, unlock: unlock, importPriv: importPriv, importPub: importPub, fingerprint: fingerprint,
    seal: seal, openHead: openHead, openBin: openBin, filesToPdf: filesToPdf, mergePdfs: mergePdfs,
    lsGet: lsGet, lsSet: lsSet, lsDel: lsDel, qrSvg: qrSvg, appBase: appBase, sleep: sleep };
})();
