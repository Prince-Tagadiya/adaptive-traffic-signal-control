#!/usr/bin/env python3
"""
Basic Python visualization for simulation vehicle activity.

Plots vehicle counts, queue lengths, and speeds across the simulation duration,
highlighting the warm-up period.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def plot_simulation_metrics(
    csv_path: str = "data/simulation_data.csv",
    output_path: str = "figures/vehicle_activity_overview.png",
):
    csv_file = PROJECT_ROOT / csv_path
    out_file = PROJECT_ROOT / output_path
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if not csv_file.exists():
        print(f"[Error] CSV file not found at {csv_file}")
        sys.exit(1)

    df = pd.read_csv(csv_file)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Subplot 1: Active Vehicles and Total Queue Length
    ax1.plot(df["sim_time"], df["vehicle_count"], label="Active Vehicles", color="steelblue", linewidth=1.5)
    ax1.plot(df["sim_time"], df["queue_total"], label="Total Queued (Halting)", color="crimson", linewidth=1.5)
    ax1.axvline(x=200, color="gray", linestyle="--", linewidth=1.2, label="Warm-up Boundary (200s)")
    ax1.set_ylabel("Vehicle Count")
    ax1.set_title("Intersection Vehicle Activity and Queue Dynamics Over Time")
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Subplot 2: Average Speed and Average Waiting Time
    ax2.plot(df["sim_time"], df["mean_speed"], label="Mean Speed (m/s)", color="forestgreen", linewidth=1.5)
    ax2.axvline(x=200, color="gray", linestyle="--", linewidth=1.2, label="Warm-up Boundary (200s)")
    ax2.set_xlabel("Simulation Time (seconds)")
    ax2.set_ylabel("Speed (m/s)")
    ax2.set_title("Average Vehicle Speed Over Time")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(out_file, dpi=150)
    plt.close()
    print(f"[✓] Visualization saved to: {out_file}")


if __name__ == "__main__":
    plot_simulation_metrics()
