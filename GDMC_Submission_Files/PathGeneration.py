from math import sqrt
import numpy as np
from random import randint
from HeightMap import HeightMap

class LegalPrecomp:
    def __init__(self, level, heightmap, path_width, restrictions, clearpoints=None):
        self.level = level
        self.hmap = heightmap
        self.path_width = path_width
        self.restrictions = np.array(restrictions)
        if clearpoints is not None:
            for point in clearpoints:
                x_span = range(point[0] - path_width, point[0] + path_width + 1)
                z_span = range(point[-1] - path_width, point[-1] + path_width + 1)
                for xi in x_span:
                    for zi in z_span:
                        self.restrictions[xi][zi] = 0
        self.lateral_actions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        self.diagonal_actions = [[1, 1], [1, -1], [-1, 1], [-1, -1]]
        self.actions = self.lateral_actions + self.diagonal_actions
        self.legal_actions = [[[] for z in xrange(heightmap.depth)] for x in xrange(heightmap.width)]
        self.sectors = np.full_like(heightmap.grid, -1, int)
        self.sector_sizes = {}
        self.precomputeActions()
        self.precomputeSectors()
        self.max_sector = 0
        max_count = self.sector_sizes.get(0)
        for sector in self.sector_sizes:
            count = self.sector_sizes[sector]
            if count > max_count:
                max_count = count
                self.max_sector = sector


    def isLegalAction(self, x, z, action, relative_to_grid=True):
        diagonal = action[0] and action[1]

        x1, z1 = x, z
        x2, z2 = x + action[0], z + action[1]

        # don't move out of bounds
        if relative_to_grid:
            if x1 < 0 or x1 >= (self.hmap.width) \
                    or z1 < 0 or z1 >= (self.hmap.depth) \
                    or x2 < 0 or x2 >= (self.hmap.width) \
                    or z2 < 0 or z2 >= (self.hmap.depth):
                return False
        else:
            if x1  < self.hmap.minx or x1  >= self.hmap.maxx \
                    or z1 < self.hmap.minz or z1 >= self.hmap.maxz \
                    or x2 < self.hmap.minx or x2 >= self.hmap.maxx \
                    or z2 < self.hmap.minz or z2 >= self.hmap.maxz:
                return False

        midh = self.hmap.getHeight(x2, z2)
        for xi in xrange(max(x2 - self.path_width, 0),
                        min(x2 + self.path_width + 1, len(self.restrictions))):
            for zi in xrange(max(z2 - self.path_width, 0),
                             min(z2 + self.path_width + 1, len(self.restrictions[xi]))):
                if bool(self.restrictions[xi][zi]):
                    return False
                h = self.hmap.getHeight(xi, zi)
                if not midh-1 <= h <= midh+1:
                    return False
        return True

    def precomputeActions(self):
        for xi in xrange(0, len(self.restrictions)):
            for zi in xrange(0, len(self.restrictions[xi])):
                for action in self.actions:
                    if self.isLegalAction(xi, zi, action):
                        self.legal_actions[xi][zi].append(action)

    def precomputeSectors(self):
        x = 0
        sector = 0
        while x < len(self.legal_actions):
            z = 0
            while z < len(self.legal_actions[0]):
                if self.sectors[x][z] == -1:
                    sector += 1
                    self.sector_sizes[sector] = 0
                    open = [Node(x, z)]
                    while len(open) > 0:
                        node = open.pop(0)
                        if self.sectors[node.x, node.z] != -1:
                            continue
                        self.sectors[node.x, node.z] = sector
                        self.sector_sizes[sector] += 1
                        for a in self.legal_actions[node.x][node.z]:
                            x1 = node.x + a[0]
                            z1 = node.z + a[1]
                            if x1 < 0 or x1 >= len(self.legal_actions) or z1 < 0 or z1 >= len(self.legal_actions[0]):
                                continue
                            if self.sectors[x1, z1] == -1:
                                open.append(Node(x1, z1))
                z += 1
            x += 1


class PathGenerator:

    GROUND_BLOCKS = [ 1,         2,   3,       12,    24,  80,  110, 121, 179, 208 ]
    GROUND_DATA =   [ [0,1,3,5], [0], [0,1,2], [0,1], [0], [0], [0], [0], [0], [0] ]
    PATH_MARKER = 204

    def __init__(self, x1, z1, x2, z2, level, heightmap, path_width, block_list, data_list,
                 legal, ground=None, relative_to_grid=False, old_path=None, verbose=False):
        self.level = level
        self.hmap = heightmap
        self.path_width = path_width
        self.block_list = block_list
        self.data_list = data_list
        self.v = verbose
        self.relative_to_grid = relative_to_grid
        xoffset = 0 if relative_to_grid else self.hmap.minx
        zoffset = 0 if relative_to_grid else self.hmap.minz
        self.startx = int(x1 - xoffset)
        self.startz = int(z1 - zoffset)
        self.endx = int(x2 - xoffset)
        self.endz = int(z2 - zoffset)
        self.basecost = 100
        self.open = [Node(self.startx,
                         self.startz,
                         None,
                         None,
                         0,
                         self.heuristic(self.startx, self.startz, self.endx, self.endz))]
        self.path = np.full((heightmap.maxx - heightmap.minx, heightmap.maxz - heightmap.minz), 0)
        self.lat_cost = self.basecost # cost for a lateral move
        self.diag_cost = round(sqrt(self.basecost**2 * 2)) # cost for a diagonal move
        self.legal = legal
        self.sectors = legal.sectors
        self.legal_actions = legal.legal_actions
        self.closed = np.full_like(heightmap.grid, 0)
        # ensure start and goal are not closed
        if ground is None:
            self.ground = self.mapGround()
        else:
            self.ground = ground
        self.old_path = old_path

    def heuristic(self, x1, z1, x2, z2):
        return round(sqrt((x1-x2)**2 + (z1-z2)**2) * self.basecost)


    def mapGround(self):
        print("Mapping ground blocks")
        ground_map = np.full_like(self.hmap.grid, 0)
        for xi in range(self.hmap.width):
            for zi in range(self.hmap.depth):
                x = int(xi + self.hmap.minx)
                z = int(zi + self.hmap.minz)
                y = int(self.hmap.getHeight(xi, zi, True))
                currentBlock = self.level.blockAt(x, y, z)
                if currentBlock in PathGenerator.GROUND_BLOCKS:
                    blockData = self.level.blockDataAt(x, y, z)
                    i = PathGenerator.GROUND_BLOCKS.index(currentBlock)
                    if blockData in PathGenerator.GROUND_DATA[i]:
                        ground_map[xi][zi] = 1
        return ground_map


    def makePath(self, safe=False):
        if safe:
            try:
                return self.makePath()
            except Exception:
                print ("Path fail")
                return False
        else:
            if self.v: print "Calculating...",
            calc = self.calculatePath()
            if calc:
                if self.v: print("Generating...")
                self.generatePath()
            return calc

    # Set ground blocks on path to path blocks
    def generatePath(self):
        paved = np.full_like(self.ground, False)
        for xi in xrange(len(self.path)):
            for zi in xrange(len(self.path[xi])):
                if self.path[xi, zi]:
                    if self.ground[xi, zi] and not paved[xi, zi]:
                        x = int(xi + self.hmap.minx)
                        y = int(self.hmap.getHeight(xi, zi, True))
                        z = int(zi + self.hmap.minz)
                        i = randint(0, len(self.data_list) - 1)
                        self.level.setBlockAt(x, y, z, self.block_list[i])
                        self.level.setBlockDataAt(x, y, z, self.data_list[i])
                        y2 = y + 1
                        while self.level.blockAt(x,y2,z) in HeightMap.DECORATIVE_BLOCKS:
                            if y2 - y > 2:
                                break
                            self.level.setBlockAt(x, y2, z, 0)
                            self.level.setBlockDataAt(x, y2, z, 0)
                            y2 += 1
                        paved[xi][zi] = True

    def setPath(self, node):
        while node is not None:
            for xi in xrange(max(node.x - self.path_width, 0),
                            min(node.x + self.path_width + 1, len(self.path))):
                for zi in xrange(max(node.z - self.path_width, 0),
                                 min(node.z + self.path_width + 1, len(self.path[xi]))):
                    self.path[xi, zi] = 1
            node = node.parent
        if self.v:
            print(self.path)

    def goalCheck(self, node):
        x = node.x
        z = node.z

        # If node is goal:
        if self.endx == x and self.endz == z:
            self.setPath(node)
            return True
        return False

    # A*
    def calculatePath(self):

        if self.sectors[self.startx, self.startz] != self.sectors[self.endx, self.endz]:
            return False

        while True:

            # If open is empty, search failed
            if len(self.open) == 0:
                if self.v:
                    xoffset = self.hmap.minx if self.relative_to_grid else 0
                    zoffset = self.hmap.minz if self.relative_to_grid else 0
                    startstr = "(" + str(self.startx + xoffset) + ", " + str(self.startz + zoffset) + ")"
                    endstr = "(" + str(self.endx + xoffset) + ", " + str(self.endz + zoffset) + ")"
                    print("No path found from " + startstr + " to " + endstr)
                return False

            node = self.pop_min_f()
            x = node.x
            z = node.z

            if self.goalCheck(node):
                return True
            if self.closed[x][z]:
                continue
            self.closed[x][z] = True
            for action in self.legal_actions[x][z]:
                new_x = x + action[0]
                new_z = z + action[1]
                if self.closed[new_x][new_z]:
                    continue
                new_g = node.g + (self.diag_cost if bool(action[0]) and bool(action[-1]) else self.lat_cost)
                new_h = self.heuristic(x, z, self.endx, self.endz)
                child = Node(new_x, new_z, node, action, new_g, new_h)
                self.open.append(child)

    def pop_min_f(self):
        min_node = self.open[0]
        index = 0
        for i in range(1, len(self.open)):
            min_f = min_node.g + min_node.h
            f = self.open[i].g + self.open[i].h
            if f < min_f:
                min_node = self.open[i]
                index = i
            elif f == min_f:
                if self.open[i].h < min_node.h:
                    min_node = self.open[i]
                    index = i
        return self.open.pop(index)


class Node:
    def __init__(self, x, z, parent=None, action=None, g=None, h=None):
        self.x = x
        self.z = z
        self.action = action
        self.parent = parent
        self.g = g
        self.h = h



