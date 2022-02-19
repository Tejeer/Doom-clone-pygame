import pygame
import math

from angle import Angle
from angle import RAD1
from classDef import classicDoomScreenXtoView
from data_types import SegmentRenderData
from numba import njit
import funcs
from tex_manager import TextureManager

HALFWIDTH = 320 >> 1
HALFHEIGHT = 200 >> 1
angle90 = Angle(90)
angle180 = Angle(180)


@njit(fastmath=True)
def angleToScreen(angle):
    x = 0
    # left side of fov
    if angle > 90:
        angle -= 90  # set the angle to with of player angle(0)
        x = HALFWIDTH - round(math.tan(angle * RAD1) * HALFWIDTH)
    # right side
    else:
        angle = 90 - angle
        x = HALFWIDTH + round(math.tan(angle * RAD1) * HALFWIDTH)
    return x


def clamp(n, min_val, max_val):
    return max(min(n, max_val), min_val)


class Renderer:
    def __init__(self, engine):
        self.engine = engine
        self.player = self.engine.player
        self.game_map = self.engine.game_map

        self.remap_x, self.remap_y = self.engine.remap_x, self.engine.remap_y
        self.font = pygame.font.SysFont('arial', 10)

        self.useClassicDoomScreenToAngle = True

        self.screenXtoAngle = {}
        if self.useClassicDoomScreenToAngle:
            for k, angle_val in enumerate(classicDoomScreenXtoView):
                self.screenXtoAngle[k] = Angle(angle_val)
        else:
            screenAngle = self.player.fov >> 1
            fstep = self.player.fov / (self.engine.width + 1)
            for i in range(self.engine.width + 1):
                self.screenXtoAngle[i] = screenAngle
                screenAngle -= fstep

        self.halfWidth = self.engine.width >> 1
        self.halfHeight = self.engine.height >> 1
        halfFOV = (self.player.fov >> 1)
        self.perpendicularDistToScreen = self.halfWidth / halfFOV.tan

        self.maxScale = 64
        self.minScale = 0.00390625
        self.floorClipHeight = []
        self.ceilingClipHeight = []

        self.TextureManager = TextureManager(self)

    def init_frame(self):
        self.wallRanges = [[-999999999, -1], [self.engine.width, 999999999]]
        self.floorClipHeight = [self.engine.height] * self.engine.width
        self.ceilingClipHeight = [-1] * self.engine.width

    def clipSolidWalls(self, seg, x1, x2, angle1, angle2):
        currentWallIndex = 0
        wallRangeLength = len(self.wallRanges)
        if wallRangeLength < 2:
            return

        while currentWallIndex < wallRangeLength and self.wallRanges[currentWallIndex][1] < x1 - 1:
            currentWallIndex += 1
        foundClipWall = self.wallRanges[currentWallIndex]

        if x1 < foundClipWall[0]:
            if x2 < foundClipWall[0] - 1:
                self.storeWallRange(seg, x1, x2, angle1, angle2)
                self.wallRanges.insert(currentWallIndex, [x1, x2])
                return
            self.storeWallRange(seg, x1, foundClipWall[0] - 1, angle1, angle2)
            foundClipWall[0] = x1

        if x2 <= foundClipWall[1]:
            return

        nextWallIndex = currentWallIndex
        nextWall = foundClipWall

        while x2 >= self.wallRanges[nextWallIndex + 1][0] - 1:
            self.storeWallRange(seg, nextWall[1] + 1, self.wallRanges[nextWallIndex + 1][0] - 1, angle1, angle2)
            nextWallIndex += 1
            nextWall = self.wallRanges[nextWallIndex]

            if x2 <= nextWall[1]:
                foundClipWall[1] = nextWall[1]
                if nextWallIndex != currentWallIndex:
                    currentWallIndex += 1
                    foundClipWall = self.wallRanges[currentWallIndex]
                    nextWallIndex += 1
                    del self.wallRanges[currentWallIndex:nextWallIndex]
                return

        self.storeWallRange(seg, nextWall[1] + 1, x2, angle1, angle2)
        foundClipWall[1] = x2

        if nextWallIndex != currentWallIndex:
            currentWallIndex += 1
            nextWallIndex += 1
            del self.wallRanges[currentWallIndex:nextWallIndex]

    def clipPassWalls(self, seg, x1, x2, angle1, angle2):
        currentWallIndex = 0
        length = len(self.wallRanges)

        while currentWallIndex < length and self.wallRanges[currentWallIndex][1] < x1 - 1:
            currentWallIndex += 1
        foundClipWall = self.wallRanges[currentWallIndex]

        if x1 < foundClipWall[0]:
            if x2 < foundClipWall[0] - 1:
                self.storeWallRange(seg, x1, x2, angle1, angle2)
                return
            self.storeWallRange(seg, x1, foundClipWall[0] - 1, angle1, angle2)

        if x2 <= foundClipWall[1]:
            return

        nextWallIndex = currentWallIndex
        nextWall = foundClipWall

        while x2 >= self.wallRanges[nextWallIndex + 1][0] - 1:
            self.storeWallRange(seg, nextWall[1] + 1, self.wallRanges[nextWallIndex + 1][0] - 1, angle1, angle2)
            nextWallIndex += 1
            nextWall = self.wallRanges[nextWallIndex]

            if x2 <= nextWall[1]:
                return

        self.storeWallRange(seg, nextWall[1] + 1, x2, angle1, angle2)

    def storeWallRange(self, seg, x1, x2, angle1, angle2):
        if x1 == x2:
            return
        self.calcWallHeight(seg, x1, x2, angle1, angle2)

    def drawWallInFov(self, seg, v1Angle, v2Angle, angle1, angle2):
        x1 = angleToScreen(angle1.angle)
        x2 = angleToScreen(angle2.angle)

#        only solid walls
        if not seg.leftSec:
            self.clipSolidWalls(seg, x1, x2, v1Angle, v2Angle)
            return

#        only closed doors
        if funcs.isClosedDoor(seg):
            self.clipSolidWalls(seg, x1, x2, v1Angle, v2Angle)
            return

#        see through walls
        if funcs.isPassWall(seg):
            self.clipPassWalls(seg, x1, x2, v1Angle, v2Angle)

    def render(self, render_auto_map=False):
        if render_auto_map:
            self.render_auto_map()
        else:
            self.game_map.render_bsp_nodes()

    def render_auto_map(self):
        for line in self.game_map.linedef:
            svertex, evertex = line.startVertex, line.endVertex
            pygame.draw.line(self.engine.display, (255, 255, 255),
                             self.remap_x(svertex.x), self.remap_y(svertex.y),
                             self.remap_x(evertex.x), self.remap_y(evertex.y))

    def calcWallHeight(self, seg, x1, x2, v1angle, v2angle):
        renderData = SegmentRenderData(x1, x2, v1angle, v2angle)
        renderData.normalAngle = angle90 + seg.angle

        # equivalent to (v1angle.angle - NormalAngle)
        normalToV1Angle = renderData.normalAngle - v1angle

        renderData.distToV1 = self.player.distance(seg.startVertex)
        renderData.distToNormal = normalToV1Angle.cos * renderData.distToV1

        renderData.v1ScaleFactor = self.scaleFactor(x1, renderData)
        renderData.v2ScaleFactor = self.scaleFactor(x2, renderData)

        renderData.steps = (renderData.v2ScaleFactor - renderData.v1ScaleFactor) / (x2 - x1)

        renderData.rightSecCeiling = seg.rightSec.CeilingHeight - self.player.z
        renderData.rightSecFloor = seg.rightSec.FloorHeight - self.player.z

        renderData.ceilingStep = -(renderData.rightSecCeiling * renderData.steps)
        renderData.ceilingEnd = round(self.halfHeight - (renderData.rightSecCeiling * renderData.v1ScaleFactor))

        renderData.floorStep = -(renderData.rightSecFloor * renderData.steps)
        renderData.floorStart = round(self.halfHeight - (renderData.rightSecFloor * renderData.v1ScaleFactor))

        renderData.seg = seg

        if seg.leftSec:
            renderData.leftSecCeiling = seg.leftSec.CeilingHeight - self.player.z
            renderData.leftSecFloor = seg.leftSec.FloorHeight - self.player.z

            self.ceilingFloorUpdate(renderData)

            if renderData.leftSecCeiling < renderData.rightSecCeiling:
                renderData.drawUpperSection = True
                renderData.upperHeightStep = -(renderData.leftSecCeiling * renderData.steps)
                renderData.upperHeight = round(self.halfHeight - (renderData.leftSecCeiling * renderData.v1ScaleFactor))

            if renderData.leftSecFloor > renderData.rightSecFloor:
                renderData.drawLowerSection = True
                renderData.lowerHeightStep = -(renderData.leftSecFloor * renderData.steps)
                renderData.lowerHeight = round(self.halfHeight - (renderData.leftSecFloor * renderData.v1ScaleFactor))

        self.drawWall(renderData)

    def drawWall(self, renderData):
        currentX = renderData.v1XScreen
        while currentX <= renderData.v2XScreen:
            currentCeilingEnd = renderData.ceilingEnd
            currentFloorStart = renderData.floorStart

            currentX, currentCeilingEnd, currentFloorStart, valid = self.ValidateRange(renderData, currentX, currentCeilingEnd, currentFloorStart)
            if not valid:
                continue
            if renderData.seg.leftSec:
                self.drawUpperSection(renderData, currentX, currentCeilingEnd)
                self.drawLowerSection(renderData, currentX, currentFloorStart)
            else:
                self.drawMiddleSection(renderData, currentX, currentCeilingEnd, currentFloorStart)
            renderData.ceilingEnd += renderData.ceilingStep
            renderData.floorStart += renderData.floorStep
            currentX += 1

    def drawLowerSection(self, renderData, currentX, currentFloorStart):
        if renderData.drawLowerSection:
            lowerHeight = renderData.lowerHeight
            renderData.lowerHeight += renderData.lowerHeightStep

            if lowerHeight <= self.ceilingClipHeight[currentX]:
                lowerHeight = self.ceilingClipHeight[currentX] + 1
            if lowerHeight <= currentFloorStart:
                surf = self.TextureManager.textures[renderData.rightSideMidTex]
                dist = self.distance(currentX, renderData)
                alpha = (50000 / (int(dist) + 0.001))
                surf.set_alpha(alpha)
                self.engine.display.blit(pygame.transform.scale(surf, (1, int(currentFloorStart + 1) - int(lowerHeight))), (currentX, lowerHeight))
                self.floorClipHeight[currentX] = lowerHeight
            else:
                self.floorClipHeight[currentX] = currentFloorStart + 1
        elif renderData.updateFloor:
            self.floorClipHeight[currentX] = currentFloorStart + 1

    def drawMiddleSection(self, renderData, currentX, CeilingEnd, FloorStart):
        surf = self.TextureManager.textures[renderData.rightSideMidTex]
        dist = self.distance(currentX, renderData)
        alpha = (50000 / (int(dist) + 0.001))
        surf.set_alpha(alpha)
        wall_column = pygame.transform.scale(surf, (1, int(FloorStart + 1 - CeilingEnd)))
        self.engine.display.blit(wall_column, (currentX, CeilingEnd))
        self.ceilingClipHeight[(currentX)] = self.engine.height
        self.floorClipHeight[(currentX)] = -1

    def drawUpperSection(self, renderData, currentX, currentCeilingEnd):
        if renderData.drawUpperSection:
            upperHeight = renderData.upperHeight
            renderData.upperHeight += renderData.upperHeightStep

            if upperHeight >= self.floorClipHeight[currentX]:
                upperHeight = self.floorClipHeight[currentX] - 1
            if upperHeight >= currentCeilingEnd:
                surf = self.TextureManager.textures[renderData.rightSideMidTex]
                dist = self.distance(currentX, renderData)
                alpha = (50000 / (int(dist) + 0.001))
                surf.set_alpha(alpha)

                wall_height = int(upperHeight + 1) - int(currentCeilingEnd)
                wall_column = pygame.transform.scale(surf, (1, wall_height))
                self.engine.display.blit(wall_column, (currentX, currentCeilingEnd))
                self.ceilingClipHeight[currentX] = upperHeight
            else:
                self.ceilingClipHeight[currentX] = currentCeilingEnd - 1
        elif renderData.updateCeiling:
            self.ceilingClipHeight[currentX] = currentCeilingEnd - 1

    def ValidateRange(self, renderData, currentX, CeilingEnd, FloorStart):
        currentX = int(currentX)
        if CeilingEnd < self.ceilingClipHeight[currentX] + 1:
            CeilingEnd = self.ceilingClipHeight[currentX] + 1
        if FloorStart >= self.floorClipHeight[currentX]:
            FloorStart = self.floorClipHeight[currentX] - 1
        if CeilingEnd > FloorStart:
            renderData.ceilingEnd += renderData.ceilingStep
            renderData.floorStart += renderData.floorStep
            currentX += 1
            return currentX, CeilingEnd, FloorStart, False
        return currentX, CeilingEnd, FloorStart, True

    def render_player(self) -> None:
        px = self.engine.remap_x(self.player.x)
        py = self.engine.remap_y(self.player.y)
        pygame.draw.circle(self.engine.display, (255, 0, 0), (px, py), 1)
        pygame.draw.line(self.engine.display, (255, 255, 0),
                         (px, py),
                         (px + self.player.cos * 5, py - self.player.sin * 5))

    def show_fps(self, pos=(5, 3)) -> None:
        text = self.font.render(str(int(self.engine.clock.get_fps())), False, (255, 255, 255))
        self.engine.display.blit(text, pos)

    def scaleFactor(self, vxscreen: int, renderData) -> [float, int]:
        '''
        (distToNormal / scewAngle.cos) => distance to the vertex
        (self.perpendicularDistToScreen / screenXAngle.cos) => distance to the screen
        scaling factor = distance to the vertex / distance to the screen
        simplifying (self.perpendicularDistToScreen / screenXAngle.cos) / (distToNormal / scew_angle.cos)
        we get, (self.perpendicularDistToScreen * scew_angle.cos) / (distToNormal * screenXAngle.cos)
        '''
        screenXAngle = self.screenXtoAngle[vxscreen]
        scew_angle = screenXAngle + self.player.angle - renderData.normalAngle
        dist = renderData.distToNormal * screenXAngle.cos
        scaleFactor = (self.perpendicularDistToScreen * scew_angle.cos) / dist
        return clamp(scaleFactor, self.minScale, self.maxScale)

    def distance(self, vxscreen, renderData) -> float:
        '''
        inverseNormalAngle = normalAngle - angle180
        viewRelativeAngle= inverseNormalAngle - (self.player.angle + viewAngle)
        interceptDistance = distToNormal / viewRelativeAngle.cos
        return abs(viewAngle.cos * interceptDistance)
        '''
        viewAngle = self.screenXtoAngle[vxscreen]
        viewRelativeAngle = viewAngle + self.player.angle - renderData.normalAngle
        interceptDistance = renderData.distToNormal / viewRelativeAngle.cos
        return abs(interceptDistance)

    def ceilingFloorUpdate(self, renderData) -> None:
        if not renderData.seg.leftSec:
            renderData.updateFloor = True
            renderData.updateCeiling = True
            return

        if renderData.leftSecCeiling != renderData.rightSecCeiling:
            renderData.updateCeiling = True

        if renderData.leftSecFloor != renderData.rightSecFloor:
            renderData.updateFloor = True

        if renderData.seg.leftSec.CeilingHeight <= renderData.seg.rightSec.FloorHeight or renderData.seg.leftSec.FloorHeight >= renderData.seg.rightSec.CeilingHeight:
            renderData.updateCeiling = True
            renderData.updateFloor = True

        if renderData.seg.rightSec.CeilingHeight <= self.player.z:
            renderData.updateCeiling = False

        if renderData.seg.rightSec.FloorHeight >= self.player.z:
            renderData.updateFloor = False
