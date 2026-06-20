export default function TimeFilter({ hour, onHourChange }) {
  return (
    <section className="panel panel-time">
      <header className="panel-head">
        <h3>Time Simulator</h3>
        <span className="panel-tag">{`${hour.toString().padStart(2, "0")}:00-${((hour + 1) % 24)
          .toString()
          .padStart(2, "0")}:00`}</span>
      </header>
      <p className="panel-copy">
        Move the hour to see how parking violations change congestion, queue length, and enforcement priority.
      </p>
      <input
        className="time-slider"
        type="range"
        min="0"
        max="23"
        step="1"
        value={hour}
        onChange={(event) => onHourChange(Number(event.target.value))}
      />
      <div className="time-markers">
        {[0, 6, 9, 12, 15, 18, 21, 23].map((marker) => (
          <button
            key={marker}
            type="button"
            className={`time-chip ${marker === hour ? "active" : ""}`}
            onClick={() => onHourChange(marker)}
          >
            {marker.toString().padStart(2, "0")}
          </button>
        ))}
      </div>
    </section>
  );
}
