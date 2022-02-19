def isClosedDoor(seg):
    return (seg.leftSec.CeilingHeight <= seg.rightSec.FloorHeight or
            seg.leftSec.FloorHeight >= seg.rightSec.CeilingHeight)


def isPassWall(seg):
    return (seg.rightSec.CeilingHeight != seg.leftSec.CeilingHeight or
            seg.rightSec.FloorHeight != seg.leftSec.FloorHeight)
