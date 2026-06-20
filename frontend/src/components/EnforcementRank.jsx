export default function EnforcementRank({
  rows,
  selectedZoneId,
  onZoneSelect,
  onZoneHover,
  onDispatch,
  onExport,
  className = "",
}) {
  return (
    <section className={`panel panel-rank ${className}`.trim()}>
      <header className="panel-head">
        <h3>Enforcement Priority Queue</h3>
        <div className="panel-head-actions">
          <button type="button" className="ghost-btn" onClick={onExport}>
            Export CSV
          </button>
          <span className="panel-tag">Sorted by priority</span>
        </div>
      </header>
      <div className="rank-table-wrap">
        <table className="rank-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Zone</th>
              <th>Priority</th>
              <th>CIS</th>
              <th>Response Time</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map((row, index) => (
              <tr
                key={row.id}
                className={`${row.tier.toLowerCase()} ${selectedZoneId === row.id ? "selected-row" : ""} ${
                  index === 0 ? "top-priority-row" : ""
                }`.trim()}
                onClick={() => onZoneSelect(row.id)}
                onMouseEnter={() => onZoneHover(row.id)}
                onMouseLeave={() => onZoneHover("")}
              >
                <td>{row.rank}</td>
                <td className="zone-name-cell">{row.name}</td>
                <td className="score-cell">{row.priority_score}</td>
                <td className="score-cell">{row.cis}</td>
                <td className="response-cell">{`${row.response_time_min} min`}</td>
                <td>
                  {row.tier === "RED" ? (
                    <button
                      type="button"
                      className="dispatch-btn"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDispatch(row);
                      }}
                    >
                      → Dispatch
                    </button>
                  ) : (
                    <span className="dispatch-placeholder">Monitoring</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
