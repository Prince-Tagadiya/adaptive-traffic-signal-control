"""
Basic Density-Based Adaptive Traffic Signal Controller.

An intermediate baseline controller that allocates green phases based on
real-time queue density on the opposing intersection approaches.

Density Metric:
- Number of halting vehicles (speed < 0.1 m/s) on each incoming approach:
  - North (N_J0_0), South (S_J0_0) -> D_NS = Q_N + Q_S
  - East (E_J0_0), West (W_J0_0)   -> D_EW = Q_E + Q_W

Operational Constraints:
- Minimum Green Time: 15s (prevents erratic phase toggling)
- Maximum Green Time: 50s (limits maximum phase hold)
- Yellow Clearance Time: 3s (mandatory yellow transition)
- Starvation Prevention: If the red approach has waiting vehicles for >= 45s,
  it triggers a mandatory phase change as soon as minimum green is satisfied.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from controllers.base_controller import BaseSignalController


class BasicDensityController(BaseSignalController):
    """
    Density-based adaptive controller comparing D_NS vs D_EW with
    min/max green constraints and starvation prevention.
    """

    def __init__(
        self,
        tl_id: str = "J0",
        min_green: int = 15,
        max_green: int = 50,
        yellow_time: int = 3,
        starvation_red_time: int = 45,
    ):
        super().__init__(tl_id=tl_id)
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.starvation_red_time = starvation_red_time

        self.incoming_lanes = {
            "N": "N_J0_0",
            "S": "S_J0_0",
            "E": "E_J0_0",
            "W": "W_J0_0",
        }

        # Internal state tracking
        self.phase_state = "NS_GREEN"  # 'NS_GREEN', 'NS_YELLOW', 'EW_GREEN', 'EW_YELLOW'
        self.elapsed_green_time = 0
        self.elapsed_yellow_time = 0
        self.consecutive_red_wait = {"NS": 0, "EW": 0}

        # Decision history log
        self.decisions_log: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Reset internal state machine and logs for clean re-execution."""
        self.phase_state = "NS_GREEN"
        self.elapsed_green_time = 0
        self.elapsed_yellow_time = 0
        self.consecutive_red_wait = {"NS": 0, "EW": 0}
        self.decisions_log = []

    def get_decisions_df(self) -> pd.DataFrame:
        """Return the logged decisions as a pandas DataFrame."""
        return pd.DataFrame(self.decisions_log)

    def step(self, sim_time: float, traci_conn: Any) -> Dict[str, Any]:
        """
        Step logic executed every simulation second:
        1. Measure queues on all four incoming approaches.
        2. Calculate D_NS and D_EW.
        3. Evaluate min_green, max_green, starvation, and demand criteria.
        4. Transition traffic light phases via TraCI.
        5. Log decision rationale.
        """
        tl = traci_conn.trafficlight
        lane = traci_conn.lane

        # 1. Measure approach queues (halting vehicles: speed < 0.1 m/s)
        q_n = lane.getLastStepHaltingNumber(self.incoming_lanes["N"])
        q_s = lane.getLastStepHaltingNumber(self.incoming_lanes["S"])
        q_e = lane.getLastStepHaltingNumber(self.incoming_lanes["E"])
        q_w = lane.getLastStepHaltingNumber(self.incoming_lanes["W"])

        # 2. Compute directional demand
        d_ns = q_n + q_s
        d_ew = q_e + q_w

        decision_reason = "MAINTAIN"
        selected_direction = "NS" if self.phase_state in ["NS_GREEN", "NS_YELLOW"] else "EW"

        # 3. State Machine transitions
        if self.phase_state == "NS_GREEN":
            tl.setPhase(self.tl_id, 0)
            self.elapsed_green_time += 1

            # Track red wait for the competing EW approach
            if d_ew > 0:
                self.consecutive_red_wait["EW"] += 1
            else:
                self.consecutive_red_wait["EW"] = 0
            self.consecutive_red_wait["NS"] = 0

            # Decision logic after min_green
            if self.elapsed_green_time < self.min_green:
                decision_reason = "MIN_GREEN_HOLD"
            else:
                if self.elapsed_green_time >= self.max_green and d_ew > 0:
                    decision_reason = "MAX_GREEN_EXCEEDED"
                    self.phase_state = "NS_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 1)
                elif self.consecutive_red_wait["EW"] >= self.starvation_red_time and d_ew > 0:
                    decision_reason = "STARVATION_PREVENTION"
                    self.phase_state = "NS_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 1)
                elif d_ew > d_ns:
                    decision_reason = "DEMAND_SWITCH_EW_HIGHER"
                    self.phase_state = "NS_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 1)
                else:
                    decision_reason = "DEMAND_MAINTAIN_NS"

            selected_direction = "NS"

        elif self.phase_state == "NS_YELLOW":
            tl.setPhase(self.tl_id, 1)
            self.elapsed_yellow_time += 1
            decision_reason = "YELLOW_CLEARANCE"
            selected_direction = "EW"  # Clearing for EW

            if self.elapsed_yellow_time >= self.yellow_time:
                self.phase_state = "EW_GREEN"
                self.elapsed_green_time = 0
                tl.setPhase(self.tl_id, 2)

        elif self.phase_state == "EW_GREEN":
            tl.setPhase(self.tl_id, 2)
            self.elapsed_green_time += 1

            # Track red wait for the competing NS approach
            if d_ns > 0:
                self.consecutive_red_wait["NS"] += 1
            else:
                self.consecutive_red_wait["NS"] = 0
            self.consecutive_red_wait["EW"] = 0

            # Decision logic after min_green
            if self.elapsed_green_time < self.min_green:
                decision_reason = "MIN_GREEN_HOLD"
            else:
                if self.elapsed_green_time >= self.max_green and d_ns > 0:
                    decision_reason = "MAX_GREEN_EXCEEDED"
                    self.phase_state = "EW_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 3)
                elif self.consecutive_red_wait["NS"] >= self.starvation_red_time and d_ns > 0:
                    decision_reason = "STARVATION_PREVENTION"
                    self.phase_state = "EW_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 3)
                elif d_ns > d_ew:
                    decision_reason = "DEMAND_SWITCH_NS_HIGHER"
                    self.phase_state = "EW_YELLOW"
                    self.elapsed_yellow_time = 0
                    tl.setPhase(self.tl_id, 3)
                else:
                    decision_reason = "DEMAND_MAINTAIN_EW"

            selected_direction = "EW"

        elif self.phase_state == "EW_YELLOW":
            tl.setPhase(self.tl_id, 3)
            self.elapsed_yellow_time += 1
            decision_reason = "YELLOW_CLEARANCE"
            selected_direction = "NS"  # Clearing for NS

            if self.elapsed_yellow_time >= self.yellow_time:
                self.phase_state = "NS_GREEN"
                self.elapsed_green_time = 0
                tl.setPhase(self.tl_id, 0)

        current_phase = tl.getPhase(self.tl_id)

        # 4. Log decision record
        self.decisions_log.append({
            "sim_time": sim_time,
            "North_queue": q_n,
            "South_queue": q_s,
            "East_queue": q_e,
            "West_queue": q_w,
            "NS_demand": d_ns,
            "EW_demand": d_ew,
            "current_signal_phase": current_phase,
            "selected_green_direction": selected_direction,
            "reason_for_switching": decision_reason,
            "elapsed_green_time": self.elapsed_green_time,
        })

        return {
            "phase_state": self.phase_state,
            "current_phase": current_phase,
            "selected_direction": selected_direction,
            "decision_reason": decision_reason,
            "d_ns": d_ns,
            "d_ew": d_ew,
        }
