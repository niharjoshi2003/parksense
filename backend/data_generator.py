from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Hotspot:
    id: str
    name: str
    lat: float
    lng: float
    road_criticality: float
    adjacency_score: float
    base_weight: float
    lane_count: float
    route_hint: str
    critical_asset: bool


HOTSPOTS: list[Hotspot] = [
    Hotspot(
        id="koramangala_5th_block_bus_stop",
        name="Koramangala 5th Block Bus Stop",
        lat=12.9352,
        lng=77.6245,
        road_criticality=0.79,
        adjacency_score=0.74,
        base_weight=1.18,
        lane_count=3.0,
        route_hint="Forum Mall exit lane",
        critical_asset=False,
    ),
    Hotspot(
        id="indiranagar_100ft_road_metro",
        name="Indiranagar 100ft Road Metro",
        lat=12.9784,
        lng=77.6408,
        road_criticality=0.71,
        adjacency_score=0.69,
        base_weight=1.03,
        lane_count=3.0,
        route_hint="CMH Road inbound curb",
        critical_asset=False,
    ),
    Hotspot(
        id="mg_road_brigade_road_junction",
        name="MG Road-Brigade Road junction",
        lat=12.9716,
        lng=77.6074,
        road_criticality=0.77,
        adjacency_score=0.72,
        base_weight=1.04,
        lane_count=3.0,
        route_hint="Brigade signal frontage",
        critical_asset=False,
    ),
    Hotspot(
        id="silk_board_flyover_approach",
        name="Silk Board flyover approach",
        lat=12.9177,
        lng=77.6235,
        road_criticality=0.98,
        adjacency_score=0.93,
        base_weight=1.42,
        lane_count=3.5,
        route_hint="Hosur Road service lane",
        critical_asset=True,
    ),
    Hotspot(
        id="whitefield_itpl_gate_1",
        name="Whitefield ITPL Gate 1",
        lat=12.9849,
        lng=77.7480,
        road_criticality=0.84,
        adjacency_score=0.78,
        base_weight=1.11,
        lane_count=3.0,
        route_hint="ITPL gate shoulder",
        critical_asset=False,
    ),
    Hotspot(
        id="hebbal_flyover_north",
        name="Hebbal flyover north",
        lat=13.0358,
        lng=77.5970,
        road_criticality=0.92,
        adjacency_score=0.9,
        base_weight=1.25,
        lane_count=3.5,
        route_hint="airport corridor loop",
        critical_asset=True,
    ),
    Hotspot(
        id="jayanagar_4th_block_market",
        name="Jayanagar 4th Block market",
        lat=12.9250,
        lng=77.5938,
        road_criticality=0.68,
        adjacency_score=0.67,
        base_weight=0.96,
        lane_count=2.5,
        route_hint="11th Main curb market edge",
        critical_asset=False,
    ),
    Hotspot(
        id="hsr_layout_sector_7",
        name="HSR Layout Sector 7",
        lat=12.9116,
        lng=77.6387,
        road_criticality=0.74,
        adjacency_score=0.7,
        base_weight=1.01,
        lane_count=3.0,
        route_hint="27th Main feeder",
        critical_asset=False,
    ),
    Hotspot(
        id="marathahalli_bridge",
        name="Marathahalli bridge",
        lat=12.9591,
        lng=77.7009,
        road_criticality=0.95,
        adjacency_score=0.89,
        base_weight=1.33,
        lane_count=3.5,
        route_hint="service road merge underpass",
        critical_asset=True,
    ),
    Hotspot(
        id="electronic_city_phase_1_toll",
        name="Electronic City Phase 1 toll",
        lat=12.8399,
        lng=77.6770,
        road_criticality=0.88,
        adjacency_score=0.82,
        base_weight=1.14,
        lane_count=3.0,
        route_hint="toll plaza pre-queue shoulder",
        critical_asset=False,
    ),
    Hotspot(
        id="yeshwanthpur_metro_exit",
        name="Yeshwanthpur Metro exit",
        lat=13.0270,
        lng=77.5540,
        road_criticality=0.76,
        adjacency_score=0.74,
        base_weight=1.07,
        lane_count=3.0,
        route_hint="metro pickup bay edge",
        critical_asset=False,
    ),
    Hotspot(
        id="shivajinagar_bus_terminus",
        name="Shivajinagar bus terminus",
        lat=12.9855,
        lng=77.6025,
        road_criticality=0.87,
        adjacency_score=0.86,
        base_weight=1.23,
        lane_count=2.8,
        route_hint="bus terminus outer ring",
        critical_asset=True,
    ),
]

VEHICLE_TYPES = ["2W", "Car", "Auto", "Cab", "Goods"]
BEAT_CODES = ["B-03", "B-05", "B-08", "B-12", "B-14", "B-18", "B-22"]


def _hour_bias(hour: int) -> float:
    if 7 <= hour <= 11:
        return 1.24
    if 16 <= hour <= 21:
        return 1.42
    if 12 <= hour <= 15:
        return 1.03
    return 0.72


def _vehicle_lane_bias(vehicle_type: str) -> float:
    return {
        "2W": 0.65,
        "Car": 1.0,
        "Auto": 0.88,
        "Cab": 1.04,
        "Goods": 1.28,
    }[vehicle_type]


def _sample_hour(rng: random.Random) -> int:
    evening_peak = int(rng.gauss(18.2, 1.8))
    morning_peak = int(rng.gauss(9.1, 1.7))
    off_peak = int(rng.gauss(13.2, 3.6))
    draw = rng.random()
    if draw < 0.46:
        hour = evening_peak
    elif draw < 0.8:
        hour = morning_peak
    else:
        hour = off_peak
    return max(0, min(23, hour))


def generate_synthetic_dataset(row_count: int = 1000, seed: int = 72) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    weights = [hotspot.base_weight for hotspot in HOTSPOTS]
    dataset: list[dict[str, Any]] = []

    for idx in range(row_count):
        hotspot = rng.choices(HOTSPOTS, weights=weights, k=1)[0]
        hour = _sample_hour(rng)
        minute = rng.randint(0, 59)
        timestamp = now - timedelta(hours=(24 - hour), minutes=(60 - minute))
        vehicle_type = rng.choices(
            VEHICLE_TYPES,
            weights=[0.4, 0.22, 0.17, 0.12, 0.09],
            k=1,
        )[0]

        lane_block_pct = min(
            95.0,
            max(
                6.0,
                rng.gauss(
                    20.0 * hotspot.base_weight * _vehicle_lane_bias(vehicle_type) * _hour_bias(hour),
                    8.5,
                ),
            ),
        )
        dwell_min = max(
            2.0,
            rng.gauss(
                7.5 * _hour_bias(hour) * _vehicle_lane_bias(vehicle_type),
                4.2,
            ),
        )

        confidence = round(max(0.62, min(0.99, rng.gauss(0.87, 0.07))), 3)

        record = {
            "violation_id": f"VIO-{idx + 1:05d}",
            "zone_id": hotspot.id,
            "zone_name": hotspot.name,
            "lat": hotspot.lat + rng.uniform(-0.00055, 0.00055),
            "lng": hotspot.lng + rng.uniform(-0.00065, 0.00065),
            "captured_at": timestamp.isoformat() + "Z",
            "captured_hour": hour,
            "vehicle_type": vehicle_type,
            "dwell_min": round(dwell_min, 2),
            "lane_block_pct": round(lane_block_pct, 2),
            "confidence": confidence,
            "beat_code": rng.choice(BEAT_CODES),
        }
        dataset.append(record)

    return dataset


def write_dataset_json(path: Path, row_count: int = 1000, seed: int = 72) -> list[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset = generate_synthetic_dataset(row_count=row_count, seed=seed)
    path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    return dataset


def load_or_generate_dataset(path: Path, row_count: int = 1000, seed: int = 72) -> list[dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return write_dataset_json(path=path, row_count=row_count, seed=seed)


if __name__ == "__main__":
    output_path = Path(__file__).parent / "synthetic_violations.json"
    rows = write_dataset_json(output_path, row_count=1000, seed=72)
    print(f"Generated {len(rows)} rows at {output_path}")
