export default function AIBriefing({ zone }) {
  if (!zone) {
    return (
      <section className="panel panel-briefing">
        <header className="panel-head">
          <h3>Automated Situation Report</h3>
          <span className="panel-tag">No zone selected</span>
        </header>
      </section>
    );
  }

  return (
    <section className="panel panel-briefing">
      <header className="panel-head">
        <h3>Automated Situation Report</h3>
        <span className="panel-tag">{`Confidence ${Math.round(zone.confidence * 100)}%`}</span>
      </header>
      <p className="briefing-copy">{zone.ai_insight}</p>
      <p className="briefing-note">
        Generated using {zone.insight_source || "deterministic-rule-engine"} (no LLM text generation).
      </p>
      <div className="briefing-footer">
        <span>{`Beat lead: ${zone.suggested_patrols[0].beat_code}`}</span>
        <span>{`ETA ${zone.suggested_patrols[0].eta_min} min`}</span>
        <span>{`Projected recovery +${zone.suggested_patrols[0].impact_recovery_pct}%`}</span>
      </div>
    </section>
  );
}
