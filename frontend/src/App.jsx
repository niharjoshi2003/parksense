import { useEffect, useMemo, useState } from "react";
import AIBriefing from "./components/AIBriefing";
import CommandMap from "./components/CommandMap";
import EnforcementRank from "./components/EnforcementRank";
import TimeFilter from "./components/TimeFilter";
import ViolationTimeline from "./components/ViolationTimeline";
import ZoneIntelPanel from "./components/ZoneIntelPanel";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function buildWsUrl(apiBase) {
  return `${apiBase.replace("http://", "ws://").replace("https://", "wss://")}/ws/live`;
}

export default function App() {
  const [hour, setHour] = useState(18);
  const [overview, setOverview] = useState(null);
  const [zoneDetail, setZoneDetail] = useState(null);
  const [selectedZoneId, setSelectedZoneId] = useState("");
  const [hoveredZoneId, setHoveredZoneId] = useState("");
  const [liveFeed, setLiveFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toastMessage, setToastMessage] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchOverview() {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_BASE}/api/v1/dashboard/overview?hour=${hour}`);
        if (!response.ok) {
          throw new Error("Could not load Bengaluru command overview.");
        }
        const data = await response.json();
        if (cancelled) {
          return;
        }
        setOverview(data);

        const preferredZone = data.top_hotspots[0];
        if (!selectedZoneId || !data.zones.some((zone) => zone.id === selectedZoneId)) {
          setSelectedZoneId(preferredZone);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || "Unable to reach backend.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchOverview();
    return () => {
      cancelled = true;
    };
  }, [hour, selectedZoneId]);

  useEffect(() => {
    if (!selectedZoneId) {
      return;
    }
    let cancelled = false;

    async function fetchZone() {
      try {
        const response = await fetch(`${API_BASE}/api/v1/zones/${selectedZoneId}?hour=${hour}`);
        if (!response.ok) {
          throw new Error("Could not load zone intelligence.");
        }
        const data = await response.json();
        if (!cancelled) {
          setZoneDetail(data);
        }
      } catch {
        if (!cancelled) {
          setZoneDetail(null);
        }
      }
    }

    fetchZone();
    return () => {
      cancelled = true;
    };
  }, [selectedZoneId, hour]);

  useEffect(() => {
    const ws = new WebSocket(buildWsUrl(API_BASE));
    ws.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data);
        setLiveFeed((previous) => [event, ...previous].slice(0, 4));
      } catch {
        // Ignore malformed event payload.
      }
    };
    return () => ws.close();
  }, []);

  const selectedZone = zoneDetail?.zone || null;
  const forecast = zoneDetail?.forecast || null;

  async function handleDispatch(row) {
    setToastMessage(`Dispatching ${row.best_patrol} to ${row.name}...`);
    try {
      const response = await fetch(`${API_BASE}/api/v1/enforcement/deploy?hour=${hour}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ zone_id: row.id, route_id: row.best_patrol_route_id }),
      });
      if (!response.ok) {
        throw new Error("Dispatch failed");
      }
      const result = await response.json();
      setToastMessage(
        `${result.beat_code} dispatched to ${result.zone_name}: priority ${result.before_priority} -> ${result.after_priority}, ~${result.estimated_person_delay_saved_min} commuter-min saved`
      );
    } catch {
      setToastMessage(`Unable to dispatch unit to ${row.name}`);
    }
  }

  function handleExportQueueCsv() {
    const rows = overview?.enforcement_rank || [];
    if (!rows.length) {
      setToastMessage("No rows available to export.");
      return;
    }

    const header = ["rank", "zone", "tier", "priority_score", "cis", "response_time_min", "best_patrol"];
    const records = rows.map((row) => [
      row.rank,
      row.name,
      row.tier,
      row.priority_score,
      row.cis,
      row.response_time_min,
      row.best_patrol,
    ]);

    const csv = [header, ...records]
      .map((record) => record.map((value) => `"${String(value).replaceAll("\"", "\"\"")}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", `parksense-priority-queue-${hour.toString().padStart(2, "0")}00.csv`);
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    setToastMessage("Priority queue exported as CSV.");
  }

  const topHeadline = useMemo(() => {
    if (!overview?.enforcement_rank?.length) {
      return "Loading Bengaluru parking risk picture...";
    }
    const top = overview.enforcement_rank[0];
    return `Immediate attention: ${top.name} (Priority ${top.priority_score})`;
  }, [overview]);

  const cityPressure = useMemo(() => {
    if (!overview?.zones?.length) {
      return 0;
    }
    const averageCis = overview.zones.reduce((sum, zone) => sum + zone.cis, 0) / overview.zones.length;
    return Math.round(averageCis);
  }, [overview]);

  const sparklineFromTimeline = useMemo(() => {
    const timeline = overview?.timeline || [];
    return (selector) => {
      if (!timeline.length) {
        return "20,18 40,14 60,16 80,10 100,12";
      }
      const values = timeline.map(selector);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const span = max - min || 1;
      return values
        .map((value, index) => {
          const x = (index / (values.length - 1)) * 100;
          const y = 24 - ((value - min) / span) * 20;
          return `${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ");
    };
  }, [overview]);

  const kpiCards = useMemo(
    () => [
      {
        key: "red",
        label: "Red Zones",
        value: overview?.kpis?.red_zones ?? "--",
        tone: "red",
        trend: sparklineFromTimeline((point) => point.avg_cis),
      },
      {
        key: "amber",
        label: "Amber Zones",
        value: overview?.kpis?.amber_zones ?? "--",
        tone: "amber",
        trend: sparklineFromTimeline((point) => point.violation_index),
      },
      {
        key: "green",
        label: "Green Zones",
        value: overview?.kpis?.green_zones ?? "--",
        tone: "green",
        trend: sparklineFromTimeline((point) => 100 - point.avg_cis),
      },
      {
        key: "delay",
        label: "Delay Prevented",
        value: `${overview?.kpis?.commuter_delay_prevented_min ?? "--"}`,
        suffix: "min",
        tone: "accent",
        trend: sparklineFromTimeline((point) => point.violation_index),
      },
    ],
    [overview, sparklineFromTimeline]
  );

  useEffect(() => {
    if (!toastMessage) {
      return;
    }
    const timeout = window.setTimeout(() => setToastMessage(""), 4200);
    return () => window.clearTimeout(timeout);
  }, [toastMessage]);

  useEffect(() => {
    const raf = window.requestAnimationFrame(() => setMounted(true));
    return () => window.cancelAnimationFrame(raf);
  }, []);

  if (error) {
    return (
      <main className={`dashboard-shell ${mounted ? "is-mounted" : ""}`.trim()}>
        <section className="panel error-panel">
          <h2>Backend link interrupted</h2>
          <p>{error}</p>
          <button type="button" onClick={() => window.location.reload()}>
            Retry connection
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className={`dashboard-shell ${mounted ? "is-mounted" : ""}`.trim()}>
      <header className="topbar animate-navbar" style={{ "--enter-delay": "0ms" }}>
        <div>
          <h1>ParkSense — Bengaluru Parking Enforcement Intelligence</h1>
          <p>{topHeadline}</p>
        </div>
        <div className="topbar-meta">
          <span className="live-badge">LIVE</span>
          <span>{`Window ${hour.toString().padStart(2, "0")}:00-${((hour + 1) % 24)
            .toString()
            .padStart(2, "0")}:00`}</span>
        </div>
      </header>

      <section className="kpi-row">
        {kpiCards.map((card, index) => (
          <article
            key={card.key}
            className={`kpi-card tone-${card.tone} animate-kpi`}
            style={{ "--enter-delay": `${100 + index * 100}ms` }}
          >
            <label>{card.label}</label>
            <strong>
              {card.value}
              {card.suffix ? <small>{card.suffix}</small> : null}
            </strong>
            <svg className="sparkline" viewBox="0 0 100 26" preserveAspectRatio="none" role="img" aria-label={`${card.label} trend`}>
              <polyline points={card.trend} />
            </svg>
          </article>
        ))}
      </section>

      <section className="content-grid">
        <div className="column-left animate-left-panel" style={{ "--enter-delay": "500ms" }}>
          <TimeFilter hour={hour} onHourChange={setHour} />
          <ViolationTimeline timeline={overview?.timeline || []} currentHour={hour} />
          <section className="panel panel-livefeed">
            <header className="panel-head">
              <h3>Live Event Feed</h3>
              <span className="panel-tag">WebSocket stream</span>
            </header>
            <ul className="feed-list">
              {liveFeed.map((event) => (
                <li key={`${event.timestamp}-${event.zone_id}`}>
                  <strong>{event.zone_name}</strong>
                  <span>{event.brief}</span>
                </li>
              ))}
              {!liveFeed.length && <li>Waiting for live updates from backend stream.</li>}
            </ul>
          </section>
        </div>

        <div className="column-center">
          <CommandMap
            zones={overview?.zones || []}
            topHotspotIds={overview?.top_hotspots || []}
            selectedZoneId={selectedZoneId}
            hoveredZoneId={hoveredZoneId}
            cityPressure={cityPressure}
            onZoneSelect={setSelectedZoneId}
          />
          <ZoneIntelPanel zone={selectedZone} forecast={forecast} />
        </div>

        <div className="column-right">
          <EnforcementRank
            rows={overview?.enforcement_rank || []}
            selectedZoneId={selectedZoneId}
            onZoneSelect={setSelectedZoneId}
            onZoneHover={setHoveredZoneId}
            onDispatch={handleDispatch}
            onExport={handleExportQueueCsv}
            className="animate-right-queue"
          />
          <AIBriefing zone={selectedZone} />
        </div>
      </section>

      {loading && <div className="loading-overlay">Updating congestion and priority scores...</div>}
      {toastMessage && <div className="toast-message">{toastMessage}</div>}
    </main>
  );
}
