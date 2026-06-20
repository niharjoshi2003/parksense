import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet.heat";

const TILE_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

export default function CommandMap({
  zones,
  topHotspotIds,
  selectedZoneId,
  hoveredZoneId,
  cityPressure,
  onZoneSelect,
}) {
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef(new Map());
  const heatLayerRef = useRef(null);
  const fitCompletedRef = useRef(false);
  const heatBaseRef = useRef([]);
  const pulseIntervalRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    const map = L.map(mapContainerRef.current, {
      center: [12.9716, 77.6205],
      zoom: 11,
      minZoom: 10,
      maxZoom: 15,
      attributionControl: false,
      zoomControl: false,
      preferCanvas: true,
    });

    L.tileLayer(TILE_URL, {
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    L.control
      .zoom({
        position: "topright",
      })
      .addTo(map);

    mapRef.current = map;

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current.clear();
      if (pulseIntervalRef.current) {
        window.clearInterval(pulseIntervalRef.current);
      }
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || !zones?.length) {
      return;
    }

    const map = mapRef.current;
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current.clear();
    const boundsPoints = [];

    zones.forEach((zone) => {
      const markerClassName = [
        "zone-marker",
        `tier-${zone.tier.toLowerCase()}`,
        topHotspotIds.includes(zone.id) ? "pulse-hotspot" : "",
        selectedZoneId === zone.id ? "selected" : "",
        hoveredZoneId === zone.id ? "hovered" : "",
      ]
        .filter(Boolean)
        .join(" ");

      const marker = L.marker([zone.lat, zone.lng], {
        icon: L.divIcon({
          className: markerClassName,
          html: `
        <span class="zone-dot"></span>
        <span class="zone-label">${zone.priority_score.toFixed(0)}</span>
      `,
          iconSize: [42, 42],
          iconAnchor: [21, 21],
        }),
      });

      marker.on("click", () => onZoneSelect(zone.id));
      marker.addTo(map);
      markersRef.current.set(zone.id, marker);
      boundsPoints.push([zone.lat, zone.lng]);
    });

    if (!heatLayerRef.current) {
      heatLayerRef.current = L.heatLayer([], {
        radius: 34,
        blur: 24,
        maxZoom: 14,
        minOpacity: 0.3,
        gradient: {
          0.22: "#3B82F6",
          0.45: "#F59E0B",
          0.82: "#EF4444",
        },
      }).addTo(map);
    }

    heatBaseRef.current = zones.map((zone) => {
      const urgencyBoost = topHotspotIds.includes(zone.id) ? 0.22 : 0;
      const baseIntensity = Math.min(1, zone.priority_score / 100 + urgencyBoost + 0.2);
      return [zone.lat, zone.lng, baseIntensity];
    });
    heatLayerRef.current.setLatLngs(heatBaseRef.current);

    if (!fitCompletedRef.current && boundsPoints.length) {
      map.fitBounds(boundsPoints, {
        padding: [44, 44],
        maxZoom: 12,
      });
      fitCompletedRef.current = true;
    }

    if (pulseIntervalRef.current) {
      window.clearInterval(pulseIntervalRef.current);
    }
    let phase = 0;
    pulseIntervalRef.current = window.setInterval(() => {
      if (!heatLayerRef.current) {
        return;
      }
      phase += 0.45;
      const pulsed = heatBaseRef.current.map((point, index) => [
        point[0],
        point[1],
        Math.max(0.18, Math.min(1, point[2] * (0.86 + Math.sin(phase + index * 0.4) * 0.16))),
      ]);
      heatLayerRef.current.setLatLngs(pulsed);
    }, 820);
  }, [zones, selectedZoneId, hoveredZoneId, topHotspotIds, onZoneSelect]);

  useEffect(() => {
    if (!mapRef.current || !selectedZoneId || !zones?.length) {
      return;
    }
    const selected = zones.find((zone) => zone.id === selectedZoneId);
    if (!selected) {
      return;
    }
    mapRef.current.flyTo([selected.lat, selected.lng], 12.2, {
      animate: true,
      duration: 0.8,
    });
  }, [selectedZoneId, zones]);

  const pressureValue = Math.round(cityPressure || 0);
  const criticalPressure = pressureValue >= 75;

  return (
    <section className="panel panel-map animate-map" style={{ "--enter-delay": "400ms" }}>
      <header className="panel-head">
        <h3>Hotspot Map</h3>
        <span className="panel-tag">Live heatmap</span>
      </header>
      <div className="map-shell">
        <div ref={mapContainerRef} className="map-canvas" />
        <aside className={`gridlock-fuse ${criticalPressure ? "critical" : ""}`}>
          <div className="fuse-ring" style={{ "--fuse-angle": `${Math.round((pressureValue / 100) * 360)}deg` }}>
            <span>{pressureValue}%</span>
          </div>
          <div className="fuse-copy">
            <strong>City Congestion Load</strong>
            <small>{criticalPressure ? "High load" : "Within normal range"}</small>
          </div>
        </aside>
      </div>
      <footer className="map-legend">
        <span className="legend-item">
          <i className="legend-dot tier-red-dot" />
          Red: dispatch now
        </span>
        <span className="legend-item">
          <i className="legend-dot tier-amber-dot" />
          Amber: pre-emptive sweep
        </span>
        <span className="legend-item">
          <i className="legend-dot tier-green-dot" />
          Green: monitored
        </span>
      </footer>
    </section>
  );
}
