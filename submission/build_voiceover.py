"""Generates voiceover.wav from the narration sections using offline TTS (Windows SAPI)."""
import os, wave, tempfile
import pyttsx3

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "voiceover.wav")

SECTIONS = [
    "Every day, Bengaluru loses thousands of hours to traffic. And one big, invisible reason is parking. A few cars in the wrong place can turn a six-lane road into a crawl. So I built ParkSense.",
    "Here's the problem. Near markets, metro stations, and event venues, people park illegally or double-park. That squeezes traffic into fewer lanes and creates jams. Today, enforcement teams patrol almost blindly. They don't have a live map showing which spots are actually hurting traffic the most. And when every zone looks equally bad, it's impossible to know where to send a patrol first. So the worst jams keep coming back, day after day.",
    "My approach started with one simple insight: not every wrongly parked car matters the same. A car blocking a main road at six PM is a serious problem. The same car on a quiet street at midnight is not. So instead of just counting cars, I measure how much each spot is actually hurting traffic flow. That single idea became the heart of ParkSense.",
    "This is the ParkSense dashboard. On the left, a live map of Bengaluru shows parking hotspots as a heatmap. Red means act now, amber means keep an eye on it, and green means it's calm. On the right, every zone is ranked in a priority queue, so an officer instantly knows where to go first.",
    "Each hotspot gets a Congestion Impact Score, from zero to one hundred. It's built from five things: how many cars are parked illegally, the time of day, how important the road is, the risk of the jam spilling into junctions, and the history of repeat offenders. Together, these give one honest number for how badly a spot is hurting traffic.",
    "Let me click on our top red zone. Instantly, ParkSense gives a plain-English situation report. It explains what's happening here, and which patrol to send. No jargon, no guesswork. Just a clear recommendation an officer can act on right away.",
    "And this isn't a black box. I can click show raw payload, and see the exact breakdown behind every score. Judges, officers, and engineers can all check how a number was reached. Everything is explainable.",
    "Now watch what happens when I move the time slider. At six PM, the city lights up red. But at midnight, most zones turn green. The model isn't just always red. It follows real demand, hour by hour.",
    "And here's the best part. With one click, I can dispatch a patrol. ParkSense updates the priority, and even estimates the commuter-minutes we just saved. That closes the gap between spotting a problem and actually fixing it.",
    "Under the hood, it's a Python and FastAPI engine computing the scores live, with a React and Leaflet dashboard. The data is reproducible, and the briefings come from a clear rule engine, so the results are explainable every single time. That's ParkSense. Turning everyday parking data into smart, targeted enforcement. Thanks for watching.",
]

PAUSE_SEC = 0.9

engine = pyttsx3.init()
voices = engine.getProperty("voices")
print("Available voices:")
for v in voices:
    print("  -", v.name)
# Prefer a clearer voice if present (Zira/Hazel/Aria), else default.
pref = None
for v in voices:
    n = v.name.lower()
    if any(k in n for k in ["zira", "hazel", "aria", "jenny"]):
        pref = v.id
        break
if pref:
    engine.setProperty("voice", pref)
engine.setProperty("rate", 150)
engine.setProperty("volume", 1.0)

tmpdir = tempfile.mkdtemp()
parts = []
for i, txt in enumerate(SECTIONS):
    p = os.path.join(tmpdir, f"s{i:02d}.wav")
    engine.save_to_file(txt, p)
    parts.append(p)
engine.runAndWait()

# Stitch with silence between sections.
with wave.open(parts[0], "rb") as w0:
    params = w0.getparams()
silence = b"\x00" * int(params.framerate * params.sampwidth * params.nchannels * PAUSE_SEC)

with wave.open(OUT, "wb") as out:
    out.setparams(params)
    for i, p in enumerate(parts):
        with wave.open(p, "rb") as w:
            out.writeframes(w.readframes(w.getnframes()))
        if i != len(parts) - 1:
            out.writeframes(silence)

with wave.open(OUT, "rb") as w:
    dur = w.getnframes() / w.getframerate()
print(f"Saved {OUT}  ({dur:.1f}s = {int(dur//60)}m {int(dur%60)}s)")
