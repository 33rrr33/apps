/**
 * しゃべって予定帳 × Google（カレンダー・Gmail・ウィジェット・Apple Watch）連携
 *
 * 使い方（くわしくはアプリの ⚙︎ →「Googleカレンダー・Gmail」）
 *  1. script.google.com で新しいプロジェクトを作り、このコードを全部貼り付けて保存
 *  2. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *     次のユーザーとして実行：自分 / アクセスできるユーザー：全員
 *  3. 出てきた「ウェブアプリのURL」をアプリに貼る
 *
 * このコードはあなたのGoogleアカウントの中だけで動きます。
 * 下の合言葉を知っている人（＝あなたのアプリ・ウィジェット・ショートカット）しか使えません。
 */
const TOKEN = '__TOKEN__';
const VERSION = 2;

/* ===== 入口 ===== */
function doGet(e) {
  const p = (e && e.parameter) || {};
  if (!p.token) return out({ ok: true, app: 'yotei', version: VERSION, msg: '予定帳のGoogle連携は動いています' });
  if (p.token !== TOKEN) return p.action === 'addText' ? text('合言葉がちがいます') : out({ ok: false, error: '合言葉がちがいます' });
  try {
    if (p.action === 'widget') return out(widgetData());
    if (p.action === 'addText') return text(addText(p.text || ''));
    return out({ ok: false, error: 'unknown action' });
  } catch (err) {
    return p.action === 'addText' ? text('うまくいきませんでした：' + errMsg(err)) : out({ ok: false, error: errMsg(err) });
  }
}

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out({ ok: false, error: 'bad request' }); }
  if (!req || req.token !== TOKEN) return out({ ok: false, error: '合言葉がちがいます' });
  try {
    switch (req.action) {
      case 'ping':
        return out({ ok: true, version: VERSION, calendar: cal().getName(), ai: !!prop('ai_key') });
      case 'upsertEvents':
        return out({ ok: true, results: (req.events || []).map(upsert) });
      case 'deleteEvent': {
        const ev = findEv(req.gcalId);
        if (ev) ev.deleteEvent();
        return out({ ok: true });
      }
      case 'listEvents':
        return out({ ok: true, events: listEvents(req.from, req.to) });
      case 'searchMail':
        return out({ ok: true, mails: searchMail(req.query, req.max) });
      case 'syncItems':
        return out(Object.assign({ ok: true }, syncItems(req.items || [], req.tombs || {})));
      case 'setAiKey': {
        const pr = PropertiesService.getScriptProperties();
        pr.setProperty('ai_key', String(req.key || ''));
        pr.setProperty('ai_model', String(req.model || ''));
        pr.setProperty('lead', String(req.lead || 10));
        return out({ ok: true });
      }
      case 'addText':
        return out({ ok: true, message: addText(req.text || '') });
      default:
        return out({ ok: false, error: 'unknown action' });
    }
  } catch (err) {
    return out({ ok: false, error: errMsg(err) });
  }
}

/* ===== 小物 ===== */
function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function text(s) { return ContentService.createTextOutput(String(s)).setMimeType(ContentService.MimeType.TEXT); }
function errMsg(err) { return String((err && err.message) || err); }
function prop(k) { return PropertiesService.getScriptProperties().getProperty(k) || ''; }
function cal() { return CalendarApp.getDefaultCalendar(); }
function tz() { return cal().getTimeZone() || Session.getScriptTimeZone(); }
function findEv(id) {
  if (!id) return null;
  try { return cal().getEventById(id); } catch (e) { return null; }
}
function dayOf(ymd) { return Utilities.parseDate(ymd + ' 12:00', tz(), 'yyyy-MM-dd HH:mm'); }
function ymdOf(d) { return Utilities.formatDate(d, tz(), 'yyyy-MM-dd'); }
function addDaysYmd(ymd, n) { const d = dayOf(ymd); d.setDate(d.getDate() + n); return ymdOf(d); }
function epochOf(ymd, hm) { return Utilities.parseDate(ymd + ' ' + hm, tz(), 'yyyy-MM-dd HH:mm').getTime(); }
function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

/* ===== カレンダー ===== */
// 予定を入れる（gcalId があれば書きかえる）
function upsert(x) {
  try {
    const allDay = !x.start;
    let ev = findEv(x.gcalId);
    if (ev && ev.isRecurringEvent()) ev = null; // くり返し予定はさわらない
    if (ev) {
      ev.setTitle(x.title);
      ev.setDescription(x.description || '');
      ev.setLocation(x.location || '');
      if (allDay) ev.setAllDayDate(dayOf(x.date));
      else ev.setTime(new Date(x.start), new Date(x.end));
    } else {
      const opt = { description: x.description || '', location: x.location || '' };
      ev = allDay
        ? cal().createAllDayEvent(x.title, dayOf(x.date), opt)
        : cal().createEvent(x.title, new Date(x.start), new Date(x.end), opt);
    }
    if (!allDay && x.remind != null) {
      ev.removeAllReminders();
      ev.addPopupReminder(Number(x.remind));
    }
    return { id: x.id, gcalId: ev.getId() };
  } catch (err) {
    return { id: x.id, error: errMsg(err) };
  }
}

// 期間内の予定を読む
function listEvents(from, to) {
  const start = Utilities.parseDate(from + ' 00:00', tz(), 'yyyy-MM-dd HH:mm');
  const end = Utilities.parseDate(to + ' 23:59', tz(), 'yyyy-MM-dd HH:mm');
  return cal().getEvents(start, end).map(function (ev) {
    const allDay = ev.isAllDayEvent();
    const s = allDay ? ev.getAllDayStartDate() : ev.getStartTime();
    return {
      gcalId: ev.getId(),
      title: ev.getTitle(),
      allDay: allDay,
      date: ymdOf(s),
      time: allDay ? '' : Utilities.formatDate(s, tz(), 'HH:mm'),
      dur: allDay ? 0 : Math.round((ev.getEndTime() - ev.getStartTime()) / 60000),
      recurring: ev.isRecurringEvent(),
      location: ev.getLocation() || '',
      description: (ev.getDescription() || '').slice(0, 300)
    };
  });
}

/* ===== Gmail ===== */
function searchMail(query, max) {
  const threads = GmailApp.search(query || 'newer_than:3d', 0, Math.min(Number(max) || 10, 20));
  return threads.map(function (th) {
    const msgs = th.getMessages();
    const m = msgs[msgs.length - 1];
    return {
      subject: m.getSubject(),
      from: m.getFrom(),
      date: Utilities.formatDate(m.getDate(), tz(), 'yyyy-MM-dd HH:mm'),
      body: (m.getPlainBody() || '').replace(/\n{3,}/g, '\n\n').slice(0, 2500)
    };
  });
}

/* ===== 予定帳のデータ（アプリ・Safari・ウィジェット・Watchで共有） ===== */
const CHUNK = 2000;
function loadStore() {
  const all = PropertiesService.getScriptProperties().getProperties();
  const n = Number(all.store_n || 0);
  let s = '';
  for (let i = 0; i < n; i++) s += all['store_' + i] || '';
  try { const o = s ? JSON.parse(s) : null; if (o && o.items) return o; } catch (e) {}
  return { items: [], tombs: {} };
}
function saveStore(st) {
  const pr = PropertiesService.getScriptProperties();
  const old = Number(pr.getProperty('store_n') || 0);
  const s = JSON.stringify(st);
  const n = Math.ceil(s.length / CHUNK);
  const obj = { store_n: String(n) };
  for (let i = 0; i < n; i++) obj['store_' + i] = s.slice(i * CHUNK, (i + 1) * CHUNK);
  pr.setProperties(obj, false);
  for (let i = n; i < old; i++) pr.deleteProperty('store_' + i);
}
// あたらしいほう（upd が大きいほう）を残す。消したもの（tombs）は消す
function mergeStore(st, items, tombs) {
  const now = Date.now(), map = {}, tb = Object.assign({}, st.tombs || {});
  Object.keys(tombs || {}).forEach(function (id) { tb[id] = Math.max(tb[id] || 0, Number(tombs[id]) || 0); });
  (st.items || []).concat(items || []).forEach(function (it) {
    if (!it || !it.id) return;
    const cur = map[it.id];
    if (!cur || (Number(it.upd) || 0) > (Number(cur.upd) || 0)) map[it.id] = it;
  });
  const out = [];
  Object.keys(map).forEach(function (id) {
    const it = map[id];
    if (tb[id] && tb[id] >= (Number(it.upd) || 0)) return;
    if (it.done && it.doneAt && now - it.doneAt > 14 * 864e5) return; // 2週間より前の「できた」は片づける
    out.push(it);
  });
  Object.keys(tb).forEach(function (id) { if (now - tb[id] > 30 * 864e5) delete tb[id]; });
  return { items: out, tombs: tb };
}
function syncItems(items, tombs) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const st = mergeStore(loadStore(), items, tombs);
    saveStore(st);
    return st;
  } finally { lock.releaseLock(); }
}

/* ===== ウィジェット用 ===== */
function evKey(gcalId, rec, date) { return rec ? gcalId + '@' + date : gcalId; }
function widgetData() {
  const st = loadStore();
  const from = ymdOf(new Date()), to = addDaysYmd(from, 2);
  const have = {};
  const items = st.items.filter(function (i) { return i.date && i.date >= from && i.date <= to; }).map(function (i) {
    if (i.gcalId) have[evKey(i.gcalId, i.gcalRec, i.date)] = 1;
    return { title: i.title, emoji: i.emoji || '', date: i.date, time: i.time || '', dur: i.dur || 30, done: !!i.done, location: i.location || '' };
  });
  listEvents(from, to).forEach(function (ev) {
    if (have[evKey(ev.gcalId, ev.recurring, ev.date)]) return;
    const m = ev.title.match(/^(\p{Extended_Pictographic}️?)\s*/u);
    items.push({ title: m ? ev.title.slice(m[0].length) : ev.title, emoji: m ? m[1] : '📅', date: ev.date, time: ev.time, dur: ev.dur || 30, done: false, location: ev.location });
  });
  const later = st.items.filter(function (i) { return !i.date && !i.done; }).length;
  const overdue = st.items.filter(function (i) { return i.date && i.date < from && !i.done && !i.gcalId; }).length;
  return { ok: true, version: VERSION, today: from, items: items, later: later, overdue: overdue };
}

/* ===== Apple Watch・Siri から話して入れる ===== */
function addText(t) {
  t = String(t || '').trim();
  if (!t) return '聞き取れませんでした。もう一度どうぞ';
  const key = prop('ai_key');
  if (!key) return 'AIの準備がまだです。予定帳の ⚙︎ →「Apple Watch・Siri」で準備してね';
  const res = gemini(key, prop('ai_model') || 'gemini-3.6-flash', buildPrompt() + '\n\n# 入力\n' + t);
  const lead = Number(prop('lead') || 10), now = Date.now(), today = ymdOf(new Date());
  const lines = [], newItems = [];
  (res.items || []).forEach(function (x) {
    const date = /^\d{4}-\d{2}-\d{2}$/.test(x.date || '') ? x.date : '';
    const time = /^\d{1,2}:\d{2}$/.test(x.time || '') ? ('0' + x.time).slice(-5) : '';
    const emoji = x.emoji || '🔹';
    if (x.kind === 'timer') { lines.push('⏱ タイマー（' + (x.duration_min || '') + '分）はiPhoneかWatchのタイマーでセットしてね'); return; }
    if (x.kind === 'alarm') {
      if (!time) return;
      let d = date || today;
      if (!date && epochOf(d, time) < now) d = addDaysYmd(d, 1);
      const s = epochOf(d, time);
      const ev = cal().createEvent('⏰ ' + (x.title || 'アラーム'), new Date(s), new Date(s + 60000), { description: '（しゃべって予定帳から）' });
      ev.removeAllReminders(); ev.addPopupReminder(0);
      lines.push('⏰ ' + label(d, time) + ' にお知らせします');
      return;
    }
    const it = {
      id: uid(), title: String(x.title || '').trim() || '（なまえなし）', emoji: emoji, date: date || null, time: time || null,
      dur: Math.max(5, Number(x.duration_min) || 30), steps: (x.steps || []).map(function (s) { return { t: s, done: false }; }),
      note: x.note || '', location: x.location || '', done: false, doneAt: null, created: now, upd: now,
      gcalId: null, gcalRec: false, src: 'watch'
    };
    if (date) {
      const desc = [];
      if (it.steps.length) desc.push('ステップ:\n' + it.steps.map(function (s) { return '・' + s.t; }).join('\n'));
      if (it.note) desc.push(it.note);
      desc.push('（しゃべって予定帳から）');
      const ev = { id: it.id, title: (emoji !== '🔹' ? emoji + ' ' : '') + it.title, date: date, description: desc.join('\n\n'), location: it.location };
      if (time) { ev.start = epochOf(date, time); ev.end = ev.start + it.dur * 60000; ev.remind = lead; }
      const r = upsert(ev);
      if (r.gcalId) it.gcalId = r.gcalId;
      lines.push('📅 ' + label(date, time) + ' ' + it.title);
    } else {
      lines.push('📥 あとで：' + it.title);
    }
    newItems.push(it);
  });
  if (newItems.length) syncItems(newItems, {});
  return lines.length ? '入れました！\n' + lines.join('\n') : '予定は見つかりませんでした';
}
function label(date, time) {
  const d = dayOf(date), w = '日月火水木金土'.charAt(d.getDay());
  return (d.getMonth() + 1) + '/' + d.getDate() + '(' + w + ')' + (time ? ' ' + time : '');
}
function buildPrompt() {
  const n = new Date(), wk = [];
  for (let i = 0; i < 21; i++) { const d = new Date(n.getTime() + i * 864e5); wk.push(ymdOf(d) + '(' + '日月火水木金土'.charAt(Number(Utilities.formatDate(d, tz(), 'u')) % 7) + ')'); }
  return [
    'あなたはADHDの人の予定管理を手伝う、正確でやさしい秘書です。',
    '下の入力は、Apple WatchやSiriに話した日本語のメモ（音声入力の誤変換をふくむことがあります）です。誤変換は文脈から読みかえ、言い直しは最後を正とします。',
    'その中から「予定」「やること」「アラーム」「タイマー」をすべて取り出して、JSONで返してください。',
    '# いまの日時', Utilities.formatDate(n, tz(), 'yyyy-MM-dd HH:mm'),
    '# カレンダー（曜日の計算はかならずこれを見ること）', wk.join(', '),
    '「来週◯曜」は、いまの週（月曜はじまり）の次の週の◯曜日。「◯曜」は今日以降でいちばん近い◯曜日。',
    '# kind: event=日時の決まった予定 / task=やること・しめ切り / alarm=「◯時に知らせて・アラーム」（time にその時刻） / timer=「◯分タイマー」（duration_min に分）',
    '# ルール',
    '- title は短く具体的に（15文字くらいまで）。日時や場所は title に入れない。emoji は1つ。',
    '- date は YYYY-MM-DD（わからなければ空文字）。しめ切りはその日を date にし、note の最初に「〆切」。',
    '- time は HH:MM（なければ空文字）。午前午後があいまいなら、ふつうの生活で自然なほう。',
    '- duration_min はかかりそうな分数（わからなければ30）。steps は取りかかりにくい用事だけ2〜5個に小分け。',
    '- location は場所、note は持ち物などの補足（なければ空文字）。transcript は入力の要点。'
  ].join('\n');
}
function gemini(key, model, promptText) {
  const schema = {
    type: 'object', properties: {
      transcript: { type: 'string' },
      items: { type: 'array', items: { type: 'object', properties: {
        kind: { type: 'string', enum: ['event', 'task', 'alarm', 'timer'] },
        title: { type: 'string' }, emoji: { type: 'string' }, date: { type: 'string' }, time: { type: 'string' },
        duration_min: { type: 'integer' }, steps: { type: 'array', items: { type: 'string' } },
        location: { type: 'string' }, note: { type: 'string' }
      }, required: ['kind', 'title', 'emoji', 'date', 'time', 'duration_min', 'steps', 'location', 'note'] } }
    }, required: ['transcript', 'items']
  };
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent?key=' + encodeURIComponent(key);
  const body = { contents: [{ parts: [{ text: promptText }] }], generationConfig: { temperature: 0.1, responseMimeType: 'application/json', responseSchema: schema } };
  let res;
  for (let i = 0; i < 3; i++) {
    res = UrlFetchApp.fetch(url, { method: 'post', contentType: 'application/json', payload: JSON.stringify(body), muteHttpExceptions: true });
    const c = res.getResponseCode();
    if (c === 200) break;
    if (c === 429 || c >= 500) { Utilities.sleep(2000 * (i + 1)); continue; }
    throw new Error('AIエラー ' + c);
  }
  if (res.getResponseCode() !== 200) throw new Error('AIが混んでいます。少ししてからもう一度');
  const j = JSON.parse(res.getContentText());
  const txt = j.candidates[0].content.parts.filter(function (p) { return !p.thought; }).map(function (p) { return p.text || ''; }).join('');
  return JSON.parse(txt.replace(/^```(?:json)?\s*|\s*```$/g, ''));
}
