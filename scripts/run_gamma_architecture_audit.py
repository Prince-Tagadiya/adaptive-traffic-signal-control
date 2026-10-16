"""
Clean Architecture Audit for Queue-Growth Weight (Gamma).

Exclusively evaluates gamma in {0.00, 0.10, 0.20, 0.30} on the dedicated
Calibration Suite (Seeds 101, 102, 103, 104).
Zero exposure to evaluation test seeds (42-46).

Frozen parameters held constant:
    alpha = 1.00
    beta  = 0.75
    delta = 0.25
    eta   = 0.25
    H     = 0.20
    Q_ref = 20.0
    A_ref = 0.40
    W_ref = 30.0
    R_ref = 50.0
    W_A   = 20
    G_min = 15, G_max = 50, R_starve = 45, Yellow = 3

Pre-declared Optimization Objective:
    J = 0.70 * (mean_wait / 25.0) + 0.20 * (mean_yellow / 150.0) + 0.10 * (mean_switches / 100.0)
"""

import sys
import time
from pathlib import Path
import multiprocessing as mp
from typing import Dict, Any, List, Tuple
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from simulation.runner import SimulationRunner
from controllers.proposed_adaptive_controller import ProposedAdaptiveSignalController

CONFIG_PATH = str(BASE_DIR / "scenarios" / "four_arm.sumocfg")
DEMAND_DIR = BASE_DIR / "scenarios" / "demand"
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CALIB_SCENARIOS = [
    ("calib_medium", "calib_medium_seed101.rou.xml", 101),
    ("calib_high", "calib_high_seed102.rou.xml", 102),
    ("calib_asym", "calib_asym_seed103.rou.xml", 103),
    ("calib_dynamic", "calib_dynamic_seed104.rou.xml", 104),
]

GAMMA_CANDIDATES = [0.00, 0.10, 0.20, 0.30]

W_TARGET = 25.0
Y_TARGET = 150.0
S_TARGET = 100.0


def run_gamma_task(args: Tuple) -> Dict[str, Any]:
    gamma, sc_name, rou_file, seed = args
    rou_path = str(DEMAND_DIR / rou_file)
    ctrl = ProposedAdaptiveSignalController(
        alpha=1.0,
        beta=0.75,
        gamma=gamma,
        delta=0.25,
        eta=0.25,
        hysteresis=0.20,
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
        "gamma": gamma,
        "scenario": sc_name,
        "wait": res["avg_waiting_time_s"],
        "delay": res["avg_delay_s"],
        "queue": res["avg_queue_length_veh"],
        "switches": res["phase_switch_count"],
        "yellow_time": res["total_yellow_lost_time_s"],
        "max_red": res["max_red_duration_s"],
        "throughput": res["cohort_a_completed"],
    }


def execute_gamma_audit(num_workers: int = 4):
    print("=" * 80)
    print("STARTING CALIBRATION-ONLY ARCHITECTURE AUDIT: QUEUE GROWTH (GAMMA)")
    print("Testing gamma in {0.00, 0.10, 0.20, 0.30} across Calibration Seeds 101-104")
    print("=" * 80)

    tasks = []
    for gamma in GAMMA_CANDIDATES:
        for sc_name, rou_file, seed in CALIB_SCENARIOS:
            tasks.append((gamma, sc_name, rou_file, seed))

    with mp.Pool(processes=num_workers) as pool:
        raw_results = pool.map(run_gamma_task, tasks)

    df_raw = pd.DataFrame(raw_results)
    records = []

    for gamma, group in df_raw.groupby("gamma"):
        mean_wait = float(group["wait"].mean())
        mean_switches = float(group["switches"].mean())
        mean_yellow = float(group["yellow_time"].mean())
        mean_delay = float(group["delay"].mean())
        mean_queue = float(group["queue"].mean())
        max_red = float(group["max_red"].max())

        j_val = 0.70 * (mean_wait / W_TARGET) + 0.20 * (mean_yellow / Y_TARGET) + 0.10 * (mean_switches / S_TARGET)

        w_med = float(group.loc[group["scenario"] == "calib_medium", "wait"].values[0])
        w_high = float(group.loc[group["scenario"] == "calib_high", "wait"].values[0])
        w_asym = float(group.loc[group["scenario"] == "calib_asym", "wait"].values[0])
        w_dyn = float(group.loc[group["scenario"] == "calib_dynamic", "wait"].values[0])

        s_med = int(group.loc[group["scenario"] == "calib_medium", "switches"].values[0])
        s_high = int(group.loc[group["scenario"] == "calib_high", "switches"].values[0])
        s_asym = int(group.loc[group["scenario"] == "calib_asym", "switches"].values[0])
        s_dyn = int(group.loc[group["scenario"] == "calib_dynamic", "switches"].values[0])

        records.append({
            "gamma": gamma,
            "composite_J": round(j_val, 5),
            "mean_wait_s": round(mean_wait, 2),
            "mean_yellow_s": round(mean_yellow, 1),
            "mean_switches": round(mean_switches, 1),
            "mean_delay_s": round(mean_delay, 2),
            "mean_queue_veh": round(mean_queue, 2),
            "max_red_s": round(max_red, 1),
            "wait_medium": round(w_med, 2),
            "wait_high": round(w_high, 2),
            "wait_asym": round(w_asym, 2),
            "wait_dynamic": round(w_dyn, 2),
            "switches_medium": s_med,
            "switches_high": s_high,
            "switches_asym": s_asym,
            "switches_dynamic": s_dyn,
        })

    df_summary = pd.DataFrame(records).sort_values("gamma").reset_index(drop=True)
    df_summary.to_csv(RESULTS_DIR / "gamma_architecture_audit_results.csv", index=False)

    print("\n" + "=" * 80)
    print("GAMMA ARCHITECTURE AUDIT RESULTS (SEEDS 101-104)")
    print("=" * 80)
    print(df_summary[["gamma", "composite_J", "mean_wait_s", "mean_yellow_s", "mean_switches", "wait_medium", "wait_high", "wait_asym", "wait_dynamic"]].to_string(index=False))
    print("=" * 80)

    return df_summary


if __name__ == "__main__":
    execute_gamma_audit()
