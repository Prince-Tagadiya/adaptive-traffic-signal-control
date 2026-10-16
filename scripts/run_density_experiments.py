#!/usr/bin/env python3
"""
Density-Based Adaptive Controller Experiment Runner.

Executes:
1. Seed 42 Density Run (exports decisions, raw step data, vehicle trips, and summary)
2. Seed 43 Density Run
3. Seed 44 Density Run
4. Compiles multi-seed summary dataset with Mean ± Std Dev
5. Displays comparison with Fixed-Time baseline.
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.runner import SimulationRunner
from controllers.basic_density_controller import BasicDensityController
from scripts.generate_routes import generate_routes


def run_density_experiment(
    seed: int,
    sim_duration: int = 1000,
    warmup_duration: int = 200,
    scenario_cfg: str = "scenarios/four_arm.sumocfg",
    routes_xml: str = "scenarios/four_arm.rou.xml",
    min_green: int = 15,
    max_green: int = 50,
    yellow_time: int = 3,
    starvation_red_time: int = 45,
) -> dict:
    """Run a single density-controlled simulation with identical network & demand."""
    cfg_path = PROJECT_ROOT / scenario_cfg
    rou_path = PROJECT_ROOT / routes_xml

    # Generate demand with exact same generator & parameters as baseline
    demand_stats = generate_routes(
        output_path=str(rou_path),
        sim_duration=sim_duration,
        seed=seed,
        p_arrival_per_arm=0.08,
        straight_prob=0.65,
        right_prob=0.20,
        left_prob=0.15,
    )

    controller = BasicDensityController(
        tl_id="J0",
        min_green=min_green,
        max_green=max_green,
        yellow_time=yellow_time,
        starvation_red_time=starvation_red_time,
    )

    runner = SimulationRunner(
        config_path=str(cfg_path),
        sim_duration=sim_duration,
        warmup_duration=warmup_duration,
        tl_id="J0",
        controller=controller,
        seed=seed,
    )

    result = runner.run()
    result["demand_stats"] = demand_stats
    result["controller"] = controller
    return result


def main():
    sim_duration = 1000
    warmup_duration = 200
    seeds = [42, 43, 44]
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("PHASE 4: BASIC DENSITY-BASED ADAPTIVE SIGNAL CONTROL EXPERIMENTS")
    print("=" * 75)
    print(f"Simulation Duration: {sim_duration}s | Warm-up: {warmup_duration}s | Evaluation: {sim_duration - warmup_duration}s")
    print("Controller Parameters: Min Green: 15s | Max Green: 50s | Yellow: 3s | Starvation Red: 45s")

    # -------------------------------------------------------------
    # 1. Run Seed 42
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[1/3] Running Basic Density Controller Seed 42...")
    res_42 = run_density_experiment(seed=42, sim_duration=sim_duration, warmup_duration=warmup_duration)
    summary_42 = res_42["summary"]

    # Save Seed 42 decision log
    decisions_df = res_42["controller"].get_decisions_df()
    decisions_file = data_dir / "density_controller_decisions_seed42.csv"
    decisions_df.to_csv(decisions_file, index=False)
    print(f"[✓] Saved controller decisions to: {decisions_file}")

    # Save Seed 42 raw step data
    raw_step_file = data_dir / "density_seed42_raw.csv"
    res_42["step_dataframe"].to_csv(raw_step_file, index=False)
    print(f"[✓] Saved step-level raw data to: {raw_step_file}")

    # Save Seed 42 vehicle-level data
    veh_file = data_dir / "density_seed42_vehicles.csv"
    res_42["vehicle_dataframe"].to_csv(veh_file, index=False)
    print(f"[✓] Saved vehicle-level raw data to: {veh_file}")

    # Save Seed 42 summary CSV
    summary_42_df = pd.DataFrame([summary_42])
    summary_file = data_dir / "density_seed42_summary.csv"
    summary_42_df.to_csv(summary_file, index=False)
    print(f"[✓] Saved density summary to: {summary_file}")

    # -------------------------------------------------------------
    # 2. Run Seed 43
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[2/3] Running Basic Density Controller Seed 43...")
    res_43 = run_density_experiment(seed=43, sim_duration=sim_duration, warmup_duration=warmup_duration)

    # -------------------------------------------------------------
    # 3. Run Seed 44
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[3/3] Running Basic Density Controller Seed 44...")
    res_44 = run_density_experiment(seed=44, sim_duration=sim_duration, warmup_duration=warmup_duration)

    # -------------------------------------------------------------
    # 4. Compile Multi-Seed Density Dataset
    # -------------------------------------------------------------
    all_runs = [
        {"seed": 42, "res": res_42},
        {"seed": 43, "res": res_43},
        {"seed": 44, "res": res_44},
    ]

    metric_rows = []
    for run in all_runs:
        s = run["res"]["summary"]
        d = run["res"]["demand_stats"]
        metric_rows.append({
            "seed": run["seed"],
            "sim_duration_s": s["sim_duration_s"],
            "warmup_duration_s": s["warmup_duration_s"],
            "vehicles_generated": d["total_vehicles"],
            "vehicles_completed": s["total_vehicles_completed"],
            "eval_throughput": s["eval_throughput_completed"],
            "avg_waiting_time_s": s["avg_waiting_time_s"],
            "avg_travel_time_s": s["avg_travel_time_s"],
            "avg_queue_length_veh": s["avg_queue_length_veh"],
            "max_queue_length_veh": s["max_queue_length_veh"],
            "avg_stops_per_veh": s["avg_stops_per_veh"],
            "total_stops": s["total_stops"],
            "mean_speed_mps": s["mean_speed_mps"],
            "avg_delay_s": s["avg_delay_s"],
            "total_delay_s": s["total_delay_s"],
        })

    all_seeds_df = pd.DataFrame(metric_rows)

    numeric_cols = [
        "vehicles_generated", "vehicles_completed", "eval_throughput",
        "avg_waiting_time_s", "avg_travel_time_s", "avg_queue_length_veh",
        "max_queue_length_veh", "avg_stops_per_veh", "total_stops",
        "mean_speed_mps", "avg_delay_s", "total_delay_s"
    ]

    mean_vals = {"seed": "Mean"}
    std_vals = {"seed": "Std"}
    for col in numeric_cols:
        mean_vals[col] = round(float(all_seeds_df[col].mean()), 2)
        std_vals[col] = round(float(all_seeds_df[col].std(ddof=1)), 2)

    export_df = pd.concat([all_seeds_df, pd.DataFrame([mean_vals, std_vals])], ignore_index=True)
    all_seeds_csv = data_dir / "density_summary_all_seeds.csv"
    export_df.to_csv(all_seeds_csv, index=False)
    print(f"\n[✓] Saved multi-seed density summary to: {all_seeds_csv}")

    # -------------------------------------------------------------
    # 5. Load Baseline for Comparison Table
    # -------------------------------------------------------------
    baseline_summary_file = data_dir / "baseline_summary_all_seeds.csv"
    if baseline_summary_file.exists():
        base_df = pd.read_csv(baseline_summary_file)
        base_mean = base_df[base_df["seed"] == "Mean"].iloc[0]
        base_std = base_df[base_df["seed"] == "Std"].iloc[0]

        print("\n" + "=" * 85)
        print("COMPARISON TABLE: FIXED-TIME BASELINE vs BASIC DENSITY CONTROLLER (MEAN ± STD)")
        print("=" * 85)
        print(f"{'Metric':<35} | {'Fixed-Time Baseline':<20} | {'Basic Density':<20}")
        print("-" * 85)

        labels = {
            "eval_throughput": "Eval Throughput (veh)",
            "avg_waiting_time_s": "Avg Waiting Time (s/veh)",
            "avg_travel_time_s": "Avg Travel Time (s/veh)",
            "avg_queue_length_veh": "Avg Queue Length (halting veh)",
            "max_queue_length_veh": "Max Queue Length (veh)",
            "avg_stops_per_veh": "Avg Stops (stops/veh)",
            "mean_speed_mps": "Mean Speed (m/s)",
            "avg_delay_s": "Avg Delay (s/veh)",
            "total_delay_s": "Total Vehicle Delay (s)",
        }

        for col, desc in labels.items():
            bm = float(base_mean[col])
            bs = float(base_std[col])
            dm = float(mean_vals[col])
            ds = float(std_vals[col])
            print(f"{desc:<35} | {bm:.2f} ± {bs:.2f}{'':<10} | {dm:.2f} ± {ds:.2f}")

        print("=" * 85)


if __name__ == "__main__":
    main()
