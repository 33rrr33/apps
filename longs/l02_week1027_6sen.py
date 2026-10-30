# 長尺「今週の神ワザ6選」（2026-11-01 06:00 公開）: iPhoneの隠し神機能①〜③＋Macの神設定①〜③の60秒パートを
# lib/assemble.py の OP/ED と結合する一回限りのスクリプト（旧方式→v2 の移行週）。
#   python3 longs/l02_week1027_6sen.py stills|render|upload
import json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
import assemble as A, partlib as PL, shortlib as SL

ROOT = SL.ROOT
S = dict(title="【保存版】今すぐ使える！iPhone＆Macの神ワザ6選まとめ", theme_spoken="iPhoneとMacの、かみワザ",
         theme="今週の神ワザ6選", publish_at="2026-11-01T06:00:00+09:00")
EPS = ["episodes/s03_iphone_hidden/ep01_back_tap.py", "episodes/s03_iphone_hidden/ep02_space_cursor.py",
       "episodes/s03_iphone_hidden/ep03_lift_subject.py", "episodes/s04_mac_settings/ep01_hot_corners.py",
       "episodes/s04_mac_settings/ep02_tap_to_click.py", "episodes/s04_mac_settings/ep03_path_bar.py"]
SHORTS = ["0Yhwm8sUFu4", "6xBvEuina7M", "KKGO0MecjkY", "U7yL4G9wMBs", "s6kqqowiqEY", "v2GA3FsK4oQ"]
SERIES = ["iPhoneの隠し神機能①", "iPhoneの隠し神機能②", "iPhoneの隠し神機能③", "Macの神設定①", "Macの神設定②", "Macの神設定③"]

def main(mode):
    parts = []
    for i, e in enumerate(EPS, 1):
        mp4 = os.path.join(ROOT, "storage", "legacy_6", f"part_{i}.mp4")
        if not os.path.exists(mp4): PL.render(os.path.join(ROOT, e), mp4)
        ln = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                                  capture_output=True, text=True).stdout)
        parts.append(dict(title=SL.load_episode(os.path.join(ROOT, e)).PART["title"], mp4=mp4, length=ln))
    wd = os.path.join(SL.CACHE, "l02_week1027"); os.makedirs(wd, exist_ok=True)
    if mode == "stills":
        from PIL import Image
        ims = [A.op_frame(S, parts, x).convert("RGB").resize((640, 360)) for x in (0.8, 5.0)] + [A.ed_frame(S, 1.5).convert("RGB").resize((640, 360))]
        sh = Image.new("RGB", (1920, 360))
        for k, im in enumerate(ims): sh.paste(im, (k * 640, 0))
        p = os.path.join(SL.OUT_DIR, "l02_week1027_sheet.png"); sh.save(p); print("sheet:", p); return
    vo = A.say({"op": "今週の、iPhoneとMacの、かみワザ6選をまとめました。気になるところから見てね！",
                "ed": "最後まで見てくれてありがとう！明日からは、平日毎日、朝と夕方にショートを投稿します。チャンネル登録してね！"}, wd)
    op_len = max(9.0, 0.6 + len(vo["op"]) / SL.SR + 1.6); ed_len = max(7.0, 0.6 + len(vo["ed"]) / SL.SR + 1.4)
    op, ed = os.path.join(wd, "op.mp4"), os.path.join(wd, "ed.mp4")
    A.card_video(op, lambda t: A.op_frame(S, parts, t), vo["op"], op_len, 7)
    A.card_video(ed, lambda t: A.ed_frame(S, t), vo["ed"], ed_len, 9)
    seq = [op] + [p["mp4"] for p in parts] + [ed]
    out = os.path.join(SL.OUT_DIR, "l02_week1027_6sen.mp4")
    ins = sum([["-i", x] for x in seq], [])
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(len(seq))) + f"concat=n={len(seq)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True, stdin=subprocess.DEVNULL)
    t = op_len; ch = ["0:00 オープニング（目次）"]
    for i, p in enumerate(parts):
        ch.append(f"{A.mmss(t)} {SL.CIRCLED[i]} {p['title']}"); t += p["length"]
    ch.append(f"{A.mmss(t)} エンディング")
    shorts = "\n".join(f"{SL.CIRCLED[i]} {SERIES[i]}：{p['title']}\nhttps://youtube.com/shorts/{SHORTS[i]}" for i, p in enumerate(parts))
    desc = ("今週のショート「iPhoneの隠し神機能」①〜③と「Macの神設定」①〜③の6本を、1本ずつくわしく解説したまとめ版です📱💻\n"
            "設定の場所や手順をステップごとに見せているので、保存して見ながら試してください。\n\n"
            "━━━━━━━━━━━━━━━━\n▼目次\n━━━━━━━━━━━━━━━━\n" + "\n".join(ch) +
            "\n\n━━━━━━━━━━━━━━━━\n▼元のショート動画\n━━━━━━━━━━━━━━━━\n" + shorts +
            "\n\n▼チャンネル登録はこちら\nhttps://www.youtube.com/@mac_oic?sub_confirmation=1\n"
            "11/2からは、平日毎日 朝6:00 と 夕方17:30 にiPhoneの便利技ショート、土日の朝6:00に5分のまとめ動画を投稿します。\n"
            "役に立ったら高評価とチャンネル登録をお願いします🙏\n\n#iPhone #Mac #iPhone便利技 #Mac便利技 #iOS #macOS #Apple #保存版")
    meta = dict(title=S["title"], description=desc, publish_at=S["publish_at"], notify_subscribers=True,
                tags=["iPhone", "Mac", "iPhone 便利技", "Mac 便利技", "iPhone 裏技", "MacBook", "iOS", "macOS", "Apple", "まとめ", "保存版"],
                comment="6つの中で、どれが一番役に立ちましたか？👇 番号でコメントしてね！")
    mp = os.path.splitext(out)[0] + ".meta.json"
    json.dump(meta, open(mp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"long": out, "length": round(t + ed_len, 1), "chapters": ch}, ensure_ascii=False, indent=1))
    if mode == "upload":
        r = subprocess.run([sys.executable, os.path.join(ROOT, "lib", "ytupload.py"), "upload", out, mp], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "render")
