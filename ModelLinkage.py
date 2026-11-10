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

        # Potential creatures to be used in a scene.
        self.spider = ModelSpider(parent, Point(0, 0, 0), shaderProg)
        self.dragonfly1 = ModelDragonfly(parent, Point(1.4, 1.4, 1.4), shaderProg,)
        self.dragonfly2 = ModelDragonfly(parent, Point(-1.4, -1.4, -1.4), shaderProg)
        self.dragonfly3 = ModelDragonfly(parent, Point(1.4, -1.4, 1.4), shaderProg)

        # Rotation speeds as follows: index 0 corresponds to the spider's front and hind legs, index 1 
        # corresponds to the spider's middle legs, and index 2 corresponds to wings of the dragonflies.
        self.rotation_speed = [3, -3, 9]

        # Current scene.
        self.scene = [self.spider, self.dragonfly1, self.dragonfly2, self.dragonfly3]

        # Initialize self.components to be used in the following for loop.
        self.components = {}

        # For each creature in the scene, add it as a child to Linkage, set it's bound radius, and
        # add its components to self.components.
        for i, comp in enumerate(self.scene):
            self.addChild(comp)
            comp.bound_radius = 0.5

            if i == 0:
                self.components.update(comp.components)
            else:

                # If the creature is a dragonfly, use this trick to 
                # have the keys for its components start with dragonfly{i}.
                self.components.update({
                    f"dragonfly{i}_{name}": component
                    for name, component in comp.components.items()
                })

        # Initialize a random direction.
        rand_direction = Point([random.random()-0.5 for _ in range(3)]).normalize()

        # Each creature in ths scene will start moving in that random direction.
        self.direction = [rand_direction] * len(self.scene)

        # A list for the potential calculated positions for each of the prey. The value at index 0 is -1 since
        # the spider is not a prey.
        self.newPreyPositions = [-1, 0, 0, 0]

        # Initialize the step size.
        self.step_size = 0.03
        

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
            if str in iterableComponentsSpider1:
                newAngle = comp.vAngle + self.rotation_speed[0]
                if newAngle < comp.vRange[0] or newAngle > comp.vRange[1]:
                    self.rotation_speed[0] *= -1
                comp.rotate(self.rotation_speed[0], comp.vAxis)
            elif str in iterableComponentsSpider2:
                newAngle = comp.vAngle + self.rotation_speed[1]
                if newAngle < comp.vRange[0] or newAngle > comp.vRange[1]:
                    self.rotation_speed[1] *= -1
                comp.rotate(self.rotation_speed[1], comp.vAxis)
            elif str in iterableComponentsFly or (str.startswith("dragonfly") and "wing" in str):
                newAngle = comp.wAngle + self.rotation_speed[2]
                if newAngle < comp.wRange[0] or newAngle > comp.wRange[1]:
                    self.rotation_speed[2] *= -1
                comp.rotate(self.rotation_speed[2], comp.wAxis)

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

        if potentialsOn:
            
            wall_coords = [Point(1, 0, 0), Point(0, 1, 0), Point(0, 0, 1), Point(-1, 0, 0), Point(0, -1, 0), Point(0, 0, -1)]

            radiiSum = self.spider.bound_radius + self.dragonfly1.bound_radius

            gradiantPred = Point(0, 0, 0)

            for i, prey in enumerate(self.scene):

                if i == 0:
                    continue

                distance = self.spider.currentPos.distance(prey.currentPos)
                gradiantPred += (2 * (prey.currentPos - self.spider.currentPos) * math.pow(math.e, -1 * (distance * distance)))
                gradiantPrey = (-2 * (self.spider.currentPos - prey.currentPos) * math.pow(math.e, -1 * (distance * distance)))
                
                for coord in wall_coords:
                    if coord.x == 1:
                        distToWallPrey = 2 - prey.currentPos.x
                        distToWallPred = 2 - self.spider.currentPos.x
                    if coord.x == -1:
                        distToWallPrey = 2 + prey.currentPos.x
                        distToWallPred = 2 + self.spider.currentPos.x
                    if coord.y == 1:
                        distToWallPrey = 2 - prey.currentPos.y
                        distToWallPred = 2 - self.spider.currentPos.y
                    if coord.y == -1:
                        distToWallPrey = 2 + prey.currentPos.y
                        distToWallPred = 2 + self.spider.currentPos.y
                    if coord.z == 1:
                        distToWallPrey = 2 - prey.currentPos.z
                        distToWallPred = 2 - self.spider.currentPos.z
                    if coord.z == -1:
                        distToWallPrey = 2 + prey.currentPos.z
                        distToWallPred = 2 + self.spider.currentPos.z
                    gradiantPred += (-2 * (coord) * math.pow(math.e, -1 * (distToWallPred * distToWallPred))) * 0.2
                    gradiantPrey += (-2 * (coord) * math.pow(math.e, -1 * (distToWallPrey * distToWallPrey))) * 0.2

                self.direction[i] = (self.direction[i] + gradiantPrey).normalize()
                self.newPreyPositions[i] = (prey.currentPos + self.step_size * self.direction[i])

            self.direction[0] = (self.direction[0] + gradiantPred).normalize()

            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]

            for i in range(1, len(self.newPreyPositions)):
                dragonfly = getattr(self, f"dragonfly{i}")
                self.newPreyPositions[i] = (
                    dragonfly.currentPos + self.step_size * self.direction[i]
                )

                distance = newPos_spider.distance(self.newPreyPositions[i])

                if distance <= radiiSum:
                    if dragonfly not in self.vivarium.toDelete:
                        self.vivarium.toDelete.append(dragonfly)

                checkTankCollision(self, self.newPreyPositions[i], dragonfly, i)
                self.newPreyPositions[i] = dragonfly.currentPos + self.step_size * self.direction[i]

            for i in range(1, len(self.newPreyPositions)):
                for j in range(i + 1, len(self.newPreyPositions)):
                    dragonflyOne = getattr(self, f"dragonfly{i}")
                    dragonflyTwo = getattr(self, f"dragonfly{j}")
                    if checkCreatureCollision(self.newPreyPositions[i], self.newPreyPositions[j], dragonflyOne.bound_radius, dragonflyTwo.bound_radius):
                        self.direction[i] = Point(-self.direction[i].x, -self.direction[i].y, -self.direction[i].z)
                        self.direction[j] = Point(-self.direction[j].x, -self.direction[j].y, -self.direction[j].z)

            for i in range(1, len(self.newPreyPositions)):
                dragonfly = getattr(self, f"dragonfly{i}")
                dragonfly.setCurrentPosition(self.newPreyPositions[i])
                dragonfly.setPreRotation(findOrientTransform(self, i))

            checkTankCollision(self, newPos_spider, self.spider, 0)

            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]
            
            self.spider.setCurrentPosition(newPos_spider)
            self.spider.setPreRotation(findOrientTransform(self, 0))
            

        else:
            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]
            checkTankCollision(self, newPos_spider, self.spider, 0)
                
            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]

            for i in range(1, len(self.newPreyPositions)):
                dragonfly = getattr(self, f"dragonfly{i}")
                self.newPreyPositions[i] = dragonfly.currentPos + self.step_size * self.direction[i]
                checkTankCollision(self, self.newPreyPositions[i], dragonfly, i)
                self.newPreyPositions[i] = dragonfly.currentPos + self.step_size * self.direction[i]

            for i in range(len(self.newPreyPositions)):
                for j in range(i + 1, len(self.newPreyPositions)):
                    if i == 0:
                        creature2 = getattr(self, f"dragonfly{j}")
                        if checkCreatureCollision(newPos_spider, self.newPreyPositions[j], self.spider.bound_radius, creature2.bound_radius):
                            self.direction[i] = Point(-self.direction[i].x, -self.direction[i].y, -self.direction[i].z)
                            self.direction[j] = Point(-self.direction[j].x, -self.direction[j].y, -self.direction[j].z)
                            newPos_spider = self.spider.currentPos + self.step_size * self.direction[i]
                            self.newPreyPositions[j] = creature2.currentPos + self.step_size * self.direction[j]
                    else:
                        creature1 = getattr(self, f"dragonfly{i}")
                        creature2 = getattr(self, f"dragonfly{j}")
                        if checkCreatureCollision(self.newPreyPositions[i], self.newPreyPositions[j], creature1.bound_radius, creature2.bound_radius):
                            self.direction[i] = Point(-self.direction[i].x, -self.direction[i].y, -self.direction[i].z)
                            self.direction[j] = Point(-self.direction[j].x, -self.direction[j].y, -self.direction[j].z)
                            self.newPreyPositions[i] = creature1.currentPos + self.step_size * self.direction[i]
                            self.newPreyPositions[j] = creature2.currentPos + self.step_size * self.direction[j]

            self.spider.setCurrentPosition(newPos_spider)
            self.spider.setPreRotation(findOrientTransform(self, 0))

            for i in range(1, len(self.newPreyPositions)):
                dragonfly = getattr(self, f"dragonfly{i}")
                dragonfly.setCurrentPosition(self.newPreyPositions[i])
                dragonfly.setPreRotation(findOrientTransform(self, i))


        self.update()

def checkTankCollision(self, proposedPosition: Point, component: Component, index: int):

    direction = self.direction[index]

    half_x = self.vivarium.tank_dimensions[0] / 2
    half_y = self.vivarium.tank_dimensions[1] / 2
    half_z = self.vivarium.tank_dimensions[2] / 2

    radius = component.bound_radius

    if proposedPosition.x + radius >= half_x or proposedPosition.x - radius <= -half_x:
        direction = Point(-direction.x, direction.y, direction.z)

    if proposedPosition.y + radius >= half_y or proposedPosition.y - radius <= -half_y:
        direction = Point(direction.x, -direction.y, direction.z)

    if proposedPosition.z + radius >= half_z or proposedPosition.z - radius <= -half_z:
        direction = Point(direction.x, direction.y, -direction.z)

    self.direction[index] = direction.normalize()

def checkCreatureCollision(pos1 : Point, pos2 : Point, radius1, radius2):
    radiiSum = radius1 + radius2
    distance = pos1.distance(pos2)
    if distance <= radiiSum:
        return True

def findOrientTransform(self, index):

    d_start = Point(0, 0, 1)
    d_end = self.direction[index]
    cross_product = d_start.cross3d(d_end).normalize()
    dot_product = d_start.dot(d_end)

    theta = math.acos(dot_product)
    quatSine = math.sin(theta / 2)

    transform = Quaternion(
        math.cos(theta / 2),
        cross_product[0] * quatSine,
        cross_product[1] * quatSine,
        cross_product[2] * quatSine
    ).toMatrix()

    return transform
    
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

        body = Sphere(Point(0, 0, 0), shaderProg, [0.09721, 0.09721, 0.29167], Ct.GREEN)

        face = Sphere(Point(0, 0.0000417, 0.33333), shaderProg, [0.10417, 0.08333, 0.10417], Ct.DARKGREEN)

        wing1 = Sphere(Point(-0.04167, 0.08333, 0.375), shaderProg, [0.08333, 0.02083, 0.29167], Ct.RED)

        wing2 = Sphere(Point(0.04167, 0.08333, 0.375), shaderProg, [0.08333, 0.02083, 0.29167], Ct.RED)

        wing3 = Sphere(Point(-0.04167, 0.08333, 0.22917), shaderProg, [0.08333, 0.02083, 0.29167], Ct.RED)

        wing4 = Sphere(Point(0.04167, 0.08333, 0.22917), shaderProg, [0.08333, 0.02083, 0.29167], Ct.RED)

        tail = Sphere(Point(0, 0, -0.20833), shaderProg, [0.04167, 0.04167, 0.41667], Ct.RED)

        eye1 = Sphere(Point(0.0625, 0.02083, 0), shaderProg, [0.0625, 0.04167, 0.0625], Ct.BLUE)

        eye2 = Sphere(Point(-0.0625, 0.02083, 0), shaderProg, [0.0625, 0.04167, 0.0625], Ct.BLUE)

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

        body = Sphere(Point(0, 0, 0), shaderProg, [0.26374, 0.26374, 0.37678], Ct.GREEN)

        face = Sphere(Point(0, 0.000113, 0.45217), shaderProg, [0.22609, 0.16957, 0.18843], Ct.DARKGREEN)

        eye1 = Sphere(Point(-0.09417, 0.000113, 0.16957), shaderProg, [0.03765, 0.03765, 0.03765], Ct.BLACK)

        eye2 = Sphere(Point(0.09417, 0.000113, 0.16957), shaderProg, [0.03765, 0.03765, 0.03765], Ct.BLACK)

        pupil1 = Sphere(Point(0.01504, 0.000113, 0.03017), shaderProg, [0.01130, 0.01130, 0.01130], Ct.WHITE)

        pupil2 = Sphere(Point(0.01504, 0.000113, 0.03017), shaderProg, [0.01130, 0.01130, 0.01130], Ct.WHITE)

        tooth1 = Cone(Point(-0.09417, -0.07539, 0.18843), shaderProg, [0.01130, 0.03765, 0.07539], Ct.RED)

        tooth2 = Cone(Point(0.09417, -0.07539, 0.18843), shaderProg, [0.01130, 0.03765, 0.07539], Ct.RED)

        tailPart1 = Sphere(Point(0, 0.05652, -0.36548), shaderProg, [-0.07539, -0.07539, -0.07539], Ct.CYAN)

        tailPart2 = Cone(Point(0, 0.03765, 0.26374), shaderProg, [0.05652, 0.05652, 0.30148], Ct.BLUE)

        upperLeftLegLink1 = Cylinder(Point(0.18843, 0, 0.30148), shaderProg, [0.04896, 0.04896, 0.15070], Ct.YELLOW)
        upperLeftLegLink2 = Cylinder(Point(0, 0, 0.23739), shaderProg, [0.04896, 0.04896, 0.13191], Ct.BLUE)
        upperLeftLegLink3 = Cylinder(Point(0, 0, 0.13939), shaderProg, [0.04896, 0.04896, 0.03765], Ct.YELLOW)

        middleLeftLegLink1 = Cylinder(Point(0.18843, 0, 0.11304), shaderProg, [0.04896, 0.04896, 0.15070], Ct.YELLOW)
        middleLeftLegLink2 = Cylinder(Point(0, 0, 0.23739), shaderProg, [0.04896, 0.04896, 0.13191], Ct.BLUE)
        middleLeftLegLink3 = Cylinder(Point(0, 0, 0.13939), shaderProg, [0.04896, 0.04896, 0.03765], Ct.YELLOW)

        lowerLeftLegLink1 = Cylinder(Point(0.11304, 0, -0.07539), shaderProg, [0.04896, 0.04896, 0.15070], Ct.YELLOW)
        lowerLeftLegLink2 = Cylinder(Point(0, 0, 0.23739), shaderProg, [0.04896, 0.04896, 0.13191], Ct.BLUE)
        lowerLeftLegLink3 = Cylinder(Point(0, 0, 0.13939), shaderProg, [0.04896, 0.04896, 0.03765], Ct.YELLOW)

        upperRightLegLink1 = Cylinder(Point(-0.18843, 0, 0.30148), shaderProg, [0.04896, 0.04896, 0.15070], Ct.YELLOW)
        upperRightLegLink2 = Cylinder(Point(0, 0, 0.23739), shaderProg, [0.04896, 0.04896, 0.13191], Ct.BLUE)
        upperRightLegLink3 = Cylinder(Point(0, 0, 0.13939), shaderProg, [0.04896, 0.04896, 0.03765], Ct.YELLOW)

        middleRightLegLink1 = Cylinder(Point(-0.18843, 0, 0.11304), shaderProg, [0.04896, 0.04896, 0.15070], Ct.YELLOW)
        middleRightLegLink2 = Cylinder(Point(0, 0, 0.23739), shaderProg, [0.04896, 0.04896, 0.13191], Ct.BLUE)
        middleRightLegLink3 = Cylinder(Point(0, 0, 0.13939), shaderProg, [0.04896, 0.04896, 0.03765], Ct.YELLOW)

        lowerRightLegLink1 = Cylinder(Point(-0.11304, 0, -0.07539), shaderProg, [0.04896, 0.04896, 0.15070], Ct.YELLOW)
        lowerRightLegLink2 = Cylinder(Point(0, 0, 0.23739), shaderProg, [0.04896, 0.04896, 0.13191], Ct.BLUE)
        lowerRightLegLink3 = Cylinder(Point(0, 0, 0.13939), shaderProg, [0.04896, 0.04896, 0.03765], Ct.YELLOW)

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


