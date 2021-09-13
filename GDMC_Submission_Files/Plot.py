import pymclevel
from pymclevel import MCSchematic

class Plot:
    DIRECTIONS = ["n", "w", "s", "e"]
    def __init__(self, width, depth, facing = None, x = None, z = None, schematic = None, entrance = None):
        self.width = width                        # x distance from center
        self.depth = depth                        # z distance from center
        self.facing = facing                      # should be in DIRECTIONS
        self.x = x
        self.z = z
        self.schematic = schematic
        self.entrance = entrance

    def setPosition(self, x, z):
        self.x = x
        self.z = z

    def setSchematic(self, schematic):
        self.schematic = schematic

    def setEntrance(self, x, z):
        self.entrance = (x, z)

    def setFacing(self, facing):
        if facing in self.DIRECTIONS:
            self.facing = facing
        else:
            raise ValueError("Invalid direction: " + str(facing))

    def clone(self):
        if self.schematic is None:
            new_schem = None
        else:
            blocks = self.schematic._Blocks
            w, h, d = self.schematic.Width, self.schematic.Height, self.schematic.Length
            data = self.schematic.root_tag["Data"]
            new_schem = MCSchematic(shape=(w,h,d), filename='')
            new_schem._Blocks = blocks
            new_schem.root_tag["Data"] = data
        if self.entrance is not None:
            new_entrance = (self.entrance[0], self.entrance[1])
        else:
            new_entrance = None
        return Plot(self.width, self.depth, self.facing, self.x, self.z, new_schem, new_entrance)

    def __contains__(self, item):
        try:
            if len(item) < 2 or len(item) > 3:
                raise ValueError("Invalid dimensions of point " + str(item))
        except TypeError as ex:
            print(ex)
            raise TypeError("Contains must only be called on an iterable representation of a 2d or 3d point. " + \
                            "Given type: " + str(type(item)))
        if self.x is None or self.z is None:
            raise Exception("Plot does not have a valid (x,z) position")
        x, z = item[0], item[-1]
        return self.x <= x < self.x + self.width and self.z <= z < self.z + self.depth

    def getEntranceBlock(self, level, hmap):
        x = int(self.x + self.entrance[0])
        z = int(self.z + self.entrance[-1])
        y = int(hmap.getHeight(x, z, False))
        return level.blockAt(x, y, z)









