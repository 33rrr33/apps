// しゃべって予定帳ウィジェット（Scriptable 用）
// 使い方: 予定帳の「設定」→「ウィジェット」→「コードをコピー」
//         → Scriptable で新しいスクリプトを作り、全部はりつける（名前は「予定帳」）。
// ホーム画面（小・中・大）とロック画面（長方形・丸・1行）に対応。

// ====== ここは予定帳が自動で入れます（さわらなくてOK） ======
const GAS_URL = "__GAS_URL__"
const TOKEN = "__TOKEN__"
// ウィジェットをタップしたときに開くURL
const OPEN_URL = "https://33rrr33.github.io/apps/yotei/"
// =========================================================

const C = {
  bg: Color.dynamic(new Color("#F6F5F2"), new Color("#0C0C0D")),
  card: Color.dynamic(new Color("#FFFFFF"), new Color("#17171A")),
  ink: Color.dynamic(new Color("#17171A"), new Color("#F2F2F3")),
  sub: Color.dynamic(new Color("#9C9CA3"), new Color("#6E6E76")),
  accent: Color.dynamic(new Color("#E2553B"), new Color("#FF6B4E")),
  warn: Color.dynamic(new Color("#C27C0E"), new Color("#F0A63A")),
  ok: Color.dynamic(new Color("#1F9D6B"), new Color("#3CCB8F")),
}
const WD = "日月火水木金土"

// ---------- データ（ネットにつながらないときは前回の分を使う） ----------
const fm = FileManager.local()
const cachePath = fm.joinPath(fm.documentsDirectory(), "yotei-widget-cache.json")
async function loadData() {
  try {
    const url = GAS_URL + "?action=widget&token=" + encodeURIComponent(TOKEN)
    const req = new Request(url)
    req.timeoutInterval = 20
    const j = await req.loadJSON()
    if (!j.ok) throw new Error(j.error || "error")
    fm.writeString(cachePath, JSON.stringify(j))
    return j
  } catch (e) {
    if (fm.fileExists(cachePath)) {
      const j = JSON.parse(fm.readString(cachePath)); j.stale = true; return j
    }
    return { ok: false, error: String(e.message || e), items: [] }
  }
}

function pad(n) { return (n < 10 ? "0" : "") + n }
function ymd(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) }
function startOf(it) {
  if (!it.date || !it.time) return null
  const p = it.date.split("-"), t = it.time.split(":")
  return new Date(+p[0], +p[1] - 1, +p[2], +t[0], +t[1])
}
function dayName(s) {
  const p = s.split("-"); const d = new Date(+p[0], +p[1] - 1, +p[2])
  return (d.getMonth() + 1) + "/" + d.getDate() + "(" + WD[d.getDay()] + ")"
}
function sortT(a, b) {
  if (a.time && b.time) return a.time < b.time ? -1 : a.time > b.time ? 1 : 0
  if (a.time) return -1; if (b.time) return 1; return 0
}

// いま・つぎ を決める
function pick(data) {
  const now = new Date(), t = ymd(now)
  const tom = ymd(new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1))
  const all = (data.items || [])
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
  return { now, today, tomorrow, cur, next, undone: today.filter(i => !i.done) }
}

// ---------- 部品 ----------
function txt(stack, s, size, color, bold, lines) {
  const x = stack.addText(s)
  x.font = bold ? Font.boldSystemFont(size) : Font.systemFont(size)
  x.textColor = color || C.ink
  x.lineLimit = lines || 1
  x.minimumScaleFactor = 0.7
  return x
}
function relDate(stack, date, size, color) {
  // 「あと◯分」が自動で動く
  const d = stack.addDate(date)
  d.applyRelativeStyle()
  d.font = Font.boldSystemFont(size)
  d.textColor = color
  d.lineLimit = 1
  d.minimumScaleFactor = 0.7
  return d
}
function hero(w, p, size) {
  const big = size === "small" ? 17 : 20
  if (p.cur) {
    txt(w, "いま", 11, C.accent, true)
    txt(w, p.cur.it.title, big, C.ink, true, 2)
    const r = w.addStack(); r.centerAlignContent()
    txt(r, "のこり ", 12, C.sub)
    const d = r.addDate(p.cur.e); d.applyTimerStyle(); d.font = Font.boldMonospacedSystemFont(13); d.textColor = C.accent
    if (size === "small" && p.next && !p.next.tomorrow) txt(w, "つぎ " + p.next.it.time + " " + p.next.it.title, 10, C.sub)
  } else if (p.next) {
    const soon = !p.next.tomorrow && (p.next.s - p.now) <= 15 * 60000
    const col = soon ? C.warn : C.accent
    txt(w, soon ? "まもなく" : (p.next.tomorrow ? "明日のはじめ" : "つぎ"), 11, col, true)
    txt(w, p.next.it.title, big, C.ink, true, 2)
    const r = w.addStack(); r.centerAlignContent()
    txt(r, p.next.it.time + "  ", 12, C.sub, true)
    relDate(r, p.next.s, 12, col)
  } else if (p.undone.length) {
    txt(w, "まずはこれだけ", 11, C.sub, true)
    txt(w, p.undone[0].title, big, C.ink, true, 2)
    txt(w, "時間の決まった予定はもうありません", 11, C.sub, false, 2)
  } else if (p.today.length) {
    txt(w, "今日はぜんぶおわりました", size === "small" ? 15 : 17, C.ok, true, 2)
  } else {
    txt(w, "今日の予定はなし", 15, C.sub, true)
    txt(w, "タップして話して入れる", 11, C.sub, false, 2)
  }
}
function row(w, it, isNow) {
  const r = w.addStack(); r.centerAlignContent(); r.spacing = 6
  const t = txt(r, it.time || "いつでも", it.time ? 12 : 10, it.done ? C.sub : C.accent, true)
  t.font = it.time ? Font.boldMonospacedSystemFont(12) : Font.systemFont(10)
  r.addSpacer(2)
  const s = txt(r, it.title, 13, it.done ? C.sub : C.ink, isNow)
  r.addSpacer()
}

// ---------- 組み立て ----------
async function build(family) {
  const data = await loadData()
  const p = pick(data)
  const w = new ListWidget()
  w.url = OPEN_URL
  w.refreshAfterDate = new Date(Date.now() + 10 * 60000)

  // ロック画面
  if (family === "accessoryInline") {
    const n = p.cur ? p.cur.it : p.next ? p.next.it : null
    w.addText(n ? ((n.time || "") + " " + n.title) : "予定なし")
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
    if (p.cur) {
      txt(w, p.cur.it.title, 14, Color.white(), true)
      const r = w.addStack(); txt(r, "のこり ", 12, Color.white())
      const d = r.addDate(p.cur.e); d.applyTimerStyle(); d.font = Font.boldSystemFont(12)
    } else if (p.next) {
      txt(w, (p.next.tomorrow ? "明日 " : "") + p.next.it.time + " " + p.next.it.title, 14, Color.white(), true)
      relDate(w, p.next.s, 12, Color.white())
    } else {
      txt(w, p.undone.length ? "やること " + p.undone.length + "こ" : "今日の予定はなし", 14, Color.white(), true)
    }
    return w
  }

  // ホーム画面
  w.backgroundColor = C.bg
  w.setPadding(12, 14, 12, 14)
  if (!data.ok) {
    txt(w, "予定帳", 13, C.accent, true)
    txt(w, "読みこめませんでした", 12, C.ink, true, 2)
    txt(w, String(data.error || ""), 9, C.sub, false, 3)
    return w
  }
  const head = w.addStack(); head.centerAlignContent()
  txt(head, (p.now.getMonth() + 1) + "月" + p.now.getDate() + "日 " + WD[p.now.getDay()] + "曜", 11, C.sub, true)
  head.addSpacer()
  if (family !== "small") {
    const done = p.today.filter(i => i.done).length
    if (p.today.length) txt(head, done + "/" + p.today.length + " できた", 11, C.ok, true)
  }
  if (data.stale) txt(head, "  前回の内容", 10, C.warn)
  w.addSpacer(4)
  hero(w, p, family)

  if (family === "medium" || family === "large" || family === "extraLarge") {
    w.addSpacer(6)
    const rest = p.today.filter(i => !(p.cur && i === p.cur.it) && !(!p.cur && p.next && i === p.next.it) && !i.done)
    const max = family === "medium" ? 2 : 7
    rest.slice(0, max).forEach(it => row(w, it))
    if (rest.length > max) txt(w, "ほか " + (rest.length - max) + "こ", 10, C.sub)
    if (family !== "medium" && p.tomorrow.length) {
      w.addSpacer(6)
      txt(w, "明日 " + dayName(p.tomorrow[0].date), 11, C.sub, true)
      p.tomorrow.slice(0, 4).forEach(it => row(w, it))
    }
    if (family !== "medium" && (data.later || data.overdue)) {
      w.addSpacer(4)
      txt(w, (data.overdue ? "前の日から " + data.overdue + "件　" : "") + (data.later ? "あとで " + data.later + "件" : ""), 10, C.sub)
    }
  }
  w.addSpacer()
  return w
}

const family = config.widgetFamily || "large"
const widget = await build(family)
if (config.runsInWidget || config.runsInAccessoryWidget) {
  Script.setWidget(widget)
} else {
  // アプリの中で動かしたときは見本を表示
  if (family === "small") await widget.presentSmall()
  else if (family === "medium") await widget.presentMedium()
  else await widget.presentLarge()
}
Script.complete()
