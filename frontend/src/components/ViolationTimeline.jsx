export default function ViolationTimeline({ timeline, currentHour }) {
  return (
    <section className="panel panel-timeline">
      <header className="panel-head">
        <h3>24-Hour Congestion Trend</h3>
        <span className="panel-tag">CIS by hour</span>
      </header>

      <div className="timeline-graph">
        {timeline.map((point) => {
          const height = Math.max(18, Math.min(100, point.avg_cis));
          return (
            <div
              key={point.hour}
              className={`timeline-bar ${point.hour === currentHour ? "current" : ""}`}
              style={{ height: `${height}%` }}
              title={`${point.hour.toString().padStart(2, "0")}:00 | Avg CIS ${point.avg_cis} | Index ${point.violation_index}`}
            />
          );
        })}
      </div>

      <div className="timeline-labels">
        {[0, 6, 12, 18, 23].map((hour) => (
          <span key={hour}>{hour.toString().padStart(2, "0")}</span>
        ))}
      </div>
    </section>
  );
}
