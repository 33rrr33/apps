"""Weekend long video (~5 min, 1920x1080): OP with table of contents + the week's five 60s parts + ED.

    python3 lib/assemble.py 2026-11-07T06:00 stills    # OP/ED preview sheet
    python3 lib/assemble.py 2026-11-07T06:00 render    # out/<series_key>_long.mp4 + .meta.json (chapters, short links)
    python3 lib/assemble.py 2026-11-07T06:00 upload    # render (if needed) + private upload with publishAt, notifySubscribers=true

Missing or stale parts (storage/weekly_<half>_half/part_N.mp4 whose .json names another episode) are re-rendered
from the episode files with partlib, so the container may be recycled between weekdays.
After the Sunday (second half) upload, both halves' parts are moved to storage/archive/<monday>/.
"""
import asyncio, datetime as dt, glob, json, os, shutil, ssl, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shortlib as SL, partlib as PL, schedule as SC

W, H, FPS = 1920, 1080, 30
ROOT = SL.ROOT
font, txt, rr, rra, clamp, e_at, back_out = SL.font, SL.txt, SL.rr, SL.rra, SL.clamp, SL.e_at, SL.back_out
WHITE, YEL, INK = SL.WHITE, SL.YEL, SL.INK
CIRCLED = SL.CIRCLED

def episodes(s):
    eps = []
    for n in range(1, 6):
        g = sorted(glob.glob(os.path.join(ROOT, s["episode_dir"], f"ep{n:02d}_*.py")))
        if not g: raise SystemExit(f"{s['episode_dir']}: episode {n} is missing")
        eps.append(g[0])
    return eps

def ensure_parts(s, eps):
    out = []
    for n, path in enumerate(eps, 1):
        mp4 = os.path.join(ROOT, s["parts"][n - 1]); side = os.path.splitext(mp4)[0] + ".json"
        rel = os.path.relpath(path, ROOT)
        ok = os.path.exists(mp4) and os.path.exists(side) and json.load(open(side)).get("episode") == rel
        if not ok:
            print("rendering part", n, rel); PL.render(path, mp4)
        info = json.load(open(side)); info["mp4"] = mp4
        info["length"] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                                              capture_output=True, text=True).stdout)
        out.append(info)
    return out

# ---------------------------------------------------------------- OP / ED cards
def say(lines, wd):
    import edge_tts, edge_tts.communicate as cm
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca): cm._SSL_CTX = ssl.create_default_context(cafile=ca)
    os.makedirs(wd, exist_ok=True)
    async def one(k, s): await edge_tts.Communicate(s, "ja-JP-NanamiNeural", rate=PL.RATE).save(f"{wd}/{k}.mp3")
    async def main(): await asyncio.gather(*(one(k, s) for k, s in lines.items()))
    asyncio.run(main())
    d = {}
    for k in lines:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{wd}/{k}.mp3", "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", "44100", "-ac", "1", f"{wd}/{k}.wav"], check=True, stdin=subprocess.DEVNULL)
        with wave.open(f"{wd}/{k}.wav") as w: d[k] = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
    return d

def op_frame(s, parts, t):
    c = PL.BG.copy()
    p = e_at(t, 0.2, 0.5)
    t1, t2 = (s["title"].split("！", 1) + [""])[:2]
    txt(c, (W / 2, 140), t1 + ("！" if t2 else ""), 54, (220, 220, 240), anchor="mm")
    sz = 92
    while font(sz).getlength(t2 or t1) > W - 160: sz -= 4
    k = back_out(p)
    ly = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); txt(ly, (W / 2, 80), t2 or t1, sz, YEL, anchor="mm", stroke=8)
    if k > 0:
        ly = ly.resize((max(1, int(W * k)), max(1, int(160 * k))))
        c.alpha_composite(ly, (int(W / 2 - ly.width / 2), int(250 - ly.height / 2)))
    txt(c, (W / 2, 390), "目次", 40, (200, 200, 230), anchor="mm")
    for i, pt in enumerate(parts):
        a = clamp((t - 1.2 - i * 0.35) / 0.3)
        if a <= 0: continue
        y = 450 + i * 104
        rra(c, (420, y, W - 420, y + 86), 24, (255, 255, 255, int(40 * a)))
        txt(c, (470, y + 43), CIRCLED[i], 46, YEL, anchor="lm")
        txt(c, (550, y + 43), pt["title"], 44, WHITE, anchor="lm")
    return c

def ed_frame(s, t):
    c = PL.BG.copy()
    p = back_out(clamp((t - 0.2) / 0.4))
    txt(c, (W / 2, 330), "最後まで見てくれてありがとう！", 64, WHITE, anchor="mm", stroke=6)
    if p > 0:
        w = int(620 * p); h = int(130 * p)
        rr(c, (W / 2 - w / 2, 470 - h / 2, W / 2 + w / 2, 470 + h / 2), max(1, h // 2), (255, 59, 48))
        if p > 0.8: txt(c, (W / 2, 470), "チャンネル登録", 60, WHITE, anchor="mm")
    txt(c, (W / 2, 640), "平日は毎日 朝6:00 と 夕方17:30 にショートを投稿中", 44, YEL, anchor="mm")
    txt(c, (W / 2, 720), "週末はその週のまとめ（約5分）をお届けします", 40, (220, 220, 240), anchor="mm")
    return c

def card_video(path, frame_fn, voice, length, seed):
    sr = SL.SR; n = int(sr * length)
    v = np.zeros(n); s = int(0.6 * sr); e = min(n, s + len(voice)); v[s:e] = voice[: e - s]
    win = int(0.15 * sr)
    mask = np.convolve((np.abs(v) > 0.01).astype(float), np.ones(win) / win, mode="same")
    music = SL.bgm(n, seed=seed) * (1 - 0.6 * np.clip(mask * 4, 0, 1))[:, None] * 0.75
    tt = np.arange(n) / sr
    mix = (music + (v * 1.1)[:, None]) * np.clip(tt / 0.3, 0, 1)[:, None] * np.clip((length - tt) / 0.5, 0, 1)[:, None]
    wav = path + ".wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.tanh(mix * 1.2) * 0.88 * 32767).astype(np.int16).tobytes())
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", path], stdin=subprocess.PIPE)
    for k in range(int(length * FPS)):
        t = k / FPS; im = frame_fn(t)
        if length - t < 0.4: im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(1 - (length - t) / 0.4)))))
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close(); p.wait()

# ---------------------------------------------------------------- long + metadata
def mmss(x): x = int(x); return f"{x // 60}:{x % 60:02d}"

def short_links(s):
    st = json.load(open(os.path.join(ROOT, "state.json")))
    return {u["num"]: u["id"] for u in st.get("v2", {}).get("slots", {}).values()
            if u.get("series_key") == s["series_key"] and u.get("kind") == "short" and u.get("id")}

def build(when, mode):
    s = SC.slot(dt.datetime.fromisoformat(when).replace(tzinfo=SC.JST))
    if not s or s["kind"] != "long": raise SystemExit(f"{when} is not a weekend long slot")
    eps = episodes(s)
    wd = os.path.join(SL.CACHE, s["series_key"] + "_long"); os.makedirs(wd, exist_ok=True)
    if mode == "stills":
        parts = [{"title": SL.load_episode(p).PART["title"]} for p in eps]
        ims = [op_frame(s, parts, x).convert("RGB").resize((640, 360)) for x in (0.8, 4.0)] + [ed_frame(s, 1.5).convert("RGB").resize((640, 360))]
        sheet = Image.new("RGB", (640 * 3, 360))
        for k, im in enumerate(ims): sheet.paste(im, (k * 640, 0))
        p = os.path.join(SL.OUT_DIR, s["series_key"] + "_long_sheet.png"); sheet.save(p); print("sheet:", p); return
    parts = ensure_parts(s, eps)
    ja = "、".join(f"{CIRCLED[i]}{p['title']}" for i, p in enumerate(parts))
    vo = say({"op": f"今週の、{s['theme_spoken']}、5選をまとめました。気になるところから見てね！",
              "ed": "最後まで見てくれてありがとう！平日は毎日、朝と夕方にショートを投稿しています。チャンネル登録してね！"}, wd)
    op_len = max(8.0, 0.6 + len(vo["op"]) / SL.SR + 1.6); ed_len = max(7.0, 0.6 + len(vo["ed"]) / SL.SR + 1.4)
    op, ed = os.path.join(wd, "op.mp4"), os.path.join(wd, "ed.mp4")
    card_video(op, lambda t: op_frame(s, parts, t), vo["op"], op_len, 7)
    card_video(ed, lambda t: ed_frame(s, t), vo["ed"], ed_len, 9)
    seq = [op] + [p["mp4"] for p in parts] + [ed]
    out = os.path.join(SL.OUT_DIR, s["series_key"] + "_long.mp4")
    ins = sum([["-i", x] for x in seq], [])
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(len(seq))) + f"concat=n={len(seq)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True, stdin=subprocess.DEVNULL)
    # chapters + description
    t = 0.0; chapters = [f"0:00 オープニング（目次）"]; t += op_len
    for i, p in enumerate(parts):
        chapters.append(f"{mmss(t)} {CIRCLED[i]} {p['title']}"); t += p["length"]
    chapters.append(f"{mmss(t)} エンディング")
    links = short_links(s)
    shorts = "\n".join(f"{CIRCLED[i]} {p['title']}" + (f"\nhttps://youtube.com/shorts/{links[i + 1]}" if links.get(i + 1) else "")
                       for i, p in enumerate(parts))
    desc = (f"今週のショート「{s['theme']}」①〜⑤を、1本約1分でくわしく解説したまとめ版です📱\n"
            f"設定の場所や手順をステップごとに見せているので、保存して見ながら試してください。\n\n"
            f"━━━━━━━━━━━━━━━━\n▼目次\n━━━━━━━━━━━━━━━━\n" + "\n".join(chapters) +
            f"\n\n━━━━━━━━━━━━━━━━\n▼元のショート動画\n━━━━━━━━━━━━━━━━\n{shorts}\n\n"
            f"▼チャンネル登録はこちら\nhttps://www.youtube.com/@mac_oic?sub_confirmation=1\n"
            f"平日は毎日 朝6:00 と 夕方17:30 に、iPhoneの便利技ショートを投稿しています。\n"
            f"役に立ったら高評価とチャンネル登録をお願いします🙏\n\n#iPhone #iPhone便利技 #iPhone裏技 #iOS #Apple #保存版")
    meta = dict(title=s["title"], description=desc, playlist=s["theme"], publish_at=s["publish_at"], notify_subscribers=True,
                tags=["iPhone", s["theme"], "iPhone 便利技", "iPhone 裏技", "iPhone 使い方", "iOS", "Apple", "まとめ", "保存版"],
                comment=f"今週の5つ、どれが一番役に立ちましたか？👇 番号でコメントしてね！（{ja}）")
    json.dump(meta, open(os.path.splitext(out)[0] + ".meta.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"long": out, "length": round(t + ed_len, 1), "chapters": chapters}, ensure_ascii=False, indent=1))
    if mode == "upload":
        r = subprocess.run([sys.executable, os.path.join(ROOT, "lib", "ytupload.py"), "upload", out, os.path.splitext(out)[0] + ".meta.json"],
                           capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode == 0 and s["half"] == "second":
            arch = os.path.join(ROOT, "storage", "archive", s["week"]); os.makedirs(arch, exist_ok=True)
            for half in ("first", "second"):
                for f in glob.glob(os.path.join(ROOT, "storage", f"weekly_{half}_half", "*")):
                    shutil.move(f, os.path.join(arch, f"{half}_{os.path.basename(f)}"))
            print("archived parts to", arch)
    return out

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "render")
