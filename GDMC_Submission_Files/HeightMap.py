import numpy as np


class HeightMap:

    DECORATIVE_BLOCKS = [6, 27, 28, 30, 31, 32, 37, 38, 39,
                         40, 54, 66, 78, 83, 96, 106, 111, 151, 157, 171, 175,
                         183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 199, 200]
    SNOW = [78]
    WATER = [8, 9]
    HAZARD = [10, 11]
    LOGS_AND_LEAVES = [17, 162, 18, 161, 81, 99, 100, 106]

    def __init__(self, level, box):

        self.level = level
        self.box = box

        self.minx, self.maxx = box.minx, box.maxx
        self.miny, self.maxy = box.miny, box.maxy
        self.minz, self.maxz = box.minz, box.maxz
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny
        self.depth = self.maxz - self.minz
        self.grid = np.zeros((box.maxx - box.minx, box.maxz - box.minz))
        self.water = np.full_like(self.grid, 0)
        self.hazard = np.full_like(self.grid, 0)
        self.plots = []

        # set up the actual height map
        self.generateHeightMap()

    def getHeight(self, x, z, relative_to_grid = True):
        # If relative_to_grid is true, assume x and z are 0 to (max-min)
        # Otherwise, assume x and z are min to max
        if relative_to_grid:
            xoffset = zoffset = 0
        else:
            xoffset, zoffset = self.minx, self.minz
        if z - zoffset < 0 or x - xoffset < 0:
            print(x, xoffset)
            print(z, zoffset)
        try:
            return self.grid[x - xoffset, z - zoffset]
        except IndexError as ex:
            print(x, xoffset)
            print(z, zoffset)
            print(ex)
        for y in xrange(self.height, -1, -1):
            currentBlock = self.level.blockAt(x + self.minx, y + self.miny, z + self.minz)
            if currentBlock != 0:
                if currentBlock in self.DECORATIVE_BLOCKS:
                    continue
                else:
                    return y
        for y in xrange(self.level.Height, self.height, -1):
            currentBlock = self.level.blockAt(x + self.minx, y + self.miny, z + self.minz)
            if currentBlock != 0:
                if currentBlock in self.DECORATIVE_BLOCKS:
                    continue
                else:
                    return y
        return self.miny


    def mask(self, y_offset = 1, mask_block = 1, mask_data = 4):
        for x in xrange(self.width):
            for z in xrange(self.depth):
                level_x = int(x + self.minx)
                level_y = int(self.grid[x, z] + y_offset)
                level_z = int(z + self.minz)
                self.level.setBlockAt(level_x, level_y, level_z, mask_block)
                self.level.setBlockDataAt(level_x, level_y, level_z, mask_data)

    def generateHeightMap(self):

        for x in xrange(self.width):
            for z in xrange(self.depth):
                highestBlock = self.heightScan(x, z, self.maxy, self.miny)
                if highestBlock is None:
                    highestBlock = self.heightScan(x, z, self.level.Height, self.maxy)
                    if highestBlock is None:
                        highestBlock = self.heightScan(x, z, self.miny, -1)
                        if highestBlock is None:
                            highestBlock = self.miny
                self.grid[x, z] = highestBlock

    def heightScan(self, x, z, topy, bottomy):
        prevblock = None
        for y in xrange(topy, bottomy, -1):
            currentBlock = self.level.blockAt(x + self.minx, y, z + self.minz)
            if currentBlock != 0:
                if currentBlock in self.DECORATIVE_BLOCKS:
                    prevblock = currentBlock
                    continue

                # Clear trees
                elif currentBlock in self.LOGS_AND_LEAVES:
                    self.level.setBlockAt(x + self.minx, y, z + self.minz, 0)
                    self.level.setBlockDataAt(x + self.minx, y, z + self.minz, 0)

                    # Remove floating snow left behind
                    if prevblock in self.SNOW:
                        self.level.setBlockAt(x + self.minx, y+1, z + self.minz, 0)
                        self.level.setBlockDataAt(x + self.minx, y+1, z + self.minz, 0)
                    prevblock = currentBlock
                    continue
                else:
                    if currentBlock in self.WATER:
                        self.water[x, z] = 1

                    # Turn dirt to grass
                    elif currentBlock == 3:
                        data = self.level.blockDataAt(x + self.minx, y, z + self.minz)
                        if data == 0:
                            self.level.setBlockAt(x + self.minx, y, z + self.minz, 2)
                            self.level.setBlockDataAt(x + self.minx, y, z + self.minz, 0)

                    elif currentBlock in self.HAZARD:
                        self.hazard[x, z] = 1
                        y1 = y

                        # "Douse" lava (turn sources to obsidian, flowing to cobble)
                        while currentBlock in self.HAZARD and y1 > 1:
                            currentBlock = self.level.blockAt(x + self.minx, y1, z + self.minz)
                            data = self.level.blockDataAt(x + self.minx, y1, z + self.minz)
                            if data != 0:
                                replblock = 4
                            else:
                                replblock = 49
                            self.level.setBlockAt(x + self.minx, y1, z + self.minz, replblock)
                            self.level.setBlockDataAt(x + self.minx, y1, z + self.minz, 0)
                            y1 -= 1
                    return y
            prevblock = currentBlock

        return None

    def findPathPoints(self):
        points = []
        pathBlock = 204
        for xi in xrange(self.width):
            for zi in xrange(self.depth):
                x = int(xi + self.minx)
                z = int(zi + self.minz)
                y = int(self.grid[xi][zi])
                curBlock = self.level.blockAt(x, y, z)
                if curBlock == pathBlock:
                    points.append([x, y, z])
        return points

    def setPlots(self, plots):
        self.plots = plots

    def recalculateHeightForPlots(self):
        for plot in self.plots:
            entrance = plot.entrance
            x = plot.x - self.minx
            z = plot.z - self.minz
            entrance = entrance[0] + x, entrance[1] + z
            height = self.getHeight(entrance[0], entrance[1])
            w = plot.width
            d = plot.depth
            for xi in xrange(x, x + w):
                for zi in xrange(z, z + d):
                    try:
                        self.grid[xi][zi] = height
                    except IndexError as ex:
                        print ("Entrance: " + str(entrance))
                        print ("[x,z]: " + str([x, z]))
                        print ("[xi,zi]: " + str([xi, zi]))
                        raise ex


