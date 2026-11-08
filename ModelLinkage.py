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
from Quaternion import Quaternion
import ColorType as Ct
import math
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
    components: dict[str, Component] | None = None
    rotation_speed: list[list[float]] | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object) -> None:
        super(Linkage, self).__init__(position)

        self.dragonflyEaten = False

        self.dragonfly = ModelDragonfly(parent, Point(-1.2,-1.2,-1.2), shaderProg, 0.1)
        self.addChild(self.dragonfly)
        self.dragonfly.bound_radius = 0.7

        self.spider = ModelSpider(parent, Point(1.2, 1.2, 1.2), shaderProg, 0.1)
        self.addChild(self.spider)
        self.spider.bound_radius = 0.65

        self.components = self.dragonfly.components | self.spider.components 
        self.rotation_speed = [9, 3, -3]
        self.direction = [Point([random.random()-0.5 for _ in range(3)]).normalize(), Point([random.random()-0.5 for _ in range(3)]).normalize()] 
        self.step_size = 0.01
        

    def animationUpdate(self) -> None:
        ##### TODO 2: Animate your creature!
        # Requirements:
        #   1. Set reasonable joint limits for your creature to avoid self-intersections.
        #   2. The linkages should move back and forth in a periodic motion, as the creatures move about the vivarium.
        #   For example, a bird flaps its wings, a fish wiggles its fin(s), a terrestrial creature moves its legs.
        
        iterableComponentsFly = ["wing1", "wing2", "wing3", "wing4"]
        iterableComponentsSpider1 = ["upperLeftLegLink1", "lowerLeftLegLink1", "upperRightLegLink1", "lowerRightLegLink1"]
        iterableComponentsSpider2 = ["middleLeftLegLink1", "middleRightLegLink1"]
        for str, comp in self.components.items():
            if str in iterableComponentsFly:
                newAngle = comp.wAngle + self.rotation_speed[0]
                if newAngle < comp.wRange[0] or newAngle > comp.wRange[1]:
                    self.rotation_speed[0] *= -1
                comp.rotate(self.rotation_speed[0], comp.wAxis)
            elif str in iterableComponentsSpider1:
                newAngle = comp.vAngle + self.rotation_speed[1]
                if newAngle < comp.vRange[0] or newAngle > comp.vRange[1]:
                    self.rotation_speed[1] *= -1
                comp.rotate(self.rotation_speed[1], comp.vAxis)
            elif str in iterableComponentsSpider2:
                newAngle = comp.vAngle + self.rotation_speed[2]
                if newAngle < comp.vRange[0] or newAngle > comp.vRange[1]:
                    self.rotation_speed[2] *= -1
                comp.rotate(self.rotation_speed[2], comp.vAxis)

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

        d_start = Point(0, 0, 1)

        newPos_dragonfly = self.dragonfly.currentPos + self.step_size * self.direction[0]
        newPos_spider = self.spider.currentPos + self.step_size * self.direction[1]

        if not self.dragonflyEaten:
            distance = self.dragonfly.currentPos.distance(self.spider.currentPos)
            gradiant = (2 * (newPos_dragonfly - newPos_spider) * math.pow(math.e, -1 * (distance * distance))).normalize()
            self.direction[0] = -1* gradiant
            self.direction[1] = gradiant
           
            newPos_spider = self.spider.currentPos + self.step_size * self.direction[1]

            newPos_dragonfly = self.dragonfly.currentPos + self.step_size * self.direction[0]

            distance = newPos_dragonfly.distance(newPos_spider)

            radiiSum = self.dragonfly.bound_radius + self.spider.bound_radius

            if distance <= radiiSum:
                self.vivarium.toDelete.append(self.dragonfly)
                self.dragonflyEaten = True

        d_end_dragonfly = self.direction[0]
        cross_product_dragonfly = d_start.cross3d(d_end_dragonfly).normalize()
        dot_product_dragonfly = d_start.dot(d_end_dragonfly)
        theta_dragonfly = math.acos(dot_product_dragonfly)

        d_end_spider = self.direction[1]
        cross_product_spider = d_start.cross3d(d_end_spider).normalize()
        dot_product_spider = d_start.dot(d_end_spider)
        theta_spider = math.acos(dot_product_spider)

        transform_dragonfly = Quaternion(
            math.cos(theta_dragonfly / 2),
             cross_product_dragonfly[0] * math.sin(theta_dragonfly / 2),
             cross_product_dragonfly[1] * math.sin(theta_dragonfly / 2),
             cross_product_dragonfly[2] * math.sin(theta_dragonfly / 2)
        ).toMatrix()

        transform_spider = Quaternion(
            math.cos(theta_spider / 2),
             cross_product_spider[0] * math.sin(theta_spider / 2),
             cross_product_spider[1] * math.sin(theta_spider / 2),
             cross_product_spider[2] * math.sin(theta_spider / 2)
        ).toMatrix()

        if ((newPos_dragonfly.x + self.dragonfly.bound_radius >= self.vivarium.tank_dimensions[0] / 2) or 
            (newPos_dragonfly.x - self.dragonfly.bound_radius <= -self.vivarium.tank_dimensions[0] / 2)):
            self.direction[0] = Point(-self.direction[0].x, self.direction[0].y, self.direction[0].z)
        
        if ((newPos_dragonfly.y + self.dragonfly.bound_radius >= self.vivarium.tank_dimensions[1] / 2) or 
            (newPos_dragonfly.y - self.dragonfly.bound_radius <= -self.vivarium.tank_dimensions[1] / 2)):
            self.direction[0] = Point(self.direction[0].x, -self.direction[0].y, self.direction[0].z)

        if ((newPos_dragonfly.z + self.dragonfly.bound_radius >= self.vivarium.tank_dimensions[2] / 2) or 
            (newPos_dragonfly.z - self.dragonfly.bound_radius <= -self.vivarium.tank_dimensions[2] / 2)):
            self.direction[0] = Point(self.direction[0].x, self.direction[0].y, -self.direction[0].z)

        if ((newPos_spider.x + self.spider.bound_radius >= self.vivarium.tank_dimensions[0] / 2) or 
            (newPos_spider.x - self.spider.bound_radius <= -self.vivarium.tank_dimensions[0] / 2)):
            self.direction[1] = Point(-self.direction[1].x, self.direction[1].y, self.direction[1].z)
        
        if ((newPos_spider.y + self.spider.bound_radius >= self.vivarium.tank_dimensions[1] / 2) or 
            (newPos_spider.y - self.spider.bound_radius <= -self.vivarium.tank_dimensions[1] / 2)):
            self.direction[1] = Point(self.direction[1].x, -self.direction[1].y, self.direction[1].z)

        if ((newPos_spider.z + self.spider.bound_radius >= self.vivarium.tank_dimensions[2] / 2) or 
            (newPos_spider.z - self.spider.bound_radius <= -self.vivarium.tank_dimensions[2] / 2)):
            self.direction[1] = Point(self.direction[1].x, self.direction[1].y, -self.direction[1].z)

        self.spider.setCurrentPosition(newPos_spider)
        self.spider.setPreRotation(transform_spider)

        self.dragonfly.setCurrentPosition(newPos_dragonfly)
        self.dragonfly.setPreRotation(transform_dragonfly)

        # Access the Vivarium and its attributes as self.vivarium
        self.update()


class ModelDragonfly(Component):
    """
    Define our linkage model
    """

    components: dict[str, Component] | None = None
    contextParent: object | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object,
                 linkageLength: float = 0.5,
                 display_obj: Displayable | None = None) -> None:
        super().__init__(position, display_obj)
        self.contextParent = parent

        body = Sphere(Point(0, 0, 0), shaderProg, [0.11665, 0.11665, 0.35], Ct.GREEN)

        face = Sphere(Point(0, 0.00005, 0.4), shaderProg, [0.125, 0.1, 0.125], Ct.DARKGREEN)

        wing1 = Sphere(Point(-0.05, 0.1, 0.45), shaderProg, [0.1, 0.025, 0.35], Ct.RED)

        wing2 = Sphere(Point(0.05, 0.1, 0.45), shaderProg, [0.1, 0.025, 0.35], Ct.RED)

        wing3 = Sphere(Point(-0.05, 0.1, 0.275), shaderProg, [0.1, 0.025, 0.35], Ct.RED)

        wing4 = Sphere(Point(0.05, 0.1, 0.275), shaderProg, [0.1, 0.025, 0.35], Ct.RED)

        tail = Sphere(Point(0, 0, -0.25), shaderProg, [0.05, 0.05, 0.5], Ct.RED)

        eye1 = Sphere(Point(0.075, 0.025, 0), shaderProg, [0.075, 0.05, 0.075], Ct.BLUE)

        eye2 = Sphere(Point(-0.075, 0.025, 0), shaderProg, [0.075, 0.05, 0.075], Ct.BLUE)

        self.addChild(body)
        body.addChild(face)
        body.addChild(wing1)
        body.addChild(wing2)
        body.addChild(wing3)
        body.addChild(wing4)
        body.addChild(tail)
        face.addChild(eye1)
        face.addChild(eye2)
        self.components = {
            "body": body,
            "face": face,
            "wing1": wing1,
            "wing2": wing2,
            "wing3": wing3,
            "wing4": wing4,
            "eye1": eye1,
            "eye2": eye2
            }
        wing1.rotate(75, self.vAxis)
        wing2.rotate(-75, self.vAxis)
        wing3.rotate(80, self.vAxis)
        wing4.rotate(-80, self.vAxis)
        wing2.setDefaultW([0, 0, -1])
        wing4.setDefaultW([0, 0, -1])

        wing1.setRotateExtent(wing1.wAxis, -30, 30)
        wing2.setRotateExtent(wing2.wAxis, -30, 30)
        wing3.setRotateExtent(wing3.wAxis, -30, 30)
        wing4.setRotateExtent(wing4.wAxis, -30, 30)

class ModelSpider(Component):
    """
    Define our linkage model
    """

    components: dict[str, Component] | None = None
    contextParent: object | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object,
                 linkageLength: float = 0.5,
                 display_obj: Displayable | None = None) -> None:
        super().__init__(position, display_obj)
        self.contextParent = parent

        body = Sphere(Point(0,0,0), shaderProg, [0.3033, 0.3033, 0.4333], Ct.GREEN)

        face = Sphere(Point(0, 0.00013, 0.52), shaderProg, [0.26, 0.195, 0.2167], Ct.DARKGREEN)

        eye1 = Sphere(Point(-0.1083, 0.00013, 0.195), shaderProg, [0.0433, 0.0433, 0.0433], Ct.BLACK)

        eye2 = Sphere(Point(0.1083, 0.00013, 0.195), shaderProg, [0.0433, 0.0433, 0.0433], Ct.BLACK)

        pupil1 = Sphere(Point(0.0173, 0.00013, 0.0347), shaderProg, [0.013, 0.013, 0.013], Ct.WHITE)

        pupil2 = Sphere(Point(0.0173, 0.00013, 0.0347), shaderProg, [0.013, 0.013, 0.013], Ct.WHITE)

        tooth1 = Cone(Point(-0.1083, -0.0867, 0.2167), shaderProg, [0.013, 0.0433, 0.0867], Ct.RED)

        tooth2 = Cone(Point(0.1083, -0.0867, 0.2167), shaderProg, [0.013, 0.0433, 0.0867], Ct.RED)

        tailPart1 = Sphere(Point(0, 0.065, -0.4203), shaderProg, [-0.0867, -0.0867, -0.0867], Ct.CYAN)

        tailPart2 = Cone(Point(0, 0.0433, 0.3033), shaderProg, [0.065, 0.065, 0.3467], Ct.BLUE)

        upperLeftLegLink1 = Cylinder(Point(0.2167, 0, 0.3467), shaderProg, [0.0563, 0.0563, 0.1733], Ct.YELLOW)
        upperLeftLegLink2 = Cylinder(Point(0, 0, 0.273), shaderProg, [0.0563, 0.0563, 0.1517], Ct.BLUE)
        upperLeftLegLink3 = Cylinder(Point(0, 0, 0.1603), shaderProg, [0.0563, 0.0563, 0.0433], Ct.YELLOW)

        middleLeftLegLink1 = Cylinder(Point(0.2167, 0, 0.13), shaderProg, [0.0563, 0.0563, 0.1733], Ct.YELLOW)
        middleLeftLegLink2 = Cylinder(Point(0, 0, 0.273), shaderProg, [0.0563, 0.0563, 0.1517], Ct.BLUE)
        middleLeftLegLink3 = Cylinder(Point(0, 0, 0.1603), shaderProg, [0.0563, 0.0563, 0.0433], Ct.YELLOW)

        lowerLeftLegLink1 = Cylinder(Point(0.13, 0, -0.0867), shaderProg, [0.0563, 0.0563, 0.1733], Ct.YELLOW)
        lowerLeftLegLink2 = Cylinder(Point(0, 0, 0.273), shaderProg, [0.0563, 0.0563, 0.1517], Ct.BLUE)
        lowerLeftLegLink3 = Cylinder(Point(0, 0, 0.1603), shaderProg, [0.0563, 0.0563, 0.0433], Ct.YELLOW)

        upperRightLegLink1 = Cylinder(Point(-0.2167, 0, 0.3467), shaderProg, [0.0563, 0.0563, 0.1733], Ct.YELLOW)
        upperRightLegLink2 = Cylinder(Point(0, 0, 0.273), shaderProg, [0.0563, 0.0563, 0.1517], Ct.BLUE)
        upperRightLegLink3 = Cylinder(Point(0, 0, 0.1603), shaderProg, [0.0563, 0.0563, 0.0433], Ct.YELLOW)

        middleRightLegLink1 = Cylinder(Point(-0.2167, 0, 0.13), shaderProg, [0.0563, 0.0563, 0.1733], Ct.YELLOW)
        middleRightLegLink2 = Cylinder(Point(0, 0, 0.273), shaderProg, [0.0563, 0.0563, 0.1517], Ct.BLUE)
        middleRightLegLink3 = Cylinder(Point(0, 0, 0.1603), shaderProg, [0.0563, 0.0563, 0.0433], Ct.YELLOW)

        lowerRightLegLink1 = Cylinder(Point(-0.13, 0, -0.0867), shaderProg, [0.0563, 0.0563, 0.1733], Ct.YELLOW)
        lowerRightLegLink2 = Cylinder(Point(0, 0, 0.273), shaderProg, [0.0563, 0.0563, 0.1517], Ct.BLUE)
        lowerRightLegLink3 = Cylinder(Point(0, 0, 0.1603), shaderProg, [0.0563, 0.0563, 0.0433], Ct.YELLOW)


        tooth1.rotate(30, self.uAxis)
        tooth1.rotate(-20, self.vAxis)

        tooth2.rotate(30, self.uAxis)
        tooth2.rotate(20, self.vAxis)

        tailPart2.rotate(220, self.uAxis)

        upperLeftLegLink1.rotate(20, self.uAxis)
        upperLeftLegLink1.rotate(90, self.vAxis)
        
        upperLeftLegLink2.rotate(20, self.uAxis)

        upperLeftLegLink3.rotate(30, self.uAxis)

        middleLeftLegLink1.rotate(20, self.uAxis)
        middleLeftLegLink1.rotate(90, self.vAxis)

        middleLeftLegLink2.rotate(20, self.uAxis)

        middleLeftLegLink3.rotate(30, self.uAxis)

        lowerLeftLegLink1.rotate(20, self.uAxis)
        lowerLeftLegLink1.rotate(90, self.vAxis)
        
        lowerLeftLegLink2.rotate(20, self.uAxis)

        lowerLeftLegLink3.rotate(30, self.uAxis)

        upperRightLegLink1.rotate(200, self.uAxis)
        upperRightLegLink1.rotate(270, self.vAxis)
        upperRightLegLink1.rotate(180, self.wAxis)
        upperRightLegLink1.setDefaultW([0, 0, -1])

        upperRightLegLink2.rotate(20, self.uAxis)

        upperRightLegLink3.rotate(30, self.uAxis)

        middleRightLegLink1.rotate(200, self.uAxis)
        middleRightLegLink1.rotate(270, self.vAxis)
        middleRightLegLink1.rotate(180, self.wAxis)
        middleRightLegLink1.setDefaultW([0, 0, -1])

        middleRightLegLink2.rotate(20, self.uAxis)

        middleRightLegLink3.rotate(30, self.uAxis)

        lowerRightLegLink1.rotate(200, self.uAxis)
        lowerRightLegLink1.rotate(270, self.vAxis)
        lowerRightLegLink1.rotate(180, self.wAxis)
        lowerRightLegLink1.setDefaultW([0, 0, -1])

        lowerRightLegLink2.rotate(20, self.uAxis)
        lowerRightLegLink3.rotate(30, self.uAxis)

        self.addChild(body)

        body.addChild(face)

        face.addChild(eye1)

        face.addChild(eye2)

        eye1.addChild(pupil1)

        eye2.addChild(pupil2)

        face.addChild(tooth1)

        face.addChild(tooth2)

        body.addChild(tailPart1)
        tailPart1.addChild(tailPart2)

        body.addChild(upperLeftLegLink1)
        upperLeftLegLink1.addChild(upperLeftLegLink2)
        upperLeftLegLink2.addChild(upperLeftLegLink3)

        body.addChild(middleLeftLegLink1)
        middleLeftLegLink1.addChild(middleLeftLegLink2)
        middleLeftLegLink2.addChild(middleLeftLegLink3)

        body.addChild(lowerLeftLegLink1)
        lowerLeftLegLink1.addChild(lowerLeftLegLink2)
        lowerLeftLegLink2.addChild(lowerLeftLegLink3)

        body.addChild(upperRightLegLink1)
        upperRightLegLink1.addChild(upperRightLegLink2)
        upperRightLegLink2.addChild(upperRightLegLink3)

        body.addChild(middleRightLegLink1)
        middleRightLegLink1.addChild(middleRightLegLink2)
        middleRightLegLink2.addChild(middleRightLegLink3)

        body.addChild(lowerRightLegLink1)
        lowerRightLegLink1.addChild(lowerRightLegLink2)
        lowerRightLegLink2.addChild(lowerRightLegLink3)

        self.components = {
            "body": body,
            "face": face,
            "eye1": eye1,
            "eye2": eye2,
            "pupil1": pupil1,
            "pupil2": pupil2,
            "tooth1": tooth1,
            "tooth2": tooth2,
            "tailPart1": tailPart1,
            "tailPart2": tailPart2,
            "upperLeftLegLink1": upperLeftLegLink1,
            "upperLeftLegLink2": upperLeftLegLink2,
            "upperLeftLegLink3": upperLeftLegLink3,
            "middleLeftLegLink1": middleLeftLegLink1,
            "middleLeftLegLink2": middleLeftLegLink2,
            "middleLeftLegLink3": middleLeftLegLink3,
            "lowerLeftLegLink1": lowerLeftLegLink1,
            "lowerLeftLegLink2": lowerLeftLegLink2,
            "lowerLeftLegLink3": lowerLeftLegLink3,
            "upperRightLegLink1": upperRightLegLink1,
            "upperRightLegLink2": upperRightLegLink2,
            "upperRightLegLink3": upperRightLegLink3,
            "middleRightLegLink1": middleRightLegLink1,
            "middleRightLegLink2": middleRightLegLink2,
            "middleRightLegLink3": middleRightLegLink3,
            "lowerRightLegLink1": lowerRightLegLink1,
            "lowerRightLegLink2": lowerRightLegLink2,
            "lowerRightLegLink3": lowerRightLegLink3,
        }

        upperLeftLegLink1.setRotateExtent(upperLeftLegLink1.vAxis, 50, 100)

        middleLeftLegLink1.setRotateExtent(middleLeftLegLink1.vAxis, 50, 100)

        lowerLeftLegLink1.setRotateExtent(lowerLeftLegLink1.vAxis, 50, 100)

        upperRightLegLink1.setRotateExtent(upperRightLegLink1.vAxis, 230, 280)

        middleRightLegLink1.setRotateExtent(middleRightLegLink1.vAxis, 230, 280)

        lowerRightLegLink1.setRotateExtent(lowerRightLegLink1.vAxis, 230, 280)


