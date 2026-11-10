// 予定帳ウィジェット（Scriptable 用）
// 使い方: 予定帳の「設定」→「ウィジェット」→「コードをコピー」
//         → Scriptable で新しいスクリプトを作り、全部はりつける（名前は「予定帳」）
//         → 一度 ▶ を押して、カレンダーとリマインダーへのアクセスを「許可」。
// ホーム画面（小・中・大）とロック画面（長方形・丸・1行）に対応。
//
// 出す予定：
//   ・予定帳の予定（予定帳の「ウィジェットに反映」ボタンで送ったもの）
//   ・iPhone のカレンダー（Googleアカウントを入れていれば Googleカレンダーも）
//   ・今日が期限のリマインダー
//   ・予定帳を Google とつないでいるときは、Google を通して予定帳の予定を自動で読みます

// ====== ここは予定帳が自動で入れます（さわらなくてOK） ======
const GAS_URL = "__GAS_URL__"
const TOKEN = "__TOKEN__"
// =========================================================

// 表示しないカレンダー（名前の一部でOK）
const HIDE_CALENDARS = ["祝日", "Holidays", "誕生日", "Birthdays"]
// iPhone のカレンダー・リマインダーも出す
const SHOW_CALENDAR = true
const SHOW_REMINDERS = true
// ウィジェットをタップしたときに開くURL
const OPEN_URL = "https://33rrr33.github.io/apps/yotei/"

/* ---------- 色（予定帳と同じ） ---------- */
const dyn = (l, d) => Color.dynamic(new Color(l), new Color(d))
const C = {
  bg: dyn("#F6F5F2", "#0C0C0D"),
  surface: dyn("#FFFFFF", "#17171A"),
  ink: dyn("#17171A", "#F2F2F3"),
  ink2: dyn("#5B5B63", "#A6A6AE"),
  mute: dyn("#9C9CA3", "#6E6E76"),
  line: dyn("#D9D7D2", "#3A3A40"),
  accent: dyn("#E2553B", "#FF6B4E"),
  ok: dyn("#1F9D6B", "#3CCB8F"),
  warn: dyn("#C27C0E", "#F0A63A"),
  hero: dyn("#17171A", "#F2F2F3"),
  heroInk: dyn("#F6F5F2", "#111113"),
  heroSub: dyn("#A5A5AC", "#5F5F67"),
}
const ACCENT = new Color("#E2553B")
const WD = "日月火水木金土"

/* ---------- 小物 ---------- */
const fm = FileManager.local()
const dir = fm.documentsDirectory()
const cachePath = fm.joinPath(dir, "yotei-widget-cache.json")
const appPath = fm.joinPath(dir, "yotei-app-items.json")
const USE_GAS = /^https:\/\//.test(GAS_URL)
function pad(n) { return (n < 10 ? "0" : "") + n }
function ymd(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) }
function hm(d) { return pad(d.getHours()) + ":" + pad(d.getMinutes()) }
function startOf(it) {
  if (!it.date || !it.time) return null
  const p = it.date.split("-"), t = it.time.split(":")
  return new Date(+p[0], +p[1] - 1, +p[2], +t[0], +t[1])
}
function sortT(a, b) {
  if (a.time && b.time) return a.time < b.time ? -1 : a.time > b.time ? 1 : 0
  if (a.time) return -1; if (b.time) return 1; return 0
}

/* ---------- 予定帳から「ウィジェットに反映」で送られてきたとき ---------- */
const q = (typeof args !== "undefined" && args.queryParameters) || {}
let justSaved = false
if (q.data) {
  try {
    const d = JSON.parse(q.data)
    fm.writeString(appPath, JSON.stringify(d))
    justSaved = true
  } catch (e) { /* 読めなければ何もしない */ }
}

/* ---------- データを集める ---------- */
async function loadCalendar() {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const end = new Date(start.getTime() + 3 * 864e5)
  const items = []
  let overdue = 0
  if (SHOW_CALENDAR) {
    let cals = await Calendar.forEvents()
    cals = cals.filter(c => !HIDE_CALENDARS.some(h => c.title.indexOf(h) >= 0))
    const evs = await CalendarEvent.between(start, end, cals)
    for (const e of evs) {
      if (e.isAllDay) {
        for (let d = new Date(Math.max(e.startDate, start)); d < e.endDate && d < end; d = new Date(d.getTime() + 864e5)) {
          items.push({ title: e.title, date: ymd(d), time: "", dur: 0, done: false, allDay: true, location: e.location || "" })
        }
      } else {
        items.push({ title: e.title, date: ymd(e.startDate), time: hm(e.startDate),
          dur: Math.max(1, Math.round((e.endDate - e.startDate) / 60000)), done: false, location: e.location || "" })
      }
    }
  }
  if (SHOW_REMINDERS) {
    try {
      const rs = await Reminder.allDueToday()
      for (const r of rs) {
        items.push({ title: r.title, date: ymd(now), time: r.dueDateIncludesTime && r.dueDate ? hm(r.dueDate) : "", dur: 15, done: r.isCompleted, location: "" })
      }
      overdue = (await Reminder.allIncomplete()).filter(r => r.dueDate && r.dueDate < start).length
    } catch (e) { /* リマインダーを許可していなければ出さない */ }
  }
  return { items, overdue }
}

async function loadGas() {
  try {
    const req = new Request(GAS_URL + "?action=widget&token=" + encodeURIComponent(TOKEN))
    req.timeoutInterval = 20
    const j = await req.loadJSON()
    if (!j.ok) throw new Error(j.error || "error")
    fm.writeString(cachePath, JSON.stringify(j))
    return j
  } catch (e) {
    if (fm.fileExists(cachePath)) { const j = JSON.parse(fm.readString(cachePath)); j.stale = true; return j }
    throw e
  }
}

function sameItem(a, b) { return a.title === b.title && a.date === b.date && (a.time || "") === (b.time || "") }

async function loadData() {
  let items = [], later = 0, overdue = 0, stale = false, err = ""
  if (USE_GAS) {
    try { const j = await loadGas(); items = j.items || []; later = j.later || 0; overdue = j.overdue || 0; stale = !!j.stale }
    catch (e) { err = String(e.message || e) }
  } else if (fm.fileExists(appPath)) {
    try {
      const a = JSON.parse(fm.readString(appPath))
      items = a.items || []
      later = a.later || 0; overdue = a.overdue || 0
    } catch (e) {}
  }
  try {
    const c = await loadCalendar()
    c.items.forEach(e => { if (!items.some(i => sameItem(i, e))) items.push(e) })
    overdue += c.overdue
  } catch (e) {
    if (!items.length && !USE_GAS) err = "Scriptable で一度 ▶ を押して、カレンダーへのアクセスを許可してください"
  }
  return { ok: !err || items.length > 0, error: err, items, later, overdue, stale }
}

/* ---------- いま・つぎ ---------- */
function pick(data) {
  const now = new Date(), t = ymd(now)
  const tom = ymd(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1))
  const all = data.items || []
  const today = all.filter(i => i.date === t).sort(sortT)
  const tomorrow = all.filter(i => i.date === tom && !i.done).sort(sortT)
  let cur = null, next = null
  for (const it of today) {
    if (it.done) continue
    const s = startOf(it); if (!s) continue
    const e = new Date(s.getTime() + (it.dur || 30) * 60000)
    if (s <= now && now < e && !cur) cur = { it, s, e }
    else if (s > now && !next) next = { it, s }
  }
  if (!next) {
    const tm = tomorrow.find(i => startOf(i))
    if (tm) next = { it: tm, s: startOf(tm), tomorrow: true }
  }
  const undone = today.filter(i => !i.done && !i.allDay)
  const done = today.filter(i => i.done).length
  return { now, today, tomorrow, cur, next, undone, done }
}

/* ---------- 部品 ---------- */
function T(stack, s, size, color, weight, lines) {
  const x = stack.addText(String(s))
  x.font = weight === "heavy" ? Font.heavySystemFont(size) : weight === "bold" ? Font.boldSystemFont(size)
    : weight === "semi" ? Font.semiboldSystemFont(size) : weight === "medium" ? Font.mediumSystemFont(size) : Font.systemFont(size)
  x.textColor = color
  x.lineLimit = lines || 1
  x.minimumScaleFactor = 0.6
  return x
}
function H(parent) { const s = parent.addStack(); s.layoutHorizontally(); s.centerAlignContent(); return s }
function V(parent) { const s = parent.addStack(); s.layoutVertically(); return s }
function dot(stack, color, size) {
  const d = stack.addStack(); d.size = new Size(size, size); d.cornerRadius = size / 2; d.backgroundColor = color
  return d
}
function bar(stack, width, p) {
  const h = 4, dc = new DrawContext()
  dc.size = new Size(width, h); dc.opaque = false; dc.respectScreenScale = true
  const track = new Path(); track.addRoundedRect(new Rect(0, 0, width, h), 2, 2)
  dc.setFillColor(new Color("#E2553B", 0.22)); dc.addPath(track); dc.fillPath()
  const fw = Math.max(h, Math.min(1, Math.max(0, p)) * width)
  const fill = new Path(); fill.addRoundedRect(new Rect(0, 0, fw, h), 2, 2)
  dc.setFillColor(ACCENT); dc.addPath(fill); dc.fillPath()
  const img = stack.addImage(dc.getImage()); img.imageSize = new Size(width, h)
  return img
}
function sym(stack, name, size, color) {
  const s = SFSymbol.named(name); s.applyFont(Font.systemFont(size))
  const img = stack.addImage(s.image); img.imageSize = new Size(size, size); img.tintColor = color
  return img
}
function countdown(stack, date, size, color) {
  // 「1時間8分」が自動で減っていく
  const d = stack.addDate(date); d.applyRelativeStyle()
  d.font = Font.heavySystemFont(size); d.textColor = color; d.lineLimit = 1; d.minimumScaleFactor = 0.5
  return d
}

/* いまのカード（アプリの黒いカードと同じ） */
function heroCard(parent, p, o) {
  const card = V(parent)
  card.backgroundColor = C.hero; card.cornerRadius = o.radius == null ? 18 : o.radius
  card.setPadding(o.pad, o.pad + 2, o.pad, o.pad + 2)
  if (o.width) card.size = new Size(o.width, 0)
  const big = o.big || 28, title = o.title || 17

  if (p.cur || p.next) {
    const isCur = !!p.cur, it = isCur ? p.cur.it : p.next.it
    const soon = !isCur && !p.next.tomorrow && (p.next.s - p.now) <= 15 * 60000
    const lab = H(card); lab.spacing = 5
    dot(lab, C.accent, 6)
    T(lab, isCur ? "いま" : soon ? "まもなく" : p.next.tomorrow ? "明日のはじめ" : "つぎ", 11, isCur || soon ? C.accent : C.heroSub, "semi")
    lab.addSpacer()
    T(lab, isCur ? (o.compact ? "〜" + hm(p.cur.e) : it.time + "–" + hm(p.cur.e)) : it.time + "から", 11, C.heroSub, "medium")
    card.addSpacer(o.compact ? 4 : 6)
    T(card, it.title, title, C.heroInk, "bold", 2)
    if (o.compact) {
      card.addSpacer()
      T(card, isCur ? "のこり" : "あと", 10, C.heroSub, "medium")
      countdown(card, isCur ? p.cur.e : p.next.s, big, C.heroInk)
    } else {
      card.addSpacer(6)
      const row = H(card); row.spacing = 4; row.bottomAlignContent()
      T(row, isCur ? "のこり" : "あと", 11, C.heroSub, "medium")
      countdown(row, isCur ? p.cur.e : p.next.s, big, C.heroInk)
    }
    if (isCur || (!p.next.tomorrow && (p.next.s - p.now) <= 120 * 60000)) {
      card.addSpacer(8)
      const prog = isCur ? 1 - (p.cur.e - p.now) / ((p.cur.it.dur || 30) * 60000) : 1 - (p.next.s - p.now) / (120 * 60000)
      bar(card, o.barW, prog)
    }
    if (!o.compact && it.location) {
      card.addSpacer(6)
      const m = H(card); m.spacing = 4
      sym(m, "mappin", 10, C.heroSub); T(m, it.location, 11, C.heroSub, "", 1)
    }
    if (o.showNext && isCur && p.next && !p.next.tomorrow) {
      card.addSpacer(8)
      const n = H(card); n.spacing = 6
      T(n, "つぎ", 11, C.heroSub, "medium"); T(n, p.next.it.time, 11, C.heroSub, "semi"); T(n, p.next.it.title, 11, C.heroSub, "", 1)
    }
  } else if (p.undone.length) {
    T(card, "まずはこれだけ", 11, C.heroSub, "semi")
    card.addSpacer(6)
    T(card, p.undone[0].title, title, C.heroInk, "bold", 2)
    card.addSpacer(4)
    T(card, "時間の決まった予定は、今日はもうありません", 10, C.heroSub, "", 2)
  } else {
    T(card, "今日", 11, C.heroSub, "semi")
    card.addSpacer(6)
    T(card, p.today.length ? "ぜんぶ、おわりました" : "予定はまだありません", title, C.heroInk, "bold", 2)
    card.addSpacer(4)
    T(card, p.today.length ? "おつかれさまでした" : "タップして話して入れる", 10, C.heroSub, "", 2)
  }
  if (o.fill) card.addSpacer()
  return card
}

/* 一覧の1行（アプリのタイムラインと同じ） */
function row(parent, it, o) {
  const r = H(parent); r.spacing = 8
  const tc = V(r); tc.size = new Size(o.timeW || 38, 0)
  T(tc, it.time || (it.allDay ? "終日" : "いつでも"), it.time ? 12 : 9, it.done ? C.mute : C.ink, it.time ? "semi" : "")
  sym(r, it.done ? "checkmark.circle.fill" : "circle", 14, it.done ? C.ok : C.line)
  const b = V(r)
  T(b, it.title, o.size || 13, it.done ? C.mute : C.ink, it.done ? "" : "semi", 1)
  r.addSpacer()
  return r
}

/* ---------- 組み立て ---------- */
async function build(family) {
  const data = await loadData()
  const p = pick(data)
  const w = new ListWidget()
  w.url = OPEN_URL
  w.refreshAfterDate = new Date(Date.now() + 10 * 60000)

  // ---- ロック画面 ----
  if (family === "accessoryInline") {
    const n = p.cur ? p.cur.it : p.next ? p.next.it : null
    w.addText(n ? (n.time + " " + n.title) : "予定なし")
    return w
  }
  if (family === "accessoryCircular") {
    w.addAccessoryWidgetBackground = true
    const n = p.cur ? p.cur.e : p.next && !p.next.tomorrow ? p.next.s : null
    if (n) { const d = w.addDate(n); d.applyTimerStyle(); d.font = Font.boldSystemFont(11); d.centerAlignText() }
    else { const t = w.addText("なし"); t.font = Font.boldSystemFont(12); t.centerAlignText() }
    return w
  }
  if (family === "accessoryRectangular") {
    const white = Color.white()
    if (p.cur || p.next) {
      const it = p.cur ? p.cur.it : p.next.it
      T(w, (p.cur ? "いま " : p.next.tomorrow ? "明日 " + it.time + " " : it.time + " ") + it.title, 13, white, "bold", 1)
      const r = H(w); r.spacing = 4
      T(r, p.cur ? "のこり" : "あと", 11, white, "")
      const d = r.addDate(p.cur ? p.cur.e : p.next.s); d.applyRelativeStyle(); d.font = Font.heavySystemFont(16); d.textColor = white
    } else {
      T(w, p.undone.length ? "やること " + p.undone.length + "件" : "今日の予定はなし", 14, white, "bold")
    }
    return w
  }

  // ---- ホーム画面 ----
  w.backgroundColor = C.bg
  if (!data.ok) {
    w.setPadding(14, 16, 14, 16)
    T(w, "予定帳", 13, C.accent, "bold")
    w.addSpacer(6)
    T(w, data.error || "読みこめませんでした", 12, C.ink, "semi", 4)
    w.addSpacer()
    return w
  }

  if (family === "small") {
    // まるごと「いま」のカード
    w.backgroundColor = C.hero
    w.setPadding(14, 12, 14, 12)
    heroCard(w, p, { pad: 0, radius: 0, big: 22, title: 15, barW: 128, compact: true, fill: true })
    return w
  }

  if (family === "medium") {
    w.setPadding(12, 12, 12, 14)
    const h = H(w); h.spacing = 12; h.topAlignContent()
    heroCard(h, p, { pad: 12, big: 20, title: 15, barW: 128, width: 158, compact: true, fill: true })
    const right = V(h); right.spacing = 7
    const head = H(right)
    T(head, (p.now.getMonth() + 1) + "月" + p.now.getDate() + "日 " + WD[p.now.getDay()], 12, C.ink, "bold")
    head.addSpacer()
    if (p.today.length) T(head, p.done + "/" + p.today.length, 11, C.ok, "semi")
    const rest = p.today.filter(i => !(p.cur && i === p.cur.it) && !(!p.cur && p.next && i === p.next.it) && !i.done)
    rest.slice(0, 4).forEach(it => row(right, it, { size: 12, timeW: 40 }))
    if (!rest.length) T(right, p.tomorrow.length ? "明日 " + (p.tomorrow[0].time || "") + " " + p.tomorrow[0].title : "ほかの予定はありません", 11, C.mute, "", 2)
    right.addSpacer()
    return w
  }

  // large / extraLarge
  w.setPadding(14, 16, 12, 16)
  const head = H(w)
  const hd = V(head)
  T(hd, (p.now.getMonth() + 1) + "月" + p.now.getDate() + "日", 20, C.ink, "heavy")
  T(hd, WD[p.now.getDay()] + "曜日" + (data.stale ? "・前回の内容" : ""), 11, C.mute, "medium")
  head.addSpacer()
  if (p.today.length) T(head, p.done + " / " + p.today.length + " できた", 11, C.mute, "medium")
  w.addSpacer(8)
  heroCard(w, p, { pad: 13, big: 28, title: 18, barW: 280 })
  w.addSpacer(8)

  const list = V(w)
  list.backgroundColor = C.surface; list.cornerRadius = 16; list.setPadding(9, 12, 9, 12); list.spacing = 6
  const rest = p.today.filter(i => !(p.cur && i === p.cur.it) && !(!p.cur && p.next && i === p.next.it))
  const lh = H(list)
  T(lh, "今日", 11, C.mute, "semi"); lh.addSpacer(); T(lh, p.today.length + "件", 11, C.mute, "")
  const max = p.cur || p.next ? 3 : 6
  rest.slice(0, max).forEach(it => row(list, it, {}))
  if (rest.length > max) T(list, "ほか " + (rest.length - max) + "件", 10, C.mute, "")
  if (!rest.length) {
    if (p.tomorrow.length) {
      T(list, "明日", 11, C.mute, "semi")
      p.tomorrow.slice(0, 3).forEach(it => row(list, it, {}))
    } else T(list, "ほかの予定はありません", 12, C.mute, "")
  }
  if (data.later || data.overdue) {
    const f = H(list); f.spacing = 10
    if (data.overdue) T(f, "やり残し " + data.overdue + "件", 10, C.warn, "medium")
    if (data.later) T(f, "あとで " + data.later + "件", 10, C.mute, "medium")
  }
  w.addSpacer()
  return w
}

const family = config.widgetFamily || "large"
const widget = await build(family)
if (config.runsInWidget || config.runsInAccessoryWidget) {
  Script.setWidget(widget)
} else {
  if (justSaved) {
    const a = new Alert()
    a.title = "ウィジェットに反映しました"
    a.message = "ホーム画面のウィジェットは、数分以内に新しくなります。"
    a.addAction("OK")
    await a.presentAlert()
  }
  if (family === "small") await widget.presentSmall()
  else if (family === "medium") await widget.presentMedium()
  else await widget.presentLarge()
}
Script.complete()
