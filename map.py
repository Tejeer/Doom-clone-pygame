import numpy as np

from angle import Angle, DEG1
from math import atan2


class Map:
    def __init__(self, name, engine):
        self.data = {}

        self.name = name
        self.engine = engine
        self.player = self.engine.player
        self.subSecIdentifier = np.uint16(0x8000)  # 32768
        self.playerInSubsector = None
        self.maxSubsectorLimit = 160  # reduces some quality
        self.continueTrasverse = 1
        self.frame = 0

    @property
    def get_name(self):
        return self.name

    def build_linedef(self):
        side_def_length = len(self.data['SIDEDEFS'])
        for linedef in self.data['LINEDEFS']:
            linedef.startVertex = self.data['VERTEXES'][linedef.startVertex]
            linedef.endVertex = self.data['VERTEXES'][linedef.endVertex]
            linedef.rightSideDef = self.data['SIDEDEFS'][linedef.rightSideDef]

            if linedef.leftSideDef < side_def_length:
                linedef.leftSideDef = self.data['SIDEDEFS'][linedef.leftSideDef]
            else:
                linedef.leftSideDef = None

    def build_Seg(self):
        for seg in self.data['SEGS']:
            seg.startVertex = self.data['VERTEXES'][seg.startVertexId]
            seg.endVertex = self.data['VERTEXES'][seg.endVertexId]
            seg.linedef = self.data['LINEDEFS'][seg.lineDefId]
            seg.angle = float(seg.angle << 16) * 8.38190317e-8
            seg.offset = (seg.offset << 16) / (1 << 16)

            right_side_def = seg.linedef.rightSideDef
            left_side_def = seg.linedef.leftSideDef

            if seg.direction:
                left_side_def = seg.linedef.rightSideDef
                right_side_def = seg.linedef.leftSideDef

            seg.rightSec = None
            seg.leftSec = None
            if right_side_def:
                seg.rightSec = right_side_def.sector
            if left_side_def:
                seg.leftSec = left_side_def.sector
            del seg.startVertexId, seg.endVertexId, seg.lineDefId

    def build_sidedef(self):
        for sidedef in self.data['SIDEDEFS']:
            sidedef.sector = self.data['SECTORS'][sidedef.sectorId]
            del sidedef.sectorId

    def add_data(self, data_name, data):
        if not self.data.__contains__(data_name):
            self.data[data_name] = []
        self.data[data_name].append(data)

    def point_on_left(self, nodeId):
        node = self.data['NODES'][nodeId]
        dx = self.player.x - node.x
        dy = self.player.y - node.y
        return ((dx * node.changeY - dy * node.changeX) <= 0)

    def render_subsector(self, subsector_id):
        subsector = self.data['SSECTORS'][subsector_id]
        for i in range(subsector.segCount):
            if self.trasversedSubsectors > self.maxSubsectorLimit:
                self.continueTrasverse = 0
            seg = self.data['SEGS'][subsector.firstSegId + i]
            v1Angle, v2Angle, angle1, angle2 = self.player.clipVertexes(seg.startVertex, seg.endVertex)
            if angle1:
                self.trasversedSubsectors += 1
                self.engine.renderer.drawWallInFov(seg, v1Angle, v2Angle, angle1, angle2)

    def checkBBox(self, box):
        for point in [box.topleft, box.topright, box.bottomleft, box.bottomright]:
            radians = atan2(point[1] - self.player.y, point[0] - self.player.x)
            angle = Angle(radians * DEG1)
            angle = angle - self.player.angle + self.player.half_fov
            if angle < 180 and angle > 0:
                return True
        return False

    def render_bsp_nodes(self, nodeId=235):
        if not nodeId:
            nodeId = 235  # root node ->len(self.nodes) - 1
        stack = [nodeId]
        while len(stack):
            if not self.continueTrasverse:
                return
            currentNodeId = stack.pop()
            if (currentNodeId & self.subSecIdentifier):
                self.render_subsector(currentNodeId & (~self.subSecIdentifier))
                if not self.playerInSubsector:
                    self.playerInSubsector = self.data['SSECTORS'][currentNodeId & (~self.subSecIdentifier)]
                continue
            side = self.point_on_left(currentNodeId)
            node = self.data['NODES'][currentNodeId]
            stack.append(node.children[side])

            if self.checkBBox(node.bboxes[side ^ 1]):
                stack.append(node.children[side ^ 1])

    def locate_player(self):
        thing = self.data['THINGS'][0]
        self.player.set_x(thing.x)
        self.player.set_y(thing.y)
        self.player.set_angle(thing.angle)
        self.player.id = 1

    def initFrame(self):
        self.playerInSubsector = None
        self.continueTrasverse = 1
        self.trasversedSubsectors = 0
