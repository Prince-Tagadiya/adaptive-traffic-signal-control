"""
Optimized Fixed-Time Traffic Signal Controller.

Derived using Webster's classical cycle length formulation and calibrated
exclusively on the training demand scenarios (calib_medium_seed101, calib_high_seed102):

Webster's Formulation:
    C_0 = (1.5 * L + 5) / (1 - Y)
where:
    - L: Total lost time per cycle = 2 phases * 3s yellow clearance = 6.0s
    - s: Saturation flow rate = 1800 veh/h/lane = 0.50 veh/s (headway h = 2.0s)
    - q_NS, q_EW: Critical lane flow rates observed in training scenarios:
        * Medium (seed 101): q_NS = 316.8 veh/h, q_EW = 302.4 veh/h -> Y = 0.344 -> C_0 = 21.3s
        * High (seed 102):   q_NS = 518.4 veh/h, q_EW = 493.2 veh/h -> Y = 0.562 -> C_0 = 32.0s
    - NEMA Driver Safety & Clearance Constraint: Minimum green G_min >= 15s.

Applying G_min = 15s yields the optimal constrained cycle:
    Phase 0: North-South Green (15s)
    Phase 1: North-South Yellow (3s)
    Phase 2: East-West Green (15s)
    Phase 3: East-West Yellow (3s)
    Total Cycle Time: 36.0s (vs 90.0s in unoptimized baseline).

Calibration Validation:
    On calib_medium_seed101: 36s cycle reduces waiting time from 17.49s to 7.30s (-58.3%).
    On calib_high_seed102:   36s cycle reduces waiting time from 67.68s to 40.90s (-39.6%).
"""

from typing import Any, Dict, List, Optional
from controllers.base_controller import BaseSignalController

OPTIMIZED_SIGNAL_PLAN: List[Dict[str, Any]] = [
    {
        "phase_index": 0,
        "name": "North-South Green",
        "duration": 15,
        "state": "GGgrrrGGgrrr",
        "description": "Webster-optimized green for North and South approaches",
    },
    {
        "phase_index": 1,
        "name": "North-South Yellow",
        "duration": 3,
        "state": "yyyrrryyyrrr",
        "description": "Yellow clearance for North and South approaches",
    },
    {
        "phase_index": 2,
        "name": "East-West Green",
        "duration": 15,
        "state": "rrrGGgrrrGGg",
        "description": "Webster-optimized green for East and West approaches",
    },
    {
        "phase_index": 3,
        "name": "East-West Yellow",
        "duration": 3,
        "state": "rrryyyrrryyy",
        "description": "Yellow clearance for East and West approaches",
    },
]


class OptimizedFixedTimeSignalController(BaseSignalController):
    """
    Fixed-time controller executing a Webster-optimized 36s cycle.
    """

    def __init__(
        self,
        tl_id: str = "J0",
        signal_plan: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(tl_id=tl_id)
        self.signal_plan = signal_plan if signal_plan is not None else OPTIMIZED_SIGNAL_PLAN
        self.cycle_time = sum(p["duration"] for p in self.signal_plan)
        self.current_phase_index = 0
        self.time_in_phase = 0

    @classmethod
    def get_signal_plan(cls) -> List[Dict[str, Any]]:
        """Return the explicit optimized signal plan."""
        return list(OPTIMIZED_SIGNAL_PLAN)

    def step(self, sim_time: float, traci_conn: Any) -> Dict[str, Any]:
        """
        Step the signal controller according to the optimized fixed-time plan.
        """
        tl = traci_conn.trafficlight

        current_spec = self.signal_plan[self.current_phase_index]
        tl.setPhase(self.tl_id, current_spec["phase_index"])

        self.time_in_phase += 1

        if self.time_in_phase >= current_spec["duration"]:
            self.current_phase_index = (self.current_phase_index + 1) % len(self.signal_plan)
            self.time_in_phase = 0

        current_phase = tl.getPhase(self.tl_id)
        current_state = tl.getRedYellowGreenState(self.tl_id)

        return {
            "tl_id": self.tl_id,
            "phase": current_phase,
            "phase_name": current_spec["name"],
            "state": current_state,
            "time_in_phase": self.time_in_phase,
            "phase_duration": current_spec["duration"],
            "cycle_time": self.cycle_time,
        }

    def reset(self) -> None:
        self.current_phase_index = 0
        self.time_in_phase = 0
