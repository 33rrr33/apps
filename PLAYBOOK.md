# 毎日の自動運用 v2（2026-11-02 公開分から・ユーザー確定仕様）

**main ブランチには絶対に触らない。** このブランチ `shorts-bot` だけを使う。鍵は環境変数のみ（チャットに出さない）。

## 仕様の要点
- **2026-10-31 改訂（脱・広告感）**：ショートは v3 レイアウト必須（`SCREEN` を定義したエピソード）。上30%＝黒帯に特大テロップ（`HOOK` は0秒から最大サイズで点滅、以降は `TELOPS`）、中55%＝実機のiPhone画面を最大表示（`SCREEN_CROP` で要の部分を拡大）、下15%＝操作キャプション（`ACTIONS`、例「空白キー長押し」「2本指スワイプ」）。イラストや小さいモックアップを主役にしない。**挨拶・前置き（今日は〜／紹介します等）は禁止**（shortlib が検出して止める）。`HOOK` は損失回避・限定の強い言葉（例「これ設定してない人\n[全員損]してます」「9割が知らない\n[iPhoneの神機能]」「今すぐ設定開いて！\n{放置厳禁}」）。
- **シリーズ固定**：前半（月朝〜水朝）は毎週『iPhone爆速神操作』①〜⑤、後半（水夕〜金夕）は毎週『iPhone隠し神機能』①〜⑤。ネタは themes.json の topics を週5本ずつ（足りなければ追加）。
- **全てiPhoneで統一**（Macのネタは出さない。2026-10-31 ユーザー指定）。
- APIで公開設定（status）を変える時は、`embeddable: true`・`publicStatsViewable: true` も一緒に送る（送らないと埋め込みがオフになる）。
- **同じ時刻に2本以上公開しない（ショートと長尺、内容が違っても禁止。ユーザー指定）**。ytupload.py は state.json の予約と同じ時刻のアップロードを拒否する。
- **iPhone特化・週替わり2シリーズ**：前半（月朝〜水朝 ①〜⑤）／後半（水夕〜金夕 ①〜⑤）。テーマは `config/themes.json` の pool を週ごとに順番に（前半=pool[2w%6]・後半=pool[(2w+1)%6]、一周したらループ）。
- **枠（公開時刻 JST）**：月〜金 06:00 と 17:30（計10本・各20秒ショート）、**土06:00 前半まとめ長尺、日06:00 後半まとめ長尺**（各約5分）。土日の夕方は配信なし（2026-10-30 ユーザー指定で土日は朝6時）。
- **公開の24時間前に生成・予約**：06:00 のトリガーは翌日06:00枠（金→土の前半まとめ、土→日の後半まとめもここ）、17:30 のトリガーは翌日17:30枠を作る（金・土の夕方はスキップ）。`python3 lib/schedule.py next morning|evening` が「何を作るか」を返す（`plan` で3週間分の一覧）。
- **デュアル生成**：平日は1つのエピソードファイルから ①20秒の縦ショート（shortlib）と ②約60秒の横型パート（partlib、`PART` 定義）を作る。パートは `storage/weekly_<first|second>_half/part_N.mp4`（git 管理外。コンテナが消えても週末に assemble がエピソードから自動で作り直す）。
- **YouTube**：`privacyStatus=private`＋`publishAt`（+09:00）。`notify_subscribers`：ショート false／週末長尺 true（meta.json に書く）。
- タイトル：ショート `{テーマ}{丸数字} #Shorts`、土曜 `【保存版】今すぐ使える！{前半テーマ}5選まとめ`、日曜 `【決定版】知らなきゃ損する！{後半テーマ}5選まとめ`（schedule.py が出す）。

## 0. 準備
```bash
cd /home/user/apps && git fetch origin shorts-bot
[ -d /home/user/shorts-bot ] || git worktree add /home/user/shorts-bot origin/shorts-bot
cd /home/user/shorts-bot && git checkout -B shorts-bot origin/shorts-bot
python3 -c "import edge_tts" 2>/dev/null || pip install -q edge-tts
```
CHANNEL.md も読む。

## 1. 何を作るか
`python3 lib/schedule.py next morning`（06:00 実行）/ `next evening`（17:30 実行）。
- `kind: skip` → 作らない（コメントだけして終わり）。
- `kind: legacy` → 旧方式（下の「旧方式」節。2026-11-01 の Macの神設定③＋6選長尺だけ）。
- `kind: short` → 2〜4。
- `kind: long` → 5。
- state.json の `v2.slots[<公開日時>]` に `id` が既にあれば**作り直さない**（二重アップロード防止）。

## 2. エピソードを書く（kind: short）
- ファイルは schedule の `episode`（例 `episodes/w20261102_first/ep01_calc_delete.py`）。**`episodes/w20261102_first/ep01_calc_delete.py`（v3：SCREEN / SCREEN_CROP / HOOK / HOOK_SPOKEN / TELOPS / ACTIONS / PART）を手本に**。
- `SERIES = dict(key=<series_key>, title=<theme>, spoken=<theme_spoken>, hook_split=<hook_split>, total=5)`、`NUM`、`SLUG`、`NEXT`（次回ネタの短い名前。⑤は「まとめ動画は土曜17:30」または「日曜17:30」）。
- 本編は核心の操作だけをテンポよく（20秒・shortlib のガードに従う）。読み上げの「神」は「かみ」。
- **`PART`**（60秒の詳細版）：`title`、`intro`、`steps`＝5〜6個の（画面ラベル, 読み上げ, ショートのアニメの区間）、`outro`。設定アプリの場所・手順を丁寧に。長さ 55〜65 秒を目安（partlib が長さを表示）。
- ネタ（topic）は themes.json のもの。事実は正確に（メニュー名・対応iOS）。自信がない細部は出さない。テーマが2周目で topics が足りない（topic が null）時は、avoid と過去回に被らない5本を themes.json の topics に追加してから作る。

## 3. 確認 → 書き出し
```bash
python3 lib/shortlib.py <episode> stills   # Read で目視確認 → 直す
python3 lib/shortlib.py <episode> render
python3 lib/partlib.py  <episode> stills   # 横型パートの確認
python3 lib/partlib.py  <episode> render --out <schedule の part>
```

## 4. アップロード（ショート）
`out/<name>.meta.json`：title（schedule の title）、詳しい description（使い方・ここもすごい・シリーズ①〜⑤の一覧・「土曜/日曜の朝6:00に5分まとめ」・投稿時間の案内）、tags（#なし）、playlist=テーマ名、`publish_at`、`"notify_subscribers": false`、comment。
`python3 lib/ytupload.py upload out/<name>.mp4 out/<name>.meta.json` → state.json `v2.slots[<YYYY-MM-DDTHH:MM>]` に id などを記録（comment_posted=false）。
playlist_error が出ても動画は上がっている → `python3 lib/ytupload.py playlist <id> <テーマ名>`。id が分からない時は `python3 lib/ytupload.py recent`。

## 5. 週末の長尺（kind: long）
`python3 lib/assemble.py <YYYY-MM-DDTHH:MM> stills` で OP/ED を確認 → `python3 lib/assemble.py <…> upload`。
OP（タイトル＋目次）＋パート①〜⑤＋ED（登録誘導）を結合し、説明欄にチャプター・元ショートのリンク・登録誘導を自動で入れ、notifySubscribers=true で予約。日曜分のアップロード後はパートを storage/archive/<週> に移す。

## 6. コメント・通知・記録
- 実行のたびに最後に：**今日のこの時刻に公開された枠**（v2.slots の今日の 06:00 / 17:30）が comment_posted=false なら `python3 lib/ytupload.py comment <id> "<comment>"` → true に。ユーザーへは一言「コメントを付けました、固定してね」。
- LINE は**夕方（17:30）の実行だけ** 1通、固定文：`python3 lib/notify_line.py "$(printf '今日の予定は終わりましたか？\n終わっていない場合は終わらせましょうね！')"`
- ショートを SendUserFile（status=proactive）で送り、短く落ち着いた日本語で結果を伝える（何を何時に予約したか）。
- state.json 更新 → `git add -A && git commit`（末尾にセッション指定の Co-Authored-By / Claude-Session 行）→ `git push -q origin shorts-bot`（失敗時のみ 2,4,8,16 秒で再試行）。

## 失敗したとき
作れなかった時は低品質なものを出さず、理由を1〜2行で伝える（24時間前なので、次の実行か手動で間に合う）。

---

# 旧方式（〜2026-11-01 公開分）
# 毎日のショート動画づくり（17:35 JST 自動実行・**翌日分を前日に予約**）

**2026-10-28 から（ユーザー指定）**：毎日17:35に実行し、
1. その日17:30に公開された動画（state.json uploads の今日の日付）に固定コメント案を投稿（`ytupload.py comment`）→ comment_posted=true。「コメントを付けました、固定してね」と一言。
2. **翌日（JST）の回**を作り、非公開アップロード＋**翌日17:30の予約公開**（publish_at は翌日の日付）。以下の手順の「今日」は「翌日」と読み替える。
3. LINE固定文面を送る → 動画を SendUserFile → 記録して push。
（日曜の長尺は土曜の実行で、ショートと一緒に作って予約する。）

ユーザー（日本語話者）のYouTubeショート用に、毎日1本、20秒ちょうどの縦型動画（1080×1920）を作ってスマホ（このセッション）に届ける。
YouTubeへの投稿はユーザーが自分で行う。**`main` ブランチには絶対にpushしない。**このブランチ `shorts-bot` だけを使う。

## 0. 準備
```bash
cd /home/user/apps && git fetch origin shorts-bot
[ -d /home/user/shorts-bot ] || git worktree add /home/user/shorts-bot origin/shorts-bot
cd /home/user/shorts-bot && git checkout -B shorts-bot origin/shorts-bot   # 既にある場合も最新に
python3 -c "import edge_tts" 2>/dev/null || pip install -q edge-tts
```
（フォントは初回に自動ダウンロード。ffmpeg / Pillow / numpy は環境に入っている前提。）

（`CHANNEL.md` も必ず読む：チャンネル名・長尺動画との連動・説明欄のルール）

## 1. 今日やることを決める（曜日ごと）
今日の日付（JST）で `state.json` の `schedule` を見る。載っていなければ `weekly` のルール（2026-10-26 にユーザーが変更）：
- **月・火・水：シリーズA ①②③**（各20秒ショート）
- **木・金・土：シリーズB ①②③**（各20秒ショート）
- **日：長尺**（約6分・横型）＝今週のA①〜③＋B①〜③の6本を、それぞれ約1分にくわしくしたまとめ。あわせて来週のA・Bを企画して state.json に追加。
- シリーズは毎週新しいテーマで①から、3本（`total: 3`）で完結。最終回③の `NEXT` は次のシリーズ名。
- アップロードは常に**非公開**まで。公開・予約はユーザーが決める（ユーザーの指示）。

### 長尺の作り方（土曜）
- `longs/l01_renkei10.py` を手本に `longs/lNN_<日付>.py` を作り、`python3 lib/longlib.py <file> stills` → シートを Read で確認 → `render`（10〜15分）。
- `INTRO_TITLE`（2行）、`OUTRO_TITLE`、`TIP_WORD`、`TIPS`（ショート①〜⑤と同じネタ。ショートでは入らなかった手順の続き・応用・注意点まで。steps は3〜4個）。6本（A①〜③＋B①〜③）なら `TIP_TARGET = 55` 前後で全体約6分。INTRO_TITLE は例 ("今週の", "神ワザ6選")。
- 画面アニメは `TIP_FN` に自作（ctx.ms=Mac画面 820x500, ctx.ps=iPhone画面 190x420, ctx.on(k)/ctx.e(k) でフェーズ。点はphase len(steps)+1）。組み込み（clip, handoff, mirror, camera, scan, call, sms, hotspot, notif, code）は key 名だけで再利用可。
- 完成後 state.json のそのシリーズに `"long_video": "<長尺タイトル>"` を入れる（翌日からのショートのエンドカードがこの長尺を案内する）。
- 長尺のタイトル案：`【完全保存版】<テーマ><N>選`。説明欄には各ワザの**チャプター（0:00 形式）**を必ず入れる。

### 一気見ショートの作り方（日曜）
- `episodes/<series>/recap.py`：`SERIES`（その週のシリーズ）、`NUM, SLUG = 0, "recap"`、`RECAP = [("ep01_xxx.py", "画面に出すネタ名", "読み上げ（例：Handoff。ページの続きがMacで！）"), ...]`、`NEXT`（来週のシリーズ名）、`NEXT_SPOKEN`（例：来週は、かみショートカット編！）。長さは自動（5本で約30秒）。
- 各回の見せ場は、エピソードに `RECAP_AT(T)` があればその時刻、無ければ本編2行目の直前から約4秒。
- タイトル：`<シリーズ名> 一気見まとめ #Shorts`。関連動画は前日（土曜）の長尺。

## 1b. ショートのネタを決める
- `state.json` を読む。`current_series` の中で最初の `"status": "todo"` が今日の回。
- 全部 `done` なら **新シリーズを企画**する：
  - Apple製品まわり（Mac / iPhone / iPad / AirPods / Apple Watch など）で、「知らないと損」系の実用ネタ5本。
  - `used_topics_outside_series` と過去シリーズのネタと被らないこと。
  - 事実は正確に（メニュー名・設定の場所・対応OS）。自信がない細部は画面に出さない。
  - `key` は `sNN_<英単語>`、`title` は画面表示（例「iPhoneの神隠し機能」）、`spoken` は読み上げ用（**「神」は必ず「かみ」とひらがなで**。他にも誤読しそうな漢字はひらがなに）、`hook_split` はフック画面の上段・下段（下段の末尾に①〜⑤が付く）。
  - `state.json` に新シリーズを追加し、`current_series` を切り替える。

## 2. エピソードを書く
`episodes/<series>/epNN_<slug>.py` を作る。**`episodes/s01_renkei/ep01_handoff.py` を手本に**同じ構成で（ep01〜03は15秒時代の作品。20秒では本編を1行増やす）：
- `SERIES` は state.json の内容と一致させる。`NUM`, `SLUG`。
- `BODY` は4行前後の (id, 読み上げ文, 次までの間)。ナレーション全体で11〜13秒程度。手順①②→結果→おまけ（応用・注意点）の流れにすると20秒が自然に埋まる。`build_timeline` は、20秒に収まらない場合と、本編が短すぎて締め（CTA）が5.5秒を超える場合にエラーになる。前者は文を短く、後者は1行足すか間/`BODY_HOLD`を延ばす。
- `CTA`：締めの大見出し2行（例「同じApple IDで / Handoffをオン」）と読み上げ（例「保存して試してね！」）。約1.5〜3秒の短い場面。
- `NEXT`：次回のネタ名（例 `NEXT = "インスタントホットスポット"`）。シリーズ最終回は次シリーズ名。エンドカードの次回予告に出る。
- 最後の約4秒は shortlib が**標準エンドカード**（完全版への誘導・下向き矢印・登録のお願い・次回予告・音声）を自動で付ける。エピソード側で作らない。長尺のリンク先は state.json の series `long_video`（新シリーズで対応する長尺がまだ無ければ null にすると「登録してね」版になる）。
- `draw_body(c, t, T)`：実際の画面操作を再現するアニメーション。`stage()` で Mac + iPhone、または必要なら片方だけ。見出しは `telop()`（「① …」「② …」→結果）、補足は `badge()`。キー操作は `keycaps()`、移動は `fly()`。
- `sfx(T)` と `stills(T)` も用意する。
- 半透明の塗りは必ず `rra()` / `fade()` を使う（`rr()` に半透明色を渡すと下が抜けて黒くなる）。
- 大事な表示は y=1550 より上に置く（下はショートのUIで隠れる）。iPhone（右下）に隠れる位置に重要なUIを置かない。

## 3. 確認 → 書き出し
```bash
python3 lib/shortlib.py episodes/<series>/epNN_<slug>.py stills   # out/<name>_sheet.png を Read で目視確認（最後のコマはエンドカード）
python3 lib/shortlib.py episodes/<series>/epNN_<slug>.py render   # out/<name>.mp4（約1分）
```
シートで「文字のはみ出し・重なり・隠れ・誤字・事実の誤り」を確認し、直してから render。
`ffprobe` で長さ20.0秒・音声ありを確認。

## 4. 届ける
- 動画は `/tmp/claude-0/-home-user-apps/<session>/scratchpad/` など、ユーザーが開ける場所にコピーしてから送る。
- `SendUserFile`（files=[mp4の絶対パス], status="proactive", display="render", caption="<シリーズ名><丸数字>（20秒）"）。
- その後、日本語メッセージで **CHANNEL.md の「投稿メタデータ一式」**（タイトル・詳しい説明欄・タグ・固定コメント案・関連動画に設定する長尺・公開時間と24時間放置のリマインド）を渡し、今日のネタ一言と次回予告を添える。
- **YouTubeタイトルは必ずこの形式で統一（ユーザー指定）**：`<シリーズ名><丸数字> #Shorts`
  - 例：`MacとiPhoneの神連携機能③ #Shorts`
  - ネタ名や【】・煽り文句などは付け足さない。シリーズ名は state.json の `title` そのまま、丸数字は①〜⑤。コピペしやすいようコードブロックで1行だけ示す。

## 4b. YouTubeへ自動アップロード（**state.json の upload_mode が "api" の時**。"manual" の時はAPIでは上げず、動画ファイル＋投稿メタデータ一式を渡す）
- meta.json の `publish_at` に **その日の `publish_time`（17:30）JST** を入れて予約公開を試す。結果の `publish_at` が null なら予約は入っていないので、「Studioで17:30に予約してください」と伝える。入っていれば「17:30に自動で公開されます。関連動画だけ選んでください」と伝える。
- `out/<name>.meta.json` を書く：`{"title", "description", "tags": [...], "playlist": "<シリーズ名>", "publish_at": "<公開日>T17:30:00+09:00", "comment": "<固定コメント案>"}`（ショートの公開時刻は state.json の予定・ユーザーの指示に合わせる）
- `python3 lib/ytupload.py upload out/<name>.mp4 out/<name>.meta.json` → 結果の id / url を state.json の history に保存。
- 審査前（`YT_AUDITED` 未設定）は **非公開で上がる**。メッセージでは「アップロード済み：Studioで公開設定を“スケジュール 17:30”に切り替え＋関連動画を選ぶだけ」と伝える（説明欄などの長いコピペは不要になる。タイトル等はメッセージに短く添えるだけでよい）。
- **公開されたらすぐコメントする**（ユーザーの希望）：予約公開を入れたら、send_later で「公開5分後（17:35 JST）」に自分宛てのリマインドを入れ、その時に `python3 lib/ytupload.py comment <id> "<comment>"` で固定コメント案を投稿して state.json の comment_posted を true にする。非公開・予約中の動画にはコメントできない。
- 環境変数が無い・エラーの時は、従来どおり動画ファイルとメタデータ一式を送る（エラーは一言だけ）。

## 4c. LINEにも知らせる（環境変数 LINE_CHANNEL_TOKEN がある時）
- 送るのは1通だけ。**文面はユーザー指定のこの言葉で固定**（タイトルやURLは付けない）：
  `python3 lib/notify_line.py "$(printf '今日の予定は終わりましたか？\n終わっていない場合は終わらせましょうね！')"`
- 失敗しても動画づくりは止めない（Claudeアプリの通知は別に届くので、エラーは一言だけ）。無料枠は月200通なので1日1〜2通まで。

## 5. 記録して push
- `state.json`：今日の回を `"status": "done"`, `"date"` を付け、`history` に追加。
- `git add -A && git commit -m "<シリーズ名><丸数字>: <ネタ>"`（コミットメッセージ末尾にセッションの指定どおりの Co-Authored-By / Claude-Session 行）
- `git push -u origin shorts-bot`（ネットワーク失敗時のみ 2,4,8,16秒で再試行）。

## 失敗したとき
何かで作れなかった日は、無理に低品質なものを出さず、何が起きたかを1〜2行でユーザーに伝える（state.json は進めない）。
