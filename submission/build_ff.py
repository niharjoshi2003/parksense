"""
Fast assembler using ffmpeg directly (no per-frame Python compositing).
Reuses the recorded webm in _video_work, builds card segments + a demo segment
with burned-in lower-third labels, then concatenates into the silent MP4.
"""
import os, glob, subprocess
import imageio_ffmpeg
import build_video as bv

FF = imageio_ffmpeg.get_ffmpeg_exe()
WORK = bv.WORK
OUT = os.path.join(bv.HERE, "ParkSense-Demo-NoVoice.mp4")
W, H = bv.W, bv.H
DUR = bv.DUR
START = 6.0  # trim offset into the webm (after page load)
LT_X, LT_Y = 70, 950


def run(args):
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error"] + args, check=True)


def card_segment(png, dur, out):
    run(["-loop", "1", "-t", f"{dur}", "-i", png,
         "-vf", f"scale={W}:{H},setsar=1,fps=30,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-r", "30", out])


def demo_segment(webm, lts, out):
    demo_len = sum(DUR[bv.DEMO_START:bv.DEMO_END + 1])
    inputs = ["-ss", f"{START}", "-t", f"{demo_len}", "-i", webm]
    for _, png in lts:
        inputs += ["-i", png]
    fc = [f"[0:v]scale={W}:{H},setsar=1,fps=30[bg]"]
    prev = "bg"
    off = 0.0
    for i, (d, _png) in enumerate(lts):
        nxt = f"v{i}"
        fc.append(
            f"[{prev}][{i + 1}:v]overlay={LT_X}:{LT_Y}:enable='between(t,{off:.2f},{off + d:.2f})'[{nxt}]"
        )
        prev = nxt
        off += d
    filt = ";".join(fc)
    run(inputs + ["-filter_complex", filt, "-map", f"[{prev}]",
                  "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                  "-r", "30", out])


def main():
    print("assets...")
    title = bv.card_title()
    problem = bv.card_problem()
    insight = bv.card_insight()
    outro = bv.card_outro()
    lts = [(DUR[bv.DEMO_START + i], bv.lower_third(lbl)) for i, lbl in enumerate(bv.DEMO_LABELS)]

    webm = sorted(glob.glob(os.path.join(WORK, "*.webm")), key=os.path.getmtime)[-1]
    print("demo source:", os.path.basename(webm))

    segs = []
    for name, png, idx in [("seg0", title, 0), ("seg1", problem, 1), ("seg2", insight, 2)]:
        out = os.path.join(WORK, f"{name}.mp4")
        print("card", idx)
        card_segment(png, DUR[idx], out)
        segs.append(out)

    demo_out = os.path.join(WORK, "seg_demo.mp4")
    print("demo segment (with labels)...")
    demo_segment(webm, lts, demo_out)
    segs.append(demo_out)

    outro_out = os.path.join(WORK, "seg_outro.mp4")
    print("outro card")
    card_segment(outro, DUR[9], outro_out)
    segs.append(outro_out)

    listfile = os.path.join(WORK, "concat.txt")
    with open(listfile, "w") as f:
        for s in segs:
            f.write(f"file '{s.replace(os.sep, '/')}'\n")
    print("concat -> final...")
    run(["-f", "concat", "-safe", "0", "-i", listfile,
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", OUT])
    print("DONE ->", OUT)


if __name__ == "__main__":
    main()
