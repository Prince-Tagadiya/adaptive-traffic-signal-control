"""
Base traffic signal controller interface.

Provides an extensible abstraction for modular signal control algorithms.
Subclasses can implement fixed-time, actuated, or density/queue-based adaptive controllers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSignalController(ABC):
    """Abstract base class for traffic light controllers."""

    def __init__(self, tl_id: str):
        self.tl_id = tl_id

    @abstractmethod
    def step(self, sim_time: float, traci_conn: Any) -> Dict[str, Any]:
        """
        Called at each simulation step to observe environment state
        and optionally update traffic light phases.

        Returns a dictionary containing controller state diagnostics.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal controller state."""
        pass
