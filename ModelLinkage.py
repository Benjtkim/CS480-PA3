"""
Model our creature and wrap it in one class
First version at 09/28/2021

:author: micou(Zezhou Sun)
:version: 2021.2.1

Modified by Daniel Scrivener 08/2022
"""
from __future__ import annotations

import random

from Component import Component
from Displayable import Displayable
from Shapes import Cube, Cone, Sphere, Cylinder
from Point import Point
import ColorType as Ct
from EnvironmentObject import EnvironmentObject

try:
    import OpenGL

    try:
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
    except ImportError:
        from ctypes import util

        orig_util_find_library = util.find_library


        def new_util_find_library(name):
            res = orig_util_find_library(name)
            if res:
                return res
            return '/System/Library/Frameworks/' + name + '.framework/' + name


        util.find_library = new_util_find_library
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
except ImportError:
    raise ImportError("Required dependency PyOpenGL not present")

##### TODO 1: Construct your two different creatures
# Requirements:
#   1. Your predator and prey must be visually and semantically distinct from one another, AND distinct from the default
#   "jellyfish"-like creature (Linkage) below. Each design should clearly correspond to some kind of creature.
#   2. For the basic parts of your creatures, feel free to use routines provided with the previous assignment.
#   You are also free to create your own basic parts, but they must be polyhedral (solid).
#   You are welcome to reuse your PA2 creature in this assignment.
#   3. The creatures you design should have moving linkages of the basic parts: legs, arms, wings, antennae,
#   fins, tentacles, etc.
#   4. Model requirements:
#         1. Predator: Should have at least two moving parts in addition to the main body.
#         2. Prey: Should have at least one moving part in addition to the main body.
#         3. The predator and prey should have distinguishable, different colors.
#         4. All models should have a distinguishable head/front relative to the tail/rear side.
#   5. Vivarium requirements:
#         1. A test scene with only one (1) predator and one (1) prey, bound to key "T/t".
#         2. A default scene with at least one (1) predator and two (2) prey, reset after pressing key "R/r".

class Linkage(Component, EnvironmentObject):
    """
    A Linkage with animation enabled and is defined as an object in environment
    """
    components: list[Component] | None = None
    rotation_speed: list[list[float]] | None = None
    translation_speed: Point | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object) -> None:
        super(Linkage, self).__init__(position)
        arm1 = ModelArm(parent, Point((0, 0, 0)), shaderProg, 0.1)
        arm2 = ModelArm(parent, Point((0, 0, 0)), shaderProg, 0.1)
        arm2.setDefaultAngle(120, arm2.vAxis)
        arm3 = ModelArm(parent, Point((0, 0, 0)), shaderProg, 0.1)
        arm3.setDefaultAngle(240, arm3.vAxis)

        self.components = arm1.components + arm2.components + arm3.components
        self.addChild(arm1)
        self.addChild(arm2)
        self.addChild(arm3)

        self.rotation_speed = []
        for comp in self.components:

            comp.setRotateExtent(comp.uAxis, 0, 35)
            comp.setRotateExtent(comp.vAxis, -45, 45)
            comp.setRotateExtent(comp.wAxis, -45, 45)
            self.rotation_speed.append([0.5, 0, 0])

        self.translation_speed = Point([random.random()-0.5 for _ in range(3)]).normalize() * 0.01

        self.bound_center = Point((0, 0, 0))
        self.bound_radius = 0.1 * 4
        self.species_id = 1

    def animationUpdate(self) -> None:
        ##### TODO 2: Animate your creature!
        # Requirements:
        #   1. Set reasonable joint limits for your creature to avoid self-intersections.
        #   2. The linkages should move back and forth in a periodic motion, as the creatures move about the vivarium.
        #   For example, a bird flaps its wings, a fish wiggles its fin(s), a terrestrial creature moves its legs.

        # create periodic animation for creature joints
        for i, comp in enumerate(self.components):
            comp.rotate(self.rotation_speed[i][0], comp.uAxis)
            comp.rotate(self.rotation_speed[i][1], comp.vAxis)
            comp.rotate(self.rotation_speed[i][2], comp.wAxis)
            if comp.uAngle in comp.uRange:  # rotation reached the limit
                self.rotation_speed[i][0] *= -1
            if comp.vAngle in comp.vRange:
                self.rotation_speed[i][1] *= -1
            if comp.wAngle in comp.wRange:
                self.rotation_speed[i][2] *= -1
        self.vAngle = (self.vAngle + 3) % 360

        self.update()

    def stepForward(self, potentialsOn: bool) -> None:

        ##### TODO 3: Tank collision detection
        # Requirements:
        #   1. Your creatures should always stay within the fixed-size 3D "tank". You should do collision detection
        #   between the creatures and the tank walls. When creatures hit the tank walls, they should turn and change
        #   direction to stay within the tank.
        #   2. Use a bounding sphere or bounding box for collision detection. (Spheres are easiest.)
        #   3. After collision, the outgoing direction should be a proper reflection. You can use a reflection vector
        #   about a plane to decide the after-collision direction.
        #   4. Before implementing TODO 4, you can test this by initializing each creature with a random "target"
        #   direction and having it move continuously in that direction until a collision occurs.

        ##### TODO 4: "Hunting" simulation with potentials and creature collision
        # Requirements:
        #   1. Your creatures should have a prey/predator relationship. For example, you could have a bug being chased
        #   by a spider, or a fish eluding a shark. This means your creature should react to other creatures in the tank.
        #       1. Use potential functions to change its direction based on other creatures' locations, their
        #       inter-creature distances, and their current configuration.
        #       2. You should detect collisions between creatures.
        #           1. Predator-prey collision: The prey should disappear (get eaten) from the tank.
        #           2. Collision between the same species: They should bounce apart from each other. You can use a
        #           reflection vector about a plane to decide the after-collision direction.
        #   2. Your creatures should be able to move in 3 dimensions, not only on a plane.
        #   3. Respect potentialsOn (toggled with the "P" key, ON by default):
        #       * ON (teal background): all of the above behavior applies.
        #       * OFF (gray background): creatures do not react to one another. They keep their last target direction
        #       and move in a straight line, changing direction only when they collide with another creature or the
        #       tank walls.
        #   We recommend modularizing shared functions (bouncing two creatures off each other, checking the tank
        #   walls, etc.) within the EnvironmentObject class so that all creatures can inherit them.

        ##### TODO 5: Creature orientation
        # Requirements:
        #   1. Creatures should face the "target" direction in which they are currently moving. For instance, a fish
        #   should be facing the direction in which it swims. Since creatures move in 3 dimensions, they should be
        #   able to face any direction in 3D space.
        #   2. You have multiple choices as to how you accomplish this:
        #       * Non-cumulative (rotate from the model's default facing direction to the target facing direction
        #       on each frame): orthonormal basis transformation, or quaternions (use .toMatrix() to get the
        #       final 4x4 transform)
        #       * Cumulative (keep track of a "total" rotation that the creature has accumulated over its lifetime,
        #       hardest): quaternions

        ##### BONUS 7: Group behaviors
        # Requirements:
        #   1. Add at least 5 creatures to the vivarium and make it possible for creatures to engage in group behaviors,
        #   for instance flocking together. This can be achieved by implementing the
        #   [Boids animation algorithms](http://www.red3d.com/cwr/boids/) of Craig Reynolds.
        #   2. Your in-person demo should make the flocking behavior very obvious/easy to see in order to receive credit.

        # Access the Vivarium and its attributes as self.vivarium

        pass

class ModelArm(Component):
    """
    Define our linkage model
    """

    components: list[Component] | None = None
    contextParent: object | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object,
                 linkageLength: float = 0.5,
                 display_obj: Displayable | None = None) -> None:
        super().__init__(position, display_obj)
        self.components = []
        self.contextParent = parent

        link1 = Cube(Point((0, 0, 0)), shaderProg, [linkageLength / 4, linkageLength / 4, linkageLength], Ct.DARKORANGE1)
        link2 = Cube(Point((0, 0, linkageLength)), shaderProg, [linkageLength / 4, linkageLength / 4, linkageLength], Ct.DARKORANGE2)
        link3 = Cube(Point((0, 0, linkageLength)), shaderProg, [linkageLength / 4, linkageLength / 4, linkageLength], Ct.DARKORANGE3)
        link4 = Cube(Point((0, 0, linkageLength)), shaderProg, [linkageLength / 4, linkageLength / 4, linkageLength], Ct.DARKORANGE4)

        self.addChild(link1)
        link1.addChild(link2)
        link2.addChild(link3)
        link3.addChild(link4)

        self.components = [link1, link2, link3, link4]


