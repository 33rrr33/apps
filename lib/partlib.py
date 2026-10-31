"""60-second landscape "part" (1920x1080) made from the same episode file as the 20s Short.

The episode adds a PART dict next to its Short definitions:
    PART = dict(
        title="計算機で1桁だけ消す",                       # shown in the header and in the weekend long's chapters
        intro="計算機で打ち間違えたとき、全部消していませんか？",   # spoken over the title card
        steps=[("計算機を開く", "まず、計算機アプリを開いて、数字を入力します。", ("body", "b2")),
               ...],                                          # (label on screen, spoken, window of the Short's animation)
        outro="打ち間違えても、もう全部消さなくて大丈夫です。",
    )
A window is (start, end) in the Short's timeline: a number, a cue name ("body", "cta", "b1"…), or "b2+0.5".
The Short's animation in that window is replayed slowly while the step is explained (its telops/badges are hidden).
4〜6 steps → about 60 seconds.

Usage:
    python3 lib/partlib.py <episode.py> stills
    python3 lib/partlib.py <episode.py> render [--out storage/weekly_first_half/part_1.mp4]
"""
import asyncio, json, os, re, ssl, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shortlib as SL

W, H, FPS = 1920, 1080, 30
RATE = "+10%"
CIRCLED = SL.CIRCLED
WHITE, YEL, INK, GRAY, GREEN, PURPLE, BLUE = SL.WHITE, SL.YEL, SL.INK, SL.GRAY, SL.GREEN, SL.PURPLE, SL.BLUE
font, txt, rr, rra, clamp, e_at, ease_out, back_out = SL.font, SL.txt, SL.rr, SL.rra, SL.clamp, SL.e_at, SL.ease_out, SL.back_out
BG = SL.grad(W, H, (22, 26, 58), (58, 28, 92), horiz=True)
DEV_BOX = (70, 150, 70 + 900, 150 + 833)          # where the Short's device area is placed (crop 1080x1000 -> 900x833)
CROP = (0, 500, 1080, 1500)
PANEL_X = 1030

# ---------------------------------------------------------------- timeline
def cue(T, spec):
    if isinstance(spec, (int, float)): return float(spec)
    m = re.fullmatch(r"\s*(\w+)\s*([+-]\s*[\d.]+)?\s*", spec)
    base = {"body": T.body, "cta": T.cta}.get(m.group(1), None)
    if base is None: base = T.at[m.group(1)]
    return base + (float(m.group(2).replace(" ", "")) if m.group(2) else 0.0)

def lines(ep):
    P = ep.PART
    d = {"intro": f"{ep.SERIES['spoken']}、その{ep.NUM}。{P['intro']}"}
    for i, (_, s, _) in enumerate(P["steps"]): d[f"s{i}"] = s
    d["outro"] = P["outro"]
    return d

def tts(ep, workdir):
    import edge_tts, edge_tts.communicate as cm
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca): cm._SSL_CTX = ssl.create_default_context(cafile=ca)
    vo = os.path.join(workdir, "vo"); os.makedirs(vo, exist_ok=True)
    L = lines(ep); p = os.path.join(vo, "durs.json")
    if os.path.exists(p):
        d = json.load(open(p))
        if d["lines"] == L: return d["durs"]
    async def one(k, s):
        for i in range(4):
            try: return await edge_tts.Communicate(s, "ja-JP-NanamiNeural", rate=RATE).save(f"{vo}/{k}.mp3")
            except Exception:
                if i == 3: raise
                await asyncio.sleep(2)
    async def main(): await asyncio.gather(*(one(k, s) for k, s in L.items()))
    asyncio.run(main())
    durs = {}
    for k in L:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{vo}/{k}.mp3", "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", "44100", "-ac", "1", f"{vo}/{k}.wav"], check=True, stdin=subprocess.DEVNULL)
        durs[k] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{vo}/{k}.wav"],
                                       capture_output=True, text=True).stdout)
    json.dump({"lines": L, "durs": durs}, open(p, "w"), ensure_ascii=False, indent=1)
    return durs

class PT: pass

def timeline(ep, durs, ST):
    P = PT(); P.at = {}; t = 0.6
    P.at["intro"] = t; t += durs["intro"] + 1.0
    P.steps = []
    for i, (label, spoken, win) in enumerate(ep.PART["steps"]):
        a, b = cue(ST, win[0]), cue(ST, win[1])
        dur = max(5.0, durs[f"s{i}"] + 1.0)
        P.at[f"s{i}"] = t + 0.3
        P.steps.append((t, t + dur, a, b, label))
        t += dur
    P.outro = t; P.at["outro"] = t + 0.3; t += durs["outro"] + 1.6
    P.total = t
    return P

# ---------------------------------------------------------------- drawing
def short_canvas(ep, ST, ts):
    if hasattr(ep, "SCREEN"):                           # v3 episodes: the iPhone screen itself, as large as the box allows
        box_w, box_h = DEV_BOX[2] - DEV_BOX[0], DEV_BOX[3] - DEV_BOX[1]
        c = SL.grad(box_w, box_h, (30, 34, 70), (70, 36, 110))
        scr = ep.SCREEN(ts, ST); s = (box_h - 40) / scr.height; w = int(scr.width * s)
        scr = scr.resize((w, box_h - 40), Image.LANCZOS)
        m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, scr.height - 1), int(52 * s), fill=255)
        x0 = (box_w - w) // 2
        SL.rr(c, (x0 - 8, 12, x0 + w + 8, box_h - 12), int(58 * s), (30, 30, 34), outline=(110, 110, 120), width=3)
        c.paste(scr, (x0, 20), m)
        return c
    c = SL.BG.copy()
    ep.draw_body(c, ts, ST)
    return c.crop(CROP).resize((DEV_BOX[2] - DEV_BOX[0], DEV_BOX[3] - DEV_BOX[1]), Image.LANCZOS)

def device(c, ep, ST, P, t):
    ts = None
    for (s, e, a, b, _) in P.steps:
        if s <= t < e: ts = a + (b - a) * clamp((t - s) / ((e - s) * 0.85))
    if ts is None:
        ts = P.steps[0][2] if t < P.steps[0][0] else P.steps[-1][3]
    im = short_canvas(ep, ST, ts)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 36, fill=255)
    SL.shadow(c, DEV_BOX, 36, blur=24, off=14, a=150)
    c.paste(im, DEV_BOX[:2], m)

def header(c, ep, P, t):
    tag = f"{ep.SERIES['title']}{CIRCLED[ep.NUM - 1]}"
    f = font(34); w = f.getlength(tag) + 56
    rr(c, (70, 46, 70 + w, 106), 30, YEL)
    txt(c, (70 + w / 2, 76), tag, 34, INK, anchor="mm")
    txt(c, (100 + w, 76), ep.PART["title"], 46, WHITE, anchor="lm", stroke=4)

def panel(c, ep, P, t, L):
    x0, x1 = PANEL_X, W - 70
    if t < P.steps[0][0]:                                # title card
        p = e_at(t, 0.2, 0.5)
        txt(c, (x0, 300), "今日のワザ", 40, (200, 200, 230), anchor="lm")
        for i, s in enumerate(SL.bwrap(ep.PART["title"], font(76), x1 - x0)[:3]):
            txt(c, (x0, 400 + i * 100), s, 76, YEL, anchor="lm", stroke=6)
        if p > 0 and getattr(ep, "CTA", None):
            SL.rra(c, (x0, 720, x0 + font(36).getlength(ep.CTA["chip"]) + 60, 784), 32, (255, 255, 255, 40))
            txt(c, (x0 + 30, 752), ep.CTA["chip"], 36, WHITE, anchor="lm")
        return
    if t >= P.outro:                                     # summary card
        txt(c, (x0, 260), "まとめ", 44, (200, 200, 230), anchor="lm")
        y = 340
        for s, col, size in ep.CTA["lines"]:
            txt(c, (x0, y), s, min(78, size - 20), col, anchor="lm", stroke=6); y += min(78, size - 20) + 34
        rra(c, (x0, y + 30, x1, y + 130), 24, (255, 255, 255, 30))
        txt(c, (x0 + 30, y + 80), "保存して、あとで試してね！", 40, WHITE, anchor="lm")
        return
    y = 190
    for i, (s, e, a, b, label) in enumerate(P.steps):
        cur = s <= t < e; done = t >= e
        h = 104
        if cur: rr(c, (x0 - 10, y, x1, y + h - 14), 22, (255, 214, 10))
        else: rra(c, (x0 - 10, y, x1, y + h - 14), 22, (255, 255, 255, 34 if done else 18))
        col = INK if cur else (WHITE if done else (190, 190, 210))
        txt(c, (x0 + 20, y + 45), f"STEP {i + 1}", 26, col, anchor="lm")
        lab = label
        while font(36).getlength(lab) > x1 - x0 - 210 and len(lab) > 2: lab = lab[:-2] + "…"
        txt(c, (x0 + 150, y + 45), lab, 36, col, anchor="lm")
        if done: SL.check(c, x1 - 60, y + 26, 34, GREEN, 6)
        y += h
    # subtitle of the current line
    for k, at in P.at.items():
        if k.startswith("s") and at <= t < at + P.durs[k] + 0.6:
            box = (x0 - 10, 860, x1, 1030)
            rra(c, box, 24, (0, 0, 0, 120))
            for j, s in enumerate(SL.bwrap(L[k], font(38, False), x1 - x0 - 50)[:3]):
                txt(c, (x0 + 15, 895 + j * 50), s, 38, WHITE, bold=False, anchor="lm")

def frame(ep, ST, P, L, t):
    c = BG.copy()
    header(c, ep, P, t)
    device(c, ep, ST, P, t)
    panel(c, ep, P, t, L)
    for (s, *_rest) in P.steps + [(P.outro,)]:
        if s <= t < s + 0.12:
            c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(90 * (1 - (t - s) / 0.12)))))
    if t < 0.4: c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - t / 0.4)))))
    if P.total - t < 0.5: c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(1 - (P.total - t) / 0.5)))))
    ImageDraw.Draw(c).rectangle((0, H - 8, int(W * t / P.total), H), fill=YEL + (255,))
    return c.convert("RGB")

# ---------------------------------------------------------------- audio
def make_audio(path, ep, P, workdir):
    sr = SL.SR; n = int(sr * P.total)
    voice = np.zeros(n); fx = np.zeros(n)
    for k, at in P.at.items():
        with wave.open(os.path.join(workdir, "vo", f"{k}.wav")) as w:
            v = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
        s = int(at * sr); e = min(n, s + len(v)); voice[s:e] += v[: e - s]
    x = np.arange(int(0.12 * sr)) / sr
    pop = np.sin(2 * np.pi * (900 + 600 * np.exp(-x * 60)) * x) * np.exp(-x * 40)
    for s, *_ in P.steps + [(P.outro,)]:
        i = int(s * sr); fx[i:i + len(pop)] += pop[: max(0, min(len(pop), n - i))] * 0.25
    win = int(0.15 * sr)
    mask = np.convolve((np.abs(voice) > 0.01).astype(float), np.ones(win) / win, mode="same")
    music = SL.bgm(n, seed=ep.NUM + 50) * (1 - 0.62 * np.clip(mask * 4, 0, 1))[:, None] * 0.75
    mix = music + (fx + voice * 1.1)[:, None]
    t = np.arange(n) / sr
    mix *= np.clip(t / 0.4, 0, 1)[:, None] * np.clip((P.total - t) / 0.8, 0, 1)[:, None]
    pcm = (np.tanh(mix * 1.2) * 0.88 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- runner
def prepare(path):
    ep = SL.load_episode(path)
    if not hasattr(ep, "PART"): raise SystemExit(f"{path} has no PART definition")
    ep.telop = ep.badge = lambda *a, **k: None           # the part has its own captions
    name = SL.out_name(ep)
    swd = os.path.join(SL.CACHE, name)                   # the Short's narration (for its timeline)
    os.makedirs(swd, exist_ok=True)
    SL.TOTAL = getattr(ep, "DURATION", SL.DEFAULT_TOTAL)
    ST = SL.build_timeline(ep, SL.load_durs(ep, swd))
    wd = os.path.join(SL.CACHE, name + "_part"); os.makedirs(wd, exist_ok=True)
    durs = tts(ep, wd)
    P = timeline(ep, durs, ST); P.durs = durs
    return ep, ST, P, lines(ep), wd, name

def render(path, out=None, mode="render"):
    ep, ST, P, L, wd, name = prepare(path)
    print(f"part length {P.total:.1f}s", "(target 55-65s)" if not 50 <= P.total <= 70 else "")
    if mode == "stills":
        ts = [1.5] + [(s + e) / 2 for s, e, *_ in P.steps] + [P.outro + 1.2]
        ims = [frame(ep, ST, P, L, x).resize((640, 360)) for x in ts]
        sheet = Image.new("RGB", (640 * 4, 360 * ((len(ims) + 3) // 4)))
        for k, im in enumerate(ims): sheet.paste(im, ((k % 4) * 640, (k // 4) * 360))
        p = os.path.join(SL.OUT_DIR, name + "_part_sheet.png"); sheet.save(p); print("sheet:", p); return p
    make_audio(os.path.join(wd, "audio.wav"), ep, P, wd)
    out = out or os.path.join(SL.OUT_DIR, name + "_part.mp4")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", os.path.join(wd, "audio.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for k in range(int(P.total * FPS)): p.stdin.write(frame(ep, ST, P, L, k / FPS).tobytes())
    p.stdin.close(); p.wait()
    json.dump({"episode": os.path.relpath(os.path.abspath(path), SL.ROOT), "title": ep.PART["title"], "length": round(P.total, 2)},
              open(os.path.splitext(out)[0] + ".json", "w"), ensure_ascii=False)
    print("part:", out)
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    out = a[a.index("--out") + 1] if "--out" in a else None
    render(a[0], out, a[1] if len(a) > 1 else "render")
