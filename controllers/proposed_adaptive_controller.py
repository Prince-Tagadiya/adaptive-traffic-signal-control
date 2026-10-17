"""
Simplified Research Adaptive Traffic Signal Controller.

Mathematically grounded, lightweight adaptive controller combining:
1. Normalized Queue Length: q_i(t) = min(Q_i(t) / Q_ref, 2.0)
2. Normalized Arrival Rate: a_i(t) = min(A_i(t) / A_ref, 2.0)
3. Normalized Waiting Burden: w_i(t) = min(AW_i(t) / W_ref, 2.0)
4. Continuous Red-Time Aging / Fairness: r_i(t) = min(R_i(t) / R_ref, 1.0)
5. Hysteresis Switching Barrier: H = 0.20 (Frozen via Clean Calibration)

Queue growth (added after the calibration-only architecture audit):
6. Normalized positive queue growth g_i(t) = clip((Q_i(t) - Q_i(t-W_G)) / W_G / G_ref, -1, 1),
   weighted by gamma = 0.10 (used only when gamma > 0).

Not included:
- Unconstrained predictive demand backlog (redundant on single-lane approaches)

NEMA Safety Constraints:
- Minimum Green: G_min = 15s
- Maximum Green: G_max = 50s
- Yellow Clearance: Y = 3s
- Starvation Ceiling: R_starve = 45s

Calibration Status:
- FROZEN BEFORE TEST SET EVALUATION.
- Calibrated exclusively on Seeds 101-104 (Clean Calibration Suite).
- Architecture independently audited on Seeds 101-104: gamma = 0.10 confirmed.
- Frozen Parameter Vector:
    alpha = 1.00
    beta  = 0.75
    gamma = 0.10
    delta = 0.25
    eta   = 0.25
    H     = 0.20
"""

import collections
import time
from typing import Any, Dict, List, Optional
import pandas as pd
from controllers.base_controller import BaseSignalController


class ProposedAdaptiveSignalController(BaseSignalController):
    """
    Transparent, simplified adaptive traffic signal controller.
    Parameters are FROZEN based on clean calibration (Seeds 101-104).
    """

    def __init__(
        self,
        tl_id: str = "J0",
        min_green: int = 15,
        max_green: int = 50,
        yellow_time: int = 3,
        starvation_red_time: int = 45,
        w_arrival: int = 20,
        # Frozen Component Weights (Clean Calibration Suite Seeds 101-104)
        alpha: float = 1.0,        # Queue anchor weight (Fixed)
        beta: float = 0.75,        # Arrival rate weight (Calibrated)
        gamma: float = 0.10,       # Queue growth weight (Architecture Audit: gamma=0.10)
        delta: float = 0.25,       # Waiting burden weight (Calibrated)
        eta: float = 0.25,         # Continuous fairness / red-age weight (Calibrated)
        hysteresis: float = 0.20,  # Switching barrier H (Calibrated)
        # Normalization Reference Constants
        q_ref: float = 20.0,       # Class A: about 150 m of queue at 7.5 m per vehicle (5.0 m + 2.5 m gap), ~62% of the 242.8 m approach lane
        a_ref: float = 0.40,       # Class A: 80% saturation flow (1440 veh/h)
        w_ref: float = 30.0,       # Class C: HCM LOS C boundary threshold
        r_ref: float = 50.0,       # Class B: Engineering constraint (G_max)
        w_growth: int = 10,        # Backward finite-difference window W_G = 10s
        g_ref: float = 0.50,       # Class A: Saturation accumulation rate (0.5 veh/s)
        noise_std: float = 0.0,    # Sensor measurement noise
    ):
        super().__init__(tl_id=tl_id)
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.starvation_red_time = starvation_red_time
        self.w_arrival = w_arrival
        self.w_growth = w_growth
        self.g_ref = g_ref

        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.eta = eta
        self.hysteresis = hysteresis

        self.q_ref = q_ref
        self.a_ref = a_ref
        self.w_ref = w_ref
        self.r_ref = r_ref
        self.noise_std = noise_std

        self.incoming_lanes = {
            "N": "N_J0_0",
            "S": "S_J0_0",
            "E": "E_J0_0",
            "W": "W_J0_0",
        }

        # Rolling arrival history buffer
        self.arrival_history = {app: collections.deque(maxlen=self.w_arrival + 1) for app in self.incoming_lanes}
        self.queue_history = {app: collections.deque(maxlen=self.w_growth + 1) for app in self.incoming_lanes}
        self.consecutive_red = {"NS": 0, "EW": 0}

        # State machine
        self.phase_state = "NS_GREEN"  # 'NS_GREEN', 'NS_YELLOW', 'EW_GREEN', 'EW_YELLOW'
        self.elapsed_green_time = 0
        self.elapsed_yellow_time = 0

        # Full decision logging
        self.decisions_log: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Reset internal buffers and timers for fresh simulation run."""
        self.phase_state = "NS_GREEN"
        self.elapsed_green_time = 0
        self.elapsed_yellow_time = 0
        self.consecutive_red = {"NS": 0, "EW": 0}
        self.arrival_history = {app: collections.deque(maxlen=self.w_arrival + 1) for app in self.incoming_lanes}
        self.queue_history = {app: collections.deque(maxlen=self.w_growth + 1) for app in self.incoming_lanes}
        self.decisions_log = []

    def get_decisions_df(self) -> pd.DataFrame:
        """Return full decision log as a pandas DataFrame."""
        return pd.DataFrame(self.decisions_log)

    def step(self, sim_time: float, traci_conn: Any) -> Dict[str, Any]:
        """
        Execute one control cycle step:
        1. Observe state -> 2. Normalize -> 3. Aggregate -> 4. Check safety & hysteresis -> 5. Actuate.
        """
        t_start_compute = time.perf_counter_ns()

        tl = traci_conn.trafficlight
        lane = traci_conn.lane
        vehicle = traci_conn.vehicle

        # ---------------------------------------------------------
        # Step 1: Raw Traffic Measurements per Approach
        # ---------------------------------------------------------
        raw_queues: Dict[str, int] = {}
        raw_avg_waits: Dict[str, float] = {}
        raw_arrivals: Dict[str, float] = {}

        for app, lane_id in self.incoming_lanes.items():
            # 1.1 Halting Queue Q_i(t)
            q = lane.getLastStepHaltingNumber(lane_id)
            if self.noise_std > 0.0:
                import random
                noise = random.gauss(0, self.noise_std)
                q = max(0, int(round(q + noise)))
            raw_queues[app] = q
            self.queue_history[app].append(q)

            # 1.2 Rolling Arrival Rate A_i(t) (entering upstream zone)
            lane_vehs = lane.getLastStepVehicleIDs(lane_id)
            inflow_count = sum(1 for v in lane_vehs if vehicle.getLanePosition(v) < 100.0)
            self.arrival_history[app].append(inflow_count)
            a_rate = sum(self.arrival_history[app]) / len(self.arrival_history[app]) / 10.0
            raw_arrivals[app] = a_rate

            # 1.3 Waiting Burden AW_i(t)
            total_wait_app = 0.0
            halt_count = 0
            for v in lane_vehs:
                if vehicle.getSpeed(v) < 0.1:
                    total_wait_app += vehicle.getAccumulatedWaitingTime(v)
                    halt_count += 1
            raw_avg_waits[app] = total_wait_app / max(halt_count, 1)

        # ---------------------------------------------------------
        # Step 2: Dimensionless Normalization
        # ---------------------------------------------------------
        norm_q = {app: min(raw_queues[app] / self.q_ref, 2.0) for app in self.incoming_lanes}
        norm_a = {app: min(raw_arrivals[app] / self.a_ref, 2.0) for app in self.incoming_lanes}
        norm_w = {app: min(raw_avg_waits[app] / self.w_ref, 2.0) for app in self.incoming_lanes}

        # Queue Growth Rate g_i(t) over backward window W_G
        norm_g = {}
        for app in self.incoming_lanes:
            if self.gamma > 0.0 and len(self.queue_history[app]) > self.w_growth:
                q_prev = self.queue_history[app][0]
                g_rate = (raw_queues[app] - q_prev) / float(self.w_growth)
                norm_g[app] = max(-1.0, min(1.0, g_rate / self.g_ref))
            else:
                norm_g[app] = 0.0

        q_ns = raw_queues["N"] + raw_queues["S"]
        q_ew = raw_queues["E"] + raw_queues["W"]

        # ---------------------------------------------------------
        # Step 3: Phase Aggregation and Continuous Red-Age Tracking
        # ---------------------------------------------------------
        if self.phase_state in ["EW_GREEN", "EW_YELLOW"]:
            if q_ns > 0:
                self.consecutive_red["NS"] += 1
            else:
                self.consecutive_red["NS"] = 0
            self.consecutive_red["EW"] = 0
        else:
            if q_ew > 0:
                self.consecutive_red["EW"] += 1
            else:
                self.consecutive_red["EW"] = 0
            self.consecutive_red["NS"] = 0

        r_ns = min(self.consecutive_red["NS"] / self.r_ref, 1.0)
        r_ew = min(self.consecutive_red["EW"] / self.r_ref, 1.0)

        g_ns = (max(0.0, norm_g["N"]) + max(0.0, norm_g["S"])) if self.gamma > 0.0 else 0.0
        g_ew = (max(0.0, norm_g["E"]) + max(0.0, norm_g["W"])) if self.gamma > 0.0 else 0.0

        # Composite Phase Scores S_p(t)
        score_ns = (
            self.alpha * (norm_q["N"] + norm_q["S"])
            + self.beta * (norm_a["N"] + norm_a["S"])
            + self.gamma * g_ns
            + self.delta * (norm_w["N"] + norm_w["S"])
            + self.eta * r_ns
        )

        score_ew = (
            self.alpha * (norm_q["E"] + norm_q["W"])
            + self.beta * (norm_a["E"] + norm_a["W"])
            + self.gamma * g_ew
            + self.delta * (norm_w["E"] + norm_w["W"])
            + self.eta * r_ew
        )

        decision_reason = "MAINTAIN"
        selected_direction = "NS" if self.phase_state in ["NS_GREEN", "NS_YELLOW"] else "EW"

        # ---------------------------------------------------------
        # Step 4: Decision Logic with Safety Limits and Hysteresis
        # ---------------------------------------------------------
        if self.phase_state == "NS_GREEN":
            tl.setPhase(self.tl_id, 0)
            self.elapsed_green_time += 1

            if self.elapsed_green_time < self.min_green:
                decision_reason = "MIN_GREEN_HOLD"
            else:
                # 4.1 Max Green Limit
                if self.elapsed_green_time >= self.max_green and q_ew > 0:
                    decision_reason = "MAX_GREEN_EXCEEDED"
                    self.phase_state = "NS_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 1)
                # 4.2 Absolute Starvation Ceiling
                elif self.consecutive_red["EW"] >= self.starvation_red_time and q_ew > 0:
                    decision_reason = "STARVATION_CEILING"
                    self.phase_state = "NS_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 1)
                # 4.3 Composite Pressure with Hysteresis
                elif score_ew > (score_ns + self.hysteresis):
                    decision_reason = "PRESSURE_SWITCH_EW_HIGHER"
                    self.phase_state = "NS_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 1)
                else:
                    decision_reason = "PRESSURE_MAINTAIN_NS"

            selected_direction = "NS"

        elif self.phase_state == "NS_YELLOW":
            tl.setPhase(self.tl_id, 1)
            self.elapsed_yellow_time += 1
            decision_reason = "YELLOW_CLEARANCE"
            selected_direction = "EW"

            if self.elapsed_yellow_time >= self.yellow_time:
                self.phase_state = "EW_GREEN"
                self.elapsed_green_time = 0
                tl.setPhase(self.tl_id, 2)

        elif self.phase_state == "EW_GREEN":
            tl.setPhase(self.tl_id, 2)
            self.elapsed_green_time += 1

            if self.elapsed_green_time < self.min_green:
                decision_reason = "MIN_GREEN_HOLD"
            else:
                # 4.1 Max Green Limit
                if self.elapsed_green_time >= self.max_green and q_ns > 0:
                    decision_reason = "MAX_GREEN_EXCEEDED"
                    self.phase_state = "EW_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 3)
                # 4.2 Absolute Starvation Ceiling
                elif self.consecutive_red["NS"] >= self.starvation_red_time and q_ns > 0:
                    decision_reason = "STARVATION_CEILING"
                    self.phase_state = "EW_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 3)
                # 4.3 Composite Pressure with Hysteresis
                elif score_ns > (score_ew + self.hysteresis):
                    decision_reason = "PRESSURE_SWITCH_NS_HIGHER"
                    self.phase_state = "EW_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 3)
                else:
                    decision_reason = "PRESSURE_MAINTAIN_EW"

            selected_direction = "EW"

        elif self.phase_state == "EW_YELLOW":
            tl.setPhase(self.tl_id, 3)
            self.elapsed_yellow_time += 1
            decision_reason = "YELLOW_CLEARANCE"
            selected_direction = "NS"

            if self.elapsed_yellow_time >= self.yellow_time:
                self.phase_state = "NS_GREEN"
                self.elapsed_green_time = 0
                tl.setPhase(self.tl_id, 0)

        t_end_compute = time.perf_counter_ns()
        compute_time_us = (t_end_compute - t_start_compute) / 1000.0
        current_phase = tl.getPhase(self.tl_id)

        # Log decision step
        self.decisions_log.append({
            "sim_time": sim_time,
            "current_phase": current_phase,
            "selected_phase": selected_direction,
            "Q_N": raw_queues["N"],
            "Q_S": raw_queues["S"],
            "Q_E": raw_queues["E"],
            "Q_W": raw_queues["W"],
            "A_N": round(raw_arrivals["N"], 4),
            "A_S": round(raw_arrivals["S"], 4),
            "A_E": round(raw_arrivals["E"], 4),
            "A_W": round(raw_arrivals["W"], 4),
            "W_N": round(raw_avg_waits["N"], 2),
            "W_S": round(raw_avg_waits["S"], 2),
            "W_E": round(raw_avg_waits["E"], 2),
            "W_W": round(raw_avg_waits["W"], 2),
            "R_NS": self.consecutive_red["NS"],
            "R_EW": self.consecutive_red["EW"],
            "Score_NS": round(score_ns, 4),
            "Score_EW": round(score_ew, 4),
            "Hysteresis_Margin": self.hysteresis,
            "Switch_Reason": decision_reason,
            "Elapsed_Green": self.elapsed_green_time,
            "Compute_Time_us": round(compute_time_us, 2),
        })

        return {
            "phase_state": self.phase_state,
            "current_phase": current_phase,
            "selected_direction": selected_direction,
            "decision_reason": decision_reason,
            "score_ns": score_ns,
            "score_ew": score_ew,
            "compute_time_us": compute_time_us,
        }
