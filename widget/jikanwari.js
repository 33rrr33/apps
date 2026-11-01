// 時間割ウィジェット（Scriptable 用）
// 使い方: Scriptable アプリで新しいスクリプトを作り、このファイルの中身を全部はりつける。
// ホーム画面（小・中・大）とロック画面（長方形・1行）のウィジェットに対応。
//
// 写真から時間割を入れるとき:
//   「時間割カメラ」ページで写真を読み取り →「ウィジェットに送る」でコピー →
//   Scriptable でこのスクリプトを ▶ 実行すると、コピーした時間割が保存される。
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

// ウィジェットをタップしたときに開くURL（空なら Scriptable が開く）
const OPEN_URL = ""

// 教科ごとの色（ない教科は灰色）
const SUBJECT_COLORS = {
  国語: "#FF3B30", 算数: "#007AFF", 理科: "#34C759", 社会: "#FF9500",
  英語: "#AF52DE", 体育: "#30B0C7", 音楽: "#FF2D55", 図工: "#FFCC00",
  道徳: "#A2845E", 総合: "#5856D6", 学活: "#64D2FF", 生活: "#8BC34A",
}
// ==========================================

// ====== 写真から作った時間割の読みこみ ======
const PREFIX = "JIKANWARI:"
const fm = FileManager.local()
const savePath = fm.joinPath(fm.documentsDirectory(), "jikanwari.json")

function applyData(d) {
  if (!d || typeof d !== "object" || !d.days || typeof d.days !== "object") {
    throw new Error("時間割データの形がちがいます")
  }
  if (d.title) TITLE = String(d.title)
  if (Array.isArray(d.times) && d.times.length) {
    TIMES = d.times.map((t) => [String((t && t[0]) || ""), String((t && t[1]) || "")])
  }
  TIMETABLE = {}
  for (const k of Object.keys(d.days)) {
    TIMETABLE[k] = (Array.isArray(d.days[k]) ? d.days[k] : []).map((x) => String(x || ""))
  }
  if (d.nextDayAfter) NEXT_DAY_AFTER = String(d.nextDayAfter)
}

async function showAlert(title, message) {
  const a = new Alert()
  a.title = title
  a.message = message
  a.addAction("OK")
  await a.presentAlert()
}

// 1) 前に保存した時間割があれば使う
if (fm.fileExists(savePath)) {
  try { applyData(JSON.parse(fm.readString(savePath))) } catch (e) { /* 見本のまま */ }
}

// 2) アプリで ▶ 実行したとき: コピーされた時間割があれば保存する
if (!config.runsInWidget) {
  const raw = String((args.queryParameters && args.queryParameters.data) || Pasteboard.pasteString() || "").trim()
  if (raw.startsWith(PREFIX)) {
    try {
      const d = JSON.parse(raw.slice(PREFIX.length))
      applyData(d)
      fm.writeString(savePath, JSON.stringify(d))
      await showAlert("時間割を読みこみました", "ウィジェットにも数分以内に反映されます。")
    } catch (e) {
      await showAlert("読みこめませんでした", "「時間割カメラ」でもう一度「ウィジェットに送る」を押してから実行してください。")
    }
  }
}

const DAY = ["日", "月", "火", "水", "木", "金", "土"]

const C = {
  bg: Color.dynamic(new Color("#FFFFFF"), new Color("#1C1C1E")),
  text: Color.dynamic(new Color("#1C1C1E"), new Color("#F2F2F7")),
  sub: new Color("#8E8E93"),
  accent: new Color("#FF9500"),
  hl: Color.dynamic(new Color("#FFF1DC"), new Color("#3A2A12")),
}

function toMin(hm) {
  if (!hm || !hm.includes(":")) return NaN
  const [h, m] = hm.split(":").map(Number)
  return h * 60 + m
}

function ymd(d) {
  const p = (n) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

// その日の教科リスト（休みなら null）。最後の空きコマは切りすてる
function lessonsOf(d) {
  if (HOLIDAYS.includes(ymd(d))) return null
  const list = (TIMETABLE[DAY[d.getDay()]] || []).slice()
  while (list.length && !list[list.length - 1]) list.pop()
  return list.length ? list : null
}

// ---- どの日を表示するか決める ----
const now = new Date()
const nowMin = now.getHours() * 60 + now.getMinutes()
const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
const target = new Date(today)
if (nowMin >= toMin(NEXT_DAY_AFTER)) target.setDate(target.getDate() + 1)
for (let i = 0; i < 30 && !lessonsOf(target); i++) target.setDate(target.getDate() + 1)

const list = lessonsOf(target) || []
const diff = Math.round((target - today) / 86400000)
const when = diff === 0 ? "きょう" : diff === 1 ? "あした" : `${DAY[target.getDay()]}曜日`
const dateLabel = `${target.getMonth() + 1}/${target.getDate()}(${DAY[target.getDay()]})`

const periods = list.map((s, i) => ({ i, n: i + 1, s, t: TIMES[i] && TIMES[i][0] && TIMES[i][1] ? TIMES[i] : null }))

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
if (OPEN_URL) w.url = OPEN_URL

if (family === "accessoryInline") {
  const subj = periods.map((p) => (p.s ? p.s[0] : "・")).join("")
  w.addText(`${when} ${subj || "なし"}`)
} else if (family === "accessoryRectangular") {
  const h = w.addText(`${when} ${dateLabel}`)
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
    const h3 = head.addText(TITLE)
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
const marks = [toMin(NEXT_DAY_AFTER)]
if (diff === 0) periods.forEach((p) => p.t && marks.push(toMin(p.t[0]), toMin(p.t[1])))
const nextMark = marks.filter((m) => m > nowMin).sort((a, b) => a - b)[0]
const refresh = new Date(today)
if (nextMark !== undefined) refresh.setMinutes(nextMark)
else refresh.setDate(refresh.getDate() + 1)
w.refreshAfterDate = refresh

if (config.runsInWidget) {
  Script.setWidget(w)
} else {
  await w.presentLarge()
}
Script.complete()
