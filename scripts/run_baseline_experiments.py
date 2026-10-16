#!/usr/bin/env python3
"""
Baseline Experiment Runner and Determinism Verifier.

Executes:
1. Seed 42 Baseline Run
2. Seed 42 Repeat Run for strict determinism verification
3. Seed 43 Run
4. Seed 44 Run

Collects post-warmup research metrics, exports CSV datasets,
and computes mean ± std dev across seeds.
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.runner import SimulationRunner
from controllers.fixed_time_controller import FixedTimeSignalController
from scripts.generate_routes import generate_routes


def run_single_experiment(
    seed: int,
    sim_duration: int = 1000,
    warmup_duration: int = 200,
    scenario_cfg: str = "scenarios/four_arm.sumocfg",
    routes_xml: str = "scenarios/four_arm.rou.xml",
) -> dict:
    """Generate demand for the given seed and execute the simulation."""
    cfg_path = PROJECT_ROOT / scenario_cfg
    rou_path = PROJECT_ROOT / routes_xml

    # Generate demand deterministically for this seed
    demand_stats = generate_routes(
        output_path=str(rou_path),
        sim_duration=sim_duration,
        seed=seed,
        p_arrival_per_arm=0.08,
        straight_prob=0.65,
        right_prob=0.20,
        left_prob=0.15,
    )

    controller = FixedTimeSignalController(tl_id="J0")
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
    return result


def main():
    sim_duration = 1000
    warmup_duration = 200
    seeds = [42, 43, 44]
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print("PHASE 3: FIXED-TIME CONTROLLER RESEARCH BASELINE EXPERIMENTS")
    print("=" * 75)
    print(f"Simulation Duration: {sim_duration}s | Warm-up: {warmup_duration}s | Evaluation: {sim_duration - warmup_duration}s")
    print("Explicit Signal Cycle: 90s (NS Green: 42s, NS Yellow: 3s, EW Green: 42s, EW Yellow: 3s)")

    # -------------------------------------------------------------
    # 1. Run Baseline Seed 42 (Run 1)
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[1/4] Running Baseline Seed 42 (Primary Run)...")
    res_42_run1 = run_single_experiment(seed=42, sim_duration=sim_duration, warmup_duration=warmup_duration)
    summary_42 = res_42_run1["summary"]

    # Save Seed 42 raw step data
    raw_step_file = data_dir / "baseline_seed42_raw.csv"
    res_42_run1["step_dataframe"].to_csv(raw_step_file, index=False)
    print(f"[✓] Saved step-level raw data to: {raw_step_file}")

    # Save Seed 42 vehicle-level data
    veh_file = data_dir / "baseline_seed42_vehicles.csv"
    res_42_run1["vehicle_dataframe"].to_csv(veh_file, index=False)
    print(f"[✓] Saved vehicle-level raw data to: {veh_file}")

    # Save Seed 42 summary CSV
    summary_42_df = pd.DataFrame([summary_42])
    summary_file = data_dir / "baseline_seed42_summary.csv"
    summary_42_df.to_csv(summary_file, index=False)
    print(f"[✓] Saved baseline summary to: {summary_file}")

    # -------------------------------------------------------------
    # 2. Run Baseline Seed 42 (Run 2: Determinism Verification)
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[2/4] Running Baseline Seed 42 (Repeat Run for Determinism Check)...")
    res_42_run2 = run_single_experiment(seed=42, sim_duration=sim_duration, warmup_duration=warmup_duration)

    # Compare summary metrics
    deterministic = True
    differing_keys = []
    for k in summary_42:
        val1 = summary_42[k]
        val2 = res_42_run2["summary"][k]
        if val1 != val2:
            deterministic = False
            differing_keys.append((k, val1, val2))

    print("\n--- DETERMINISM VERIFICATION RESULT ---")
    if deterministic:
        print("[✓] STRICT DETERMINISM CONFIRMED: Run 1 and Run 2 produced 100% IDENTICAL metrics!")
    else:
        print(f"[✗] Discrepancies detected between runs: {differing_keys}")

    # -------------------------------------------------------------
    # 3. Run Seed 43
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[3/4] Running Baseline Seed 43...")
    res_43 = run_single_experiment(seed=43, sim_duration=sim_duration, warmup_duration=warmup_duration)

    # -------------------------------------------------------------
    # 4. Run Seed 44
    # -------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[4/4] Running Baseline Seed 44...")
    res_44 = run_single_experiment(seed=44, sim_duration=sim_duration, warmup_duration=warmup_duration)

    # -------------------------------------------------------------
    # 5. Compile Multi-Seed Baseline Dataset
    # -------------------------------------------------------------
    all_runs = [
        {"seed": 42, "res": res_42_run1},
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

    # Calculate Mean and Std
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
    all_seeds_csv = data_dir / "baseline_summary_all_seeds.csv"
    export_df.to_csv(all_seeds_csv, index=False)
    print(f"\n[✓] Saved multi-seed baseline summary to: {all_seeds_csv}")

    # -------------------------------------------------------------
    # 6. Display Clean Summary Table
    # -------------------------------------------------------------
    print("\n" + "=" * 75)
    print("BASELINE SUMMARY TABLE (SEEDS 42, 43, 44)")
    print("=" * 75)
    print(f"{'Metric':<35} | {'Seed 42':<10} | {'Seed 43':<10} | {'Seed 44':<10} | {'Mean ± Std':<15}")
    print("-" * 90)

    labels = {
        "vehicles_generated": "Vehicles Generated (Demand)",
        "vehicles_completed": "Total Completed Vehicles",
        "eval_throughput": "Eval Throughput (Post-Warmup)",
        "avg_waiting_time_s": "Avg Waiting Time (s/veh)",
        "avg_travel_time_s": "Avg Travel Time (s/veh)",
        "avg_queue_length_veh": "Avg Queue Length (halting veh)",
        "max_queue_length_veh": "Max Queue Length (veh)",
        "avg_stops_per_veh": "Avg Number of Stops (stops/veh)",
        "mean_speed_mps": "Mean Speed (m/s)",
        "avg_delay_s": "Avg Vehicle Delay / Time Loss (s)",
        "total_delay_s": "Total Vehicle Delay (s)",
    }

    for col, desc in labels.items():
        v42 = all_seeds_df.loc[all_seeds_df['seed'] == 42, col].values[0]
        v43 = all_seeds_df.loc[all_seeds_df['seed'] == 43, col].values[0]
        v44 = all_seeds_df.loc[all_seeds_df['seed'] == 44, col].values[0]
        m = mean_vals[col]
        s = std_vals[col]
        print(f"{desc:<35} | {v42:<10} | {v43:<10} | {v44:<10} | {m} ± {s}")

    print("=" * 75)


if __name__ == "__main__":
    main()
