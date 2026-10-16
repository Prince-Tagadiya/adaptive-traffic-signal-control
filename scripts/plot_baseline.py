#!/usr/bin/env python3
"""
Research-Quality Plotting Script for Fixed-Time Baseline Simulation.

Generates readable, publication-quality figures:
1. Queue length vs simulation time
2. Average waiting time vs simulation time
3. Cumulative throughput (completed vehicles) vs simulation time
4. Combined 3-panel figure
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def plot_baseline_figures(raw_csv_path: str = "data/baseline_seed42_raw.csv"):
    csv_file = PROJECT_ROOT / raw_csv_path
    figures_dir = PROJECT_ROOT / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    if not csv_file.exists():
        print(f"[Error] Raw data file not found at: {csv_file}")
        sys.exit(1)

    df = pd.read_csv(csv_file)
    warmup_t = 200

    # Global style settings for clean research graphics
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
    # Plot 1: Queue Length vs Simulation Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["sim_time"], df["queue_total"], label="Total Queued (Halting)", color="#c0392b", alpha=0.9)
    # Add a rolling average for trend readability
    rolling_queue = df["queue_total"].rolling(window=45, min_periods=1).mean()
    ax.plot(df["sim_time"], rolling_queue, label="Rolling Mean (45s window)", color="#7f1d1d", linewidth=2.0, linestyle="--")
    ax.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.5, label=f"Warm-up Boundary ({warmup_t}s)")
    ax.axvspan(0, warmup_t, color="#e5e7eb", alpha=0.5, label="Warm-up Period")

    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Queued Vehicles (halting)")
    ax.set_title("Baseline Fixed-Time Controller: Queue Length vs Simulation Time (Seed 42)")
    ax.set_xlim(0, 1000)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    out1 = figures_dir / "baseline_queue_length.png"
    plt.savefig(out1, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 1: {out1}")

    # -------------------------------------------------------------
    # Plot 2: Average Waiting Time vs Simulation Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["sim_time"], df["mean_waiting_time"], label="Active Mean Waiting Time", color="#d97706", alpha=0.9)
    rolling_wait = df["mean_waiting_time"].rolling(window=45, min_periods=1).mean()
    ax.plot(df["sim_time"], rolling_wait, label="Rolling Mean (45s window)", color="#92400e", linewidth=2.0, linestyle="--")
    ax.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.5, label=f"Warm-up Boundary ({warmup_t}s)")
    ax.axvspan(0, warmup_t, color="#e5e7eb", alpha=0.5, label="Warm-up Period")

    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Average Waiting Time (s)")
    ax.set_title("Baseline Fixed-Time Controller: Average Waiting Time vs Simulation Time (Seed 42)")
    ax.set_xlim(0, 1000)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9)

    out2 = figures_dir / "baseline_waiting_time.png"
    plt.savefig(out2, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 2: {out2}")

    # -------------------------------------------------------------
    # Plot 3: Traffic Throughput / Completed Vehicles vs Simulation Time
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df["sim_time"], df["cumulative_arrived"], label="Cumulative Completed Vehicles", color="#2563eb", linewidth=2.0)
    ax.plot(df["sim_time"], df["eval_throughput"], label="Evaluation Window Throughput (Post-Warmup)", color="#059669", linewidth=2.0, linestyle="-.")
    ax.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.5, label=f"Warm-up Boundary ({warmup_t}s)")
    ax.axvspan(0, warmup_t, color="#e5e7eb", alpha=0.5, label="Warm-up Period")

    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Vehicles Completed")
    ax.set_title("Baseline Fixed-Time Controller: Throughput vs Simulation Time (Seed 42)")
    ax.set_xlim(0, 1000)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", framealpha=0.9)

    out3 = figures_dir / "baseline_throughput.png"
    plt.savefig(out3, dpi=200)
    plt.close()
    print(f"[✓] Saved Plot 3: {out3}")

    # -------------------------------------------------------------
    # Plot 4: Combined 3-Panel Figure
    # -------------------------------------------------------------
    fig, (ax_q, ax_w, ax_t) = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

    # Subplot A: Queue
    ax_q.plot(df["sim_time"], df["queue_total"], color="#c0392b", linewidth=1.4, label="Queued Vehicles")
    ax_q.plot(df["sim_time"], rolling_queue, color="#7f1d1d", linewidth=1.8, linestyle="--", label="Rolling Mean")
    ax_q.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.2)
    ax_q.axvspan(0, warmup_t, color="#e5e7eb", alpha=0.4)
    ax_q.set_ylabel("Queue (veh)")
    ax_q.set_title("Baseline Signal Performance (Seed 42)")
    ax_q.grid(True, linestyle=":", alpha=0.5)
    ax_q.legend(loc="upper right", fontsize=9)

    # Subplot B: Waiting Time
    ax_w.plot(df["sim_time"], df["mean_waiting_time"], color="#d97706", linewidth=1.4, label="Mean Wait (s)")
    ax_w.plot(df["sim_time"], rolling_wait, color="#92400e", linewidth=1.8, linestyle="--", label="Rolling Mean")
    ax_w.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.2)
    ax_w.axvspan(0, warmup_t, color="#e5e7eb", alpha=0.4)
    ax_w.set_ylabel("Wait Time (s)")
    ax_w.grid(True, linestyle=":", alpha=0.5)
    ax_w.legend(loc="upper right", fontsize=9)

    # Subplot C: Throughput
    ax_t.plot(df["sim_time"], df["cumulative_arrived"], color="#2563eb", linewidth=1.8, label="Cumulative Arrived")
    ax_t.plot(df["sim_time"], df["eval_throughput"], color="#059669", linewidth=1.8, linestyle="-.", label="Eval Throughput")
    ax_t.axvline(x=warmup_t, color="#555555", linestyle=":", linewidth=1.2, label=f"Warm-up ({warmup_t}s)")
    ax_t.axvspan(0, warmup_t, color="#e5e7eb", alpha=0.4)
    ax_t.set_xlabel("Simulation Time (s)")
    ax_t.set_ylabel("Throughput (veh)")
    ax_t.grid(True, linestyle=":", alpha=0.5)
    ax_t.legend(loc="upper left", fontsize=9)

    out4 = figures_dir / "baseline_metrics_combined.png"
    plt.savefig(out4, dpi=200)
    plt.close()
    print(f"[✓] Saved Combined Plot: {out4}")


if __name__ == "__main__":
    plot_baseline_figures()
