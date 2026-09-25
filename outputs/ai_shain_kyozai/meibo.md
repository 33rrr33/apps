# 社員名簿（meibo）

この会社に実在する社員の一覧です。
`.claude/agents/` の中身とここは、いつも一致していること（ずれたら育成担当が直す）。

| ファイル | 名前 | 役割 | 成果物 | 権限（tools） |
|---|---|---|---|---|
| `.claude/agents/kikaku.md` | 企画担当 | 何を作る／直すかを決める | 企画メモ（`outputs/ai_shain_kyozai/kikaku_memo.md`） | Read, Grep, Glob, Write |
| `.claude/agents/kaihatsu.md` | 開発担当 | アプリを作り・直す | アプリのコード（`furigana/` `cockpit/` `all/` `index.html` など） | Read, Grep, Glob, Edit, Write, Bash |
| `.claude/agents/kensa.md` | 検査役 | 成果物を公開前に点検（直さない） | 検査報告（口頭） | Read, Grep, Glob |
| `.claude/agents/ikusei.md` | 育成担当 | 社員プロンプトを育てる／名簿・育成ログを整える | 社員プロンプト・`kyoiku_log.md`・`meibo.md` | Read, Grep, Glob, Edit, Write |
| `.claude/agents/kansa.md` | 監査担当 | 社員プロンプトを点検（矛盾・重複・死んだルール・名簿ずれ） | 監査報告・`feedback_log.md` | Read, Grep, Glob, Edit, Write |

## 権限のひとこと（詳しくは運用マニュアル §5）

- 点検・検査だけの役（**検査役**）は Write / Edit を持たない。
- 監査担当が Write / Edit を持つのは `feedback_log.md` 記録のためだけ（明文化された唯一の例外）。
