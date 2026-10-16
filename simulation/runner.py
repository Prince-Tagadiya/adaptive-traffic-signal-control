"""
Simulation Runner for Traffic Signal Research.

Encapsulates headless SUMO simulation management via TraCI, stepping logic,
fine-grained metric collection (both step-level and cohort-isolated vehicle-level data),
and export of raw and summary datasets.

Methodological Rigor:
- Distinguishes strictly between:
  Cohort A: Vehicles that both depart >= warmup AND arrive >= warmup (Pure Evaluation Cohort)
  Cohort B: Vehicles that depart < warmup but arrive >= warmup (Boundary Crossing Cohort)
  Cohort C: Vehicles that depart < warmup and arrive < warmup (Pure Warm-up Cohort)
- Supports explicit immutable route file binding (One Realization -> Multiple Controllers)
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import traci


class SimulationRunner:
    """
    Executes a reproducible SUMO simulation run and records fine-grained
    research metrics for signal control baseline and comparison.
    """

    def __init__(
        self,
        config_path: str,
        route_path: Optional[str] = None,
        sim_duration: int = 1000,
        warmup_duration: int = 200,
        tl_id: str = "J0",
        controller: Optional[Any] = None,
        seed: int = 42,
    ):
        self.config_path = str(Path(config_path).resolve())
        self.route_path = str(Path(route_path).resolve()) if route_path else None
        self.sim_duration = sim_duration
        self.warmup_duration = warmup_duration
        self.tl_id = tl_id
        self.controller = controller
        self.seed = seed

        self.incoming_lanes = {
            "N": "N_J0_0",
            "S": "S_J0_0",
            "E": "E_J0_0",
            "W": "W_J0_0",
        }

        # Locating sumo executable
        self.sumo_bin = self._resolve_sumo_binary()

    def _resolve_sumo_binary(self) -> str:
        """Find the headless command-line sumo binary."""
        try:
            import sumolib
            binary = sumolib.checkBinary("sumo")
            if binary and os.path.exists(binary):
                return binary
        except Exception:
            pass

        venv_bin = Path(sys.prefix) / "bin" / "sumo"
        if venv_bin.exists():
            return str(venv_bin)

        if "SUMO_HOME" in os.environ:
            sh_bin = Path(os.environ["SUMO_HOME"]) / "bin" / "sumo"
            if sh_bin.exists():
                return str(sh_bin)

        import shutil
        which_sumo = shutil.which("sumo")
        if which_sumo:
            return which_sumo

        raise RuntimeError("SUMO command-line binary could not be found.")

    def run(self) -> Dict[str, Any]:
        """
        Executes the full simulation run and collects both step-level
        and vehicle-level metrics with strict cohort isolation.
        """
        sumo_cmd = [
            self.sumo_bin,
            "-c", self.config_path,
            "--no-step-log", "true",
            "--no-warnings", "true",
            "--duration-log.disable", "true",
            "--seed", str(self.seed),
            "--waiting-time-memory", "1000",
        ]

        if self.route_path:
            sumo_cmd.extend(["--route-files", self.route_path])

        if self.controller:
            self.controller.reset()

        traci.start(sumo_cmd)

        step_records: List[Dict[str, Any]] = []
        vehicle_records: List[Dict[str, Any]] = []

        # Vehicle lifecycle tracking
        depart_times: Dict[str, float] = {}
        route_ids: Dict[str, str] = {}
        stop_counts: Dict[str, int] = {}
        is_halting: Dict[str, bool] = {}
        accumulated_waits: Dict[str, float] = {}
        accumulated_delays: Dict[str, float] = {}
        final_distances: Dict[str, float] = {}

        all_departed = set()
        all_arrived = set()
        phase_durations_observed: Dict[int, int] = {}
        phase_switch_count = 0
        total_yellow_steps = 0
        prev_phase = None

        # Red elapsed tracking for maximum red statistics
        max_observed_red = 0
        current_red_wait = {"NS": 0, "EW": 0}

        try:
            for step in range(self.sim_duration):
                sim_time = traci.simulation.getTime()

                # Step controller if supplied
                if self.controller:
                    self.controller.step(sim_time, traci)

                traci.simulationStep()
                sim_time = traci.simulation.getTime()

                # 1. Track newly departed vehicles
                newly_departed = traci.simulation.getDepartedIDList()
                for v in newly_departed:
                    all_departed.add(v)
                    depart_times[v] = sim_time
                    stop_counts[v] = 0
                    is_halting[v] = False
                    accumulated_waits[v] = 0.0
                    accumulated_delays[v] = 0.0
                    final_distances[v] = 0.0
                    try:
                        route_ids[v] = traci.vehicle.getRouteID(v)
                    except Exception:
                        route_ids[v] = "unknown"

                # 2. Track active vehicles state
                active_veh_ids = list(traci.vehicle.getIDList())
                veh_count = len(active_veh_ids)

                step_speeds = []
                step_waits = []

                for v in active_veh_ids:
                    speed = traci.vehicle.getSpeed(v)
                    step_speeds.append(speed)

                    curr_wait = traci.vehicle.getWaitingTime(v)
                    step_waits.append(curr_wait)

                    accumulated_waits[v] = traci.vehicle.getAccumulatedWaitingTime(v)
                    accumulated_delays[v] = traci.vehicle.getTimeLoss(v)
                    final_distances[v] = traci.vehicle.getDistance(v)

                    # Detect stop event (transition into speed < 0.1 m/s)
                    if speed < 0.1:
                        if not is_halting.get(v, False):
                            stop_counts[v] = stop_counts.get(v, 0) + 1
                            is_halting[v] = True
                    else:
                        is_halting[v] = False

                # 3. Track newly arrived (completed) vehicles with strict cohort labeling
                newly_arrived = traci.simulation.getArrivedIDList()
                for v in newly_arrived:
                    all_arrived.add(v)
                    arr_time = sim_time
                    dep_time = depart_times.get(v, 0.0)
                    trav_time = arr_time - dep_time
                    wait_time = accumulated_waits.get(v, 0.0)
                    delay_time = accumulated_delays.get(v, 0.0)
                    stops = stop_counts.get(v, 0)
                    dist = final_distances.get(v, 0.0)
                    v_mean_speed = dist / trav_time if trav_time > 0 else 0.0

                    # Assign Cohort:
                    # Cohort A: Pure Post-Warmup (departed >= warmup AND arrived >= warmup)
                    # Cohort B: Boundary Crossing (departed < warmup AND arrived >= warmup)
                    # Cohort C: Pure Warmup (departed < warmup AND arrived < warmup)
                    if dep_time >= self.warmup_duration and arr_time >= self.warmup_duration:
                        cohort = "A_eval_pure"
                    elif dep_time < self.warmup_duration and arr_time >= self.warmup_duration:
                        cohort = "B_boundary_cross"
                    else:
                        cohort = "C_warmup_internal"

                    vehicle_records.append({
                        "vehicle_id": v,
                        "route_id": route_ids.get(v, "unknown"),
                        "depart_time": dep_time,
                        "arrival_time": arr_time,
                        "travel_time": round(trav_time, 2),
                        "waiting_time": round(wait_time, 2),
                        "time_loss_delay": round(delay_time, 2),
                        "stop_count": stops,
                        "distance_m": round(dist, 2),
                        "mean_speed_mps": round(v_mean_speed, 4),
                        "cohort": cohort,
                    })

                # Aggregate step quantities
                if veh_count > 0:
                    mean_speed = sum(step_speeds) / veh_count
                    total_wait = sum(step_waits)
                    mean_wait = total_wait / veh_count
                else:
                    mean_speed = 0.0
                    total_wait = 0.0
                    mean_wait = 0.0

                # Queue (halting vehicles speed < 0.1 m/s) and density per incoming lane
                queue_n = traci.lane.getLastStepHaltingNumber(self.incoming_lanes["N"])
                queue_s = traci.lane.getLastStepHaltingNumber(self.incoming_lanes["S"])
                queue_e = traci.lane.getLastStepHaltingNumber(self.incoming_lanes["E"])
                queue_w = traci.lane.getLastStepHaltingNumber(self.incoming_lanes["W"])
                queue_total = queue_n + queue_s + queue_e + queue_w

                density_n = traci.lane.getLastStepVehicleNumber(self.incoming_lanes["N"])
                density_s = traci.lane.getLastStepVehicleNumber(self.incoming_lanes["S"])
                density_e = traci.lane.getLastStepVehicleNumber(self.incoming_lanes["E"])
                density_w = traci.lane.getLastStepVehicleNumber(self.incoming_lanes["W"])

                tl_phase = traci.trafficlight.getPhase(self.tl_id)
                tl_state = traci.trafficlight.getRedYellowGreenState(self.tl_id)
                phase_durations_observed[tl_phase] = phase_durations_observed.get(tl_phase, 0) + 1

                # Track phase switches and yellow intervals
                if prev_phase is not None and tl_phase != prev_phase:
                    phase_switch_count += 1
                if tl_phase in [1, 3]:  # Yellow phases
                    total_yellow_steps += 1
                prev_phase = tl_phase

                # Track red times
                d_ns = queue_n + queue_s
                d_ew = queue_e + queue_w
                if tl_phase in [2, 3]:  # NS is Red
                    current_red_wait["NS"] += 1
                    current_red_wait["EW"] = 0
                    if current_red_wait["NS"] > max_observed_red:
                        max_observed_red = current_red_wait["NS"]
                elif tl_phase in [0, 1]:  # EW is Red
                    current_red_wait["EW"] += 1
                    current_red_wait["NS"] = 0
                    if current_red_wait["EW"] > max_observed_red:
                        max_observed_red = current_red_wait["EW"]

                is_warmup = sim_time < self.warmup_duration
                cohort_a_throughput = sum(1 for rec in vehicle_records if rec["cohort"] == "A_eval_pure")

                step_records.append({
                    "step": step + 1,
                    "sim_time": sim_time,
                    "is_warmup": is_warmup,
                    "active_vehicles": veh_count,
                    "cumulative_departed": len(all_departed),
                    "cumulative_arrived": len(all_arrived),
                    "cohort_a_throughput": cohort_a_throughput,
                    "mean_speed": round(mean_speed, 4),
                    "total_waiting_time": round(total_wait, 2),
                    "mean_waiting_time": round(mean_wait, 2),
                    "queue_N": queue_n,
                    "queue_S": queue_s,
                    "queue_E": queue_e,
                    "queue_W": queue_w,
                    "queue_total": queue_total,
                    "density_N": density_n,
                    "density_S": density_s,
                    "density_E": density_e,
                    "density_W": density_w,
                    "tl_phase": tl_phase,
                    "tl_state": tl_state,
                })

        finally:
            traci.close()

        step_df = pd.DataFrame(step_records)
        veh_df = pd.DataFrame(vehicle_records)

        # 4. Evaluation period analysis (post-warmup: sim_time >= warmup_duration)
        eval_step_df = step_df[~step_df["is_warmup"]]

        # Primary Cohort A (Pure Post-Warmup)
        cohort_a_df = veh_df[veh_df["cohort"] == "A_eval_pure"] if not veh_df.empty else pd.DataFrame()
        # Broad Cohort A+B (All vehicles arriving post-warmup)
        cohort_ab_df = veh_df[veh_df["cohort"].isin(["A_eval_pure", "B_boundary_cross"])] if not veh_df.empty else pd.DataFrame()

        def compute_cohort_stats(df_subset):
            if df_subset.empty:
                return {
                    "count": 0, "avg_wait": 0.0, "avg_travel": 0.0,
                    "avg_delay": 0.0, "total_delay": 0.0, "avg_stops": 0.0,
                    "total_stops": 0, "mean_speed": 0.0
                }
            return {
                "count": len(df_subset),
                "avg_wait": round(float(df_subset["waiting_time"].mean()), 2),
                "avg_travel": round(float(df_subset["travel_time"].mean()), 2),
                "avg_delay": round(float(df_subset["time_loss_delay"].mean()), 2),
                "total_delay": round(float(df_subset["time_loss_delay"].sum()), 2),
                "avg_stops": round(float(df_subset["stop_count"].mean()), 2),
                "total_stops": int(df_subset["stop_count"].sum()),
                "mean_speed": round(float(df_subset["mean_speed_mps"].mean()), 2),
            }

        stats_a = compute_cohort_stats(cohort_a_df)
        stats_ab = compute_cohort_stats(cohort_ab_df)

        # Step-level metrics during evaluation period
        avg_queue_length = round(float(eval_step_df["queue_total"].mean()), 2)
        max_queue_length = int(eval_step_df["queue_total"].max())
        step_mean_speed = round(float(eval_step_df["mean_speed"].mean()), 2)

        summary_metrics = {
            "seed": self.seed,
            "sim_duration_s": self.sim_duration,
            "warmup_duration_s": self.warmup_duration,
            "eval_duration_s": self.sim_duration - self.warmup_duration,
            "total_vehicles_departed": len(all_departed),
            "total_vehicles_completed": len(all_arrived),
            # Primary Research Cohort A (Depart >= warmup & Arrive >= warmup)
            "cohort_a_completed": stats_a["count"],
            "avg_waiting_time_s": stats_a["avg_wait"],
            "avg_travel_time_s": stats_a["avg_travel"],
            "avg_delay_s": stats_a["avg_delay"],
            "total_delay_s": stats_a["total_delay"],
            "avg_stops_per_veh": stats_a["avg_stops"],
            "total_stops": stats_a["total_stops"],
            "mean_speed_mps": stats_a["mean_speed"],
            # Secondary Operational & Queue Metrics
            "avg_queue_length_veh": avg_queue_length,
            "max_queue_length_veh": max_queue_length,
            "step_mean_speed_mps": step_mean_speed,
            "phase_switch_count": phase_switch_count,
            "total_yellow_lost_time_s": total_yellow_steps,
            "max_red_duration_s": max_observed_red,
            # Broad Cohort A+B (For legacy comparison)
            "cohort_ab_completed": stats_ab["count"],
            "cohort_ab_avg_wait_s": stats_ab["avg_wait"],
            "cohort_ab_avg_travel_s": stats_ab["avg_travel"],
            "cohort_ab_avg_delay_s": stats_ab["avg_delay"],
            "phase_step_counts": phase_durations_observed,
        }

        return {
            "summary": summary_metrics,
            "step_dataframe": step_df,
            "vehicle_dataframe": veh_df,
        }
