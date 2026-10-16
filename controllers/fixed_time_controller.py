"""
Fixed-time traffic signal controller.

Maintains an explicit predefined static signal timing plan for the 4-arm intersection:
- Phase 0: North-South Green (42s)
- Phase 1: North-South Yellow (3s)
- Phase 2: East-West Green (42s)
- Phase 3: East-West Yellow (3s)
Total Cycle Time: 90s.
"""

from typing import Any, Dict, List, Optional
from controllers.base_controller import BaseSignalController

# Explicit baseline signal plan specification
BASELINE_SIGNAL_PLAN: List[Dict[str, Any]] = [
    {
        "phase_index": 0,
        "name": "North-South Green",
        "duration": 42,
        "state": "GGgrrrGGgrrr",
        "description": "Green for North and South approaches (straight and right free, left yields)",
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
        "duration": 42,
        "state": "rrrGGgrrrGGg",
        "description": "Green for East and West approaches (straight and right free, left yields)",
    },
    {
        "phase_index": 3,
        "name": "East-West Yellow",
        "duration": 3,
        "state": "rrryyyrrryyy",
        "description": "Yellow clearance for East and West approaches",
    },
]


class FixedTimeSignalController(BaseSignalController):
    """
    Fixed-time controller executing an explicit static signal timing cycle.
    """

    def __init__(
        self,
        tl_id: str = "J0",
        signal_plan: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(tl_id=tl_id)
        self.signal_plan = signal_plan if signal_plan is not None else BASELINE_SIGNAL_PLAN
        self.cycle_time = sum(p["duration"] for p in self.signal_plan)
        self.current_phase_index = 0
        self.time_in_phase = 0

    @classmethod
    def get_signal_plan(cls) -> List[Dict[str, Any]]:
        """Return the explicit baseline signal plan."""
        return list(BASELINE_SIGNAL_PLAN)

    def step(self, sim_time: float, traci_conn: Any) -> Dict[str, Any]:
        """
        Steps the signal controller according to the explicit fixed-time plan.
        """
        tl = traci_conn.trafficlight

        # Set the current phase in SUMO
        current_spec = self.signal_plan[self.current_phase_index]
        tl.setPhase(self.tl_id, current_spec["phase_index"])

        self.time_in_phase += 1

        # Check if phase duration has completed
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
