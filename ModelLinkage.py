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

class Linkage(Component, EnvironmentObject):
    """
    A Linkage with animation enabled and is defined as an object in environment
    """
    components: dict[str, Component] | None = None
    rotation_speed: list[list[float]] | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object) -> None:
        super(Linkage, self).__init__(position)

        # Sets the default scene when simulation is started up.

        # Fields to determine which creatures are still in the scene/whether there are any 
        # prey creatures (dragonflies) left.
        self.preyStillActive = True
        self.preyEaten = 0
        self.eatenPrey = set()
        self.delected_creatures = [False, False, False, False]

        # Potential creatures to be used in a scene.
        self.spider = ModelSpider(parent, Point(0, 0, 0), shaderProg)
        self.dragonfly1 = ModelDragonfly(parent, Point(1.4, 1.4, 1.4), shaderProg,)
        self.dragonfly2 = ModelDragonfly(parent, Point(-1.4, -1.4, -1.4), shaderProg)
        self.dragonfly3 = ModelDragonfly(parent, Point(1.4, -1.4, 1.4), shaderProg)

        # Rotation speeds as follows: index 0 corresponds to the spider's front and hind legs, index 1 
        # corresponds to the spider's middle legs, and index 2 corresponds to wings of the dragonflies.
        self.rotation_speed = [3, -3, 9]

        # Default scene.
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
        self.direction = [rand_direction.copy()] * len(self.scene)

        # A list for the potential calculated positions for each of the prey. The value at index 0 is -1 since
        # the spider is not a prey.
        self.newPreyPositions = [0] * len(self.scene)
        self.newPreyPositions[0] = -1

        # Initialize the step size.
        self.step_size = 0.03

    # Function that sets the corresponding scene depending on if t or r is pressed.
    def setScene(self, testScene: bool) -> None:

        # Remove all creatures that were left in the prior scene.
        self.children.clear()

        # Reset every creature to its original position.
        for creature in [self.spider, self.dragonfly1,
                        self.dragonfly2, self.dragonfly3]:

            creature.setCurrentPosition(creature.defaultPos.copy())
        
        # Choose which creatures should be active.
        if testScene:
            self.scene = [self.spider, self.dragonfly1]
        else:
            self.scene = [
                self.spider,
                self.dragonfly1,
                self.dragonfly2,
                self.dragonfly3
            ]

        # Reinitialize the component dictionary.
        self.components = {}

        for i, comp in enumerate(self.scene):
            self.addChild(comp)
            comp.bound_radius = 0.5

            if i == 0:
                self.components.update(comp.components)
            else:
                self.components.update({
                    f"dragonfly{i}_{name}": component
                    for name, component in comp.components.items()
                })

        # Reset movement directions.
        rand_direction = Point([random.random() - 0.5 for _ in range(3)]).normalize()

        self.direction = [rand_direction.copy() for _ in self.scene]

        # Reset potential positions.
        self.newPreyPositions = [0] * len(self.scene)
        self.newPreyPositions[0] = -1

        # Reset eaten prey tracking.
        self.preyEaten = 0
        self.eatenPrey.clear()
        self.preyStillActive = True

        self.delected_creatures = [False] * len(self.scene)

        # Update the component hierarchy.
        self.update()
        

    def animationUpdate(self) -> None:

        # The components that should be animated if the creature is a dragonfly are its wings. If the creature is a spider,
        # its legs should be animated.
        iterableComponentsDragonfly = ["wing1", "wing2", "wing3", "wing4"]
        iterableComponentsSpider1 = ["upperLeftLegLink1", "lowerLeftLegLink1", "upperRightLegLink1", "lowerRightLegLink1"]
        iterableComponentsSpider2 = ["middleLeftLegLink1", "middleRightLegLink1"]

        # For each component in self.components, check if if is an interable component. If it is, find the new angle
        # the limb should be rotated by, and if it's outside the bounds, rotate in the other direction/
        # negate the rotation speed. Finally, carry out hte rotation.
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
            elif str in iterableComponentsDragonfly or (str.startswith("dragonfly") and "wing" in str):
                newAngle = comp.wAngle + self.rotation_speed[2]
                if newAngle < comp.wRange[0] or newAngle > comp.wRange[1]:
                    self.rotation_speed[2] *= -1
                comp.rotate(self.rotation_speed[2], comp.wAxis)

        self.update()

    def stepForward(self, potentialsOn: bool) -> None:

        ##### BONUS 7: Group behaviors
        # Requirements:
        #   1. Add at least 5 creatures to the vivarium and make it possible for creatures to engage in group behaviors,
        #   for instance flocking together. This can be achieved by implementing the
        #   [Boids animation algorithms](http://www.red3d.com/cwr/boids/) of Craig Reynolds.
        #   2. Your in-person demo should make the flocking behavior very obvious/easy to see in order to receive credit.

        if potentialsOn:

            # Normal vectors to each of the walls.
            wall_coords = [Point(1, 0, 0), Point(0, 1, 0), Point(0, 0, 1), Point(-1, 0, 0), Point(0, -1, 0), Point(0, 0, -1)]

            # The gradiant for the pred will start off as (0, 0, 0) and will need to be accumulated to its final value.
            gradiantPred = Point(0, 0, 0)

            # No need to do calcuations involving dragonflies if there aren't any.
            if self.preyStillActive:

                # Loops through each creature in self.scene, but we want to iterate over only the prey creatures.
                for i, prey in enumerate(self.scene):

                    # If the index is 0, the loop is looking at the spider. If self.delected_creatures[i] is true,
                    # the corresponding creature is no longer a part of the scene. In either case, we need to 
                    # ignore this creature.
                    if i == 0 or self.delected_creatures[i]:
                        continue

                    # Calculate the distance from the spider to the current prey, and add to gradiantPred or set 
                    # gradiantPrey accordingly using that distance. The calculation prey.currentPos - self.spider.currentPos
                    # is the vector that points from the spider to the dragonfly, so we want to add by this vector to 
                    # encourage the spider to move towards the dragonfly. On the other hand, self.spider.currentPos - 
                    # prey.currentPos points from the dragonfly to the spider so we want to negate it so the dragonfly 
                    # moves away from the spider.
                    distance = self.spider.currentPos.distance(prey.currentPos)
                    gradiantPred += (2 * (prey.currentPos - self.spider.currentPos) * math.pow(math.e, -1 * (distance * distance)))
                    gradiantPrey = (-2 * (self.spider.currentPos - prey.currentPos) * math.pow(math.e, -1 * (distance * distance)))

                    # Each of the walls will also have a negative potential, as we want each creature to stay inside their bounds. 
                    # So, for each of the wall normals, get the distance from that wall to the prey, and add the resulting gradiant 
                    # to the overall prey gradiant. 
                    for coord in wall_coords:
                        if coord.x == 1:
                            distToWallPrey = 2 - prey.currentPos.x
                        if coord.x == -1:
                            distToWallPrey = 2 + prey.currentPos.x
                        if coord.y == 1:
                            distToWallPrey = 2 - prey.currentPos.y
                        if coord.y == -1:
                            distToWallPrey = 2 + prey.currentPos.y
                        if coord.z == 1:
                            distToWallPrey = 2 - prey.currentPos.z
                        if coord.z == -1:
                            distToWallPrey = 2 + prey.currentPos.z
                        gradiantPrey += (-2 * (coord) * math.pow(math.e, -1 * (distToWallPrey * distToWallPrey))) * 0.2

                    # Add the accumulated prey gradiant to the previous direction and normalize to get the direction
                    # for this frame. Calculate using currentPos to get the new position of the dragonfly for
                    # this frame.
                    self.direction[i] = (self.direction[i] + gradiantPrey).normalize()
                    # self.direction[i] = gradiantPrey.normalize() # Either do this or the above. The above looks better.
                    self.newPreyPositions[i] = (prey.currentPos + self.step_size * self.direction[i])

                # Same idea as above but for the spider.
                for coord in wall_coords:
                    if coord.x == 1:
                        distToWallPred = 2 - self.spider.currentPos.x
                    if coord.x == -1:
                        distToWallPred = 2 + self.spider.currentPos.x
                    if coord.y == 1:
                        distToWallPred = 2 - self.spider.currentPos.y
                    if coord.y == -1:
                        distToWallPred = 2 + self.spider.currentPos.y
                    if coord.z == 1:
                        distToWallPred = 2 - self.spider.currentPos.z
                    if coord.z == -1:
                        distToWallPred = 2 + self.spider.currentPos.z
                    gradiantPred += (-2 * (coord) * math.pow(math.e, -1 * (distToWallPred * distToWallPred))) * 0.2

                self.direction[0] = (self.direction[0] + gradiantPred).normalize()
                # self.direction[0] = gradiantPred.normalize() # Either do this or the above. The above looks better.

            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]

            # The code in this if statement checks if a spider has collided with any of the dragonflies, 
            # or if any of the dragonflies have collided with any other dragonfly.
            if self.preyStillActive:

                # For each dragonfly in the current scene:
                for i in range(1, len(self.scene)):

                    # If it had been deleted continue.
                    if self.delected_creatures[i]:
                        continue

                    # Get the dragonfly object, find the sum of radii between it and the spider, 
                    # and get the current distance between them.
                    dragonfly = self.scene[i]
                    radiiSum = self.spider.bound_radius + dragonfly.bound_radius
                    distance = newPos_spider.distance(self.newPreyPositions[i])

                    # If they're colliding (if the distance between them is less than the 
                    # sum of the radii), and the dragonfly has not been deleted yet,
                    if distance <= radiiSum and dragonfly not in self.eatenPrey:

                        # add it to the eatenPrey set, mark it for deletion by appending
                        # it to the vivarium's toDelete list, mark that it has been deleted
                        # in self.deleted_creatures, and set the count of prey eaten to 
                        # how many prey are in the eatenPrey set, as those are the same.
                        self.eatenPrey.add(dragonfly)
                        self.vivarium.toDelete.append(dragonfly)
                        self.delected_creatures[i] = True
                        self.preyEaten = len(self.eatenPrey)

                    # Check if it is colliding with the tank. If it is, the helper function
                    # would have reversed its direction accordingly, so its new position has to 
                    # be recalculated.
                    checkTankCollision(self, self.newPreyPositions[i], dragonfly, i)
                    self.newPreyPositions[i] = dragonfly.currentPos + self.step_size * self.direction[i]

                # Check to see if there are any prey left.
                self.preyStillActive = self.preyEaten < len(self.scene) - 1

                # This nested for loop will iterate over each unique pair of dragonflies.
                for i in range(1, len(self.newPreyPositions)):
                    for j in range(i + 1, len(self.newPreyPositions)):

                        # Get the dragonfly objects from self.scene.
                        dragonflyOne = self.scene[i]
                        dragonflyTwo = self.scene[j]

                        # If the two are colliding, the checkCreatureCollision helper function will 
                        # return true. Get the two normal vectors of that collision, and use
                        # the given reflect function to alter the directions accordingly.
                        # After the directions have been altered, find the new positions the dragonflies
                        # should be at.
                        if checkCreatureCollision(self.newPreyPositions[i], self.newPreyPositions[j], dragonflyOne.bound_radius, dragonflyTwo.bound_radius):
                            normalVector1 = self.newPreyPositions[i] - self.newPreyPositions[j]
                            normalVector2 = -1 * normalVector1
                            reflectedVectori = self.direction[i].reflect(normalVector1)
                            reflectedVectorj = self.direction[j].reflect(normalVector2)
                            self.direction[i] = reflectedVectori
                            self.direction[j] = reflectedVectorj
                            self.newPreyPositions[i] = dragonflyOne.currentPos + self.step_size * self.direction[i]
                            self.newPreyPositions[j] = dragonflyTwo.currentPos + self.step_size * self.direction[j]

                # For each dragonfly, set its current position to what was calculated, and its pre-rotation,
                # which is calculated in the helper function findOrientTransform.
                for i in range(1, len(self.newPreyPositions)):
                    dragonfly = self.scene[i]
                    dragonfly.setCurrentPosition(self.newPreyPositions[i])
                    dragonfly.setPreRotation(findOrientTransform(self, i))

            # Check if the spider is colliding with the tank.
            checkTankCollision(self, newPos_spider, self.spider, 0)
            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]

            # Set the spider's current position and pre-rotation.
            self.spider.setCurrentPosition(newPos_spider)
            self.spider.setPreRotation(findOrientTransform(self, 0))

        # If potentials are not on, all we need to worry about are tank and creature collisions.
        # Look above for that information.
        else:
            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]
            checkTankCollision(self, newPos_spider, self.spider, 0)
                
            newPos_spider = self.spider.currentPos + self.step_size * self.direction[0]

            if self.preyStillActive:
                for i in range(1, len(self.newPreyPositions)):

                    if self.delected_creatures[i]:
                        continue

                    dragonfly = self.scene[i]
                    self.newPreyPositions[i] = dragonfly.currentPos + self.step_size * self.direction[i]
                    checkTankCollision(self, self.newPreyPositions[i], dragonfly, i)
                    self.newPreyPositions[i] = dragonfly.currentPos + self.step_size * self.direction[i]

                for i in range(len(self.newPreyPositions)):
                    for j in range(i + 1, len(self.newPreyPositions)):
                        if i == 0:
                            creature2 = self.scene[j]
                            if checkCreatureCollision(newPos_spider, self.newPreyPositions[j], self.spider.bound_radius, creature2.bound_radius):
                                normalVector1 = newPos_spider - self.newPreyPositions[j]
                                normalVector2 = -1 * normalVector1
                                reflectedVectori = self.direction[i].reflect(normalVector1)
                                reflectedVectorj = self.direction[j].reflect(normalVector2)
                                self.direction[i] = reflectedVectori
                                self.direction[j] = reflectedVectorj
                        else:
                            creature1 = self.scene[i]
                            creature2 = self.scene[j]
                            if checkCreatureCollision(self.newPreyPositions[i], self.newPreyPositions[j], creature1.bound_radius, creature2.bound_radius):
                                normalVector1 = self.newPreyPositions[i] - self.newPreyPositions[j]
                                normalVector2 = -1 * normalVector1
                                reflectedVectori = self.direction[i].reflect(normalVector1)
                                reflectedVectorj = self.direction[j].reflect(normalVector2)
                                self.direction[i] = reflectedVectori
                                self.direction[j] = reflectedVectorj

            self.spider.setCurrentPosition(newPos_spider)
            self.spider.setPreRotation(findOrientTransform(self, 0))

            if self.preyStillActive:
                for i in range(1, len(self.newPreyPositions)):
                    if self.delected_creatures[i]:
                        continue
                    dragonfly = self.scene[i]
                    dragonfly.setCurrentPosition(self.newPreyPositions[i])
                    dragonfly.setPreRotation(findOrientTransform(self, i))


        self.update()

# Function takes in a proposed position, the creature, and its index in self.scene to determine
# whether the creature is colliding with any of the tank walls.
def checkTankCollision(self, proposedPosition: Point, component: Component, index: int):

    # Get the direciton of the creature so it can be modified in the case of a collision.
    direction = self.direction[index]

    # The tank has dimensions [4, 4, 4], and the center is (0, 0, 0), so to determine a collision, 
    # we check to see if the position of the creature added by its bound radius is greater than or 
    # equal to half the tank's dimensions.
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

    # Set self.direction[index] equal to the calculated direction.
    self.direction[index] = direction.normalize()

# To determine a collision between two creatures, see if the distance between
# them is less than or equal to the sum of the radii of their bounding 
# spheres.
def checkCreatureCollision(pos1 : Point, pos2 : Point, radius1, radius2):
    radiiSum = radius1 + radius2
    distance = pos1.distance(pos2)
    if distance <= radiiSum:
        return True

# Used the material in discussion to make the quaternion for creature
# orientation using d_start and d_end, where d_start is the initial direction 
# the crature is facing, and d_end is the direction it intends to travel in.
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

# Models a dragonfly.
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

# Models a spider.
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


