(function () {
  "use strict";

  var CLIENT_ID = "382885832208-6hh3jrjd23a1q4jqas4c8i8ks97vjlfj.apps.googleusercontent.com";
  var LS_SECRET = "cockpit_secret_v1";
  // Client secret is NEVER stored in this (public) code. It lives only in this browser's
  // localStorage, entered once by the user. Google requires it even with PKCE for web clients.
  function getSecret() { try { return localStorage.getItem(LS_SECRET) || ""; } catch (e) { return ""; } }
  function setSecret(v) { try { localStorage.setItem(LS_SECRET, v); } catch (e) {} }
  // Authorization Code + PKCE flow — works for restricted scopes (Gmail), returns a refresh token.
  var GMAIL_ENABLED = true;
  var SCOPES = GMAIL_ENABLED
    ? "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar"
    : "https://www.googleapis.com/auth/calendar";
  var MAIL_QUERY = "is:unread in:inbox -category:promotions -category:social";
  var TASK_CAL_NAME = "タスク管理";
  var R_CAL_NAME = "R";
  var TZ = "Asia/Tokyo";
  var DOW = ["日", "月", "火", "水", "木", "金", "土"];
  var LS_LINE = "cockpit_line_v1";

  var $ = function (id) { return document.getElementById(id); };
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function fmtTime(d) { return pad(d.getHours()) + ":" + pad(d.getMinutes()); }
  function todayStr() { var d = new Date(); return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function isoDate(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function nextDayStr(s) { var d = new Date(s + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + 1); return d.toISOString().slice(0, 10); }
  function fmtDueShort(s) { var p = (s || "").split("-"); return p.length === 3 ? (Number(p[1]) + "/" + Number(p[2])) : ""; }
  function addOneHour(hhmm) { var p = (hhmm || "").split(":"); var h = (Number(p[0]) + 1) % 24; return pad(h) + ":" + (p[1] || "00"); }
  function todayBounds() { var s = new Date(); s.setHours(0, 0, 0, 0); var e = new Date(s); e.setDate(e.getDate() + 1); return { startTime: s.toISOString(), endTime: e.toISOString(), key: s.toDateString() }; }
  function wideWindow() { var s = new Date(); s.setHours(0, 0, 0, 0); s.setDate(s.getDate() - 31); var e = new Date(); e.setHours(0, 0, 0, 0); e.setDate(e.getDate() + 366); return { start: s.toISOString(), end: e.toISOString() }; }
  function humanGap(ms) { var m = Math.round(ms / 60000); if (m < 1) return "まもなく"; if (m < 60) return "あと" + m + "分"; var h = Math.floor(m / 60), mm = m % 60; return "あと" + h + "時間" + mm + "分"; }
  function shortGap(ms) { var m = Math.round(ms / 60000); if (m < 1) return "まもなく"; if (m < 60) return m + "分"; var h = Math.floor(m / 60), mm = m % 60; return h + "時間" + mm + "分"; }
  function senderName(s) { if (!s) return ""; var m = /^\s*"?([^"<]+?)"?\s*</.exec(s); if (m) return m[1].trim(); var at = s.indexOf("@"); return at > 0 ? s.slice(0, at) : s; }

  // ---------- state ----------
  var calEvents = {}, calStatus = {}, calNames = {};
  var displayCals = [], taskCalId = "", rCalId = "";
  var mailItems = null, mailStatus = "load", mailTotal = 0;
  var calTasks = [];        // tasks derived from タスク管理 calendar (all-day)
  var lineItems = lsLineLoad(); // LINE返信 (per-device)
  var kindSel = "task";
  var heroEv = null;
  var dayKey = todayBounds().key;

  function lsLineLoad() { try { return JSON.parse(localStorage.getItem(LS_LINE) || "[]"); } catch (e) { return []; } }
  function lsLineSave() { try { localStorage.setItem(LS_LINE, JSON.stringify(lineItems)); } catch (e) {} }

  // ---------- auth (OAuth 2.0 Authorization Code + PKCE, full-page redirect — no library, iOS-safe) ----------
  var AUTH_EP = "https://accounts.google.com/o/oauth2/v2/auth";
  var TOKEN_EP = "https://oauth2.googleapis.com/token";
  var LS_TOK = "cockpit_tok_v2";
  var PKCE_KEY = "cockpit_pkce";
  var accessToken = null, tokenExpiry = 0, refreshToken = null, authed = false, pendingErr = "";

  function redirectUri() {
    var p = location.pathname.replace(/index\.html$/, "");
    if (p.charAt(p.length - 1) !== "/") p += "/";
    return location.origin + p; // e.g. https://33rrr33.github.io/apps/cockpit/
  }
  function saveTok() { try { localStorage.setItem(LS_TOK, JSON.stringify({ t: accessToken, e: tokenExpiry, r: refreshToken })); } catch (e) {} }
  function loadTok() {
    try {
      var o = JSON.parse(localStorage.getItem(LS_TOK) || "null");
      if (o) {
        if (o.r) refreshToken = o.r;
        if (o.t && o.e && Date.now() < o.e) { accessToken = o.t; tokenExpiry = o.e; return true; }
      }
    } catch (e) {}
    return false;
  }
  function clearTok() { accessToken = null; tokenExpiry = 0; refreshToken = null; authed = false; try { localStorage.removeItem(LS_TOK); } catch (e) {} }
  function resetAuthBtn() { var b = $("authBtn"); if (b) b.textContent = "Googleと接続"; }
  function storeTokens(d) {
    if (d.access_token) { accessToken = d.access_token; tokenExpiry = Date.now() + (Number(d.expires_in || 3600) * 1000) - 60000; }
    if (d.refresh_token) refreshToken = d.refresh_token;
    saveTok();
  }

  function errMsg(code) {
    if (!code) return "";
    if (code === "access_denied") return "アクセスが許可されませんでした。警告画面では小さい「続行」を押してください（青い「安全なページに戻る」は押さない）。";
    if (code === "redirect_uri_mismatch") return "リダイレクトURI未登録です。Cloud Console でこのページのURLを承認済みリダイレクトURIに追加してください。";
    if (code === "admin_policy_enforced") return "組織のポリシーで許可されていません。個人のGoogleアカウントでお試しください。";
    return "接続できませんでした（" + code + "）。もう一度お試しください。";
  }

  // ---- PKCE helpers ----
  function b64url(bytes) {
    var s = btoa(String.fromCharCode.apply(null, new Uint8Array(bytes)));
    return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function randVerifier() { var a = new Uint8Array(48); crypto.getRandomValues(a); return b64url(a); }
  function challengeOf(verifier) {
    return crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier)).then(function (d) { return b64url(d); });
  }

  // start the login: build PKCE, remember the verifier, then full-page redirect to Google (no popup)
  function connect() {
    if (!getSecret()) { resetAuthBtn(); showSecretPrompt(); return; }  // ask for the on-device secret first
    var verifier = randVerifier();
    try { sessionStorage.setItem(PKCE_KEY, verifier); } catch (e) {}
    challengeOf(verifier).then(function (chal) {
      var params = new URLSearchParams({
        client_id: CLIENT_ID,
        redirect_uri: redirectUri(),
        response_type: "code",
        scope: SCOPES,
        code_challenge: chal,
        code_challenge_method: "S256",
        access_type: "offline",
        include_granted_scopes: "true",
        prompt: "consent",
        state: "cockpit"
      });
      location.href = AUTH_EP + "?" + params.toString();
    }).catch(function () { resetAuthBtn(); showAuthGate("接続の準備に失敗しました。もう一度お試しください。"); });
  }

  // exchange the ?code=... returned by Google for tokens (browser→Google, CORS-enabled)
  function exchangeCode(code) {
    var verifier = "";
    try { verifier = sessionStorage.getItem(PKCE_KEY) || ""; } catch (e) {}
    var body = new URLSearchParams({
      grant_type: "authorization_code",
      code: code,
      client_id: CLIENT_ID,
      client_secret: getSecret(),
      redirect_uri: redirectUri(),
      code_verifier: verifier
    });
    return fetch(TOKEN_EP, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body.toString() })
      .then(function (r) { return r.json(); })
      .then(function (d) { try { sessionStorage.removeItem(PKCE_KEY); } catch (e) {} return d; });
  }
  // silently get a fresh access token from the stored refresh token (no user interaction)
  function doRefresh() {
    if (!refreshToken) return Promise.reject({ error: "no_refresh" });
    var body = new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken,
      client_id: CLIENT_ID,
      client_secret: getSecret()
    });
    return fetch(TOKEN_EP, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body.toString() })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d && d.access_token) { storeTokens(d); return accessToken; } throw d || {}; });
  }

  function ensureToken() {
    if (accessToken && Date.now() < tokenExpiry) return Promise.resolve(accessToken);
    return doRefresh().catch(function () {
      clearTok(); showAuthGate("接続の有効期限が切れました。もう一度「Googleと接続」を押してください。");
      return Promise.reject({ error: "reauth" });
    });
  }
  function gfetch(url, opts) {
    opts = opts || {};
    return ensureToken().then(function (tok) {
      var h = Object.assign({}, opts.headers, { Authorization: "Bearer " + tok });
      return fetch(url, Object.assign({}, opts, { headers: h }));
    }).then(function (r) {
      if (r.status === 401) {
        // token rejected mid-use: try one silent refresh, then retry the request
        return doRefresh().then(function (tok) {
          var h = Object.assign({}, opts.headers, { Authorization: "Bearer " + tok });
          return fetch(url, Object.assign({}, opts, { headers: h }));
        }).catch(function () { clearTok(); showAuthGate("接続の有効期限が切れました。もう一度「Googleと接続」を押してください。"); throw { status: 401 }; });
      }
      return r;
    }).then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw { status: r.status, body: t }; });
      if (r.status === 204) return null;
      return r.json();
    });
  }

  // ---------- auth gate UI ----------
  function ensureAuthGate() {
    var g = $("authGate");
    if (g) return g;
    g = document.createElement("div");
    g.id = "authGate"; g.className = "authgate"; g.hidden = true;
    g.innerHTML =
      '<div class="authcard">' +
      '<div class="authmark">🧭</div>' +
      '<div class="authttl">きょうの司令塔</div>' +
      '<div class="authsub">Gmail・Googleカレンダーとつないで、今日やることを一目で。</div>' +
      '<button class="authbtn" id="authBtn">Googleと接続</button>' +
      '<div class="authnote" id="authNote" hidden></div>' +
      '<div class="authsec" id="secretRow" hidden>' +
        '<div class="authseclbl">この端末で初回のみ：クライアントシークレット（GOCSPX-…）を貼り付け</div>' +
        '<input class="authsecin" id="secretInput" type="password" inputmode="text" autocomplete="off" placeholder="GOCSPX-…" />' +
        '<button class="authbtn sm" id="secretSave">保存して接続</button>' +
        '<div class="authsecnote">この値はこの端末の中だけに保存され、外部やコードには残りません。</div>' +
      '</div>' +
      "</div>";
    document.body.appendChild(g);
    $("authBtn").addEventListener("click", function () { $("authNote").hidden = true; $("authBtn").textContent = "接続中…"; connect(); });
    $("secretSave").addEventListener("click", function () {
      var v = ($("secretInput").value || "").trim();
      if (!/^GOCSPX-/.test(v)) { $("authNote").textContent = "「GOCSPX-」で始まる値を貼り付けてください。"; $("authNote").hidden = false; return; }
      setSecret(v); $("secretRow").hidden = true; $("authNote").hidden = true; $("authBtn").textContent = "接続中…"; connect();
    });
    return g;
  }
  function showSecretPrompt() { var g = ensureAuthGate(); g.hidden = false; $("secretRow").hidden = false; setSync("local"); var i = $("secretInput"); if (i) i.focus(); }
  function showAuthGate(msg) {
    var g = ensureAuthGate(); g.hidden = false;
    if (msg) { $("authNote").textContent = msg; $("authNote").hidden = false; }
    setSync("local");
  }
  function hideAuthGate() { var g = $("authGate"); if (g) g.hidden = true; }

  function setSync(state) {
    var c = $("syncChip"); if (!c) return; c.hidden = false;
    if (state === "db") { c.textContent = "☁ 連携中"; c.className = "chip-sync ok"; }
    else { c.textContent = "未接続"; c.className = "chip-sync local"; }
  }

  // ---------- header date ----------
  function renderHeader() {
    var now = new Date();
    $("dNum").textContent = (now.getMonth() + 1) + "月" + now.getDate() + "日";
    $("dDow").textContent = "(" + DOW[now.getDay()] + ")";
  }
  function touchStamp() { $("stamp").textContent = "更新 " + fmtTime(new Date()); }

  // ---------- calendar helpers ----------
  function evStart(e) { return e.start && (e.start.dateTime || e.start.date); }
  function isAllDay(e) { return !!(e.start && e.start.date && !e.start.dateTime); }
  function startMs(e) { return isAllDay(e) ? 0 : new Date(e.start.dateTime).getTime(); }
  function mergedEvents() {
    var all = [];
    Object.keys(calEvents).forEach(function (id) {
      (calEvents[id] || []).forEach(function (e) { if (e && e.status !== "cancelled" && evStart(e)) all.push(e); });
    });
    all.sort(function (a, b) { return startMs(a) - startMs(b); });
    return all;
  }

  // ---------- render: hero ----------
  function renderHero() {
    var hero = $("hero"), content = $("heroContent");
    heroEv = null;
    if (!authed) { hero.setAttribute("data-state", "ok"); content.innerHTML = '<div class="hero-empty"><span class="sub">接続待ち…</span></div>'; return; }
    var all = mergedEvents(), timed = all.filter(function (e) { return !isAllDay(e); }), now = Date.now();
    var ongoing = null, next = null;
    for (var i = 0; i < timed.length; i++) {
      var st = new Date(timed[i].start.dateTime).getTime();
      var en = timed[i].end && timed[i].end.dateTime ? new Date(timed[i].end.dateTime).getTime() : st + 3600000;
      if (st <= now && en > now) { ongoing = timed[i]; break; }
      if (st > now && !next) next = timed[i];
    }
    var ev = ongoing || next;
    if (!ev) {
      hero.setAttribute("data-state", "ok");
      var msg = all.length ? "この後の予定はありません" : "きょうの予定はありません";
      var sub = all.length ? "おつかれさま。やることに集中" : "予定なし。今日は身軽です";
      content.innerHTML = '<div class="hero-empty"><div><div class="big">' + msg + '</div><div class="sub">' + sub + "</div></div></div>";
      return;
    }
    heroEv = ev;
    var st2 = new Date(ev.start.dateTime).getTime(), state = "ok", cd = "";
    if (ongoing) { state = "now"; cd = "進行中"; }
    else { var gap = st2 - now; if (gap <= 15 * 60000) state = "imminent"; else if (gap <= 60 * 60000) state = "soon"; cd = humanGap(gap); }
    hero.setAttribute("data-state", state);
    var calName = (calNames[ev.__cal] && !ev.__primary) ? esc(calNames[ev.__cal]) : (ev.location ? esc(ev.location) : "");
    var calSpan = calName ? '<span class="hero-cal"> ・ ' + calName + "</span>" : "";
    var heroEnd = ev.end && ev.end.dateTime ? '<span class="hero-end">〜' + fmtTime(new Date(ev.end.dateTime)) + "</span>" : "";
    content.innerHTML =
      '<div class="hero-line">' +
      '<span class="hero-time">' + fmtTime(new Date(ev.start.dateTime)) + heroEnd + "</span>" +
      '<span class="hero-title">' + esc(ev.summary || "(タイトルなし)") + calSpan + "</span>" +
      '<span class="hero-cd">' + cd + "</span>" +
      "</div>";
  }

  // ---------- render: schedule + all-day chips ----------
  function renderSchedule() {
    var box = $("schedList"), cnt = $("schedCount"), chips = $("alldayChips");
    function clearChips() { chips.innerHTML = ""; chips.hidden = true; }
    if (!authed) { box.innerHTML = ""; clearChips(); cnt.textContent = ""; return; }
    var all = mergedEvents(), now = Date.now();
    if (!all.length) { box.innerHTML = ""; clearChips(); cnt.textContent = ""; return; }
    var upcoming = all.filter(function (e) {
      if (isAllDay(e)) return true;
      var en = e.end && e.end.dateTime ? new Date(e.end.dateTime).getTime() : startMs(e) + 3600000;
      return en > now;
    });
    cnt.innerHTML = "残り <b>" + upcoming.filter(function (e) { return !isAllDay(e); }).length + "</b> 件";
    var pool = (upcoming.length ? upcoming : all).filter(function (e) { return e !== heroEv; });
    var timed = pool.filter(function (e) { return !isAllDay(e); });
    var allday = pool.filter(function (e) { return isAllDay(e); });
    if (allday.length) {
      chips.hidden = false;
      var CMAX = 2, cShow = allday.length > CMAX ? allday.slice(0, CMAX - 1) : allday.slice(0, CMAX);
      var chtml = cShow.map(function (e) { return '<span class="ac-chip">' + esc(e.summary || "(予定)") + "</span>"; }).join("");
      if (allday.length > CMAX) chtml += '<span class="ac-chip more">+' + (allday.length - (CMAX - 1)) + "</span>";
      chips.innerHTML = chtml;
    } else clearChips();
    if (!timed.length) { box.innerHTML = ""; return; }
    box.innerHTML = timed.map(function (e) {
      var st = new Date(e.start.dateTime).getTime(), gap = st - now, u = "ok";
      if (gap <= 15 * 60000) u = "imminent"; else if (gap <= 60 * 60000) u = "soon";
      var end = e.end && e.end.dateTime ? '<span class="ev-end">〜' + fmtTime(new Date(e.end.dateTime)) + "</span>" : "";
      return '<div class="ev-row" data-state="' + u + '">' +
        '<span class="ev-time">' + fmtTime(new Date(e.start.dateTime)) + end + "</span>" +
        '<span class="ev-title">' + esc(e.summary || "(タイトルなし)") + "</span>" +
        '<span class="ev-cd">' + shortGap(gap) + "</span></div>";
    }).join("");
  }

  // ---------- render: mail ----------
  function renderMail() {
    var box = $("mailList"), cnt = $("mailCount");
    if (!authed) { box.innerHTML = ""; cnt.textContent = ""; return; }
    if (!GMAIL_ENABLED) {
      cnt.textContent = "";
      box.innerHTML = '<a class="row mailrow" href="https://mail.google.com/mail/u/0/#inbox" target="_blank" rel="noopener">' +
        '<span class="dot"></span>' +
        '<div class="r-body"><div class="r-title">Gmail を開く</div><div class="r-from">未読メールを確認する →</div></div>' +
        '<span class="chev"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg></span></a>';
      return;
    }
    if (mailStatus === "load" && !mailItems) { box.innerHTML = '<div class="skl">読み込み中…</div>'; return; }
    if (mailStatus !== "ok") { box.innerHTML = '<div class="note">メールを読み込めませんでした</div>'; cnt.textContent = ""; return; }
    var items = (mailItems || []).slice();
    if (!items.length) { box.innerHTML = '<div class="empty">未読なし。受信箱スッキリ ✓</div>'; cnt.innerHTML = ""; return; }
    items.sort(function (a, b) { if (a.important !== b.important) return a.important ? -1 : 1; return b.date - a.date; });
    var imp = items.filter(function (i) { return i.important; }).length;
    cnt.innerHTML = "<b>" + (mailTotal || items.length) + "</b> 件" + (imp ? " ・ 重要" + imp : "");
    var show = items.slice(0, 3);
    var html = show.map(function (i) {
      var href = "https://mail.google.com/mail/u/0/#inbox/" + encodeURIComponent(i.id);
      return '<a class="row mailrow ' + (i.important ? "important" : "") + '" href="' + href + '" target="_blank" rel="noopener">' +
        '<span class="dot"></span>' +
        '<div class="r-body"><div class="r-title">' + esc(i.subject) + "</div><div class=\"r-from\">" + esc(i.from) + "</div></div>" +
        '<span class="chev"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg></span></a>';
    }).join("");
    if (items.length > 3) html += '<a class="note" href="https://mail.google.com/mail/u/0/#inbox" target="_blank" rel="noopener">ほか ' + (items.length - 3) + " 件をGmailで見る →</a>";
    box.innerHTML = html;
  }

  // On phones, open the Gmail app instead of the (slow) mobile web. Falls back to web if the app
  // isn't installed. Desktop keeps the normal new-tab web link.
  function isMobile() {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  }
  function openGmailApp() {
    var web = "https://mail.google.com/mail/u/0/#inbox";
    var done = false;
    var fallback = setTimeout(function () { if (!done) window.location.href = web; }, 1200);
    function cancel() { done = true; clearTimeout(fallback); }
    window.addEventListener("pagehide", cancel, { once: true });
    document.addEventListener("visibilitychange", function vh() { if (document.hidden) { cancel(); document.removeEventListener("visibilitychange", vh); } });
    try { window.location.href = "googlegmail://"; } catch (e) { clearTimeout(fallback); window.location.href = web; }
  }
  $("mailList").addEventListener("click", function (e) {
    if (!e.target.closest("a")) return;
    if (isMobile()) { e.preventDefault(); openGmailApp(); }  // let desktop open the web link normally
  });

  // ---------- render: tasks (calTasks + lineItems) ----------
  function allTasks() {
    var arr = [];
    calTasks.forEach(function (t) { arr.push(t); });
    lineItems.forEach(function (t) { arr.push({ id: t.id, title: t.title, kind: "line", due: "", createdAt: t.createdAt || 0, local: true }); });
    return arr;
  }
  function dueKey(t) { return t.due || "9999-99-99"; }
  function sortTasks(a) { return a.slice().sort(function (x, y) { var dx = dueKey(x), dy = dueKey(y); if (dx !== dy) return dx < dy ? -1 : 1; return (x.createdAt || 0) - (y.createdAt || 0); }); }
  function renderTasks() {
    var box = $("taskList"), cnt = $("taskCount");
    var TODAY = todayStr();
    var list = allTasks();
    var over = list.filter(function (t) { return t.kind === "task" && t.due && t.due < TODAY; }).length;
    cnt.innerHTML = "残り <b>" + list.length + "</b> 件" + (over ? ' <span class="cnt-over">繰越 ' + over + "</span>" : "");
    if (!list.length) { box.innerHTML = '<div class="empty">下のボタンから追加<br>頭の中を空っぽにしよう</div>'; return; }
    function row(t) {
      var isOver = t.kind === "task" && t.due && t.due < TODAY;
      var dueBadge = t.due ? '<span class="t-due">' + fmtDueShort(t.due) + "</span>" : "";
      return '<div class="task ' + (isOver ? "overdue" : "") + '" data-id="' + esc(t.id) + '" data-kind="' + t.kind + '">' +
        '<button class="check" data-act="toggle" aria-label="完了"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5 9 17.5 20 6.5"/></svg></button>' +
        '<div class="t-body"><span class="t-title">' + esc(t.title) + "</span></div>" + dueBadge +
        '<button class="del" data-act="del" aria-label="削除">×</button></div>';
    }
    var groups = [
      { key: "task", label: "タスク", items: sortTasks(list.filter(function (t) { return t.kind !== "line"; })) },
      { key: "line", label: "LINE返信", items: sortTasks(list.filter(function (t) { return t.kind === "line"; })) }
    ];
    box.innerHTML = groups.map(function (g) {
      var body = g.items.length ? g.items.map(row).join("") : '<div class="grp-none">なし</div>';
      return '<div class="grp-col"><div class="grp-head ' + g.key + '">' + g.label + ' <span class="grp-n">' + g.items.length + "</span></div>" + body + "</div>";
    }).join("");
  }

  // ---------- calendar writes ----------
  function gcalCreate(calId, opts) {
    var body = { summary: opts.summary };
    if (opts.allDay) { body.start = { date: opts.date }; body.end = { date: nextDayStr(opts.endDate || opts.date) }; }
    else { body.start = { dateTime: opts.date + "T" + opts.start + ":00+09:00", timeZone: TZ }; body.end = { dateTime: opts.date + "T" + opts.end + ":00+09:00", timeZone: TZ }; }
    return gfetch("https://www.googleapis.com/calendar/v3/calendars/" + encodeURIComponent(calId) + "/events", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }
  function gcalDelete(calId, eventId) {
    return gfetch("https://www.googleapis.com/calendar/v3/calendars/" + encodeURIComponent(calId) + "/events/" + encodeURIComponent(eventId), { method: "DELETE" });
  }

  // ---------- loaders ----------
  function loadCalendars() {
    return gfetch("https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=250").then(function (d) {
      var items = (d && d.items) || [];
      taskCalId = ""; rCalId = ""; displayCals = []; calNames = {};
      items.forEach(function (c) {
        var name = (c.summary || "").trim();
        calNames[c.id] = name;
        if (name === TASK_CAL_NAME) { taskCalId = c.id; return; }        // tasks calendar: not displayed
        if (name === R_CAL_NAME) rCalId = c.id;
        if (/#holiday@/.test(c.id)) return;                               // skip holidays from schedule
        displayCals.push({ id: c.id, summary: name, primary: c.primary === true });
      });
      if (!displayCals.length) displayCals.push({ id: "primary", summary: "", primary: true });
    });
  }
  function loadSchedule() {
    var b = todayBounds();
    return Promise.all(displayCals.map(function (c) {
      var u = "https://www.googleapis.com/calendar/v3/calendars/" + encodeURIComponent(c.id) +
        "/events?singleEvents=true&orderBy=startTime&maxResults=50&timeMin=" + encodeURIComponent(b.startTime) + "&timeMax=" + encodeURIComponent(b.endTime);
      return gfetch(u).then(function (d) {
        var evs = (d && d.items) || [];
        evs.forEach(function (e) { e.__cal = c.id; e.__primary = c.primary; });
        calEvents[c.id] = evs; calStatus[c.id] = "ok";
      }).catch(function () { calEvents[c.id] = []; calStatus[c.id] = "err"; });
    })).then(function () { touchStamp(); renderHero(); renderSchedule(); });
  }
  function loadTasks() {
    if (!taskCalId) { calTasks = []; renderTasks(); return Promise.resolve(); }
    var w = wideWindow();
    var u = "https://www.googleapis.com/calendar/v3/calendars/" + encodeURIComponent(taskCalId) +
      "/events?singleEvents=true&orderBy=startTime&maxResults=250&timeMin=" + encodeURIComponent(w.start) + "&timeMax=" + encodeURIComponent(w.end);
    return gfetch(u).then(function (d) {
      var items = (d && d.items) || [];
      calTasks = items.filter(function (e) { return e.status !== "cancelled" && e.start; }).map(function (e) {
        var day = e.start.date || (e.start.dateTime || "").slice(0, 10);
        return { id: e.id, title: e.summary || "(タスク)", kind: "task", due: day, calId: taskCalId, eventId: e.id, createdAt: new Date(e.created || Date.now()).getTime() };
      });
      renderTasks();
    }).catch(function () { renderTasks(); });
  }
  function loadMail() {
    if (!GMAIL_ENABLED) { renderMail(); return Promise.resolve(); }
    var u = "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=20&q=" + encodeURIComponent(MAIL_QUERY);
    return gfetch(u).then(function (d) {
      var msgs = (d && d.messages) || []; mailTotal = (d && d.resultSizeEstimate) || msgs.length;
      var top = msgs.slice(0, 8);
      return Promise.all(top.map(function (m) {
        return gfetch("https://gmail.googleapis.com/gmail/v1/users/me/messages/" + m.id + "?format=metadata&metadataHeaders=Subject&metadataHeaders=From")
          .catch(function () { return null; });
      }));
    }).then(function (arr) {
      mailItems = (arr || []).filter(Boolean).map(function (mm) {
        var h = {}; ((mm.payload && mm.payload.headers) || []).forEach(function (x) { h[x.name] = x.value; });
        return { id: mm.threadId || mm.id, subject: h.Subject || "(件名なし)", from: senderName(h.From || ""), date: Number(mm.internalDate) || 0, important: (mm.labelIds || []).indexOf("IMPORTANT") >= 0 };
      });
      mailStatus = "ok"; touchStamp(); renderMail();
    }).catch(function (e) { mailStatus = "err"; renderMail(); });
  }
  var loading = false;
  function loadAll() {
    if (!authed || loading) return; loading = true;
    loadCalendars().then(function () {
      return Promise.all([loadSchedule(), loadTasks(), loadMail()]);
    }).catch(function () {}).then(function () { loading = false; });
  }
  function refreshLive() { if (authed) { loadSchedule(); loadTasks(); loadMail(); } }

  // ---------- task interactions ----------
  $("taskList").addEventListener("click", function (e) {
    var btn = e.target.closest("[data-act]"); if (!btn) return;
    var rowEl = e.target.closest(".task"); if (!rowEl) return;
    var id = rowEl.getAttribute("data-id"), kind = rowEl.getAttribute("data-kind");
    // both 完了 and 削除 remove the item (task → delete calendar event; LINE → remove local)
    if (kind === "line") { lineItems = lineItems.filter(function (x) { return x.id !== id; }); lsLineSave(); renderTasks(); return; }
    var t = calTasks.filter(function (x) { return x.id === id; })[0];
    calTasks = calTasks.filter(function (x) { return x.id !== id; }); renderTasks();
    if (t && t.eventId) { gcalDelete(t.calId, t.eventId).then(function () { loadTasks(); }).catch(function () { loadTasks(); }); }
  });

  // ---------- add popup ----------
  function setTmKind(k) {
    kindSel = k;
    $("tmKindTask").setAttribute("aria-pressed", k === "task" ? "true" : "false");
    $("tmKindLine").setAttribute("aria-pressed", k === "line" ? "true" : "false");
    $("tmDateWrap").hidden = (k === "line");
    $("tmTitle").placeholder = k === "line" ? "例：田中さんに日程を返信" : "例：連絡プリント作成";
  }
  function openAddModal(kind) {
    setTmKind(kind === "line" ? "line" : "task");
    $("tmTitle").value = ""; $("tmDate").value = todayStr(); $("tmStart").value = ""; $("tmEnd").value = "";
    $("tmNote").hidden = true; $("tmAdded").hidden = true; $("tmSave").disabled = false; $("tmSave").textContent = "追加";
    $("taskModal").hidden = false; $("tmTitle").focus();
  }
  function closeAddModal() { $("taskModal").hidden = true; }
  var addedTimer = null;
  function afterAdd() { $("tmAdded").hidden = false; if (addedTimer) clearTimeout(addedTimer); addedTimer = setTimeout(function () { $("tmAdded").hidden = true; }, 1600); $("tmTitle").value = ""; $("tmStart").value = ""; $("tmEnd").value = ""; $("tmTitle").focus(); }
  function saveFromModal() {
    var title = ($("tmTitle").value || "").trim(); var note = $("tmNote");
    if (!title) { note.textContent = "内容を入力してください。"; note.hidden = false; return; }
    note.hidden = true;
    if (kindSel === "line") {
      lineItems.push({ id: "l" + Date.now() + Math.random().toString(36).slice(2, 6), title: title, createdAt: Date.now() });
      lsLineSave(); renderTasks(); afterAdd(); return;
    }
    if (!authed) { note.textContent = "先にGoogleと接続してください。"; note.hidden = false; return; }
    var date = $("tmDate").value || "", start = $("tmStart").value || "", end = $("tmEnd").value || "";
    if (!date) { note.textContent = "日付を選んでください。"; note.hidden = false; return; }
    $("tmSave").disabled = true; $("tmSave").textContent = "追加中…";
    var done = function () { $("tmSave").disabled = false; $("tmSave").textContent = "追加"; };
    if (start) {
      var rCal = rCalId || taskCalId;
      if (!rCal) { done(); note.textContent = "「R」カレンダーが見つかりません。"; note.hidden = false; return; }
      gcalCreate(rCal, { summary: title, allDay: false, date: date, start: start, end: (end && end > start) ? end : addOneHour(start) })
        .then(function () { done(); afterAdd(); setTimeout(loadSchedule, 400); })
        .catch(function () { done(); note.textContent = "追加できませんでした。"; note.hidden = false; });
    } else {
      if (!taskCalId) { done(); note.textContent = "「タスク管理」カレンダーが見つかりません。"; note.hidden = false; return; }
      gcalCreate(taskCalId, { summary: title, allDay: true, date: date, endDate: date })
        .then(function () { done(); afterAdd(); setTimeout(loadTasks, 400); })
        .catch(function () { done(); note.textContent = "追加できませんでした。"; note.hidden = false; });
    }
  }
  $("openTaskBtn").addEventListener("click", function () { openAddModal("task"); });
  $("openLineBtn").addEventListener("click", function () { openAddModal("line"); });
  $("tmCancel").addEventListener("click", closeAddModal);
  $("taskModal").addEventListener("click", function (e) { if (e.target === $("taskModal")) closeAddModal(); });
  $("tmKindTask").addEventListener("click", function () { setTmKind("task"); $("tmTitle").focus(); });
  $("tmKindLine").addEventListener("click", function () { setTmKind("line"); $("tmTitle").focus(); });
  $("tmSave").addEventListener("click", saveFromModal);
  $("tmTitle").addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); saveFromModal(); } });

  // ---------- add-event modal (＋予定 → primary calendar) ----------
  function openEvtModal() {
    $("evtTitle").value = ""; $("evtDate").value = todayStr(); $("evtAllday").checked = false; $("evtTimeRow").hidden = false;
    $("evtStart").value = "09:00"; $("evtEnd").value = "10:00"; $("evtNote").hidden = true; $("evtSave").disabled = false; $("evtSave").textContent = "カレンダーに追加";
    $("evtModal").hidden = false; $("evtTitle").focus();
  }
  function closeEvtModal() { $("evtModal").hidden = true; }
  $("addEventBtn").addEventListener("click", function () { if (!authed) { showAuthGate(""); return; } openEvtModal(); });
  $("evtCancel").addEventListener("click", closeEvtModal);
  $("evtModal").addEventListener("click", function (e) { if (e.target === $("evtModal")) closeEvtModal(); });
  $("evtAllday").addEventListener("change", function () { $("evtTimeRow").hidden = $("evtAllday").checked; });
  $("evtSave").addEventListener("click", function () {
    var title = ($("evtTitle").value || "").trim(), date = $("evtDate").value, note = $("evtNote");
    if (!title) { note.textContent = "タイトルを入力してください。"; note.hidden = false; return; }
    if (!date) { note.textContent = "日付を選んでください。"; note.hidden = false; return; }
    var allDay = $("evtAllday").checked, opts = { summary: title, allDay: allDay, date: date, endDate: date };
    if (!allDay) { opts.start = $("evtStart").value || "09:00"; opts.end = $("evtEnd").value || opts.start; }
    note.hidden = true; $("evtSave").disabled = true; $("evtSave").textContent = "追加中…";
    gcalCreate("primary", opts).then(function () {
      $("evtSave").disabled = false; $("evtSave").textContent = "カレンダーに追加"; closeEvtModal(); setTimeout(loadSchedule, 400);
    }).catch(function () { $("evtSave").disabled = false; $("evtSave").textContent = "カレンダーに追加"; note.textContent = "追加できませんでした。"; note.hidden = false; });
  });

  // ---------- clock + auto refresh ----------
  setInterval(function () {
    renderHeader();
    var k = todayBounds().key;
    if (k !== dayKey) { dayKey = k; refreshLive(); }
    renderHero(); renderSchedule();
  }, 30000);
  setInterval(refreshLive, 90000);
  document.addEventListener("visibilitychange", function () { if (!document.hidden && authed) refreshLive(); });

  // ---------- boot ----------
  renderHeader(); renderHero(); renderSchedule(); renderMail(); renderTasks();
  ensureAuthGate();

  // did we just come back from Google with an authorization code (or error) in the query string?
  var qp = new URLSearchParams(location.search || "");
  var retCode = qp.get("code"), retErr = qp.get("error");
  if (retCode || retErr) { try { history.replaceState(null, "", location.pathname); } catch (e) {} }

  if (retCode) {
    var b = $("authBtn"); if (b) b.textContent = "接続中…";
    exchangeCode(retCode).then(function (d) {
      if (d && d.access_token) { storeTokens(d); authed = true; hideAuthGate(); setSync("db"); loadAll(); }
      else { resetAuthBtn(); showAuthGate("トークン取得に失敗しました（" + ((d && (d.error_description || d.error)) || "error") + "）。もう一度お試しください。"); }
    }).catch(function () { resetAuthBtn(); showAuthGate("トークン取得に失敗しました。通信環境を確認して、もう一度お試しください。"); });
  } else if (retErr) {
    showAuthGate(errMsg(retErr));
  } else if (loadTok()) {
    authed = true; hideAuthGate(); setSync("db"); loadAll();          // valid saved access token
  } else if (refreshToken) {
    // access token expired but we have a refresh token — renew silently, no re-login
    doRefresh().then(function () { authed = true; hideAuthGate(); setSync("db"); loadAll(); })
      .catch(function () { showAuthGate(""); });
  } else {
    showAuthGate("");
  }
})();
