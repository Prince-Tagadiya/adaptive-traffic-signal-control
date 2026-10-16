"""
Phase 9 — Blind Final Test Evaluation Script.

Executes 140 independent simulation runs:
4 controllers x 7 scenarios x 5 seeds (42, 43, 44, 45, 46).
Strict Cohort A evaluation (depart >= 200s AND arrive >= 200s).

Controllers:
    C0: Original Fixed-Time Controller (90s cycle)
    C1: Webster-Calibrated Minimum-Cycle Fixed-Time Controller (36s cycle)
    C2: Basic Queue-Based Adaptive Controller
    C3: Proposed Composite Adaptive Controller (Frozen: alpha=1.0, beta=0.75, gamma=0.10, delta=0.25, eta=0.25, H=0.20)

Follows strict data separation: No parameter modification or statistical hypothesis testing.
"""

import sys
import time
from pathlib import Path
import multiprocessing as mp
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from simulation.runner import SimulationRunner
from controllers.fixed_time_controller import FixedTimeSignalController
from controllers.optimized_fixed_time_controller import OptimizedFixedTimeSignalController
from controllers.basic_density_controller import BasicDensityController
from controllers.proposed_adaptive_controller import ProposedAdaptiveSignalController

CONFIG_PATH = str(BASE_DIR / "scenarios" / "four_arm.sumocfg")
DEMAND_DIR = BASE_DIR / "scenarios" / "demand"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CONTROLLERS = [
    ("C0_Original_FixedTime", "FixedTimeSignalController"),
    ("C1_Webster_FixedTime", "OptimizedFixedTimeSignalController"),
    ("C2_Basic_Queue", "BasicDensityController"),
    ("C3_Proposed_Adaptive", "ProposedAdaptiveSignalController"),
]

SCENARIOS = [
    "low",
    "medium",
    "high",
    "oversaturated",
    "asym_ns",
    "asym_ew",
    "dynamic",
]

SEEDS = [42, 43, 44, 45, 46]


def create_controller_instance(ctrl_type: str):
    """Instantiate fresh controller instance with frozen parameters."""
    if ctrl_type == "FixedTimeSignalController":
        return FixedTimeSignalController()
    elif ctrl_type == "OptimizedFixedTimeSignalController":
        return OptimizedFixedTimeSignalController()
    elif ctrl_type == "BasicDensityController":
        return BasicDensityController(min_green=15, max_green=50, yellow_time=3, starvation_red_time=45)
    elif ctrl_type == "ProposedAdaptiveSignalController":
        # Uses exact frozen defaults: alpha=1.0, beta=0.75, gamma=0.10, delta=0.25, eta=0.25, H=0.20
        c = ProposedAdaptiveSignalController()
        assert c.alpha == 1.0, f"Expected alpha=1.0, got {c.alpha}"
        assert c.beta == 0.75, f"Expected beta=0.75, got {c.beta}"
        assert c.gamma == 0.10, f"Expected gamma=0.10, got {c.gamma}"
        assert c.delta == 0.25, f"Expected delta=0.25, got {c.delta}"
        assert c.eta == 0.25, f"Expected eta=0.25, got {c.eta}"
        assert c.hysteresis == 0.20, f"Expected hysteresis=0.20, got {c.hysteresis}"
        return c
    else:
        raise ValueError(f"Unknown controller type: {ctrl_type}")


def run_evaluation_task(task_args: Tuple) -> Dict[str, Any]:
    """Worker task executing a single controller x scenario x seed run."""
    c_id, ctrl_type, scenario, seed = task_args
    rou_file = f"demand_{scenario}_seed{seed}.rou.xml"
    rou_path = str(DEMAND_DIR / rou_file)

    controller = create_controller_instance(ctrl_type)

    runner = SimulationRunner(
        config_path=CONFIG_PATH,
        route_path=rou_path,
        controller=controller,
        seed=seed,
        warmup_duration=200,
        sim_duration=1000,
    )
    res = runner.run()["summary"]

    return {
        "controller_id": c_id,
        "controller_class": ctrl_type,
        "scenario": scenario,
        "seed": seed,
        # Cohort A Primary Metrics
        "throughput_cohort_a": res["cohort_a_completed"],
        "mean_waiting_time_s": res["avg_waiting_time_s"],
        "mean_travel_time_s": res["avg_travel_time_s"],
        "mean_delay_s": res["avg_delay_s"],
        "total_delay_s": res["total_delay_s"],
        "mean_stops_per_veh": res["avg_stops_per_veh"],
        "mean_speed_mps": res["mean_speed_mps"],
        # Step / System Level Metrics
        "mean_queue_veh": res["avg_queue_length_veh"],
        "max_queue_veh": res["max_queue_length_veh"],
        "phase_switch_count": res["phase_switch_count"],
        "total_yellow_lost_time_s": res["total_yellow_lost_time_s"],
        "max_red_duration_s": res["max_red_duration_s"],
    }


def execute_blind_test_evaluation(num_workers: int = 6):
    t0 = time.time()
    print("=" * 80)
    print("PHASE 9 — BLIND FINAL TEST EVALUATION")
    print(f"4 Controllers x 7 Scenarios x 5 Seeds = 140 Runs | Workers: {num_workers}")
    print("Test Seeds: [42, 43, 44, 45, 46] | Cohort: Strict A (depart >= 200s, arrive >= 200s)")
    print("=" * 80)

    # 1. Build all 140 tasks
    tasks = []
    for c_id, ctrl_type in CONTROLLERS:
        for scenario in SCENARIOS:
            for seed in SEEDS:
                tasks.append((c_id, ctrl_type, scenario, seed))

    print(f"Dispatched {len(tasks)} simulation tasks...")

    # 2. Execute parallel evaluation
    with mp.Pool(processes=num_workers) as pool:
        raw_results = pool.map(run_evaluation_task, tasks)

    elapsed = time.time() - t0
    print(f"[✓] Completed all {len(raw_results)} runs in {elapsed:.1f}s ({elapsed/len(raw_results):.2f}s/run)")

    df_per_seed = pd.DataFrame(raw_results)

    # Sort deterministically
    df_per_seed = df_per_seed.sort_values(
        by=["scenario", "seed", "controller_id"]
    ).reset_index(drop=True)

    # Export raw per-seed results
    per_seed_csv = RESULTS_DIR / "final_test_results_per_seed.csv"
    df_per_seed.to_csv(per_seed_csv, index=False)
    print(f"[✓] Saved per-seed results to: {per_seed_csv} ({len(df_per_seed)} rows)")

    # 3. Determinism Check: Repeat C3 Proposed on medium scenario, seed 42
    print("\n--- RUNNING DETERMINISM CHECK ---")
    det_task = ("C3_Proposed_Adaptive", "ProposedAdaptiveSignalController", "medium", 42)
    det_res = run_evaluation_task(det_task)

    # Find the original run
    orig_row = df_per_seed[
        (df_per_seed["controller_id"] == "C3_Proposed_Adaptive")
        & (df_per_seed["scenario"] == "medium")
        & (df_per_seed["seed"] == 42)
    ].iloc[0].to_dict()

    check_keys = [
        "throughput_cohort_a", "mean_waiting_time_s", "mean_travel_time_s",
        "mean_delay_s", "mean_queue_veh", "phase_switch_count"
    ]
    det_passed = True
    print("Comparison (Original vs Determinism Check):")
    for k in check_keys:
        v_orig = orig_row[k]
        v_det = det_res[k]
        match = (v_orig == v_det)
        if not match:
            det_passed = False
        print(f"  {k:<25}: Original={v_orig:<8} | Repeat={v_det:<8} | Match={match}")

    print(f"Determinism Check Status: {'PASSED (Bit-level Identical)' if det_passed else 'FAILED'}")

    # 4. Compute Aggregate Summary (Mean ± SD across seeds 42-46)
    metric_cols = [
        "throughput_cohort_a",
        "mean_waiting_time_s",
        "mean_travel_time_s",
        "mean_delay_s",
        "total_delay_s",
        "mean_stops_per_veh",
        "mean_speed_mps",
        "mean_queue_veh",
        "max_queue_veh",
        "phase_switch_count",
        "total_yellow_lost_time_s",
        "max_red_duration_s",
    ]

    summary_rows = []
    for (scenario, c_id), grp in df_per_seed.groupby(["scenario", "controller_id"]):
        row = {
            "scenario": scenario,
            "controller_id": c_id,
            "n_seeds": len(grp),
        }
        for m in metric_cols:
            mean_val = float(grp[m].mean())
            std_val = float(grp[m].std())
            row[f"{m}_mean"] = round(mean_val, 2)
            row[f"{m}_sd"] = round(std_val, 2)
            row[f"{m}_formatted"] = f"{mean_val:.2f} ± {std_val:.2f}"
        summary_rows.append(row)

    df_summary = pd.DataFrame(summary_rows)
    # Order by scenario then controller
    scenario_order = {s: i for i, s in enumerate(SCENARIOS)}
    controller_order = {c[0]: i for i, c in enumerate(CONTROLLERS)}
    df_summary["sc_order"] = df_summary["scenario"].map(scenario_order)
    df_summary["ctrl_order"] = df_summary["controller_id"].map(controller_order)
    df_summary = df_summary.sort_values(by=["sc_order", "ctrl_order"]).drop(columns=["sc_order", "ctrl_order"]).reset_index(drop=True)

    summary_csv = RESULTS_DIR / "final_test_summary.csv"
    df_summary.to_csv(summary_csv, index=False)
    print(f"[✓] Saved summary results to: {summary_csv} ({len(df_summary)} rows)")

    # Print Compact Summary Table
    print("\n" + "=" * 95)
    print(f"{'SCENARIO':<15} | {'CONTROLLER':<24} | {'WAIT (s) (Mean ± SD)':<20} | {'DELAY (s)':<18} | {'SWITCHES':<12}")
    print("-" * 95)
    for _, r in df_summary.iterrows():
        print(f"{r['scenario']:<15} | {r['controller_id']:<24} | {r['mean_waiting_time_s_formatted']:<20} | {r['mean_delay_s_formatted']:<18} | {r['phase_switch_count_formatted']:<12}")
    print("=" * 95)

    return df_per_seed, df_summary, det_passed


if __name__ == "__main__":
    execute_blind_test_evaluation()
