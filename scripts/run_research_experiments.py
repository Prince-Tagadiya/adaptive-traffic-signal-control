"""
Master Research Experiment Runner for Adaptive Traffic Signal Control.

Executes:
1. Multi-Demand & Multi-Seed Benchmark (Fixed-Time, Basic Queue, Proposed Controller)
   across 7 scenarios and 5 random seeds (42-46) using immutable route files.
2. Systematic Ablation Study (Models 0 through 6).
3. Robustness Experiments (Sensor noise sigma in [0.0, 1.0, 2.0, 3.0]).
4. Sensitivity Experiments (G_min, G_max, Hysteresis H, Arrival Window W_A).
5. Computational Cost Profiling (Decision step runtime in microseconds).
6. Statistical Significance Tests (Paired differences, 95% CIs, Wilcoxon, Paired t-tests, Cohen's d).

All outputs are saved to results/ and data/ in reproducible CSV formats.
"""

import os
import sys
import time
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from simulation.runner import SimulationRunner
from controllers.fixed_time_controller import FixedTimeSignalController
from controllers.basic_density_controller import BasicDensityController
from controllers.proposed_adaptive_controller import ProposedAdaptiveSignalController

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = str(BASE_DIR / "scenarios" / "four_arm.sumocfg")
DEMAND_DIR = BASE_DIR / "scenarios" / "demand"
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = BASE_DIR / "data"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 43, 44, 45, 46]
SCENARIOS = ["low", "medium", "high", "oversaturated", "asym_ns", "asym_ew", "dynamic"]


def get_route_path(scenario: str, seed: int) -> str:
    path = DEMAND_DIR / f"demand_{scenario}_seed{seed}.rou.xml"
    if not path.exists():
        raise FileNotFoundError(f"Route file not found: {path}")
    return str(path)


def run_benchmark_experiments() -> pd.DataFrame:
    """
    Executes the 3 controllers (Fixed, Basic, Proposed) across 7 scenarios and 5 seeds.
    Principle: ONE TRAFFIC REALIZATION -> MULTIPLE CONTROLLERS.
    """
    print("\n" + "=" * 70)
    print("RUNNING MULTI-DEMAND & MULTI-SEED BENCHMARK (105 RUNS)")
    print("=" * 70)

    records = []

    for scenario in SCENARIOS:
        print(f"\n---> Scenario: {scenario.upper()}")
        for seed in SEEDS:
            route_path = get_route_path(scenario, seed)

            # Controller 1: Fixed-Time Baseline
            c_fixed = FixedTimeSignalController()
            r_fixed = SimulationRunner(
                config_path=CONFIG_PATH,
                route_path=route_path,
                controller=c_fixed,
                seed=seed,
            ).run()
            res_fixed = r_fixed["summary"]
            res_fixed.update({
                "controller": "Fixed-Time",
                "scenario": scenario,
            })
            records.append(res_fixed)

            # Controller 2: Basic Queue-Based Controller
            c_basic = BasicDensityController()
            r_basic = SimulationRunner(
                config_path=CONFIG_PATH,
                route_path=route_path,
                controller=c_basic,
                seed=seed,
            ).run()
            res_basic = r_basic["summary"]
            res_basic.update({
                "controller": "Basic-Queue",
                "scenario": scenario,
            })
            records.append(res_basic)

            # Controller 3: Full Proposed Controller
            c_prop = ProposedAdaptiveSignalController(
                alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.4, hysteresis=0.25
            )
            r_prop = SimulationRunner(
                config_path=CONFIG_PATH,
                route_path=route_path,
                controller=c_prop,
                seed=seed,
            ).run()
            res_prop = r_prop["summary"]
            res_prop.update({
                "controller": "Proposed-Adaptive",
                "scenario": scenario,
            })
            records.append(res_prop)

            # If seed == 42, export decisions log and timeseries for plotting
            if seed == 42 and scenario == "medium":
                c_prop.get_decisions_df().to_csv(DATA_DIR / "proposed_controller_decisions_seed42.csv", index=False)
                r_fixed["step_dataframe"].to_csv(DATA_DIR / "timeseries_fixed_seed42.csv", index=False)
                r_basic["step_dataframe"].to_csv(DATA_DIR / "timeseries_basic_seed42.csv", index=False)
                r_prop["step_dataframe"].to_csv(DATA_DIR / "timeseries_proposed_seed42.csv", index=False)

            print(
                f"  Seed {seed:2d} | "
                f"Fixed Wait: {res_fixed['avg_waiting_time_s']:5.2f}s | "
                f"Basic Wait: {res_basic['avg_waiting_time_s']:5.2f}s | "
                f"Proposed Wait: {res_prop['avg_waiting_time_s']:5.2f}s"
            )

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "multi_demand_comparison_results.csv", index=False)
    print(f"\n[OK] Saved multi-demand benchmark results to {RESULTS_DIR / 'multi_demand_comparison_results.csv'}")
    return df


def run_ablation_experiments() -> pd.DataFrame:
    """
    Executes the 7 ablation models on Medium and High demand scenarios across 5 seeds:
    Model 0: Fixed-Time
    Model 1: Basic Queue Only (alpha=1.0, others=0, H=0)
    Model 2: Queue + Arrival (alpha=1.0, beta=0.5)
    Model 3: Queue + Arrival + Growth (gamma=0.3)
    Model 4: Queue + Arrival + Growth + Waiting Burden (delta=0.4)
    Model 5: Queue + Arrival + Growth + Wait + Continuous Fairness (eta=0.4)
    Model 6: Full Proposed (+ Hysteresis H=0.25)
    """
    print("\n" + "=" * 70)
    print("RUNNING COMPONENT ABLATION STUDY (MODELS 0 TO 6)")
    print("=" * 70)

    ablation_configs = [
        ("Model_0_FixedTime", "Fixed-Time Plan", None),
        ("Model_1_QueueOnly", "Q only", dict(alpha=1.0, beta=0.0, gamma=0.0, delta=0.0, eta=0.0, hysteresis=0.0)),
        ("Model_2_QueueArrival", "Q + A", dict(alpha=1.0, beta=0.5, gamma=0.0, delta=0.0, eta=0.0, hysteresis=0.0)),
        ("Model_3_QueueArrivalGrowth", "Q + A + G", dict(alpha=1.0, beta=0.5, gamma=0.3, delta=0.0, eta=0.0, hysteresis=0.0)),
        ("Model_4_QueueArrivalGrowthWait", "Q + A + G + W", dict(alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.0, hysteresis=0.0)),
        ("Model_5_QueueArrivalGrowthWaitFair", "Q + A + G + W + R", dict(alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.4, hysteresis=0.0)),
        ("Model_6_FullProposed", "Full (+ Hysteresis)", dict(alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.4, hysteresis=0.25)),
    ]

    records = []
    test_scenarios = ["medium", "high"]

    for sc in test_scenarios:
        print(f"\n---> Ablation Scenario: {sc.upper()}")
        for model_id, model_name, kwargs in ablation_configs:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                if kwargs is None:
                    ctrl = FixedTimeSignalController()
                else:
                    ctrl = ProposedAdaptiveSignalController(**kwargs)

                runner = SimulationRunner(
                    config_path=CONFIG_PATH,
                    route_path=route_path,
                    controller=ctrl,
                    seed=seed,
                )
                res = runner.run()["summary"]
                res.update({
                    "model_id": model_id,
                    "model_name": model_name,
                    "scenario": sc,
                })
                records.append(res)

            # Print average wait across seeds
            m_df = pd.DataFrame([r for r in records if r["model_id"] == model_id and r["scenario"] == sc])
            mean_w = m_df["avg_waiting_time_s"].mean()
            mean_d = m_df["avg_delay_s"].mean()
            mean_sw = m_df["phase_switch_count"].mean()
            print(f"  {model_id:<32} | Avg Wait: {mean_w:5.2f}s | Avg Delay: {mean_d:5.2f}s | Switches: {mean_sw:4.1f}")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "ablation_study_results.csv", index=False)
    print(f"\n[OK] Saved ablation study results to {RESULTS_DIR / 'ablation_study_results.csv'}")
    return df


def run_robustness_experiments() -> pd.DataFrame:
    """
    Evaluates Proposed Controller under queue observation noise (sigma in [0.0, 1.0, 2.0, 3.0]).
    """
    print("\n" + "=" * 70)
    print("RUNNING ROBUSTNESS EXPERIMENTS (MEASUREMENT NOISE)")
    print("=" * 70)

    noise_levels = [0.0, 1.0, 2.0, 3.0]
    records = []

    for sc in ["medium", "high"]:
        print(f"\n---> Robustness Scenario: {sc.upper()}")
        for sigma in noise_levels:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                ctrl = ProposedAdaptiveSignalController(
                    alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.4,
                    hysteresis=0.25, noise_std=sigma
                )
                runner = SimulationRunner(
                    config_path=CONFIG_PATH,
                    route_path=route_path,
                    controller=ctrl,
                    seed=seed,
                )
                res = runner.run()["summary"]
                res.update({
                    "scenario": sc,
                    "noise_sigma": sigma,
                })
                records.append(res)

            sub_df = pd.DataFrame([r for r in records if r["scenario"] == sc and r["noise_sigma"] == sigma])
            print(f"  Noise Sigma = {sigma:3.1f} | Avg Wait: {sub_df['avg_waiting_time_s'].mean():5.2f}s | Avg Queue: {sub_df['avg_queue_length_veh'].mean():5.2f}")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "robustness_study_results.csv", index=False)
    print(f"\n[OK] Saved robustness results to {RESULTS_DIR / 'robustness_study_results.csv'}")
    return df


def run_sensitivity_experiments() -> pd.DataFrame:
    """
    Evaluates parameter sensitivity for G_min, G_max, Hysteresis, and Arrival Window W_A.
    """
    print("\n" + "=" * 70)
    print("RUNNING SENSITIVITY EXPERIMENTS (PARAMETER SWEEPS)")
    print("=" * 70)

    records = []
    sc = "medium"

    # 1. Sweep G_min
    for gmin in [10, 15, 20]:
        for seed in SEEDS:
            ctrl = ProposedAdaptiveSignalController(min_green=gmin)
            res = SimulationRunner(CONFIG_PATH, get_route_path(sc, seed), controller=ctrl, seed=seed).run()["summary"]
            res.update({"param_tested": "G_min", "param_val": gmin, "scenario": sc})
            records.append(res)

    # 2. Sweep G_max
    for gmax in [35, 50, 70]:
        for seed in SEEDS:
            ctrl = ProposedAdaptiveSignalController(max_green=gmax)
            res = SimulationRunner(CONFIG_PATH, get_route_path(sc, seed), controller=ctrl, seed=seed).run()["summary"]
            res.update({"param_tested": "G_max", "param_val": gmax, "scenario": sc})
            records.append(res)

    # 3. Sweep Hysteresis
    for h in [0.0, 0.15, 0.25, 0.40]:
        for seed in SEEDS:
            ctrl = ProposedAdaptiveSignalController(hysteresis=h)
            res = SimulationRunner(CONFIG_PATH, get_route_path(sc, seed), controller=ctrl, seed=seed).run()["summary"]
            res.update({"param_tested": "Hysteresis", "param_val": h, "scenario": sc})
            records.append(res)

    # 4. Sweep Arrival Window W_A
    for wa in [10, 20, 30]:
        for seed in SEEDS:
            ctrl = ProposedAdaptiveSignalController(w_arrival=wa)
            res = SimulationRunner(CONFIG_PATH, get_route_path(sc, seed), controller=ctrl, seed=seed).run()["summary"]
            res.update({"param_tested": "Window_WA", "param_val": wa, "scenario": sc})
            records.append(res)

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "sensitivity_study_results.csv", index=False)
    print(f"\n[OK] Saved sensitivity results to {RESULTS_DIR / 'sensitivity_study_results.csv'}")
    return df


def run_statistical_and_cost_analysis(benchmark_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs rigorous matched-pair statistical tests between Proposed and Baselines,
    and profiles controller decision runtime in microseconds.
    """
    print("\n" + "=" * 70)
    print("RUNNING STATISTICAL INFERENCE & COMPUTATIONAL COST PROFILING")
    print("=" * 70)

    # 1. Statistical Analysis
    stat_records = []
    for sc in SCENARIOS:
        sub_df = benchmark_df[benchmark_df["scenario"] == sc]

        # Match seeds
        prop_vals = sub_df[sub_df["controller"] == "Proposed-Adaptive"].sort_values("seed")
        fixed_vals = sub_df[sub_df["controller"] == "Fixed-Time"].sort_values("seed")
        basic_vals = sub_df[sub_df["controller"] == "Basic-Queue"].sort_values("seed")

        # Compare against Fixed-Time
        diff_fixed_wait = prop_vals["avg_waiting_time_s"].values - fixed_vals["avg_waiting_time_s"].values
        diff_fixed_delay = prop_vals["avg_delay_s"].values - fixed_vals["avg_delay_s"].values

        # Compare against Basic-Queue
        diff_basic_wait = prop_vals["avg_waiting_time_s"].values - basic_vals["avg_waiting_time_s"].values
        diff_basic_delay = prop_vals["avg_delay_s"].values - basic_vals["avg_delay_s"].values

        def get_stats(diffs):
            mean_d = float(np.mean(diffs))
            std_d = float(np.std(diffs, ddof=1)) if len(diffs) > 1 else 0.0
            n = len(diffs)
            se = std_d / np.sqrt(n) if n > 0 else 0.0
            # 95% CI
            t_crit = stats.t.ppf(0.975, df=n - 1) if n > 1 else 0.0
            ci_low = mean_d - t_crit * se
            ci_high = mean_d + t_crit * se
            cohen_d = mean_d / std_d if std_d > 0 else 0.0

            # Paired t-test
            try:
                t_stat, p_val_t = stats.ttest_1samp(diffs, 0.0)
            except Exception:
                t_stat, p_val_t = 0.0, 1.0

            # Wilcoxon signed rank test
            try:
                w_stat, p_val_w = stats.wilcoxon(diffs)
            except Exception:
                w_stat, p_val_w = 0.0, 1.0

            return {
                "mean_diff": round(mean_d, 2),
                "std_diff": round(std_d, 2),
                "ci_95_low": round(ci_low, 2),
                "ci_95_high": round(ci_high, 2),
                "t_stat": round(float(t_stat), 3),
                "p_val_ttest": float(p_val_t),
                "p_val_wilcoxon": float(p_val_w),
                "cohen_d": round(cohen_d, 3),
            }

        st_fixed_wait = get_stats(diff_fixed_wait)
        st_basic_wait = get_stats(diff_basic_wait)

        stat_records.append({
            "scenario": sc,
            "comparison": "Proposed vs Fixed-Time",
            "metric": "avg_waiting_time_s",
            **st_fixed_wait
        })
        stat_records.append({
            "scenario": sc,
            "comparison": "Proposed vs Basic-Queue",
            "metric": "avg_waiting_time_s",
            **st_basic_wait
        })

    stats_df = pd.DataFrame(stat_records)
    stats_df.to_csv(RESULTS_DIR / "statistical_tests.csv", index=False)
    print(f"[OK] Saved statistical test results to {RESULTS_DIR / 'statistical_tests.csv'}")

    # 2. Computational Cost Analysis
    # Load logged decisions for seed 42 to profile execution time
    dec_file = DATA_DIR / "proposed_controller_decisions_seed42.csv"
    if dec_file.exists():
        d_df = pd.read_csv(dec_file)
        comp_times = d_df["Compute_Time_us"].dropna().values
        mean_us = float(np.mean(comp_times))
        max_us = float(np.max(comp_times))
        min_us = float(np.min(comp_times))
        std_us = float(np.std(comp_times))
        decisions_per_sec = 1_000_000.0 / mean_us if mean_us > 0 else 0.0

        cost_records = [{
            "controller": "Proposed-Adaptive",
            "mean_compute_us": round(mean_us, 2),
            "std_compute_us": round(std_us, 2),
            "min_compute_us": round(min_us, 2),
            "max_compute_us": round(max_us, 2),
            "decisions_per_second": round(decisions_per_sec, 1),
            "total_decisions_profiled": len(comp_times),
            "real_time_budget_us": 1_000_000.0, # 1 second control step
            "budget_utilization_pct": round((mean_us / 1_000_000.0) * 100, 4)
        }]
    else:
        cost_records = []

    cost_df = pd.DataFrame(cost_records)
    cost_df.to_csv(RESULTS_DIR / "computational_cost.csv", index=False)
    print(f"[OK] Saved computational cost results to {RESULTS_DIR / 'computational_cost.csv'}")

    return stats_df, cost_df


def main():
    start_time = time.time()
    print("=" * 70)
    print("STARTING FULL RESEARCH EXPERIMENT SUITE")
    print("=" * 70)

    # 1. Multi-Demand & Multi-Seed Benchmark
    benchmark_df = run_benchmark_experiments()

    # 2. Ablation Study
    run_ablation_experiments()

    # 3. Robustness Study
    run_robustness_experiments()

    # 4. Sensitivity Study
    run_sensitivity_experiments()

    # 5. Statistical & Cost Analysis
    run_statistical_and_cost_analysis(benchmark_df)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"ALL EXPERIMENTS SUCCESSFULLY EXECUTED IN {elapsed:.1f} SECONDS")
    print("=" * 70)


if __name__ == "__main__":
    main()
