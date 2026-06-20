import { useState } from "react";

function statTile(label, value, tone = "neutral") {
  return (
    <div className={`intel-stat ${tone}`} key={label}>
      <span className="intel-stat-label">{label}</span>
      <strong className="intel-stat-value">{value}</strong>
    </div>
  );
}

export default function ZoneIntelPanel({ zone, forecast }) {
  const [showRaw, setShowRaw] = useState(false);

  if (!zone || !forecast) {
    return (
      <section className="panel panel-intel">
        <header className="panel-head">
          <h3>Zone Detail</h3>
          <span className="panel-tag">Awaiting selection</span>
        </header>
        <p className="panel-copy">
          Select a hotspot to open the zone intelligence panel with congestion projection and dispatch recommendations.
        </p>
      </section>
    );
  }

  return (
    <section className="panel panel-intel">
      <header className="panel-head">
        <h3>{zone.name}</h3>
        <span className={`priority-pill ${zone.tier.toLowerCase()}`}>{`${zone.tier} ${zone.priority_score}`}</span>
      </header>

      <div className="intel-grid">
        {statTile("Congestion Impact Score", zone.cis, zone.tier.toLowerCase())}
        {statTile("Fuse to Breakdown", `${zone.minutes_to_breakdown} min`, zone.tier.toLowerCase())}
        {statTile("Lane Block", `${zone.lane_block_pct}%`, "amber")}
        {statTile("Active Violations", zone.violation_count, "red")}
      </div>

      <div className="forecast-strip">
        <span>
          Speed trend: <strong>{forecast.speed_now_kmph} km/h</strong> to{" "}
          <strong>{forecast.speed_forecast_kmph} km/h</strong>
        </span>
        <span>
          Queue forecast: <strong>{forecast.queue_forecast_m} m</strong>
        </span>
        <span>
          Spillback: <strong>{forecast.spillback_risk}</strong>
        </span>
      </div>

      <div className="patrol-suggestions">
        {zone.suggested_patrols.map((patrol) => (
          <button type="button" key={patrol.route_id} className="patrol-chip">
            <span>{patrol.beat_code}</span>
            <span>{`ETA ${patrol.eta_min}m`}</span>
            <span>{`+${patrol.impact_recovery_pct}% flow`}</span>
          </button>
        ))}
      </div>

      <div className="debug-row">
        <button type="button" className="ghost-btn" onClick={() => setShowRaw((value) => !value)}>
          {showRaw ? "Hide raw payload" : "Show raw payload"}
        </button>
      </div>
      {showRaw ? (
        <pre className="raw-json">
          {JSON.stringify(
            {
              zone: {
                id: zone.id,
                name: zone.name,
                tier: zone.tier,
                priority_score: zone.priority_score,
                cis: zone.cis,
                score_breakdown: zone.score_breakdown,
              },
              forecast,
            },
            null,
            2
          )}
        </pre>
      ) : null}
    </section>
  );
}
