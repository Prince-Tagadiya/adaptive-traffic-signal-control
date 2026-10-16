#!/usr/bin/env python3
"""
Main Experiment Runner for 4-Arm Signalized Intersection Simulation.

Runs a reproducible TraCI simulation of a standard 4-way intersection,
collects step-by-step metrics, saves raw simulation data to CSV,
and prints the formal experimental environment report.
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path so simulation and controllers can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from simulation.runner import SimulationRunner
from scripts.generate_routes import generate_routes


def main():
    parser = argparse.ArgumentParser(description="Run 4-arm intersection simulation via TraCI")
    parser.add_argument("--duration", type=int, default=1000, help="Total simulation duration in seconds")
    parser.add_argument("--warmup", type=int, default=200, help="Warm-up period in seconds")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output-csv", type=str, default="data/simulation_run_seed42.csv", help="Relative output CSV path")
    args = parser.parse_args()

    scenarios_dir = PROJECT_ROOT / "scenarios"
    cfg_file = scenarios_dir / "four_arm.sumocfg"
    rou_file = scenarios_dir / "four_arm.rou.xml"
    csv_file = PROJECT_ROOT / args.output_csv

    # 1. Generate demand with deterministic seed
    print("=" * 70)
    print("PHASE 2: TRAFFIC INTERSECTION RESEARCH SIMULATION")
    print("=" * 70)
    print(f"[*] Generating reproducible traffic demand (Seed: {args.seed})...")
    demand_stats = generate_routes(
        output_path=str(rou_file),
        sim_duration=args.duration,
        seed=args.seed,
        p_arrival_per_arm=0.08,
        straight_prob=0.65,
        right_prob=0.20,
        left_prob=0.15,
    )
    print(f"[✓] Generated {demand_stats['total_vehicles']} vehicles across 12 turn routes.")

    # 2. Run simulation
    runner = SimulationRunner(
        config_path=str(cfg_file),
        sim_duration=args.duration,
        warmup_duration=args.warmup,
        tl_id="J0",
        seed=args.seed,
    )

    result = runner.run()

    # 3. Save raw simulation data to CSV
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    df = result["dataframe"]
    df.to_csv(csv_file, index=False)
    print(f"[✓] Raw simulation data successfully saved to: {csv_file}")

    # Also save a canonical 'simulation_data.csv' symlink/copy for convenient reference
    canonical_csv = PROJECT_ROOT / "data" / "simulation_data.csv"
    df.to_csv(canonical_csv, index=False)

    # 4. Print comprehensive research environment report
    print("\n" + "=" * 70)
    print("SIMULATION EXPERIMENT SUMMARY REPORT")
    print("=" * 70)
    print(f"1. Simulation Duration:        {result['sim_duration']} seconds")
    print(f"2. Warm-up Duration:           {result['warmup_duration']} seconds (Post-warmup eval: {result['eval_duration']} seconds)")
    print(f"3. Random Seed:                {result['seed']}")
    print(f"4. Number of Vehicles Created: {demand_stats['total_vehicles']}")
    print(f"5. Number Departed:            {result['total_departed']}")
    print(f"6. Number Completed (Arrived): {result['total_arrived']}")
    print(f"7. Vehicles Remaining in Net:  {result['still_in_network']}")
    print("\n8. Route Distribution:")
    print(f"   - Straight: {demand_stats['turn_counts']['straight']} ({demand_stats['turn_counts']['straight']/demand_stats['total_vehicles']*100:.1f}%)")
    print(f"   - Right:    {demand_stats['turn_counts']['right']} ({demand_stats['turn_counts']['right']/demand_stats['total_vehicles']*100:.1f}%)")
    print(f"   - Left:     {demand_stats['turn_counts']['left']} ({demand_stats['turn_counts']['left']/demand_stats['total_vehicles']*100:.1f}%)")
    print("   - By Approach (N/S/E/W):", demand_stats["approach_counts"])

    print("\n9. Traffic Light Specification (Junction J0):")
    print("   - Cycle Time: 90 seconds (4 phases)")
    print("   - Phase 0: North-South Green  | 42s duration | State: GGgrrrGGgrrr")
    print("   - Phase 1: North-South Yellow |  3s duration | State: yyyrrryyyrrr")
    print("   - Phase 2: East-West Green    | 42s duration | State: rrrGGgrrrGGg")
    print("   - Phase 3: East-West Yellow   |  3s duration | State: rrryyyrrryyy")
    print("   - Total Steps Observed by Phase:", result["phase_step_counts"])

    print("\n10. Post Warm-up Traffic Dynamics (200s - 1000s):")
    print(f"   - Mean Queue Length (Halting Vehicles): {result['post_warmup_mean_queue']:.2f} veh")
    print(f"   - Max Queue Length Observed:           {result['post_warmup_max_queue']} veh")
    print(f"   - Mean Vehicle Speed:                  {result['post_warmup_mean_speed']:.2f} m/s")
    print(f"   - Mean Waiting Time:                   {result['post_warmup_mean_waiting_time']:.2f} s")

    print(f"\n11. Output CSV Filename:       {csv_file.relative_to(PROJECT_ROOT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
