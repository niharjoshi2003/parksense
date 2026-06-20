# ParkSense — Pitch Deck Outline (8–10 slides)

Use this as the skeleton for the Presentation upload and the demo video script.

---

### Slide 1 — Title
- **ParkSense — AI Parking Enforcement Intelligence for Bengaluru**
- Team name, Gridlock Hackathon 2.0, Theme: Poor Visibility on Parking-Induced Congestion
- One-line: *"From reactive patrols to data-ranked enforcement."*

### Slide 2 — The Problem
- On-street illegal/spillover parking chokes carriageways near commercial areas, metros, events.
- Today: enforcement is reactive & patrol-based; no heatmap of violations vs. congestion;
  hard to prioritize zones.
- (Use the theme card from the problem statement.)

### Slide 3 — The Insight
- Not all violations matter equally. A blocked lane on a critical corridor at rush hour ≠ a
  parked car on a quiet street at midnight.
- We need to **quantify traffic-flow impact**, not just count violations.

### Slide 4 — Solution Overview
- One screenshot: `02-full-dashboard.png`
- Live hotspot heatmap + Congestion Impact Score + Enforcement Priority Queue + Situation Report.

### Slide 5 — How CIS Works (the differentiator)
- Weighted score (0–100): violation pressure (0.42), temporal surge (0.22), road criticality
  (0.18), spillback risk (0.13), historical non-compliance (0.05).
- Priority = urgency (CIS) + patrol feasibility → Red / Amber / Green tiers.
- Emphasize: **fully explainable**, every component exposed in the UI (show `03-transparency...`).

### Slide 6 — It Reacts to Reality
- Two screenshots side by side: peak (`01-dashboard-peak-1800.png`) vs off-peak
  (`04-offpeak-green-zones.png`).
- Proves the model isn't "everything is always red" — it tracks real demand by hour.

### Slide 7 — Closing the Loop: Targeted Enforcement
- Priority queue → one-click Dispatch → estimated priority drop + commuter-minutes saved.
- CSV export for field teams; live WebSocket event feed for the control room.

### Slide 8 — Architecture & Tech
- FastAPI + WebSockets (CIS engine) ⇄ React + Vite + Leaflet (live heatmap).
- Seeded synthetic dataset modeling real Bengaluru hotspots; rule-based briefings (no black box).
- Simple architecture diagram: Data → CIS Engine → REST/WS API → Dashboard.

### Slide 9 — Impact & Roadmap
- Impact: prioritized enforcement, measurable congestion savings, transparent decisions.
- Roadmap: ingest real ANPR/camera feeds, optional LLM narratives, mobile app for field officers,
  integration with live traffic signal data.

### Slide 10 — Thank You / Demo
- Demo link, GitHub repo, team contacts.

---

## 60-second demo script (for the video)
1. "This is ParkSense at 6 PM peak. The map shows live illegal-parking hotspots, ranked by impact."
2. "Silk Board is our #1 red zone — Congestion Impact Score 95." (click it)
3. "The Situation Report tells the officer exactly what's happening and which patrol to send."
4. "And it's fully transparent — here's the raw score breakdown." (Show raw payload)
5. "Watch it react: at midnight, most zones go green." (drag time to 00:00)
6. "One click dispatches a patrol and estimates the commuter-minutes we just saved." (Dispatch)
7. "That's ParkSense — turning parking data into targeted enforcement."
