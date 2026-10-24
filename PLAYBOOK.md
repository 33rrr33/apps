# 毎日のショート動画づくり（16:24 JST 自動実行）

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

## 1. 今日のネタを決める
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
- `CTA`：締めの大見出し2行（例「同じApple IDで / Handoffをオン」）と読み上げ（例「保存して試してね！」）。
- `draw_body(c, t, T)`：実際の画面操作を再現するアニメーション。`stage()` で Mac + iPhone、または必要なら片方だけ。見出しは `telop()`（「① …」「② …」→結果）、補足は `badge()`。キー操作は `keycaps()`、移動は `fly()`。
- `sfx(T)` と `stills(T)` も用意する。
- 半透明の塗りは必ず `rra()` / `fade()` を使う（`rr()` に半透明色を渡すと下が抜けて黒くなる）。
- 大事な表示は y=1550 より上に置く（下はショートのUIで隠れる）。iPhone（右下）に隠れる位置に重要なUIを置かない。

## 3. 確認 → 書き出し
```bash
python3 lib/shortlib.py episodes/<series>/epNN_<slug>.py stills   # out/<name>_sheet.png を Read で目視確認
python3 lib/shortlib.py episodes/<series>/epNN_<slug>.py render   # out/<name>.mp4（約1分）
```
シートで「文字のはみ出し・重なり・隠れ・誤字・事実の誤り」を確認し、直してから render。
`ffprobe` で長さ20.0秒・音声ありを確認。

## 4. 届ける
- `SendUserFile`（files=[mp4の絶対パス], status="proactive", display="render", caption="<シリーズ名><丸数字>（20秒）"）。
- その後、短い日本語メッセージ：今日のネタ一言、YouTube用の **タイトル・概要欄1〜2行・ハッシュタグ3〜5個**、次回予告（次のネタ or 新シリーズ予定）。
- **YouTubeタイトルは必ずこの形式で統一（ユーザー指定）**：`<シリーズ名><丸数字> #shorts`
  - 例：`MacとiPhoneの神連携機能③ #shorts`
  - ネタ名や【】・煽り文句などは付け足さない。シリーズ名は state.json の `title` そのまま、丸数字は①〜⑤。コピペしやすいようコードブロックで1行だけ示す。

## 5. 記録して push
- `state.json`：今日の回を `"status": "done"`, `"date"` を付け、`history` に追加。
- `git add -A && git commit -m "<シリーズ名><丸数字>: <ネタ>"`（コミットメッセージ末尾にセッションの指定どおりの Co-Authored-By / Claude-Session 行）
- `git push -u origin shorts-bot`（ネットワーク失敗時のみ 2,4,8,16秒で再試行）。

## 失敗したとき
何かで作れなかった日は、無理に低品質なものを出さず、何が起きたかを1〜2行でユーザーに伝える（state.json は進めない）。
