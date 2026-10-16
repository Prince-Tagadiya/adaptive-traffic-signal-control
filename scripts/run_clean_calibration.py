"""
Clean Calibration Procedure for Adaptive Traffic Signal Controller.

Exclusively evaluates candidate parameter configurations on the dedicated
Calibration Suite (Seeds 101, 102, 103, 104).
Zero exposure to evaluation test seeds (42-46).

Pre-declared Optimization Objective:
    J(theta) = 0.70 * (mean_wait / 25.0) + 0.20 * (mean_yellow / 150.0) + 0.10 * (mean_switches / 100.0)

Pre-declared Search Space:
    alpha = 1.0 (fixed queue anchor)
    beta in {0.25, 0.50, 0.75}
    delta in {0.25, 0.40, 0.55}
    eta in {0.25, 0.40, 0.55}
    H in {0.00, 0.10, 0.15, 0.20, 0.25}
    (Total: 135 configurations)

Pre-declared Tie-Breaking Rule:
    1. Lower composite J
    2. If within 1%: lower phase switches
    3. If still tied: lower sum of auxiliary weights (beta + delta + eta)
    4. If still tied: smaller H
"""

import sys
import time
from pathlib import Path
import itertools
import multiprocessing as mp
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from simulation.runner import SimulationRunner
from controllers.proposed_adaptive_controller import ProposedAdaptiveSignalController

CONFIG_PATH = str(BASE_DIR / "scenarios" / "four_arm.sumocfg")
DEMAND_DIR = BASE_DIR / "scenarios" / "demand"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 4 Independent Calibration Scenarios
CALIB_SCENARIOS = [
    ("calib_medium", "calib_medium_seed101.rou.xml", 101),
    ("calib_high", "calib_high_seed102.rou.xml", 102),
    ("calib_asym", "calib_asym_seed103.rou.xml", 103),
    ("calib_dynamic", "calib_dynamic_seed104.rou.xml", 104),
]

# Pre-declared search space
BETAS = [0.25, 0.50, 0.75]
DELTAS = [0.25, 0.40, 0.55]
ETAS = [0.25, 0.40, 0.55]
HYSTERESIS_VALS = [0.00, 0.10, 0.15, 0.20, 0.25]

# Pre-declared normalization targets (Fixed before search)
W_TARGET = 25.0    # HCM LOS C delay boundary benchmark (seconds)
Y_TARGET = 150.0   # Theoretical clearance lost time target for 1000s horizon (50 switches * 3s yellow)
S_TARGET = 100.0   # Pre-declared upper bound on phase switching churn (0.1 switch/s)


def run_single_simulation(args: Tuple) -> Dict[str, Any]:
    """Worker task evaluating one (candidate, scenario) pair."""
    cfg_id, beta, delta, eta, h, sc_name, rou_file, seed = args
    rou_path = str(DEMAND_DIR / rou_file)
    ctrl = ProposedAdaptiveSignalController(
        alpha=1.0,
        beta=beta,
        delta=delta,
        eta=eta,
        hysteresis=h,
        w_arrival=20,
        q_ref=20.0,
        a_ref=0.40,
        w_ref=30.0,
        r_ref=50.0,
        min_green=15,
        max_green=50,
        yellow_time=3,
        starvation_red_time=45,
        noise_std=0.0,
    )

    runner = SimulationRunner(
        config_path=CONFIG_PATH,
        route_path=rou_path,
        controller=ctrl,
        seed=seed,
    )
    res = runner.run()["summary"]
    return {
        "cfg_id": cfg_id,
        "beta": beta,
        "delta": delta,
        "eta": eta,
        "H": h,
        "scenario": sc_name,
        "wait": res["avg_waiting_time_s"],
        "delay": res["avg_delay_s"],
        "queue": res["avg_queue_length_veh"],
        "switches": res["phase_switch_count"],
        "yellow_time": res["total_yellow_lost_time_s"],
        "max_red": res["max_red_duration_s"],
        "throughput": res["cohort_a_completed"],
    }


def compute_pareto_frontier(df: pd.DataFrame) -> pd.DataFrame:
    """Identify Pareto non-dominated configurations for (mean_wait_s, mean_yellow_s, mean_switches)."""
    pareto_mask = np.ones(len(df), dtype=bool)
    costs = df[["mean_wait_s", "mean_yellow_s", "mean_switches"]].values
    for i, c in enumerate(costs):
        if pareto_mask[i]:
            # Keep any point that is not strictly dominated by c
            dominated = np.all(costs <= c, axis=1) & np.any(costs < c, axis=1)
            pareto_mask[dominated] = False
    pareto_df = df[pareto_mask].copy()
    return pareto_df.sort_values("composite_J").reset_index(drop=True)


def run_clean_calibration(num_workers: int = 6):
    t_start = time.time()
    print("=" * 80)
    print("STARTING CLEAN CALIBRATION SUITE")
    print(f"Configurations: 135 | Scenarios: 4 | Total Simulation Runs: 540 | Workers: {num_workers}")
    print("Demands: Medium (101), High (102), Asymmetric NS (103), Dynamic (104)")
    print("Objective: J(theta) = 0.70*(wait/25) + 0.20*(yellow/150) + 0.10*(switches/100)")
    print("=" * 80)

    # 1. Build task list
    all_combos = list(itertools.product(BETAS, DELTAS, ETAS, HYSTERESIS_VALS))
    tasks = []
    cfg_lookup = {}
    for cfg_id, (beta, delta, eta, h) in enumerate(all_combos, 1):
        cfg_name = f"CFG_{cfg_id:03d}_b{beta:.2f}_d{delta:.2f}_e{eta:.2f}_H{h:.2f}"
        cfg_lookup[cfg_id] = (cfg_name, beta, delta, eta, h)
        for sc_name, rou_file, seed in CALIB_SCENARIOS:
            tasks.append((cfg_id, beta, delta, eta, h, sc_name, rou_file, seed))

    print(f"Dispatched {len(tasks)} tasks to multiprocessing pool...")

    # 2. Execute with Multiprocessing
    with mp.Pool(processes=num_workers) as pool:
        raw_results = pool.map(run_single_simulation, tasks)

    elapsed_sim = time.time() - t_start
    print(f"[✓] All 540 simulations completed in {elapsed_sim:.1f}s ({elapsed_sim/len(tasks):.2f}s/run)")

    # 3. Aggregate across scenarios for each candidate
    df_raw = pd.DataFrame(raw_results)
    candidate_records = []

    for cfg_id, group in df_raw.groupby("cfg_id"):
        cfg_name, beta, delta, eta, h = cfg_lookup[cfg_id]

        mean_wait = float(group["wait"].mean())
        std_wait = float(group["wait"].std())
        cv_wait = float(std_wait / mean_wait) if mean_wait > 0 else 0.0
        max_wait = float(group["wait"].max())
        worst_scenario = str(group.loc[group["wait"].idxmax()]["scenario"])

        mean_delay = float(group["delay"].mean())
        mean_queue = float(group["queue"].mean())
        mean_switches = float(group["switches"].mean())
        mean_yellow = float(group["yellow_time"].mean())
        max_red_observed = float(group["max_red"].max())
        mean_throughput = float(group["throughput"].mean())

        # Pre-declared Composite Objective J(theta)
        j_obj = 0.70 * (mean_wait / W_TARGET) + 0.20 * (mean_yellow / Y_TARGET) + 0.10 * (mean_switches / S_TARGET)

        record = {
            "config_id": cfg_id,
            "cfg_name": cfg_name,
            "alpha": 1.0,
            "beta": beta,
            "delta": delta,
            "eta": eta,
            "H": h,
            "aux_weight_sum": round(beta + delta + eta, 2),
            "composite_J": round(j_obj, 5),
            "mean_wait_s": round(mean_wait, 2),
            "std_wait_s": round(std_wait, 2),
            "cv_wait": round(cv_wait, 3),
            "worst_wait_s": round(max_wait, 2),
            "worst_scenario": worst_scenario,
            "mean_delay_s": round(mean_delay, 2),
            "mean_queue_veh": round(mean_queue, 2),
            "mean_switches": round(mean_switches, 1),
            "mean_yellow_s": round(mean_yellow, 1),
            "max_red_s": round(max_red_observed, 1),
            "mean_throughput": round(mean_throughput, 1),
            # Per-scenario wait times
            "wait_medium": round(float(group.loc[group["scenario"] == "calib_medium", "wait"].values[0]), 2),
            "wait_high": round(float(group.loc[group["scenario"] == "calib_high", "wait"].values[0]), 2),
            "wait_asym": round(float(group.loc[group["scenario"] == "calib_asym", "wait"].values[0]), 2),
            "wait_dynamic": round(float(group.loc[group["scenario"] == "calib_dynamic", "wait"].values[0]), 2),
            # Per-scenario switches
            "switches_medium": int(group.loc[group["scenario"] == "calib_medium", "switches"].values[0]),
            "switches_high": int(group.loc[group["scenario"] == "calib_high", "switches"].values[0]),
            "switches_asym": int(group.loc[group["scenario"] == "calib_asym", "switches"].values[0]),
            "switches_dynamic": int(group.loc[group["scenario"] == "calib_dynamic", "switches"].values[0]),
        }
        candidate_records.append(record)

    df_results = pd.DataFrame(candidate_records)

    # 4. Pareto Frontier Extraction
    pareto_df = compute_pareto_frontier(df_results)
    pareto_df.to_csv(RESULTS_DIR / "calibration_pareto_frontier.csv", index=False)

    # 5. Pre-declared Tie-Breaking & Selection Logic:
    # 1. Lower composite J
    # 2. If within 1% of minimum composite J: lower mean_switches
    # 3. If still tied: lower sum of auxiliary weights (simpler controller)
    # 4. If still tied: smaller H
    df_sorted = df_results.sort_values("composite_J").reset_index(drop=True)
    min_j = df_sorted.iloc[0]["composite_J"]
    j_threshold = min_j * 1.01  # within 1%

    top_tier = df_sorted[df_sorted["composite_J"] <= j_threshold].copy()
    top_tier = top_tier.sort_values(
        by=["mean_switches", "aux_weight_sum", "H", "composite_J"],
        ascending=[True, True, True, True]
    ).reset_index(drop=True)

    winner = top_tier.iloc[0].to_dict()

    # Determine Runner-up: second best under tie-breaking or second lowest J
    other_candidates = df_sorted[df_sorted["config_id"] != winner["config_id"]].reset_index(drop=True)
    runner_up = other_candidates.iloc[0].to_dict()

    # Save complete calibration results table
    df_sorted.to_csv(RESULTS_DIR / "calibration_search_results.csv", index=False)

    print("\n" + "=" * 80)
    print("CALIBRATION RESULTS & SELECTION")
    print("=" * 80)
    print(f"Absolute Minimum J across all 135 configs: {min_j:.5f}")
    print(f"1% Tie-Break Threshold: {j_threshold:.5f} (Candidates in tier: {len(top_tier)})")
    print(f"\nWINNER (Selected Final Controller):")
    print(f"  Configuration: {winner['cfg_name']}")
    print(f"  Weights:       alpha=1.0, beta={winner['beta']}, delta={winner['delta']}, eta={winner['eta']}, H={winner['H']}")
    print(f"  Composite J:   {winner['composite_J']:.5f}")
    print(f"  Mean Wait:     {winner['mean_wait_s']} s (std: {winner['std_wait_s']} s, worst: {winner['worst_wait_s']} s in {winner['worst_scenario']})")
    print(f"  Mean Switches: {winner['mean_switches']}")
    print(f"  Mean Yellow:   {winner['mean_yellow_s']} s")
    print(f"  Scenarios Wait: Medium={winner['wait_medium']}s, High={winner['wait_high']}s, Asym={winner['wait_asym']}s, Dynamic={winner['wait_dynamic']}s")

    print(f"\nRUNNER UP:")
    print(f"  Configuration: {runner_up['cfg_name']}")
    print(f"  Weights:       alpha=1.0, beta={runner_up['beta']}, delta={runner_up['delta']}, eta={runner_up['eta']}, H={runner_up['H']}")
    print(f"  Composite J:   {runner_up['composite_J']:.5f}")
    print(f"  Mean Wait:     {runner_up['mean_wait_s']} s (std: {runner_up['std_wait_s']} s, worst: {runner_up['worst_wait_s']} s in {runner_up['worst_scenario']})")
    print(f"  Mean Switches: {runner_up['mean_switches']}")
    print(f"  Mean Yellow:   {runner_up['mean_yellow_s']} s")
    print("=" * 80)

    return winner, runner_up, df_results, pareto_df


if __name__ == "__main__":
    run_clean_calibration()
