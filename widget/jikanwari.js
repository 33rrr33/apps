// 時間割ウィジェット（Scriptable 用）
// 使い方: Scriptable アプリで新しいスクリプトを作り、このファイルの中身を全部はりつける。
// ホーム画面（小・中・大）とロック画面（長方形・1行）のウィジェットに対応。
//
// 写真から時間割を入れるとき:
//   ウィジェットをタップ →「写真で時間割を変える」→ 開いたページで写真を読み取り
//   →「時間割をコピーする」→ もう一度ウィジェットをタップすると保存される。
//   （下の「ここを書きかえる」は、写真から入れていないときの見本）

// ====== ここを自分の時間割に書きかえる ======
let TITLE = "時間割" // 見出し（例: "3年1組"）

// 各時間の開始・終了時刻
let TIMES = [
  ["8:45", "9:30"],
  ["9:40", "10:25"],
  ["10:45", "11:30"],
  ["11:40", "12:25"],
  ["13:30", "14:15"],
  ["14:25", "15:10"],
]

// 月〜金の教科。その時間がないときは "" にする。
let TIMETABLE = {
  月: ["国語", "算数", "体育", "社会", "音楽", ""],
  火: ["算数", "国語", "理科", "理科", "図工", "図工"],
  水: ["国語", "算数", "英語", "社会", "", ""],
  木: ["算数", "国語", "体育", "道徳", "総合", "総合"],
  金: ["国語", "算数", "社会", "音楽", "学活", ""],
}

// この時刻をすぎたら、次の日の時間割を出す
let NEXT_DAY_AFTER = "16:00"

// 休みの日（祝日・行事など）。この日はとばして次の登校日を出す
const HOLIDAYS = ["2026-11-03", "2026-11-23"]

// ウィジェットをタップしたときに開くURL（空ならこのアプリのメニュー）
const OPEN_URL = ""

// 教科ごとの色（ない教科は灰色）
const SUBJECT_COLORS = {
  国語: "#FF3B30", 算数: "#007AFF", 理科: "#34C759", 社会: "#FF9500",
  英語: "#AF52DE", 体育: "#30B0C7", 音楽: "#FF2D55", 図工: "#FFCC00",
  道徳: "#A2845E", 総合: "#5856D6", 学活: "#64D2FF", 生活: "#8BC34A",
}
// ==========================================

// ====== 写真から作った時間割の読みこみ ======
// 時間割は「週ごと」に保存する（その週の月曜日の日付で区別）。
// その週の分がなければ、いちばん近い前の週の時間割を出す。
const PREFIX = "JIKANWARI:"
const KEEP_WEEKS = 12
const fm = FileManager.local()
const savePath = fm.joinPath(fm.documentsDirectory(), "jikanwari.json")
const DAY = ["日", "月", "火", "水", "木", "金", "土"]

function ymd(d) {
  const p = (n) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
function mondayOf(d) {
  const m = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  m.setDate(m.getDate() - ((m.getDay() + 6) % 7))
  return ymd(m)
}
function md(key) {
  const [, m, d] = key.split("-").map(Number)
  return `${m}/${d}`
}

function clean(d) {
  if (!d || typeof d !== "object" || !d.days || typeof d.days !== "object") {
    throw new Error("時間割データの形がちがいます")
  }
  const days = {}
  for (const k of Object.keys(d.days)) {
    days[k] = (Array.isArray(d.days[k]) ? d.days[k] : []).map((x) => String(x || ""))
  }
  const times = Array.isArray(d.times)
    ? d.times.map((t) => [String((t && t[0]) || ""), String((t && t[1]) || "")])
    : []
  const weekStart = /^\d{4}-\d{2}-\d{2}$/.test(d.weekStart || "") ? d.weekStart : null
  return { title: String(d.title || ""), times, days, nextDayAfter: String(d.nextDayAfter || ""), weekStart }
}

const SAMPLE_DATA = { title: TITLE, times: TIMES, days: TIMETABLE, nextDayAfter: NEXT_DAY_AFTER }
let store = { base: null, weeks: {} }
if (fm.fileExists(savePath)) {
  try {
    const raw = JSON.parse(fm.readString(savePath))
    if (raw && raw.weeks) store = { base: raw.base || null, weeks: raw.weeks }
    else store.base = clean(raw) // 前の形（週の区別なし）
  } catch (e) { /* 見本のまま */ }
}

// その日に使う時間割と、それがその週ちょうどの分か
function dataFor(d) {
  const key = mondayOf(d)
  const keys = Object.keys(store.weeks).sort()
  if (store.weeks[key]) return { data: store.weeks[key], exact: true }
  const prev = keys.filter((k) => k < key).pop()
  if (prev) return { data: store.weeks[prev], exact: false, from: prev }
  if (keys.length) return { data: store.weeks[keys[0]], exact: false, from: keys[0] }
  return { data: store.base || SAMPLE_DATA, exact: true }
}

async function showAlert(title, message) {
  const a = new Alert()
  a.title = title
  a.message = message
  a.addAction("OK")
  await a.presentAlert()
}

// アプリで開いたとき（ウィジェットをタップしたときも）
// コピーされた時間割があれば保存する。なければメニューを出す
const CAMERA_URL = "https://claude.ai/artifact/RCoYySGvSftnxM1gn2MCyo"
let quit = false
if (!config.runsInWidget) {
  const raw = String((args.queryParameters && args.queryParameters.data) || Pasteboard.pasteString() || "").trim()
  if (raw.startsWith(PREFIX)) {
    try {
      const d = clean(JSON.parse(raw.slice(PREFIX.length)))
      let msg
      if (d.weekStart) {
        store.weeks[d.weekStart] = d
        const keys = Object.keys(store.weeks).sort()
        while (keys.length > KEEP_WEEKS) delete store.weeks[keys.shift()]
        msg = `${md(d.weekStart)}(月) からの週の時間割として保存しました。`
      } else {
        store.base = d
        msg = "時間割を保存しました。"
      }
      fm.writeString(savePath, JSON.stringify(store))
      Pasteboard.copyString("") // 同じ時間割を何度も読みこまないように
      await showAlert("時間割を読みこみました", msg + "ウィジェットにも数分以内に反映されます。")
    } catch (e) {
      await showAlert("読みこめませんでした", "「時間割カメラ」でもう一度「時間割をコピーする」を押してから開いてください。")
    }
  } else {
    const m = new Alert()
    m.title = "時間割"
    m.message = "なにをしますか？"
    m.addAction("写真で時間割を変える")
    m.addAction("今の時間割を見る")
    m.addCancelAction("とじる")
    const choice = await m.presentSheet()
    if (choice === 0) {
      await showAlert("写真で時間割を変える", "このあと開くページで写真を撮って「時間割をコピーする」を押し、もう一度このアプリ（ウィジェット）を開いてください。")
      Safari.open(CAMERA_URL)
      quit = true
    } else if (choice !== 1) {
      quit = true
    }
  }
}

const C = {
  bg: Color.dynamic(new Color("#FFFFFF"), new Color("#1C1C1E")),
  text: Color.dynamic(new Color("#1C1C1E"), new Color("#F2F2F7")),
  sub: new Color("#8E8E93"),
  accent: new Color("#FF9500"),
  hl: Color.dynamic(new Color("#FFF1DC"), new Color("#3A2A12")),
  warn: new Color("#FF453A"),
}

function toMin(hm) {
  if (!hm || !hm.includes(":")) return NaN
  const [h, m] = hm.split(":").map(Number)
  return h * 60 + m
}

// その日の教科リスト（休みなら null）。最後の空きコマは切りすてる
function lessonsOf(d) {
  if (HOLIDAYS.includes(ymd(d))) return null
  const list = (dataFor(d).data.days[DAY[d.getDay()]] || []).slice()
  while (list.length && !list[list.length - 1]) list.pop()
  return list.length ? list : null
}

// ---- どの日を表示するか決める ----
const now = new Date()
const nowMin = now.getHours() * 60 + now.getMinutes()
const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
const switchAt = dataFor(today).data.nextDayAfter || NEXT_DAY_AFTER
const target = new Date(today)
if (nowMin >= toMin(switchAt)) target.setDate(target.getDate() + 1)
for (let i = 0; i < 30 && !lessonsOf(target); i++) target.setDate(target.getDate() + 1)

const picked = dataFor(target)
const T = picked.data
const SHOW_TITLE = T.title || TITLE
const SHOW_TIMES = T.times && T.times.length ? T.times : TIMES
// その週の時間割がまだ入っていないときの注意
const warnText = picked.exact ? "" : "この週の時間割がまだです（前の週のを表示）"

const list = lessonsOf(target) || []
const diff = Math.round((target - today) / 86400000)
const when = diff === 0 ? "きょう" : diff === 1 ? "あした" : `${DAY[target.getDay()]}曜日`
const dateLabel = `${target.getMonth() + 1}/${target.getDate()}(${DAY[target.getDay()]})`

const periods = list.map((s, i) => ({ i, n: i + 1, s, t: SHOW_TIMES[i] && SHOW_TIMES[i][0] && SHOW_TIMES[i][1] ? SHOW_TIMES[i] : null }))

// ---- いま／つぎの時間 ----
let nowIdx = -1
let nextIdx = -1
if (diff === 0) {
  for (const p of periods) {
    if (!p.s || !p.t) continue
    const s = toMin(p.t[0])
    const e = toMin(p.t[1])
    if (nowMin >= s && nowMin < e) { nowIdx = p.i; break }
    if (nowMin < s) { nextIdx = p.i; break }
  }
}

// ---- ウィジェットを組み立てる ----
const family = config.widgetFamily || "large"
const w = new ListWidget()
w.url = OPEN_URL || URLScheme.forRunningScript() // タップでメニューを開く

if (family === "accessoryInline") {
  const subj = periods.map((p) => (p.s ? p.s[0] : "・")).join("")
  w.addText(`${when} ${subj || "なし"}`)
} else if (family === "accessoryRectangular") {
  const h = w.addText(`${warnText ? "⚠︎ " : ""}${when} ${dateLabel}`)
  h.font = Font.boldSystemFont(13)
  const body = w.addText(periods.map((p) => p.s || "—").join("・") || "時間割なし")
  body.font = Font.systemFont(12)
  body.lineLimit = 2
  body.minimumScaleFactor = 0.7
} else {
  buildHomeWidget()
}

function buildHomeWidget() {
  w.backgroundColor = C.bg
  const small = family === "small"
  const medium = family === "medium"
  w.setPadding(small ? 10 : 14, small ? 10 : 14, small ? 10 : 14, small ? 10 : 14)

  // 見出し
  const head = w.addStack()
  head.centerAlignContent()
  const h1 = head.addText(when)
  h1.font = Font.heavySystemFont(small ? 15 : 17)
  h1.textColor = C.accent
  head.addSpacer(6)
  const h2 = head.addText(dateLabel)
  h2.font = Font.semiboldSystemFont(small ? 12 : 14)
  h2.textColor = C.text
  if (!small) {
    head.addSpacer()
    const h3 = head.addText(SHOW_TITLE)
    h3.font = Font.mediumSystemFont(12)
    h3.textColor = C.sub
  }
  w.addSpacer(small ? 4 : 8)

  if (!periods.length) {
    const t = w.addText("時間割がありません")
    t.font = Font.systemFont(14)
    t.textColor = C.sub
    w.addSpacer()
    return
  }

  const size = small ? (periods.length <= 5 ? 14 : 12) : medium ? 14 : 18
  if (medium) {
    // 中サイズ: 2列（前半・後半）
    const cols = w.addStack()
    const half = Math.ceil(periods.length / 2)
    const left = cols.addStack()
    left.layoutVertically()
    cols.addSpacer(8)
    const right = cols.addStack()
    right.layoutVertically()
    periods.slice(0, half).forEach((p) => addRow(left, p, size, true))
    periods.slice(half).forEach((p) => addRow(right, p, size, true))
  } else {
    periods.forEach((p) => addRow(w, p, size, !small))
  }
  w.addSpacer()
  if (warnText) {
    const wt = w.addText(small ? "⚠︎ この週の分がまだです" : "⚠︎ " + warnText)
    wt.font = Font.semiboldSystemFont(small ? 10 : 11)
    wt.textColor = C.warn
    wt.lineLimit = 1
    wt.minimumScaleFactor = 0.7
  }
}

function addRow(parent, p, size, showTime) {
  const r = parent.addStack()
  r.centerAlignContent()
  r.setPadding(2, 6, 2, 6)
  r.cornerRadius = 6
  const isNow = p.i === nowIdx
  const isNext = p.i === nextIdx
  if (isNow || isNext) r.backgroundColor = C.hl

  const num = r.addText(String(p.n))
  num.font = Font.boldRoundedSystemFont(size)
  num.textColor = C.sub
  r.addSpacer(6)

  const dot = r.addText("●")
  dot.font = Font.systemFont(Math.round(size * 0.6))
  dot.textColor = new Color(SUBJECT_COLORS[p.s] || "#8E8E93")
  r.addSpacer(4)

  const sj = r.addText(p.s || "—")
  sj.font = Font.semiboldSystemFont(size)
  sj.textColor = p.s ? C.text : C.sub
  sj.lineLimit = 1
  sj.minimumScaleFactor = 0.6
  r.addSpacer()

  if (isNow || isNext) {
    const tag = r.addText(isNow ? "いま" : "つぎ")
    tag.font = Font.boldSystemFont(Math.round(size * 0.75))
    tag.textColor = C.accent
  } else if (showTime && p.t) {
    const t = r.addText(p.t[0])
    t.font = Font.monospacedDigitSystemFont(Math.round(size * 0.75), "regular")
    t.textColor = C.sub
  }
  parent.addSpacer(2)
}

// ---- 次に書きかえる時刻（授業の始まり・終わり、切りかえ時刻）----
const marks = [toMin(switchAt)]
if (diff === 0) periods.forEach((p) => p.t && marks.push(toMin(p.t[0]), toMin(p.t[1])))
const nextMark = marks.filter((m) => m > nowMin).sort((a, b) => a - b)[0]
const refresh = new Date(today)
if (nextMark !== undefined) refresh.setMinutes(nextMark)
else refresh.setDate(refresh.getDate() + 1)
w.refreshAfterDate = refresh

if (config.runsInWidget) {
  Script.setWidget(w)
} else if (!quit) {
  await w.presentLarge()
}
Script.complete()
