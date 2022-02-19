from dataclasses import dataclass
from angle import Angle
from numpy import uint16, uint32
from pygame import Rect


@dataclass
class Header:
    wad_type: str
    dir_count: uint32
    dir_offset: uint32


@dataclass
class Directory:
    lump_offset: uint32
    lump_size: uint32
    lump_name: uint32


@dataclass
class Vertex:
    x: int
    y: int


@dataclass
class SideDef:
    xoffset: uint16
    yoffset: uint16
    upperTexture: str
    lowerTexture: str
    middleTexture: str
    sectorId: uint16


@dataclass
class LineDef:
    startVertex: int
    endVertex: int
    flags: int
    lineType: int
    secTag: str
    rightSideDef: SideDef
    leftSideDef: SideDef


@dataclass
class Thing:
    x: int
    y: int
    angle: Angle
    type: int
    flags: int


@dataclass
class SubSector:
    segCount: int
    firstSegId: int


@dataclass
class Seg:
    startVertexId: uint16
    endVertexId: uint16
    angle: Angle
    lineDefId: uint16
    direction: uint16
    offset: uint16


@dataclass
class Sector:
    FloorHeight: int
    CeilingHeight: int
    FloorTex: str
    CeilingTex: str
    LightLevel: uint16
    type: uint16
    tag: uint16


class Node:
    def __init__(self, x, y,
                 changeX, changeY,
                 rightBoxTop, rightBoxBottom, rightBoxLeft, rightBoxRight,
                 leftBoxTop, leftBoxBottom, leftBoxLeft, leftBoxRight,
                 rightChildId, leftChildId):

        self.x = x
        self.y = y

        self.changeX = changeX
        self.changeY = changeY

        width = rightBoxRight - rightBoxLeft
        height = rightBoxBottom - rightBoxTop
        self.rightBox = Rect(rightBoxLeft, rightBoxTop, width, height)

        width = leftBoxRight - leftBoxLeft
        height = leftBoxBottom - leftBoxTop
        self.leftBox = Rect(leftBoxLeft, leftBoxTop, width, height)
        self.bboxes = [self.leftBox, self.rightBox]

        self.rightChildId = rightChildId
        self.leftChildId = leftChildId
        self.children = [self.leftChildId, self.rightChildId]


@dataclass
class SegmentRenderData:
    v1XScreen: int
    v2XScreen: int

    v1Angle: Angle
    v2Angle: Angle

    distanceToV1: float = None
    distanceToNormal: float = None
    normalAngle: Angle = None
    v1ScaleFactor: float = None
    v2ScaleFactor: float = None
    steps: float = None

    rightSecCeiling: float = None
    rightSecFloor: float = None
    ceilingStep: float = None
    ceilingEnd: float = None
    floorStep: float = None
    floorStart: float = None

    leftSecCeiling: float = None
    leftSecFloor: float = None

    drawUpperSection: bool = None
    drawLowerSection: bool = None

    upperHeightStep: float = None
    upperHeight: float = None
    lowerHeightStep: float = None
    lowerHeight: float = None

    updateFloor: bool = None
    updateCeiling: bool = None

    seg: Seg = None

    @property
    def rightSideMidTex(self):
        return self.seg.linedef.rightSideDef.middleTexture
