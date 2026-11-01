"""
All creatures should be added to Vivarium. Some help functions to add/remove creature are defined here.
Created on 20181028

:author: micou(Zezhou Sun)
:version: 2021.1.1

modified by Daniel Scrivener
"""
from __future__ import annotations

import numpy as np
from Point import Point
from Component import Component
from ModelTank import Tank
from EnvironmentObject import EnvironmentObject
from ModelLinkage import Linkage


class Vivarium(Component):
    """
    The Vivarium for our animation
    """
    components: list[Component] | None = None
    parent: object | None = None
    tank: Tank | None = None
    tank_dimensions: list[float] | None = None

    ##### BONUS 6 (TODO 6 for CS680 Students): Feed your creatures
    # Requirements:
    #   Add chunks of food to the vivarium which can be eaten by your creatures.
    #     * When 'f' is pressed, have a food particle be generated at random within the vivarium.
    #     * Be sure to draw the food on the screen with an additional model. It should drop slowly to the bottom of
    #     the vivarium and remain there within the tank until eaten.
    #     * The food should disappear once it has been eaten. Food is eaten by the first creature that touches it.
    #   Important: if you create an object outside of __init__() and it doesn't show up in the tank, call its
    #   initialize() method before adding it, e.g. obj.initialize(); vivarium.addNewObjInTank(obj)

    def __init__(self, parent: object, shaderProg: object) -> None:
        self.parent = parent
        self.shaderProg = shaderProg

        self.tank_dimensions = [4, 4, 4]
        tank = Tank(Point((0,0,0)), shaderProg, self.tank_dimensions)
        super(Vivarium, self).__init__(Point((0, 0, 0)))

        # Build relationship
        self.addChild(tank)
        self.tank = tank

        # Store all components in one list, for us to access them later
        self.components = [tank]

        self.addNewObjInTank(Linkage(parent, Point((0,0,0)), shaderProg))


    def animationUpdate(self, potentialsOn: bool) -> None:
        """
        Update all creatures in vivarium
        """

        for c in self.components[::-1]:
            if isinstance(c, EnvironmentObject):
                c.animationUpdate()
                c.stepForward(potentialsOn)

        self.update()

    def delObjInTank(self, obj: Component) -> None:
        if isinstance(obj, Component):
            self.tank.children.remove(obj)
            self.components.remove(obj)

    def addNewObjInTank(self, newComponent: Component) -> None:
        if isinstance(newComponent, Component):
            self.tank.addChild(newComponent)
            self.components.append(newComponent)
        if isinstance(newComponent, EnvironmentObject):
            newComponent.vivarium = self
