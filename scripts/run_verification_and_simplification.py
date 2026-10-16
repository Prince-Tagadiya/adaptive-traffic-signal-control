"""
Verification and Simplification Study for Adaptive Traffic Signal Control.

Executes:
1. Major 4-Way Comparison:
   - C0: Original Fixed-Time Baseline (42/3/42/3, Cycle=90s)
   - C1: Optimized Fixed-Time Baseline (Webster calibrated: 15/3/15/3, Cycle=36s)
   - C2: Basic Queue Controller (Instantaneous Halting Queue Comparison)
   - C3: Proposed Composite Controller (Full Multi-Variable with Hysteresis)
   Across 7 scenarios and 5 random seeds (42-46).
2. Controller Simplification Study (Component Pruning):
   - Model A: Queue only
   - Model B: Queue + waiting burden
   - Model C: Queue + waiting + red-time fairness
   - Model D: Queue + arrival rate + waiting + fairness
   - Model E: Full Model (Queue + arrival + growth + waiting + fairness + hysteresis)
   Across Symmetric (Med, High), Asymmetric (NS, EW), and Dynamic demand profiles.
3. Queue-Growth Smoothing Investigation:
   - Variant A: No growth term (gamma = 0)
   - Variant B: Raw finite difference
   - Variant C: Exponentially smoothed growth (EMA, alpha=0.2)
   - Variant D: Simple moving-average growth (SMA)
4. Hysteresis Margin Investigation:
   - H in [0.00, 0.10, 0.25, 0.50, 1.00]
5. Noise Robustness Audit:
   - sigma in [0.0, 0.5, 1.0, 2.0, 3.0]
6. Verified Statistical Analysis:
   - Correct experimental unit: matched seed realization (N=5).
   - Paired t-tests, Wilcoxon signed-rank tests, 95% CIs, paired Cohen's d_z,
     and Holm-Bonferroni & Benjamini-Hochberg FDR multiple-comparison corrections.
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

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

SEEDS = [42, 43, 44, 45, 46]
SCENARIOS = ["low", "medium", "high", "oversaturated", "asym_ns", "asym_ew", "dynamic"]


def get_route_path(scenario: str, seed: int) -> str:
    path = DEMAND_DIR / f"demand_{scenario}_seed{seed}.rou.xml"
    if not path.exists():
        raise FileNotFoundError(f"Route file not found: {path}")
    return str(path)


# ==============================================================================
# 1. Major 4-Way Comparison
# ==============================================================================
def run_major_comparison() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("TASK 4: MAJOR 4-WAY COMPARISON (C0, C1, C2, C3 across 7 scenarios, 5 seeds)")
    print("=" * 70)

    records = []
    controllers = [
        ("C0_Original_FixedTime", lambda: FixedTimeSignalController()),
        ("C1_Optimized_FixedTime", lambda: OptimizedFixedTimeSignalController()),
        ("C2_Basic_Queue", lambda: BasicDensityController()),
        ("C3_Proposed_Composite", lambda: ProposedAdaptiveSignalController(
            alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.4, hysteresis=0.25
        )),
    ]

    for sc in SCENARIOS:
        print(f"\n---> Scenario: {sc.upper()}")
        for c_id, c_factory in controllers:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                ctrl = c_factory()
                runner = SimulationRunner(
                    config_path=CONFIG_PATH,
                    route_path=route_path,
                    controller=ctrl,
                    seed=seed,
                )
                res = runner.run()["summary"]
                res.update({
                    "controller_id": c_id,
                    "scenario": sc,
                })
                records.append(res)

            sub = pd.DataFrame([r for r in records if r["scenario"] == sc and r["controller_id"] == c_id])
            print(f"  {c_id:<24} | Wait: {sub['avg_waiting_time_s'].mean():5.2f}s | Delay: {sub['avg_delay_s'].mean():5.2f}s | Queue: {sub['avg_queue_length_veh'].mean():4.2f} | Switches: {sub['phase_switch_count'].mean():4.1f}")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "major_comparison_4controllers.csv", index=False)
    print(f"\n[OK] Saved 4-way comparison to {RESULTS_DIR / 'major_comparison_4controllers.csv'}")
    return df


# ==============================================================================
# 2. Controller Simplification & Variable Pruning Study
# ==============================================================================
def run_simplification_study() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("TASK 5 & 6: CONTROLLER SIMPLIFICATION STUDY (MODELS A TO E)")
    print("=" * 70)

    models = [
        ("Model_A_QueueOnly", dict(alpha=1.0, beta=0.0, gamma=0.0, delta=0.0, eta=0.0, hysteresis=0.0)),
        ("Model_B_QueueWait", dict(alpha=1.0, beta=0.0, gamma=0.0, delta=0.4, eta=0.0, hysteresis=0.0)),
        ("Model_C_QueueWaitFair", dict(alpha=1.0, beta=0.0, gamma=0.0, delta=0.4, eta=0.4, hysteresis=0.0)),
        ("Model_D_QueueArrivalWaitFair", dict(alpha=1.0, beta=0.5, gamma=0.0, delta=0.4, eta=0.4, hysteresis=0.0)),
        ("Model_E_FullComposite", dict(alpha=1.0, beta=0.5, gamma=0.3, delta=0.4, eta=0.4, hysteresis=0.25)),
    ]

    target_scenarios = ["medium", "high", "asym_ns", "asym_ew", "dynamic"]
    records = []

    for sc in target_scenarios:
        print(f"\n---> Simplification Scenario: {sc.upper()}")
        for m_id, kwargs in models:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                ctrl = ProposedAdaptiveSignalController(**kwargs)
                runner = SimulationRunner(
                    config_path=CONFIG_PATH,
                    route_path=route_path,
                    controller=ctrl,
                    seed=seed,
                )
                res = runner.run()["summary"]
                res.update({
                    "model_id": m_id,
                    "scenario": sc,
                })
                records.append(res)

            sub = pd.DataFrame([r for r in records if r["scenario"] == sc and r["model_id"] == m_id])
            print(f"  {m_id:<28} | Wait: {sub['avg_waiting_time_s'].mean():5.2f}s | Delay: {sub['avg_delay_s'].mean():5.2f}s | Switches: {sub['phase_switch_count'].mean():4.1f} | MaxRed: {sub['max_red_duration_s'].mean():4.1f}s")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "controller_simplification_study.csv", index=False)
    print(f"\n[OK] Saved simplification study to {RESULTS_DIR / 'controller_simplification_study.csv'}")
    return df


# ==============================================================================
# 3. Queue-Growth Smoothing Investigation
# ==============================================================================
def run_growth_smoothing_study() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("TASK 7: QUEUE-GROWTH SMOOTHING INVESTIGATION (NONE, RAW, EMA, SMA)")
    print("=" * 70)

    growth_variants = [
        ("Variant_A_None", dict(gamma=0.0, growth_smoothing="none")),
        ("Variant_B_Raw", dict(gamma=0.3, growth_smoothing="raw")),
        ("Variant_C_EMA", dict(gamma=0.3, growth_smoothing="ema", growth_ema_alpha=0.2)),
        ("Variant_D_SMA", dict(gamma=0.3, growth_smoothing="sma")),
    ]

    records = []
    for sc in ["medium", "high"]:
        print(f"\n---> Growth Smoothing Scenario: {sc.upper()}")
        for v_id, kwargs in growth_variants:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                ctrl = ProposedAdaptiveSignalController(
                    alpha=1.0, beta=0.5, delta=0.4, eta=0.4, hysteresis=0.25, **kwargs
                )
                runner = SimulationRunner(
                    config_path=CONFIG_PATH,
                    route_path=route_path,
                    controller=ctrl,
                    seed=seed,
                )
                res = runner.run()["summary"]
                res.update({
                    "variant_id": v_id,
                    "scenario": sc,
                })
                records.append(res)

            sub = pd.DataFrame([r for r in records if r["scenario"] == sc and r["variant_id"] == v_id])
            print(f"  {v_id:<16} | Wait: {sub['avg_waiting_time_s'].mean():5.2f}s | Delay: {sub['avg_delay_s'].mean():5.2f}s | Switches: {sub['phase_switch_count'].mean():4.1f}")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "growth_smoothing_study.csv", index=False)
    print(f"\n[OK] Saved growth smoothing study to {RESULTS_DIR / 'growth_smoothing_study.csv'}")
    return df


# ==============================================================================
# 4. Hysteresis Margin Investigation
# ==============================================================================
def run_hysteresis_study() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("TASK 8: HYSTERESIS INVESTIGATION (H = 0.0, 0.10, 0.25, 0.50, 1.00)")
    print("=" * 70)

    h_values = [0.00, 0.10, 0.25, 0.50, 1.00]
    records = []

    for sc in ["medium", "high"]:
        print(f"\n---> Hysteresis Scenario: {sc.upper()}")
        for h in h_values:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                ctrl = ProposedAdaptiveSignalController(
                    alpha=1.0, beta=0.5, gamma=0.0, delta=0.4, eta=0.4, hysteresis=h
                )
                runner = SimulationRunner(
                    config_path=CONFIG_PATH,
                    route_path=route_path,
                    controller=ctrl,
                    seed=seed,
                )
                res = runner.run()["summary"]
                res.update({
                    "hysteresis_H": h,
                    "scenario": sc,
                })
                records.append(res)

            sub = pd.DataFrame([r for r in records if r["scenario"] == sc and r["hysteresis_H"] == h])
            print(f"  H = {h:4.2f} | Wait: {sub['avg_waiting_time_s'].mean():5.2f}s | Switches: {sub['phase_switch_count'].mean():4.1f} | Yellow Lost: {sub['total_yellow_lost_time_s'].mean():5.1f}s | MaxRed: {sub['max_red_duration_s'].mean():4.1f}s")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "hysteresis_investigation_study.csv", index=False)
    print(f"\n[OK] Saved hysteresis investigation to {RESULTS_DIR / 'hysteresis_investigation_study.csv'}")
    return df


# ==============================================================================
# 5. Noise Robustness Audit
# ==============================================================================
def run_noise_audit() -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("TASK 2: AUDIT NOISE ROBUSTNESS (sigma in [0.0, 0.5, 1.0, 2.0, 3.0])")
    print("=" * 70)

    noise_levels = [0.0, 0.5, 1.0, 2.0, 3.0]
    records = []

    for sc in ["medium", "high"]:
        print(f"\n---> Robustness Scenario: {sc.upper()}")
        for sigma in noise_levels:
            for seed in SEEDS:
                route_path = get_route_path(sc, seed)
                ctrl = ProposedAdaptiveSignalController(
                    alpha=1.0, beta=0.5, gamma=0.0, delta=0.4, eta=0.4,
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
                    "noise_sigma": sigma,
                    "scenario": sc,
                })
                records.append(res)

            sub = pd.DataFrame([r for r in records if r["scenario"] == sc and r["noise_sigma"] == sigma])
            print(f"  Noise Sigma = {sigma:3.1f} | Wait: {sub['avg_waiting_time_s'].mean():5.2f}s | Queue: {sub['avg_queue_length_veh'].mean():4.2f} | Switches: {sub['phase_switch_count'].mean():4.1f}")

    df = pd.DataFrame(records)
    df.to_csv(RESULTS_DIR / "robustness_study_verified.csv", index=False)
    print(f"\n[OK] Saved verified robustness results to {RESULTS_DIR / 'robustness_study_verified.csv'}")
    return df


# ==============================================================================
# 6. Verified Statistical Analysis with Multiple-Comparison Corrections
# ==============================================================================
def run_verified_statistical_analysis(comp_df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 70)
    print("TASK 1: VERIFIED STATISTICAL ANALYSIS (MATCHED SEEDS N=5)")
    print("=" * 70)

    comparisons = [
        ("C3 vs C0", "Proposed-Composite vs Original Fixed-Time", "C3_Proposed_Composite", "C0_Original_FixedTime"),
        ("C3 vs C1", "Proposed-Composite vs Optimized Fixed-Time", "C3_Proposed_Composite", "C1_Optimized_FixedTime"),
        ("C3 vs C2", "Proposed-Composite vs Basic-Queue", "C3_Proposed_Composite", "C2_Basic_Queue"),
        ("C2 vs C1", "Basic-Queue vs Optimized Fixed-Time", "C2_Basic_Queue", "C1_Optimized_FixedTime"),
    ]

    stat_rows = []

    for sc in SCENARIOS:
        sub = comp_df[comp_df["scenario"] == sc]

        for pair_code, pair_label, ctrl_a, ctrl_b in comparisons:
            df_a = sub[sub["controller_id"] == ctrl_a].sort_values("seed")
            df_b = sub[sub["controller_id"] == ctrl_b].sort_values("seed")

            diffs = df_a["avg_waiting_time_s"].values - df_b["avg_waiting_time_s"].values
            n = len(diffs)
            mean_d = float(np.mean(diffs))
            std_d = float(np.std(diffs, ddof=1)) if n > 1 else 0.0
            se = std_d / np.sqrt(n) if n > 0 else 0.0

            # Two-sided 95% CI
            t_crit = stats.t.ppf(0.975, df=n - 1) if n > 1 else 0.0
            ci_low = mean_d - t_crit * se
            ci_high = mean_d + t_crit * se

            # Paired Cohen's d_z = mean_diff / std_diff
            cohen_dz = mean_d / std_d if std_d > 0 else 0.0

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

            stat_rows.append({
                "scenario": sc,
                "comparison_code": pair_code,
                "comparison_label": pair_label,
                "sample_size_N": n,
                "mean_diff_s": round(mean_d, 2),
                "std_diff_s": round(std_d, 2),
                "se_diff_s": round(se, 2),
                "ci_95_low": round(ci_low, 2),
                "ci_95_high": round(ci_high, 2),
                "t_stat": round(float(t_stat), 3),
                "p_raw_ttest": float(p_val_t),
                "p_raw_wilcoxon": float(p_val_w),
                "cohen_dz": round(cohen_dz, 3),
            })

    stats_df = pd.DataFrame(stat_rows)

    # Apply Multiple-Comparison Corrections across all hypotheses tested
    # 1. Holm-Bonferroni step-down correction
    m = len(stats_df)
    stats_df = stats_df.sort_values("p_raw_ttest").reset_index(drop=True)
    holm_p = []
    cum_max = 0.0
    for idx, row in stats_df.iterrows():
        k = idx + 1
        adj = (m - k + 1) * row["p_raw_ttest"]
        cum_max = max(cum_max, adj)
        holm_p.append(min(1.0, cum_max))
    stats_df["p_holm_bonferroni"] = np.round(holm_p, 6)

    # 2. Benjamini-Hochberg False Discovery Rate (FDR)
    bh_p = []
    for idx, row in stats_df.iterrows():
        k = idx + 1
        adj = (row["p_raw_ttest"] * m) / k
        bh_p.append(min(1.0, adj))
    # Enforce monotonicity backwards
    for i in range(len(bh_p) - 2, -1, -1):
        bh_p[i] = min(bh_p[i], bh_p[i + 1])
    stats_df["p_benjamini_hochberg"] = np.round(bh_p, 6)

    # Sort back by scenario and comparison
    stats_df = stats_df.sort_values(["scenario", "comparison_code"]).reset_index(drop=True)
    stats_df.to_csv(RESULTS_DIR / "statistical_tests_verified.csv", index=False)
    print(f"\n[OK] Saved verified statistical tests to {RESULTS_DIR / 'statistical_tests_verified.csv'}")
    return stats_df


def main():
    t_start = time.time()
    print("=" * 70)
    print("STARTING VERIFICATION AND SIMPLIFICATION RESEARCH PIPELINE")
    print("=" * 70)

    # Task 4: Major 4-way comparison
    comp_df = run_major_comparison()

    # Tasks 5 & 6: Simplification study (Models A to E)
    run_simplification_study()

    # Task 7: Queue-growth smoothing study
    run_growth_smoothing_study()

    # Task 8: Hysteresis study
    run_hysteresis_study()

    # Task 2: Noise robustness audit
    run_noise_audit()

    # Task 1: Verified statistical analysis
    run_verified_statistical_analysis(comp_df)

    elapsed = time.time() - t_start
    print("\n" + "=" * 70)
    print(f"ALL VERIFICATION & SIMPLIFICATION EXPERIMENTS COMPLETED IN {elapsed:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
