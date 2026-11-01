'''
Abstract base class for objects that participate in the vivarium simulation loop.
'''
from __future__ import annotations

from abc import ABC, abstractmethod

from Point import Point


class EnvironmentObject(ABC):
    """
    Interface for objects in the vivarium simulation.

    Subclasses must implement two methods:
        - animationUpdate: advance periodic/cyclic animation (e.g. flapping wings, wagging tails)
        - stepForward: move through the world, handle collisions and chasing/fleeing behavior

    The vivarium attribute is set automatically when the object is added to a Vivarium
    via addNewObjInTank. Use it to access tank_dimensions, other components, etc.
    """
    vivarium: object | None = None
    species_id: int = 0
    bound_center: Point = Point((0, 0, 0))
    bound_radius: float = 0.0


    @abstractmethod
    def animationUpdate(self) -> None:
        """
        Advance this object's periodic animation by one frame.
        This handles cyclic joint motion (wing flaps, leg cycles, etc.)
        that is independent of the object's movement through the world.

        Override this method in your ModelLinkage classes!
        """
        raise NotImplementedError

    @abstractmethod
    def stepForward(self, potentialsOn: bool) -> None:
        """
        Move this object forward in the simulation by one step.
        This handles translation, collision detection/response,
        and predator/prey behavior.

        Override this method in your ModelLinkage classes!
        """
        raise NotImplementedError

