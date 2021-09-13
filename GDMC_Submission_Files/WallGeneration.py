from pymclevel import MCSchematic
from pymclevel.box import Vector
import numpy as np
from HeightMap import HeightMap

class WallPlot:
    def __init__(self, x, z, direction, type=None, base=None, schematic=None):
        self.x = x
        self.z = z
        self.direction = direction
        self.type = type
        self.base = base
        self.schematic = schematic
        self.fixed_base = False
        self.height = 9
        self.special = 0
        self.prevplot = None
        self.nextplot = None

class TownWalls:
    def __init__(self, heightmap, level):
        self.hmap = heightmap
        self.level = level
        width = (heightmap.width - 1) // 5
        depth = (heightmap.depth - 1) // 5
        self.top = [WallPlot(i*5, 5, 1) for i in xrange(2, width - 1)]
        self.bot = [WallPlot(i*5, (depth - 1)*5, 3) for i in xrange(2, width - 1)]
        self.bot.reverse()
        self.right = [WallPlot((width - 1) * 5, i*5, 0) for i in xrange(2, depth - 1)]
        self.left = [WallPlot(5, i*5, 2) for i in xrange(2, depth - 1)]
        self.left.reverse()
        self.tl = WallPlot(5, 5, 2, "Wall_Corner")
        self.tr = WallPlot((width - 1) * 5, 5, 1, "Wall_Corner")
        self.bl = WallPlot(5, (depth - 1) * 5, 3, "Wall_Corner")
        self.br = WallPlot((width - 1) * 5, (depth - 1) * 5, 0, "Wall_Corner")

        # Plots listed clockwise starting at top left
        plotlist = [self.tl]
        plotlist.extend(self.top)
        plotlist.append(self.tr)
        plotlist.extend(self.right)
        plotlist.append(self.br)
        plotlist.extend(self.bot)
        plotlist.append(self.bl)
        plotlist.extend(self.left)
        self.plotlist = plotlist

        self.occupied = np.full_like(heightmap.grid, 0)
        self.gates = []
        self.corners = [self.tl, self.tr, self.bl, self.br]

        # If the wall would be a reasonable size, fix heights, set wall types, and actually generate it
        if len(self.top) > 2 and len(self.bot) > 2 and len(self.right) > 2 and len(self.left) > 2:
            self.linkWalls()
            self.scanHeight()
            if not self.scanForGate():
                return
            self.fixLevelToGate()
            self.scanForStairs()
            self.finalizeTypes()
            self.generateWall()

    def linkWalls(self):
        n = len(self.plotlist)
        for i in xrange(n):
            plot = self.plotlist[i]
            i_prev = (i-1) % n
            prevplot = self.plotlist[i_prev]
            plot.prevplot = prevplot
            i_next = (i+1) % n
            nextplot = self.plotlist[i_next]
            plot.nextplot = nextplot

    def scanHeight(self):

        # Get initial height
        for plot in self.plotlist:
            avgh = 0
            maxh = 0
            x = plot.x
            z = plot.z
            bump = 0
            for xi in xrange(x, x + 5):
                for zi in xrange(z, z+5):
                    h = self.hmap.getHeight(xi, zi)
                    maxh = max(maxh, h)
                    avgh += h
                    if self.hmap.hazard[xi, zi] or self.hmap.water[xi, zi]:
                        bump = 3
            avgh /= 25
            if maxh - avgh > 2:
                baseh = int(maxh - 2) + bump
            else:
                baseh = int(avgh) + bump
            plot.base = baseh

        # Fix heights around corners
        for corner in self.corners:
            p_neg1 = corner.prevplot
            p_neg2 = p_neg1.prevplot
            p_1 = corner.nextplot
            p_2 = p_1.nextplot
            corner_area = [p_neg2, p_neg1, corner, p_1, p_2]
            h = max([p.base for p in corner_area])
            for p in corner_area:
                if p.base != h:
                    p.fixed_base = True
                p.base = h

        # Fix heights forwards
        for plot1 in self.plotlist:
            plot2 = plot1.nextplot
            h1 = plot1.base
            h2 = plot2.base
            if h1 - h2 > 3:
                plot2.base = h1-3
                plot2.fixed_base = True
            if h2 - h1 > 3:
                plot1.base = h2-3
                plot1.fixed_base = True

        # Fix heights backwards
        reverse_plots = list(self.plotlist)
        reverse_plots.reverse()
        for plot1 in reverse_plots:
            plot2 = plot1.prevplot
            h1 = plot1.base
            h2 = plot2.base
            if h1 - h2 > 3:
                plot2.base = h1-3
                plot2.fixed_base = True
            if h2 - h1 > 3:
                plot1.base = h2-3
                plot1.fixed_base = True


    def scanForGate(self):
        heightkey1 = None

        # A dictionary of potential gates based on their base height modulo 3
        gateCandidates = {}

        # Don't spawn a bunch of gates next to each other
        cooldown = 0

        # Top, bottom, left, and right have to be done individually. A potential refactor could
        # combine top with bottom and left with right, but each of those groups are still different.

        # Comments in the "top" section apply to other sections

        for plot in self.top:
            if cooldown > 0:
                cooldown -= 1
                continue

            # If heights rounded down to the nearest multiple of 3 (for stair height change) aren't even,
            # walls around gates can become misaligned
            h = plot.base // 3 * 3
            h1 = plot.prevplot.base // 3 * 3
            h2 = plot.nextplot.base // 3 * 3

            # If the plot's height was fixed, it won't be match with the heightmap anymore, so it's not
            # a viable gate (needs to be flush with floor)
            if not plot.fixed_base and h == h1 == h2:
                viable = True

                # Check the gate's entry and exit points for matching heights, water, and hazards
                for x in xrange(plot.x, plot.x + 5):
                    z1 = plot.z - 1
                    z2 = plot.z + 5
                    if self.hmap.water[x, z1] or self.hmap.hazard[x, z1]\
                        or self.hmap.water[x, z2] or self.hmap.hazard[x, z2]:
                        viable = False
                        break
                    if self.hmap.getHeight(x, z1) != plot.base or self.hmap.getHeight(x, z2) != plot.base:
                        viable = False
                        break

                # Add to gate candidates
                if viable:
                    if gateCandidates.get(plot.base%3) is not None:
                        gateCandidates[plot.base % 3].append(plot)
                    else:
                        gateCandidates[plot.base%3] = [plot]
                    heightkey1 = plot.base % 3
                    cooldown = 20

        cooldown -= 10
        for plot in self.bot:
            if cooldown > 0:
                cooldown -= 1
                continue
            h = plot.base // 3 * 3
            h1 = plot.prevplot.base // 3 * 3
            h2 = plot.nextplot.base // 3 * 3
            if not plot.fixed_base and h == h1 == h2:
                viable = True
                for x in xrange(plot.x, plot.x + 5):
                    z1 = plot.z - 1
                    z2 = plot.z + 5
                    if self.hmap.water[x, z1] or self.hmap.hazard[x, z1]\
                        or self.hmap.water[x, z2] or self.hmap.hazard[x, z2]:
                        viable = False
                        break
                    if self.hmap.getHeight(x, z1) != plot.base or self.hmap.getHeight(x, z2) != plot.base:
                        viable = False
                        break
                if viable:
                    if gateCandidates.get(plot.base%3) is not None:
                        gateCandidates[plot.base % 3].append(plot)
                    else:
                        gateCandidates[plot.base%3] = [plot]
                    heightkey1 = plot.base % 3
                    cooldown = 20

        cooldown -= 10
        for plot in self.left:
            if cooldown > 0:
                cooldown -= 1
                continue
            h = plot.base // 3 * 3
            h1 = plot.prevplot.base // 3 * 3
            h2 = plot.nextplot.base // 3 * 3
            if not plot.fixed_base and h == h1 == h2:
                viable = True
                for z in xrange(plot.z, plot.z + 5):
                    x1 = plot.x - 1
                    x2 = plot.x + 5
                    if self.hmap.water[x1, z] or self.hmap.hazard[x1, z]\
                        or self.hmap.water[x2, z] or self.hmap.hazard[x2, z]:
                        viable = False
                        break
                    if self.hmap.getHeight(x1, z) != plot.base or self.hmap.getHeight(x2, z) != plot.base:
                        viable = False
                        break
                if viable:
                    if gateCandidates.get(plot.base%3) is not None:
                        gateCandidates[plot.base % 3].append(plot)
                    else:
                        gateCandidates[plot.base%3] = [plot]
                    heightkey1 = plot.base % 3
                    cooldown = 20

        cooldown -= 10
        for plot in self.right:
            if cooldown > 0:
                cooldown -= 1
                continue
            h = plot.base // 3 * 3
            h1 = plot.prevplot.base // 3 * 3
            h2 = plot.nextplot.base // 3 * 3
            if not plot.fixed_base and h == h1 == h2:
                viable = True
                for z in xrange(plot.z, plot.z + 5):
                    x1 = plot.x - 1
                    x2 = plot.x + 5
                    if self.hmap.water[x1, z] or self.hmap.hazard[x1, z]\
                        or self.hmap.water[x2, z] or self.hmap.hazard[x2, z]:
                        viable = False
                        break
                    if self.hmap.getHeight(x1, z) != plot.base or self.hmap.getHeight(x2, z) != plot.base:
                        viable = False
                        break
                if viable:
                    if gateCandidates.get(plot.base%3) is not None:
                        gateCandidates[plot.base % 3].append(plot)
                    else:
                        gateCandidates[plot.base%3] = [plot]
                    heightkey1 = plot.base % 3
                    cooldown = 20

        # Find the gate group with the most gates in it if there's a viable gate
        if heightkey1 is not None:
            highestCount = 0
            for heightkey in gateCandidates:
                count = len(gateCandidates[heightkey])
                if count > highestCount:
                    highestCount = count
                    heightkey1 = heightkey

            # Set found group as gates
            self.gates = gateCandidates[heightkey1]
            for plot in self.gates:
                plot.type = "Wall_Gate"
            return True
        else:
            return False

    def fixLevelToGate(self):
        if len(self.gates) == 0:
            return

        # Heights must have the same remainder when divided by 3 as gates to connect smoothly
        gateLevel = self.gates[0].base % 3
        for i in xrange(len(self.plotlist)):
            plot1 = self.plotlist[i]
            if plot1.type == "Wall_Gate":
                continue
            i2 = (i+1)%len(self.plotlist)
            plot2 = self.plotlist[i2]
            i3 = (i-1)%len(self.plotlist)
            plot3 = self.plotlist[i3]
            h1 = plot1.base
            h2 = plot2.base
            h3 = plot3.base

            # If there is a momentary dip in the wall, flatten it
            if h2 == h3:
                plot1.base = (h2 // 3)*3 + gateLevel
            else:
                plot1.base = (h1 // 3)*3 + gateLevel

    def scanForStairs(self):

        # If next plot has a different height, set current plot as a stair wall
        for i in range(len(self.plotlist)):
            plot = self.plotlist[i]
            nextplot = self.plotlist[(i+1)%len(self.plotlist)]
            if plot.type is None:
                if plot.base > nextplot.base:
                    plot.type = "Wall_Stair"
                    plot.height = 11

                    # Going down
                    plot.special = 0
                elif plot.base < nextplot.base:
                    plot.type = "Wall_Stair"
                    plot.height = 11

                    # Going up
                    plot.special = 2


    def finalizeTypes(self):

        # Set unset wall types to normal wall, store schematics
        for plot in self.plotlist:
            height = plot.height
            if plot in self.corners:
                plot.type = "Wall_Corner"
            if plot.type is None:
                plot.type = "Wall_Seg"
            filename = "./stock-filters/GDMC_Submission_Files/Schematics/" + plot.type + ".schematic"
            schematic = MCSchematic(shape=(5, height, 5), filename=filename)
            for i in xrange((plot.direction + plot.special) % 4):
                schematic.rotateLeft()
            plot.schematic = schematic

    def generateWall(self):
        for plot in self.plotlist:
            x = plot.x + self.hmap.minx
            y = plot.base
            z = plot.z + self.hmap.minz

            # Downward stairs must start lower
            if plot.type == "Wall_Stair" and plot.special == 0:
                y -= 3

            # Place wall segment
            self.level.copyBlocksFrom(plot.schematic, plot.schematic.bounds, Vector(x, y, z))

            minh = 999
            blocks = np.zeros((5,5))
            data = np.zeros((5,5))

            # Set occupied grid
            for xi in xrange(x, x+5):
                for zi in xrange(z, z+5):
                    blocks[xi - x][zi - z] = self.level.blockAt(xi, y, zi)
                    data[xi - x][zi - z] = self.level.blockDataAt(xi, y, zi)
                    minh = min(self.hmap.getHeight(xi, zi, False), minh)
                    self.occupied[xi - x + plot.x][zi - z + plot.z] = 1

            # Extend the wall downwards into non-ground blocks
            replaceable = [0] + HeightMap.DECORATIVE_BLOCKS + HeightMap.HAZARD + HeightMap.WATER
            depthcount = 0
            while depthcount < 3 and y > 2:
                foundReplacable = False
                for xi in xrange(x, x + 5):
                    for zi in xrange(z, z + 5):
                        block = self.level.blockAt(xi, y, zi)
                        if block in replaceable and not foundReplacable:
                            foundReplacable = True
                            depthcount = 0
                        self.level.setBlockAt(xi, y, zi, blocks[xi - x][zi - z])
                        self.level.setBlockDataAt(xi, y, zi, data[xi - x][zi - z])
                if not foundReplacable:
                    depthcount += 1
                y -= 1
                plot.base -= 1
                plot.height += 1













