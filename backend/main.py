from __future__ import annotations

import asyncio
import math
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data_generator import HOTSPOTS, load_or_generate_dataset


app = FastAPI(
    title="ParkSense Command API",
    version="1.0.0",
    description="Rule-based parking intelligence dashboard for Bengaluru parking enforcement.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "synthetic_violations.json"
VIOLATIONS = load_or_generate_dataset(DATA_PATH, row_count=1000, seed=72)

HOTSPOT_BY_ID = {h.id: h for h in HOTSPOTS}
CURRENT_SIM_HOUR = datetime.now(timezone.utc).hour

PATROL_ROUTES = [
    {"route_id": "route_b03", "beat_code": "B-03", "officer_count": 2, "lat": 12.9392, "lng": 77.6125},
    {"route_id": "route_b05", "beat_code": "B-05", "officer_count": 1, "lat": 12.9819, "lng": 77.6031},
    {"route_id": "route_b08", "beat_code": "B-08", "officer_count": 2, "lat": 12.9232, "lng": 77.6357},
    {"route_id": "route_b12", "beat_code": "B-12", "officer_count": 3, "lat": 12.9151, "lng": 77.6202},
    {"route_id": "route_b14", "beat_code": "B-14", "officer_count": 1, "lat": 13.0289, "lng": 77.5912},
    {"route_id": "route_b18", "beat_code": "B-18", "officer_count": 2, "lat": 12.9784, "lng": 77.7429},
    {"route_id": "route_b22", "beat_code": "B-22", "officer_count": 2, "lat": 12.8432, "lng": 77.6767},
]


class DeployRequest(BaseModel):
    zone_id: str = Field(..., description="Zone identifier")
    route_id: str = Field(..., description="Patrol route identifier")


class SimTickRequest(BaseModel):
    delta_hours: int = Field(default=1, ge=1, le=6)


def _hour_band(hour: int) -> str:
    return f"{hour:02d}:00-{(hour + 1) % 24:02d}:00"


def _demand_multiplier(hour: int) -> float:
    if 7 <= hour <= 11:
        return 1.18
    if 16 <= hour <= 21:
        return 1.42
    if 12 <= hour <= 15:
        return 0.88
    return 0.32


def _temporal_weight(captured_hour: int, selected_hour: int) -> float:
    diff = abs(captured_hour - selected_hour)
    wrapped_diff = min(diff, 24 - diff)
    return max(0.15, 1 - (wrapped_diff / 7.0))


def _normalize(value: float, floor: float = 0.0, ceil: float = 100.0) -> float:
    return max(floor, min(ceil, value))


def _zone_rows(zone_id: str) -> list[dict[str, Any]]:
    return [row for row in VIOLATIONS if row["zone_id"] == zone_id]


ZONE_HISTORY_SCORE: dict[str, float] = {}
for hotspot in HOTSPOTS:
    zone_rows = _zone_rows(hotspot.id)
    if not zone_rows:
        ZONE_HISTORY_SCORE[hotspot.id] = 45.0
        continue
    repeat_high_dwell = sum(1 for row in zone_rows if row["dwell_min"] >= 12.0)
    historical = (repeat_high_dwell / len(zone_rows)) * 100.0
    ZONE_HISTORY_SCORE[hotspot.id] = _normalize(historical)


def _distance_km(lat_a: float, lng_a: float, lat_b: float, lng_b: float) -> float:
    lat_scale = 111.0
    lng_scale = 103.0
    return math.sqrt(((lat_a - lat_b) * lat_scale) ** 2 + ((lng_a - lng_b) * lng_scale) ** 2)


def _top_patrol_suggestions(hotspot, hour: int, cis: float) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    traffic_penalty = (1.5 if 17 <= hour <= 21 else 0.7 if 8 <= hour <= 11 else 0.2)

    for route in PATROL_ROUTES:
        dist_km = _distance_km(hotspot.lat, hotspot.lng, route["lat"], route["lng"])
        base_eta = 3.0 + dist_km * 4.1 + traffic_penalty
        eta = int(round(base_eta))
        impact = int(
            _normalize(
                (route["officer_count"] * 7.5)
                + max(0.0, 22.0 - eta)
                + (cis / 3.6)
                - (dist_km * 2.6),
                8.0,
                52.0,
            )
        )
        suggestions.append(
            {
                "route_id": route["route_id"],
                "beat_code": route["beat_code"],
                "eta_min": eta,
                "impact_recovery_pct": impact,
            }
        )

    suggestions.sort(key=lambda item: (item["eta_min"], -item["impact_recovery_pct"]))
    return suggestions[:3]


def _spillback_label(score: float) -> str:
    if score >= 78:
        return "HIGH"
    if score >= 56:
        return "MEDIUM"
    return "LOW"


def _briefing_text(
    hotspot,
    selected_hour: int,
    violation_count: int,
    lane_block_pct: float,
    speed_now: float,
    speed_forecast: float,
    effective_lanes: float,
    best_patrol: dict[str, Any],
) -> str:
    window_start = max(0, selected_hour - 1)
    window_end = min(23, selected_hour + 1)
    recommend_hour = max(0, selected_hour - 1)
    unit_count = 2 if best_patrol["impact_recovery_pct"] >= 28 else 1
    return (
        f"{hotspot.name}: {violation_count} active violations around {hotspot.route_hint} "
        f"({window_start:02d}:00-{window_end:02d}:00). "
        f"Lane block is {lane_block_pct:.0f}%, reducing usable width from {hotspot.lane_count:.1f} to "
        f"{effective_lanes:.1f} lanes. "
        f"Speed is trending {speed_now:.0f} -> {speed_forecast:.0f} km/h. "
        f"Recommended response: deploy {unit_count} unit(s) via {best_patrol['beat_code']} at "
        f"{recommend_hour:02d}:45 (ETA {best_patrol['eta_min']} min), expected flow recovery "
        f"{best_patrol['impact_recovery_pct']}%."
    )


def _build_zone_snapshot(selected_hour: int) -> list[dict[str, Any]]:
    previous_hour = (selected_hour - 1) % 24
    snapshots: list[dict[str, Any]] = []

    for hotspot in HOTSPOTS:
        zone_rows = _zone_rows(hotspot.id)
        if not zone_rows:
            continue

        weighted_rows = []
        weighted_rows_prev = []
        for row in zone_rows:
            weight_now = _temporal_weight(row["captured_hour"], selected_hour)
            weighted_rows.append((row, weight_now))
            weight_prev = _temporal_weight(row["captured_hour"], previous_hour)
            weighted_rows_prev.append((row, weight_prev))

        total_weight = sum(weight for _, weight in weighted_rows)
        total_weight_prev = sum(weight for _, weight in weighted_rows_prev)
        weighted_count = total_weight * _demand_multiplier(selected_hour)
        weighted_count_prev = total_weight_prev * _demand_multiplier(previous_hour)

        lane_block_avg = (
            sum(row["lane_block_pct"] * weight for row, weight in weighted_rows) / max(total_weight, 0.01)
        )
        dwell_avg = sum(row["dwell_min"] * weight for row, weight in weighted_rows) / max(total_weight, 0.01)
        avg_confidence = (
            sum(row["confidence"] * weight for row, weight in weighted_rows) / max(total_weight, 0.01)
        )

        vehicle_counter = Counter()
        for row, weight in weighted_rows:
            bucket = row["vehicle_type"]
            vehicle_counter[bucket] += max(1, int(round(weight)))

        violation_pressure = _normalize(weighted_count * 1.15 + lane_block_avg * 0.48 + dwell_avg * 0.7)
        road_criticality = hotspot.road_criticality * 100.0
        temporal_surge = _normalize(_demand_multiplier(selected_hour) * 44.0 + weighted_count * 0.9)
        spillback_risk = _normalize(lane_block_avg * 0.95 + weighted_count * 1.35 + hotspot.adjacency_score * 16.0)
        historical_non_compliance = ZONE_HISTORY_SCORE[hotspot.id]

        cis = _normalize(
            0.42 * violation_pressure
            + 0.18 * road_criticality
            + 0.22 * temporal_surge
            + 0.13 * spillback_risk
            + 0.05 * historical_non_compliance
        )

        growth_rate = _normalize(((weighted_count - weighted_count_prev) / max(1.0, weighted_count_prev)) * 100.0)
        critical_asset_boost = 8.0 if hotspot.critical_asset else 0.0
        urgency = _normalize(0.7 * cis + 0.2 * growth_rate + 0.1 * critical_asset_boost)

        suggestions = _top_patrol_suggestions(hotspot, selected_hour, cis)
        best_suggestion = suggestions[0]
        active_assignment_penalty = 6.0 if selected_hour % 5 == 0 else 0.0
        feasibility = _normalize(
            100.0 - min(100.0, best_suggestion["eta_min"] * 5.0 + active_assignment_penalty)
        )
        priority_score = _normalize(0.75 * urgency + 0.25 * feasibility)

        if priority_score > 65:
            tier = "RED"
        elif priority_score >= 45:
            tier = "AMBER"
        else:
            tier = "GREEN"

        baseline_speed = _normalize(42.0 - hotspot.road_criticality * 14.0, 18.0, 42.0)
        speed_now = _normalize(baseline_speed - (lane_block_avg * 0.22) - (weighted_count * 0.09), 8.0, 45.0)
        speed_forecast = _normalize(speed_now - (growth_rate * 0.08) - (spillback_risk * 0.09), 5.0, 45.0)
        queue_forecast_m = int(round(_normalize(priority_score * 8.5 + spillback_risk * 4.3, 80, 950)))
        minutes_to_breakdown = int(round(_normalize(36.0 - (priority_score / 3.4) - (growth_rate / 9.5), 4.0, 42.0)))

        effective_lanes = _normalize(
            hotspot.lane_count - ((lane_block_avg / 100.0) * hotspot.lane_count * 0.9),
            0.8,
            hotspot.lane_count,
        )

        snapshots.append(
            {
                "id": hotspot.id,
                "name": hotspot.name,
                "lat": hotspot.lat,
                "lng": hotspot.lng,
                "tier": tier,
                "priority_score": round(priority_score, 1),
                "cis": round(cis, 1),
                "violation_count": int(round(weighted_count)),
                "lane_block_pct": round(lane_block_avg, 1),
                "dwell_min": round(dwell_avg, 1),
                "confidence": round(avg_confidence, 2),
                "growth_rate_15m": round(growth_rate, 1),
                "minutes_to_breakdown": minutes_to_breakdown,
                "speed_now_kmph": round(speed_now, 1),
                "speed_forecast_kmph": round(speed_forecast, 1),
                "queue_forecast_m": queue_forecast_m,
                "spillback_risk": _spillback_label(spillback_risk),
                "violations_by_vehicle": dict(vehicle_counter),
                "suggested_patrols": suggestions,
                "ai_insight": _briefing_text(
                    hotspot=hotspot,
                    selected_hour=selected_hour,
                    violation_count=int(round(weighted_count)),
                    lane_block_pct=lane_block_avg,
                    speed_now=speed_now,
                    speed_forecast=speed_forecast,
                    effective_lanes=effective_lanes,
                    best_patrol=best_suggestion,
                ),
                "insight_source": "deterministic-rule-engine",
                "score_breakdown": {
                    "violation_pressure": round(violation_pressure, 1),
                    "road_criticality": round(road_criticality, 1),
                    "temporal_surge": round(temporal_surge, 1),
                    "spillback_risk": round(spillback_risk, 1),
                    "historical_non_compliance": round(historical_non_compliance, 1),
                    "weighted_cis": {
                        "violation_pressure": 0.42,
                        "road_criticality": 0.18,
                        "temporal_surge": 0.22,
                        "spillback_risk": 0.13,
                        "historical_non_compliance": 0.05,
                    },
                    "urgency": round(urgency, 1),
                    "feasibility": round(feasibility, 1),
                },
            }
        )

    snapshots.sort(key=lambda item: item["priority_score"], reverse=True)
    if snapshots and all(zone["tier"] != "RED" for zone in snapshots):
        snapshots[0]["tier"] = "RED"
    return snapshots


def _city_timeline() -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for hour in range(24):
        zones = _build_zone_snapshot(hour)
        if not zones:
            timeline.append({"hour": hour, "avg_cis": 0.0, "violation_index": 0})
            continue
        avg_cis = sum(z["cis"] for z in zones) / len(zones)
        violation_index = int(round(sum(z["violation_count"] for z in zones) / len(zones)))
        timeline.append(
            {
                "hour": hour,
                "avg_cis": round(avg_cis, 1),
                "violation_index": violation_index,
            }
        )
    return timeline


def _overview_payload(selected_hour: int) -> dict[str, Any]:
    zones = _build_zone_snapshot(selected_hour)
    red = sum(1 for zone in zones if zone["tier"] == "RED")
    amber = sum(1 for zone in zones if zone["tier"] == "AMBER")
    green = sum(1 for zone in zones if zone["tier"] == "GREEN")
    prevented = int(
        round(
            sum(
                z["violation_count"]
                * (z["suggested_patrols"][0]["impact_recovery_pct"] / 100.0)
                * (z["cis"] / 100.0)
                * 6.5
                for z in zones
                if z["tier"] in ("RED", "AMBER")
            )
        )
    )
    top_hotspots = [zone["id"] for zone in zones[:3]]

    return {
        "meta": {
            "city": "Bengaluru",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "selected_hour": selected_hour,
            "hour_band": _hour_band(selected_hour),
        },
        "kpis": {
            "red_zones": red,
            "amber_zones": amber,
            "green_zones": green,
            "commuter_delay_prevented_min": prevented,
        },
        "top_hotspots": top_hotspots,
        "zones": zones,
        "enforcement_rank": [
            {
                "rank": idx + 1,
                "id": zone["id"],
                "name": zone["name"],
                "priority_score": zone["priority_score"],
                "tier": zone["tier"],
                "cis": zone["cis"],
                "minutes_to_breakdown": zone["minutes_to_breakdown"],
                "best_patrol": zone["suggested_patrols"][0]["beat_code"],
                "best_patrol_route_id": zone["suggested_patrols"][0]["route_id"],
                "response_time_min": zone["suggested_patrols"][0]["eta_min"],
            }
            for idx, zone in enumerate(zones)
        ],
        "timeline": _city_timeline(),
    }


def _selected_hour(hour: int | None) -> int:
    if hour is None:
        return CURRENT_SIM_HOUR
    return max(0, min(23, hour))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/dashboard/overview")
def dashboard_overview(hour: int | None = Query(default=None, ge=0, le=23)) -> dict[str, Any]:
    return _overview_payload(_selected_hour(hour))


@app.get("/api/v1/zones")
def list_zones(hour: int | None = Query(default=None, ge=0, le=23)) -> dict[str, Any]:
    selected_hour = _selected_hour(hour)
    zones = _build_zone_snapshot(selected_hour)
    return {"meta": {"selected_hour": selected_hour}, "zones": zones}


@app.get("/api/v1/zones/{zone_id}")
def zone_detail(zone_id: str, hour: int | None = Query(default=None, ge=0, le=23)) -> dict[str, Any]:
    selected_hour = _selected_hour(hour)
    zones = _build_zone_snapshot(selected_hour)
    zone = next((item for item in zones if item["id"] == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")

    return {
        "meta": {"selected_hour": selected_hour, "hour_band": _hour_band(selected_hour)},
        "zone": zone,
        "forecast": {
            "speed_now_kmph": zone["speed_now_kmph"],
            "speed_forecast_kmph": zone["speed_forecast_kmph"],
            "queue_forecast_m": zone["queue_forecast_m"],
            "spillback_risk": zone["spillback_risk"],
            "minutes_to_breakdown": zone["minutes_to_breakdown"],
        },
    }


@app.get("/api/v1/patrol-routes/live")
def patrol_routes_live(hour: int | None = Query(default=None, ge=0, le=23)) -> dict[str, Any]:
    selected_hour = _selected_hour(hour)
    availability_map = ["available", "en_route", "on_enforcement", "available"]
    traffic_factor = _demand_multiplier(selected_hour)
    routes = []
    for idx, route in enumerate(PATROL_ROUTES):
        state = availability_map[(selected_hour + idx) % len(availability_map)]
        routes.append(
            {
                **route,
                "availability_state": state,
                "eta_multiplier": round(traffic_factor + (idx * 0.04), 2),
            }
        )
    return {"meta": {"selected_hour": selected_hour}, "routes": routes}


@app.get("/api/v1/congestion-events")
def congestion_events(
    window: str = Query(default="2h", pattern=r"^\d+h$"),
    hour: int | None = Query(default=None, ge=0, le=23),
) -> dict[str, Any]:
    selected_hour = _selected_hour(hour)
    zones = _build_zone_snapshot(selected_hour)
    hours = int(window[:-1])
    now = datetime.now(timezone.utc)
    events = []
    for idx, zone in enumerate(zones[:6]):
        started_at = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=idx % max(hours, 1))
        events.append(
            {
                "event_id": f"CE-{selected_hour:02d}-{idx + 1}",
                "zone_id": zone["id"],
                "zone_name": zone["name"],
                "started_at": started_at.isoformat(),
                "speed_drop_pct": round(_normalize((zone["cis"] / 100.0) * 64.0, 12.0, 71.0), 1),
                "queue_len_m": zone["queue_forecast_m"],
                "incident_type": "Illegal Parking Cluster",
                "resolved_at": None,
            }
        )
    return {"meta": {"selected_hour": selected_hour, "window": window}, "events": events}


@app.post("/api/v1/enforcement/deploy")
def deploy_patrol(payload: DeployRequest, hour: int | None = Query(default=None, ge=0, le=23)) -> dict[str, Any]:
    selected_hour = _selected_hour(hour)
    zones = _build_zone_snapshot(selected_hour)
    zone = next((item for item in zones if item["id"] == payload.zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{payload.zone_id}' not found")

    patrol = next((item for item in zone["suggested_patrols"] if item["route_id"] == payload.route_id), None)
    if not patrol:
        raise HTTPException(status_code=404, detail=f"Route '{payload.route_id}' is not valid for zone '{payload.zone_id}'")

    reduction = min(34.0, patrol["impact_recovery_pct"] * 0.78)
    after_priority = round(_normalize(zone["priority_score"] - reduction), 1)
    delay_saved = int(round(patrol["impact_recovery_pct"] * 44))
    return {
        "zone_id": payload.zone_id,
        "zone_name": zone["name"],
        "route_id": patrol["route_id"],
        "beat_code": patrol["beat_code"],
        "before_priority": zone["priority_score"],
        "after_priority": after_priority,
        "estimated_person_delay_saved_min": delay_saved,
        "action": f"Dispatch {patrol['beat_code']} now via {HOTSPOT_BY_ID[payload.zone_id].route_hint}.",
    }


@app.post("/api/v1/sim/tick")
def sim_tick(payload: SimTickRequest) -> dict[str, Any]:
    global CURRENT_SIM_HOUR
    CURRENT_SIM_HOUR = (CURRENT_SIM_HOUR + payload.delta_hours) % 24
    return {
        "message": "Simulation clock advanced",
        "current_hour": CURRENT_SIM_HOUR,
        "overview": _overview_payload(CURRENT_SIM_HOUR),
    }


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket) -> None:
    await websocket.accept()
    rng = random.Random()
    try:
        while True:
            overview = _overview_payload(CURRENT_SIM_HOUR)
            top_zone = overview["zones"][0]
            dispatch = top_zone["suggested_patrols"][0]
            event = {
                "event_type": "live_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "selected_hour": CURRENT_SIM_HOUR,
                "zone_id": top_zone["id"],
                "zone_name": top_zone["name"],
                "delta_violations": rng.randint(1, 4),
                "priority_score": top_zone["priority_score"],
                "tier": top_zone["tier"],
                "brief": (
                    f"{top_zone['violation_count']} active stops. "
                    f"Next recommended unit {dispatch['beat_code']} ETA {dispatch['eta_min']} min."
                ),
            }
            await websocket.send_json(event)
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        return
