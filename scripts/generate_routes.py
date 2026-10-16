#!/usr/bin/env python3
"""
Standardized Route and Demand Generator for Traffic Research.

Generates reproducible traffic demand files with:
- Strict seed-based determinism
- Configurable symmetric, asymmetric, and dynamic demand profiles
- Clean XML output for SUMO
"""

import os
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def generate_routes(
    output_path: str,
    sim_duration: int = 1000,
    seed: int = 42,
    p_arrival_per_arm: Union[float, Dict[str, float]] = 0.08,
    straight_prob: float = 0.65,
    right_prob: float = 0.20,
    left_prob: float = 0.15,
    dynamic_schedule: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Generate reproducible SUMO routes file.

    Parameters:
    - output_path: destination .rou.xml file
    - sim_duration: total simulation time (seconds)
    - seed: random seed
    - p_arrival_per_arm: float for symmetric arrivals or dict {'N': pN, 'S': pS, 'E': pE, 'W': pW}
    - straight_prob, right_prob, left_prob: turn proportions
    - dynamic_schedule: optional list of intervals [{'t_start': 0, 't_end': 500, 'probs': ...}]
    """
    random.seed(seed)

    approaches = {
        "N": {"straight": "N_S", "right": "N_W", "left": "N_E"},
        "S": {"straight": "S_N", "right": "S_E", "left": "S_W"},
        "E": {"straight": "E_W", "right": "E_N", "left": "E_S"},
        "W": {"straight": "W_E", "right": "W_S", "left": "W_N"},
    }

    route_edges = {
        "N_S": "N_J0 J0_S",
        "N_W": "N_J0 J0_W",
        "N_E": "N_J0 J0_E",
        "S_N": "S_J0 J0_N",
        "S_E": "S_J0 J0_E",
        "S_W": "S_J0 J0_W",
        "E_W": "E_J0 J0_W",
        "E_N": "E_J0 J0_N",
        "E_S": "E_J0 J0_S",
        "W_E": "W_J0 J0_E",
        "W_S": "W_J0 J0_S",
        "W_N": "W_J0 J0_N",
    }

    root = ET.Element("routes")

    # Define vehicle types
    ET.SubElement(
        root,
        "vType",
        id="standard_car",
        accel="2.6",
        decel="4.5",
        sigma="0.5",
        length="5.0",
        minGap="2.5",
        maxSpeed="13.89",
    )

    # Define routes
    for r_id, edges in route_edges.items():
        ET.SubElement(root, "route", id=r_id, edges=edges)

    veh_count = 0
    route_counts = {r_id: 0 for r_id in route_edges}
    turn_counts = {"straight": 0, "right": 0, "left": 0}
    approach_counts = {app: 0 for app in approaches}

    # Stop injecting near end to allow vehicles to complete
    injection_end = max(1, sim_duration - 60)

    for t in range(0, injection_end):
        # Resolve active probabilities for this second
        if dynamic_schedule:
            active_probs = {"N": 0.08, "S": 0.08, "E": 0.08, "W": 0.08}
            for period in dynamic_schedule:
                if period["t_start"] <= t < period["t_end"]:
                    active_probs = period["probs"]
                    break
        elif isinstance(p_arrival_per_arm, dict):
            active_probs = p_arrival_per_arm
        else:
            active_probs = {app: float(p_arrival_per_arm) for app in approaches}

        for app, turns in approaches.items():
            prob = active_probs.get(app, 0.0)
            if random.random() < prob:
                r_pick = random.random()
                if r_pick < straight_prob:
                    turn_type = "straight"
                elif r_pick < straight_prob + right_prob:
                    turn_type = "right"
                else:
                    turn_type = "left"

                route_id = turns[turn_type]
                veh_id = f"veh_{app}_{veh_count}"

                ET.SubElement(
                    root,
                    "vehicle",
                    id=veh_id,
                    type="standard_car",
                    route=route_id,
                    depart=str(t),
                    departLane="0",
                    departSpeed="max",
                )

                veh_count += 1
                route_counts[route_id] += 1
                turn_counts[turn_type] += 1
                approach_counts[app] += 1

    # Pretty print XML
    import xml.dom.minidom
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed = xml.dom.minidom.parseString(xml_str)
    pretty_xml = parsed.toprettyxml(indent="    ")

    lines = pretty_xml.split("\n")
    if lines[0].startswith("<?xml"):
        pretty_xml = "\n".join(lines[1:])

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    stats = {
        "output_path": str(out_file),
        "seed": seed,
        "sim_duration": sim_duration,
        "injection_end": injection_end,
        "total_vehicles": veh_count,
        "approach_counts": approach_counts,
        "turn_counts": turn_counts,
        "route_counts": route_counts,
        "p_arrival_per_arm": p_arrival_per_arm,
        "turn_probabilities": {
            "straight": straight_prob,
            "right": right_prob,
            "left": left_prob,
        },
    }
    return stats


def generate_experiment_demand_suite(base_dir: str = "scenarios/demand"):
    """
    Generate the complete, immutable demand suite for:
    - Calibration scenarios
    - Multi-demand scenarios (Low, Medium, High, Oversaturated)
    - Asymmetric scenarios (NS-heavy, EW-heavy)
    - Dynamic scenario
    Across seeds 42, 43, 44, 45, 46.
    """
    out_dir = Path(base_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    seeds = [42, 43, 44, 45, 46]
    catalog = {}

    # 1. Calibration Scenarios (Separate seeds 101, 102, 103, 104)
    catalog["calib_medium"] = generate_routes(
        str(out_dir / "calib_medium_seed101.rou.xml"),
        sim_duration=1000, seed=101, p_arrival_per_arm=0.08
    )
    catalog["calib_high"] = generate_routes(
        str(out_dir / "calib_high_seed102.rou.xml"),
        sim_duration=1000, seed=102, p_arrival_per_arm=0.14
    )
    catalog["calib_asym"] = generate_routes(
        str(out_dir / "calib_asym_seed103.rou.xml"),
        sim_duration=1000, seed=103, p_arrival_per_arm={"N": 0.14, "S": 0.14, "E": 0.03, "W": 0.03}
    )
    dynamic_calib_profile = [
        {"t_start": 0, "t_end": 300, "probs": {"N": 0.04, "S": 0.04, "E": 0.04, "W": 0.04}},
        {"t_start": 300, "t_end": 700, "probs": {"N": 0.15, "S": 0.15, "E": 0.15, "W": 0.15}},
        {"t_start": 700, "t_end": 1000, "probs": {"N": 0.05, "S": 0.05, "E": 0.05, "W": 0.05}},
    ]
    catalog["calib_dynamic"] = generate_routes(
        str(out_dir / "calib_dynamic_seed104.rou.xml"),
        sim_duration=1000, seed=104, dynamic_schedule=dynamic_calib_profile
    )

    # 2. Main Evaluation Scenarios
    demands = {
        "low": 0.04,
        "medium": 0.08,
        "high": 0.14,
        "oversaturated": 0.18,
    }

    for d_name, p_val in demands.items():
        for s in seeds:
            key = f"{d_name}_seed{s}"
            catalog[key] = generate_routes(
                str(out_dir / f"demand_{d_name}_seed{s}.rou.xml"),
                sim_duration=1000, seed=s, p_arrival_per_arm=p_val
            )

    # 3. Asymmetric Scenarios (NS-Heavy and EW-Heavy)
    asym_ns = {"N": 0.14, "S": 0.14, "E": 0.03, "W": 0.03}
    asym_ew = {"N": 0.03, "S": 0.03, "E": 0.14, "W": 0.14}

    for s in seeds:
        key_ns = f"asym_ns_seed{s}"
        catalog[key_ns] = generate_routes(
            str(out_dir / f"demand_asym_ns_seed{s}.rou.xml"),
            sim_duration=1000, seed=s, p_arrival_per_arm=asym_ns
        )
        key_ew = f"asym_ew_seed{s}"
        catalog[key_ew] = generate_routes(
            str(out_dir / f"demand_asym_ew_seed{s}.rou.xml"),
            sim_duration=1000, seed=s, p_arrival_per_arm=asym_ew
        )

    # 4. Dynamic Scenario (Low -> High -> Low)
    dynamic_profile = [
        {"t_start": 0, "t_end": 300, "probs": {"N": 0.04, "S": 0.04, "E": 0.04, "W": 0.04}},
        {"t_start": 300, "t_end": 700, "probs": {"N": 0.15, "S": 0.15, "E": 0.15, "W": 0.15}},
        {"t_start": 700, "t_end": 1000, "probs": {"N": 0.05, "S": 0.05, "E": 0.05, "W": 0.05}},
    ]
    for s in seeds:
        key_dyn = f"dynamic_seed{s}"
        catalog[key_dyn] = generate_routes(
            str(out_dir / f"demand_dynamic_seed{s}.rou.xml"),
            sim_duration=1000, seed=s, dynamic_schedule=dynamic_profile
        )

    print(f"[✓] Generated {len(catalog)} immutable demand realization files in {out_dir}")
    return catalog


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent.parent / "scenarios" / "four_arm.rou.xml"
    stats = generate_routes(str(out_file))
    print(f"Generated standard route file: {out_file} ({stats['total_vehicles']} vehicles)")

    # Generate full immutable suite
    suite_dir = Path(__file__).resolve().parent.parent / "scenarios" / "demand"
    generate_experiment_demand_suite(str(suite_dir))
