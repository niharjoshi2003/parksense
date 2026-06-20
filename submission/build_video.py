"""
Builds ParkSense-Demo-NoVoice.mp4 : a SILENT ~4:15 video the user narrates over.

Structure (durations are fixed to match SPEAK_SCRIPT.txt timecodes):
  intro cards (hook / problem / why)  ->  live recorded demo with subtle
  lower-third labels  ->  outro card.

No audio track is added; record your own voice and drop it on top in any editor.
"""
import os, sys, glob, time
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "_video_work")
os.makedirs(WORK, exist_ok=True)
OUT = os.path.join(HERE, "ParkSense-Demo-NoVoice.mp4")
URL = "http://localhost:5173"
W, H = 1920, 1080

# ---- palette
NAVY = (11, 16, 32)
PANEL = (18, 25, 46)
WHITE = (242, 244, 248)
MUTE = (154, 166, 192)
YELLOW = (255, 194, 0)
BLUE = (45, 135, 240)

# Fixed scene durations (seconds) -> total 255s = 4:15. Matches SPEAK_SCRIPT.txt.
#       0   1   2   3   4   5   6   7   8   9
DUR = [15, 30, 25, 25, 30, 25, 20, 30, 25, 30]
DEMO_START, DEMO_END = 3, 8            # live demo covers scenes 3..8
DEMO_LEN = sum(DUR[DEMO_START:DEMO_END + 1])   # 155s

DEMO_LABELS = [
    "Live hotspot map + priority queue",
    "Congestion Impact Score  ·  0 to 100",
    "Click the top red zone  ->  situation report",
    "Show raw payload  ·  every score is visible",
    "Drag time: 6 PM red  ->  midnight green",
    "One-click dispatch  ->  minutes saved",
]


def font(size, bold=True):
    for name in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def base_card():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 12], fill=YELLOW)
    return img, d


def kicker(d, label, color=YELLOW):
    d.rectangle([120, 110, 138, 168], fill=color)
    d.text((164, 120), label.upper(), font=font(30), fill=MUTE)


def save(img, name):
    p = os.path.join(WORK, name)
    img.save(p)
    return p


def card_title():
    img, d = base_card()
    d.text((120, 360), "ParkSense", font=font(150), fill=WHITE)
    d.text((128, 545), "AI parking enforcement intelligence for Bengaluru", font=font(52), fill=YELLOW)
    d.text((130, 640), "From reactive patrols to data-ranked enforcement.", font=font(38, False), fill=MUTE)
    d.text((130, 820), "Gridlock Hackathon 2.0  ·  Theme: parking-induced congestion", font=font(30, False), fill=MUTE)
    return save(img, "card_title.png")


def card_problem():
    img, d = base_card()
    kicker(d, "The problem")
    d.text((120, 230), "Parking chaos is choking our roads", font=font(78), fill=WHITE)
    bullets = [
        ("Cars block the road.", "Illegal & double parking squeeze traffic into fewer lanes."),
        ("Patrols are guesswork.", "No live map of which spots hurt traffic the most."),
        ("Every zone looks equal.", "So the worst jams keep coming back, day after day."),
    ]
    y = 420
    for head, body in bullets:
        d.ellipse([120, y + 18, 150, y + 48], fill=YELLOW)
        d.text((180, y), head, font=font(46), fill=WHITE)
        d.text((180, y + 64), body, font=font(34, False), fill=MUTE)
        y += 165
    return save(img, "card_problem.png")


def card_insight():
    img, d = base_card()
    kicker(d, "Why we built it")
    d.text((120, 230), "Not every wrong-parked car matters the same", font=font(64), fill=WHITE)
    for i, line in enumerate(["A car on a busy main road at 6 PM is a big problem.",
                              "The same car on a quiet street at midnight is not."]):
        d.text((120, 410 + i * 70), line, font=font(44, False), fill=WHITE)
    d.rectangle([120, 620, 1800, 820], fill=PANEL)
    d.text((160, 678), "So we don't count cars —", font=font(50), fill=YELLOW)
    d.text((160, 740), "we measure how much each spot hurts traffic flow.", font=font(50), fill=WHITE)
    return save(img, "card_insight.png")


def card_outro():
    img, d = base_card()
    d.rectangle([0, H - 12, W, H], fill=YELLOW)
    kicker(d, "What's under the hood")
    d.text((120, 250), "Built to make enforcement smart", font=font(72), fill=WHITE)
    for i, line in enumerate([
        "Python + FastAPI engine computes every score live.",
        "React + Leaflet dashboard with a real-time heatmap.",
        "Rule-based briefings — explainable every single time.",
    ]):
        d.ellipse([120, 430 + i * 95 + 12, 148, 430 + i * 95 + 40], fill=YELLOW)
        d.text((180, 430 + i * 95), line, font=font(38, False), fill=WHITE)
    d.text((120, 800), "ParkSense — fixing the right zones, at the right time.", font=font(40), fill=YELLOW)
    return save(img, "card_outro.png")


LT_POS = (70, 950)


def lower_third(text):
    """Small transparent PNG strip (label), positioned later via with_position."""
    fnt = font(38)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = int(probe.textlength(text, font=fnt))
    sw, sh = tw + 150, 78
    img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, sw, sh], fill=(11, 16, 32, 225))
    d.rectangle([0, 0, 12, sh], fill=YELLOW + (255,))
    d.text((40, 18), text, font=fnt, fill=WHITE + (255,))
    safe = "".join(c if c.isalnum() else "_" for c in text)[:24]
    return save(img, f"lt_{safe}.png")


# ---------------------------------------------------------------- live demo
def record_demo():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=WORK,
            record_video_size={"width": W, "height": H},
        )
        page = ctx.new_page()
        t0 = time.time()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_selector("table.rank-table tbody tr", timeout=30000)
        page.wait_for_timeout(1200)
        ready_offset = time.time() - t0

        def hold(until):
            while time.time() < until:
                page.wait_for_timeout(50)

        # scene 3 — overview: slow mouse sweep map -> queue
        end = time.time() + DUR[3]
        for x in range(280, 1600, 45):
            page.mouse.move(x, 470)
            page.wait_for_timeout(45)
        hold(end)

        # scene 4 — score: hover the top rows slowly
        end = time.time() + DUR[4]
        rows = page.query_selector_all("table.rank-table tbody tr")
        for r in rows[:4]:
            try:
                r.hover()
            except Exception:
                pass
            page.wait_for_timeout(500)
        hold(end)

        # scene 5 — situation report: click top zone
        end = time.time() + DUR[5]
        try:
            rows[0].click()
        except Exception:
            pass
        page.wait_for_timeout(700)
        hold(end)

        # scene 6 — transparency: show raw payload + scroll
        end = time.time() + DUR[6]
        try:
            page.get_by_text("Show raw payload", exact=False).first.click()
            page.wait_for_timeout(600)
            page.mouse.move(1500, 600)
            page.mouse.wheel(0, 500)
        except Exception:
            pass
        hold(end)

        # scene 7 — time slider: step 18 -> 0
        end = time.time() + DUR[7]
        slider = page.query_selector("input.time-slider")
        steps = 18
        per = max(0.05, (DUR[7] - 1.0) / steps)
        if slider:
            slider.click()
            for _ in range(steps):
                page.keyboard.press("ArrowLeft")
                page.wait_for_timeout(int(per * 1000))
        hold(end)

        # scene 8 — dispatch: back to peak, dispatch top red zone
        end = time.time() + DUR[8]
        try:
            page.get_by_role("button", name="18").click()
            page.wait_for_selector("button.dispatch-btn", timeout=8000)
            page.wait_for_timeout(700)
            page.query_selector("button.dispatch-btn").click()
        except Exception:
            pass
        page.wait_for_timeout(1800)
        hold(end)

        page.wait_for_timeout(400)
        path = page.video.path()
        ctx.close()
        browser.close()
    return path, ready_offset


# ---------------------------------------------------------------- assemble
def assemble(intro_cards, outro_card, demo_path, ready_offset):
    from moviepy import ImageClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips

    clips = []
    for idx, cp in zip([0, 1, 2], intro_cards):
        clips.append(ImageClip(cp).with_duration(DUR[idx]))

    demo = VideoFileClip(demo_path)
    start = min(ready_offset, max(0, demo.duration - DEMO_LEN))
    demo = demo.subclipped(start, min(demo.duration, start + DEMO_LEN)).resized((W, H))

    overlays = []
    off = 0.0
    for i, label in enumerate(DEMO_LABELS):
        d = DUR[DEMO_START + i]
        png = lower_third(label)
        overlays.append(
            ImageClip(png, transparent=True)
            .with_start(off).with_duration(d).with_position(LT_POS)
        )
        off += d
    demo = CompositeVideoClip([demo] + overlays)
    clips.append(demo)

    clips.append(ImageClip(outro_card).with_duration(DUR[9]))

    video = concatenate_videoclips(clips, method="chain")
    video.write_videofile(OUT, fps=30, codec="libx264", audio=False, threads=4, preset="veryfast")


if __name__ == "__main__":
    print("1/3 cards...")
    intro = [card_title(), card_problem(), card_insight()]
    outro = card_outro()

    if "--reuse" in sys.argv:
        webms = sorted(glob.glob(os.path.join(WORK, "*.webm")), key=os.path.getmtime)
        demo_path, ready_offset = webms[-1], 6.0
        print("2/3 reusing existing demo:", os.path.basename(demo_path))
    else:
        print(f"2/3 recording live demo (~{DEMO_LEN}s)...")
        demo_path, ready_offset = record_demo()
        print("   demo recorded:", demo_path, "ready_offset", round(ready_offset, 1))

    print("3/3 assembling (silent)...")
    assemble(intro, outro, demo_path, ready_offset)
    print("DONE ->", OUT)
