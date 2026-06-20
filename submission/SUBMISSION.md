# HackerEarth Submission Draft — Gridlock Hackathon 2.0 (Round 2)

Copy each section into the matching field on the HackerEarth submission form.
Fields marked **(TODO)** need a link/file from you before publishing.

---

## 1. Title

```
ParkSense — AI Parking Enforcement Intelligence for Bengaluru
```

---

## 2. Description

```
If you've ever been stuck in traffic next to a road that's half-blocked by parked cars,
you already understand the problem ParkSense solves.

THE PROBLEM
Near markets, metro stations and event venues, people park illegally or double-park - and that
quietly chokes the whole road. The frustrating part is how enforcement works today: it's reactive,
patrol teams basically guess, and there's no simple view of which spots are actually hurting
traffic the most. So the same jams keep coming back, day after day.

WHAT WE BUILT
ParkSense is a live dashboard that spots these parking hotspots and shows how much each one is
really hurting traffic - so teams can fix the right zones, at the right time, instead of guessing.

Here's what it does:

- A live map of the city with parking hotspots as a heatmap. Red means act now, amber means keep
  an eye on it, green means it's calm.
- A Congestion Impact Score (0-100) for every hotspot. We don't just count cars - the score also
  factors in the time of day, how important the road is, the risk of the jam spilling into nearby
  junctions, and repeat offenders. One honest number for how bad a spot really is.
- A priority queue that ranks every zone by urgency and how reachable it is, with a one-click
  "Dispatch" that sends a patrol and estimates the commuter-minutes you just saved.
- A time slider so you can scrub through any hour. At 6 PM the city lights up red; by midnight it
  mostly goes green - proof that the model follows real demand instead of crying wolf.
- A plain-English situation report for each zone that says what's happening and which patrol to
  send. It's written by a clear rule engine, not a black box - so it's the same every time.
- Full transparency: one click on "Show raw payload" reveals the exact math behind every score,
  and you can export the whole queue to CSV.

WHY IT MATTERS
It does exactly what the theme asks: find the hotspots, measure their impact on traffic, and make
enforcement targeted. Every number is explainable, it all updates live, and the dispatch button
closes the gap between spotting a problem and actually doing something about it.

UNDER THE HOOD
A Python backend (FastAPI + WebSockets) does the scoring in real time, and a React + Leaflet
front-end draws the live map. The data is a reproducible, seeded dataset modeled on real Bengaluru
hotspots, so anyone can run it and get the same results.
```

---

## 3. Theme

```
Poor Visibility on Parking-Induced Congestion
```

---

## 4. Snapshots (upload these PNGs — all < 3MB)

Located in `parksense/submission/snapshots/`:

1. `01-dashboard-peak-1800.png` — main dashboard at evening peak
2. `02-full-dashboard.png` — full dashboard (map + priority queue + situation report)
3. `03-transparency-raw-payload.png` — explainable CIS score breakdown (raw payload)
4. `04-offpeak-green-zones.png` — off-peak hours showing the model reacting (green zones)

---

## 5. Video URL *(TODO)*

```
<paste your demo/pitch video link — YouTube/Drive (unlisted is fine)>
```
(We will script + record this together later.)

---

## 6. Presentation *(TODO)*

Upload the pitch deck (PDF/PPTX). Draft outline is in `parksense/submission/PITCH_OUTLINE.md`.

---

## 7. Demo Link *(TODO)*

```
<paste your live demo URL, or use http://localhost:5173 with the Instructions to Run below>
```

---

## 8. Repository URL *(TODO)*

```
<paste your GitHub repo URL after pushing>
```

---

## 9. Source Code

Upload `parksense-source.zip` (generated at the project root; excludes node_modules/dist).

---

## 10. Instructions to Run

```
PREREQUISITES
- Python 3.10+  and  Node.js 18+

1) BACKEND (terminal 1)
   cd parksense/backend
   pip install -r requirements.txt
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   # Verify: open http://127.0.0.1:8000/health  ->  {"status":"ok"}

2) FRONTEND (terminal 2)
   cd parksense/frontend
   npm install
   npm run dev
   # Open http://localhost:5173

Notes:
- The backend auto-generates the synthetic dataset on first run.
- If the backend runs on another host/port, set VITE_API_BASE before "npm run dev"
  (Windows: set VITE_API_BASE=http://127.0.0.1:8000).
```

---

## 11. Custom Attachment (optional)

You may also attach the pitch deck or a short architecture diagram here.
