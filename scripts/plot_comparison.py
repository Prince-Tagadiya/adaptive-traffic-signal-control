#!/usr/bin/env python3
"""
Comparison Plotter: Fixed-Time Baseline vs Basic Density Adaptive Controller.

Generates:
1. comparison_waiting_time.png (Over-time waiting time comparison)
2. comparison_queue_length.png (Over-time queue length comparison)
3. comparison_throughput.png   (Cumulative throughput comparison)
4. comparison_summary_barchart.png (Bar chart with error bars for main metrics)
5. density_controller_behavior.png (D_NS vs D_EW over time with active green direction)
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def plot_all_comparisons():
    data_dir = PROJECT_ROOT / "data"
    fig_dir = PROJECT_ROOT / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    base_raw_file = data_dir / "baseline_seed42_raw.csv"
    dens_raw_file = data_dir / "density_seed42_raw.csv"
    decisions_file = data_dir / "density_controller_decisions_seed42.csv"
    base_summary_file = data_dir / "baseline_summary_all_seeds.csv"
    dens_summary_file = data_dir / "density_summary_all_seeds.csv"

    for f in [base_raw_file, dens_raw_file, decisions_file, base_summary_file, dens_summary_file]:
        if not f.exists():
            print(f"[Error] Required file missing: {f}")
            sys.exit(1)

    df_base = pd.read_csv(base_raw_file)
    df_dens = pd.read_csv(dens_raw_file)
    df_dec = pd.read_csv(decisions_file)
    df_base_sum = pd.read_csv(base_summary_file)
    df_dens_sum = pd.read_csv(dens_summary_file)

    warmup_t = 200

    plt.rcParams.update({
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "lines.linewidth": 1.6,
        "figure.autolayout": True,
    })

    # -------------------------------------------------------------
    # 1. Comparison: Queue Length vs Simulation Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.8))
    # Rolling averages for clear visual contrast
    base_roll_q = df_base["queue_total"].rolling(window=45, min_periods=1).mean()
    dens_roll_q = df_dens["queue_total"].rolling(window=45, min_periods=1).mean()

    ax.plot(df_base["sim_time"], df_base["queue_total"], color="#94a3b8", alpha=0.35, linewidth=1.0)
    ax.plot(df_dens["sim_time"], df_dens["queue_total"], color="#cbd5e1", alpha=0.35, linewidth=1.0)

    ax.plot(df_base["sim_time"], base_roll_q, label="Fixed-Time Baseline (Rolling Mean)", color="#dc2626", linewidth=2.0)
    ax.plot(df_dens["sim_time"], dens_roll_q, label="Basic Density Controller (Rolling Mean)", color="#2563eb", linewidth=2.0)

    ax.axvline(x=warmup_t, color="#475569", linestyle=":", linewidth=1.5, label="Warm-up Boundary (200s)")
    ax.axvspan(0, warmup_t, color="#f1f5f9", alpha=0.6)

    # Identical scales
    max_q = max(df_base["queue_total"].max(), df_dens["queue_total"].max()) + 2
    ax.set_ylim(0, max_q)
    ax.set_xlim(0, 1000)
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Queued Vehicles (halting)")
    ax.set_title("Queue Length Comparison: Fixed-Time vs Basic Density (Seed 42)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    out1 = fig_dir / "comparison_queue_length.png"
    plt.savefig(out1, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 1: {out1}")

    # -------------------------------------------------------------
    # 2. Comparison: Average Waiting Time vs Simulation Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.8))
    base_roll_w = df_base["mean_waiting_time"].rolling(window=45, min_periods=1).mean()
    dens_roll_w = df_dens["mean_waiting_time"].rolling(window=45, min_periods=1).mean()

    ax.plot(df_base["sim_time"], df_base["mean_waiting_time"], color="#fbcfe8", alpha=0.35, linewidth=1.0)
    ax.plot(df_dens["sim_time"], df_dens["mean_waiting_time"], color="#bae6fd", alpha=0.35, linewidth=1.0)

    ax.plot(df_base["sim_time"], base_roll_w, label="Fixed-Time Baseline (Rolling Mean)", color="#d97706", linewidth=2.0)
    ax.plot(df_dens["sim_time"], dens_roll_w, label="Basic Density Controller (Rolling Mean)", color="#0284c7", linewidth=2.0)

    ax.axvline(x=warmup_t, color="#475569", linestyle=":", linewidth=1.5, label="Warm-up Boundary (200s)")
    ax.axvspan(0, warmup_t, color="#f1f5f9", alpha=0.6)

    max_w = max(df_base["mean_waiting_time"].max(), df_dens["mean_waiting_time"].max()) + 2
    ax.set_ylim(0, max_w)
    ax.set_xlim(0, 1000)
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Average Active Waiting Time (s)")
    ax.set_title("Average Waiting Time Comparison: Fixed-Time vs Basic Density (Seed 42)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    out2 = fig_dir / "comparison_waiting_time.png"
    plt.savefig(out2, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 2: {out2}")

    # -------------------------------------------------------------
    # 3. Comparison: Throughput (Completed Vehicles) vs Simulation Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(df_base["sim_time"], df_base["cumulative_arrived"], label="Fixed-Time Baseline (Total Completed)", color="#dc2626", linewidth=1.8, linestyle="--")
    ax.plot(df_dens["sim_time"], df_dens["cumulative_arrived"], label="Basic Density Controller (Total Completed)", color="#2563eb", linewidth=1.8)

    ax.plot(df_base["sim_time"], df_base["eval_throughput"], label="Fixed-Time (Post-Warmup Eval)", color="#b91c1c", linewidth=2.0)
    ax.plot(df_dens["sim_time"], df_dens["eval_throughput"], label="Basic Density (Post-Warmup Eval)", color="#1d4ed8", linewidth=2.0)

    ax.axvline(x=warmup_t, color="#475569", linestyle=":", linewidth=1.5, label="Warm-up Boundary (200s)")
    ax.axvspan(0, warmup_t, color="#f1f5f9", alpha=0.6)

    max_arr = max(df_base["cumulative_arrived"].max(), df_dens["cumulative_arrived"].max()) + 15
    ax.set_ylim(0, max_arr)
    ax.set_xlim(0, 1000)
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Vehicles Completed")
    ax.set_title("Throughput Comparison: Fixed-Time vs Basic Density (Seed 42)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", framealpha=0.9)

    out3 = fig_dir / "comparison_throughput.png"
    plt.savefig(out3, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 3: {out3}")

    # -------------------------------------------------------------
    # 4. Summary Bar Chart: Mean ± Std across Seeds
    # -------------------------------------------------------------
    b_mean = df_base_sum[df_base_sum["seed"] == "Mean"].iloc[0]
    b_std = df_base_sum[df_base_sum["seed"] == "Std"].iloc[0]
    d_mean = df_dens_sum[df_dens_sum["seed"] == "Mean"].iloc[0]
    d_std = df_dens_sum[df_dens_sum["seed"] == "Std"].iloc[0]

    metrics = [
        ("avg_waiting_time_s", "Avg Waiting Time (s)"),
        ("avg_travel_time_s", "Avg Travel Time (s)"),
        ("avg_queue_length_veh", "Avg Queue (veh)"),
        ("eval_throughput", "Throughput (veh)"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(14, 4.2))
    controllers = ["Fixed-Time", "Basic Density"]
    colors = ["#dc2626", "#2563eb"]

    for i, (m_key, m_label) in enumerate(metrics):
        ax = axes[i]
        vals = [float(b_mean[m_key]), float(d_mean[m_key])]
        errs = [float(b_std[m_key]), float(d_std[m_key])]

        bars = ax.bar(controllers, vals, yerr=errs, capsize=5, color=colors, alpha=0.85, width=0.55)
        ax.set_title(m_label, fontsize=11, fontweight="bold")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)

        # Value annotations
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.1f}",
                        xy=(bar.get_x() + bar.get_width() / 2, h / 2),
                        xytext=(0, 0), textcoords="offset points",
                        ha="center", va="center", color="white", fontweight="bold", fontsize=10)

    fig.suptitle("Performance Metric Comparison across Seeds (Mean ± Std Dev)", fontsize=13)
    out4 = fig_dir / "comparison_summary_barchart.png"
    plt.savefig(out4, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 4: {out4}")

    # -------------------------------------------------------------
    # 5. Density Controller Behavior Plot (Requirement 16)
    # -------------------------------------------------------------
    fig, (ax_d, ax_s) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, gridspec_kw={"height_ratios": [2.5, 1]})

    # Upper panel: D_NS and D_EW
    ax_d.plot(df_dec["sim_time"], df_dec["NS_demand"], label="NS Demand (Q_N + Q_S)", color="#16a34a", linewidth=1.6)
    ax_d.plot(df_dec["sim_time"], df_dec["EW_demand"], label="EW Demand (Q_E + Q_W)", color="#7c3aed", linewidth=1.6)
    ax_d.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.5, label="Warm-up Boundary")
    ax_d.set_ylabel("Queued Vehicles (Demand)")
    ax_d.set_title("Basic Density Adaptive Controller Dynamics (Seed 42)")
    ax_d.set_xlim(0, 1000)
    ax_d.set_ylim(bottom=0)
    ax_d.grid(True, linestyle=":", alpha=0.6)
    ax_d.legend(loc="upper right", framealpha=0.9)

    # Shading on upper panel indicating active green direction
    # Phase 0 = NS Green, Phase 1 = NS Yellow, Phase 2 = EW Green, Phase 3 = EW Yellow
    phase_arr = df_dec["current_signal_phase"].values
    time_arr = df_dec["sim_time"].values
    n_pts = len(time_arr)

    # Lower panel: Active Signal Direction Timeline
    # Map phase to numerical levels: 0 (NS Green), 1 (NS Yellow), 2 (EW Green), 3 (EW Yellow)
    phase_colors = {
        0: "#22c55e",  # NS Green
        1: "#eab308",  # NS Yellow
        2: "#3b82f6",  # EW Green
        3: "#f59e0b",  # EW Yellow
    }

    # Plot continuous colored bars for signal status
    for t_idx in range(n_pts - 1):
        p = phase_arr[t_idx]
        t_start = time_arr[t_idx]
        t_end = time_arr[t_idx + 1]
        c = phase_colors.get(p, "#94a3b8")
        ax_s.axvspan(t_start, t_end, color=c, alpha=0.75)

    ax_s.set_yticks([0.5])
    ax_s.set_yticklabels(["Active Phase"])
    ax_s.set_xlabel("Simulation Time (s)")
    ax_s.set_xlim(0, 1000)

    # Custom legend for phases
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#22c55e", label="NS Green"),
        Patch(facecolor="#eab308", label="NS Yellow"),
        Patch(facecolor="#3b82f6", label="EW Green"),
        Patch(facecolor="#f59e0b", label="EW Yellow"),
    ]
    ax_s.legend(handles=legend_elements, loc="upper right", ncol=4, fontsize=9)

    out5 = fig_dir / "density_controller_behavior.png"
    plt.savefig(out5, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 5: {out5}")


if __name__ == "__main__":
    plot_all_comparisons()
