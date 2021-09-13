import pymclevel
from pymclevel import level, MCSchematic, BoundingBox, TileEntity
import timeit
from pymclevel.box import Vector
from GDMC_Submission_Files.BlockReplacement import replaceBlocks, replacement_dictionaries as repldict
from GDMC_Submission_Files.HeightMap import *
from GDMC_Submission_Files.Structures import *
from GDMC_Submission_Files.Plot import Plot
from GDMC_Submission_Files.PathGeneration import PathGenerator, LegalPrecomp
from GDMC_Submission_Files.MinimumSpanningTree import Prim
from random import randint
from pymclevel import alphaMaterials, MCSchematic, MCLevel, BoundingBox
from mcplatform import *
import numpy as np
import random
import copy
import utilityFunctions as uf

inputs = (
      ("Make districts visible:", ("True", "False")),
      ("Material_farm:", alphaMaterials.Stone),
      ("Material_residece:", alphaMaterials.Stone),
      ("Material_marcket:", alphaMaterials.Stone),
      ("district number:",  (3, 1, 1000)),
      ("Max structures:", (100, 1, 250)),
      ("Buffer:", (4, 2, 20)),
      ("Maximum Land Roughness for Structure Generation:", (2, 0, 10)),
      ("Prune inaccessible areas:", ("True", "False")),
      ("Force biome materials: ", ("Calculate Biome", "Spruce", "Oak", "Birch", "Acacia", "Dark Oak", "Desert")),
      ("Note: Default material is Spruce.", "label")
)


def perform(level, box, options):
    start_time = timeit.default_timer()
    variance = options["Maximum Land Roughness for Structure Generation:"]
    max_structures = options["Max structures:"]
    plotbuffer = options["Buffer:"]
    path_width = 1
    biome_lists = {
        "spruce": [3, 5, 19, 20, 25, 32, 33, 34, 131, 133, 160, 161, 162],
        "oak": [1, 4, 6, 18, 129, 132],
        "birch": [4, 18, 27, 28, 132, 155, 156],
        "acacia": [35, 36, 163, 164],
        "dark oak": [29, 157],
        "desert": [2, 17, 130]
    }
    block = options["Material_farm:"]
    block2 = options["Material_residece:"]
    block3 = options["Material_marcket:"]
    district = options["district number:"]
    show_dis = options["Make districts visible:"]
    print(show_dis)
    print(box.minx, box.maxx, box.minz, box.maxz)
    origin = []      #distirct initialization
    for i in range(district):
        z = []
        x = random.randint(box.minx, box.maxx)
        y = random.randint(box.minz, box.maxz)
        z.append(x)
        z.append(y)
        origin.append(z)
    print('origin', origin)

    clean_origin = []    # repeating origins are removed
    for x in origin:
        if x not in clean_origin:
            clean_origin.append(x)

    n = 1
    lst = clean_origin
    list = [lst[i:i + n] for i in xrange(0, len(lst), n)]

    result = grow(clean_origin, list, box.maxx, box.maxz, box.minx, box.minz) # districts are genereted and grown
    farm, market, res = class_dis(result, level)

    if show_dis == "True":

     print("genereting distircts")    # districts are genereted in the world

     for c in xrange(len(farm)):
        for y in range(250, 0, -1):

            if level.blockAt(farm[c][0], y, farm[c][1]) in [1, 2, 3, 12, 13]:
                uf.setBlock(level, (block.ID, block.blockData), farm[c][0], y, farm[c][1])

     for c in xrange(len(res)):
        for y in range(250, 0, -1):

            if level.blockAt(res[c][0], y, res[c][1]) in [1, 2, 3, 12, 13]:
                uf.setBlock(level, (block2.ID, block2.blockData), res[c][0], y, res[c][1])

     for c in xrange(len(market)):
        for y in range(250, 0, -1):

            if level.blockAt(market[c][0], y, market[c][1]) in [1, 2, 3, 12, 13]:
                uf.setBlock(level, (block3.ID, block3.blockData), market[c][0], y, market[c][1])


    print("Done")

    # here the modefied code form Troy, Ryant and Trent is used  

    invalid_biomes = [0, 7, 16]
    prune = options["Prune inaccessible areas:"]
    if prune == "True": prune = True
    elif prune == "False": prune = False


    box_w = box.maxx - box.minx
    box_d = box.maxz - box.minz
    print("Generating heightmap and clearing trees (This may take a while.)")
    hmap = HeightMap(level, box)
    biome = options.get("Force biome materials: ")
    if biome == "Calculate Biome":
        print("Calculating biome for material type...")
        biome_count = {biome_key:0 for biome_key in biome_lists}

        # For every 4th block in the box, record its biome
        for x in xrange(box_w // 4):
            for z in xrange(box_d // 4):
                    biome = level.biomeAt((x + box.minx // 4)*4, (z + box.minz // 4)*4)
                    if biome not in invalid_biomes:
                        for biome_key in biome_lists:
                            if biome in biome_lists[biome_key]:
                                if biome_key not in biome_count:
                                    biome_count[biome_key] = 0
                                else:
                                    biome_count[biome_key] += 1
            biome = "spruce"
            count = biome_count[biome]
            for biome_key in biome_count:
                if biome_count[biome_key] > count:
                    biome = biome_key
                    count = biome_count[biome_key]
            print("Average biome determined. Material type:" + biome)
        else:
            print("Material type assigned to " + biome)
            biome = biome.lower()

        original_mats = 'spruce'
        new_mats = biome
        original_material_dict = repldict[original_mats]
        new_material_dict = repldict[new_mats]

        # Set up grid of spots that are taken up by hazards and plots
        occupancy = np.full_like(hmap.grid, 0)
        for x in xrange(box_w):
            for z in xrange(box_d):
                occupancy[x][z] = hmap.hazard[x][z] or hmap.water[x][z]

        # Set up lists of structure info
        shapes = getShapeList()
        probabilities = getProbabilityList()
        entrances = getEntranceList()
        names = getNameList()
        structure_info = [shapes, probabilities, entrances, names]
        print(structure_info)
        farm_sch = [[shapes[5], shapes[6]], [names[5], names[6]]]
        print(farm_sch)
        res_sch = [[shapes[4]], [names[4]]]
        print(res_sch)
        market_sch = [[shapes[0], shapes[1], shapes[2]], [names[0], names[1], names[2]]]
        print(market_sch)
        structure_new = [[shapes[0], shapes[1], shapes[2], shapes[4], shapes[6], shapes[7]], [probabilities[0], probabilities[1], probabilities[2], probabilities[4], probabilities[6], probabilities[7]], [entrances[0], entrances[1], entrances[2], entrances[4], entrances[6], entrances[7]], [names[0], names[0], names[2], names[4], names[6], names[7]]]

        #structure_new = [[shapes[1]], [probabilities[1]], [entrances[1]], [names[0]]]

        print("Successfully generated data for the following structures:")
        for structure_name in names:
            print(structure_name)

        # Keep track of plots spawned
        plots = []

        # Spawn each at least once
        print("Plotting every structure once...")
        if plotSetup(box, plots, structure_new, occupancy, hmap, variance, plotbuffer):
            print("Plotting structures randomly...")
            plotSetup(box, plots, structure_new, occupancy, hmap, variance, plotbuffer, True)
        print(str(len(plots)) + " potential structures plotted")

        print "Setting plots in height map"
        hmap.setPlots(plots)
        print "Recalculating plot heights"
        hmap.recalculateHeightForPlots()
        plotgrid = np.zeros_like(occupancy)
        for plot in plots:
            x = plot.x - hmap.minx
            z = plot.z - hmap.minz
            w = plot.width
            d = plot.depth
            for xi in xrange(x, x + w):
                for zi in xrange(z, z + d):
                    plotgrid[xi][zi] = 1
        points = [[plot.entrance[0] + plot.x, plot.entrance[1] + plot.z] for plot in plots]
        points_fix = [[point[0] - hmap.minx, point[-1] - hmap.minz] for point in points]
        print("Precomputing legal actions")
        legal = LegalPrecomp(level, hmap, path_width, occupancy, points_fix)

        if prune:
            print("Pruning plot list to largest connected sector and max structure count")
            confirmed_plots = []
            for plot in plots:
                x = plot.entrance[0] + plot.x - hmap.minx
                z = plot.entrance[1] + plot.z - hmap.minz
                if legal.max_sector == legal.sectors[x,z]:
                    confirmed_plots.append(plot)

            plots_end = len(confirmed_plots) if len(confirmed_plots) <= max_structures else max_structures
            plots = confirmed_plots[:plots_end]

            points = [[plot.entrance[0] + plot.x, plot.entrance[1] + plot.z] for plot in plots]
        else:
            print("Cutting plot list to max length of " + str(max_structures))
            plots = plots[:max_structures]

        print("Generating structures for plots...")
        generatePlots(plots, level, hmap, farm, res, market, farm_sch, res_sch, market_sch)

        print("Grouping points")

        mst = Prim(points)
        groups = mst.group()

        print("Groups made: " + str(len(groups)))

        print("Generating paths")
        path_block_info = new_material_dict.get("PATH_BLOCKS")
        path_blocks = [item[0] for item in path_block_info]
        path_data = [item[1] for item in path_block_info]
        ground = None
        for i in xrange(len(groups)):
            group = groups[i]
            point1, point2 = group[0], group[1]
            x1, z1 = point1[0], point1[-1]
            x2, z2 = point2[0], point2[-1]
            pathgen = PathGenerator(x1, z1, x2, z2, level, hmap, 1, path_blocks, path_data, legal, ground=ground)
            path_success = pathgen.makePath()
            ground = pathgen.ground
            print("Group " + str(i) + " - " + str(point1) + " to " + str(point2) + ": " + str(path_success))
        print("Paths generated")
        if original_mats != new_mats:
            print("Changing materials for each plot (This may take a while)")

            for i in range(len(plots)):
                print("Changing plot " + str(i + 1))
                plot = plots[i]
                x1 = plot.x
                y1 = 0
                z1 = plot.z
                x2 = plot.width
                z2 = plot.depth
                y2 = 255
                replaceBlocks(level, BoundingBox((x1, y1, z1), (x2, y2, z2)), original_material_dict, new_material_dict)


        print("Materials switched")

        level.markDirtyBox(box)

        print("Settlement generated!")

        elapsed = timeit.default_timer() - start_time
        print(elapsed)



def weighted_index_selection(probabilities):
    count = 0
    thresholds = [0] * len(probabilities)
    for i in xrange(len(probabilities)):
        count += probabilities[i]
        thresholds[i] = count
    choice_val = randint(0, max(thresholds))
    for val in thresholds:
        if choice_val <= val:
            return thresholds.index(val)


def plotSetup(box, plots, info, occupancy, hmap, variance, plotbuffer, rand=False):
    shapes, probabilities, entrances, names = info[0], info[1], info[2], info[3]
    index = 0
    while True:
        if rand:
            index = weighted_index_selection(info[1])
        elif index >= len(info[0]):
            break

        rotation = randint(0, 3)
        shape = shapes[index]
        schematic_width = shape[0]
        schematic_depth = shape[2]

        filename = "./stock-filters/GDMC_Submission_Files/Schematics/" + names[index] + ".schematic"
        print(names)
        schematic = MCSchematic(shape=shape, filename=filename)

        for i in xrange(rotation):
            schematic.rotateLeft()

        entrance = rotateEntrance(entrances[index], schematic_width, schematic_depth, rotation)
        plot = scanForPlot(schematic, occupancy, hmap, variance, plotbuffer)

        # If successful in finding a spot for the plot, add to plots, reserve space, and place schematic
        if plot is not None:

            plot.setEntrance(entrance[0], entrance[1])

            # Set occupancy for plot
            for x in xrange(plot.x, plot.x + plot.width - 1):
                for z in xrange(plot.z, plot.z + plot.depth - 1):
                    occupancy[x][z] = True

            # Plot is calculated relative to grid coordinates (heightmap grid / occupancy grid)
            # Set to level coordinates
            plot.x = plot.x + box.minx
            plot.z = plot.z + box.minz

            plots.append(plot)
            print("Count: " + str(len(plots)) + ", " + names[index] + " plotted successfully.")
            index += 1

        # Otherwise, remove the structure from spawning pools
        else:
            print("Structure ineligible: " + names[index])
            for info_list in info:
                info_list.pop(index)
            if len(names) == 0:
                print("No more plots can fit.")
                return False
    return True


def generatePlots(plots, level, hmap, farm, res, market, farm_sch, res_sch, market_sch):
    for plot in plots:
        new_schematic = []
        cord_spawn = []
        spawn_x = plot.x
        spawn_z = plot.z
        cord_spawn.append(spawn_x)
        cord_spawn.append(spawn_z)
        if cord_spawn in farm:
            print("in farm area !!!!!!!!!")
            new_index = random.randint(0, 1)
            filename = "./stock-filters/GDMC_Submission_Files/Schematics/" + farm_sch[1][new_index] + ".schematic"
            new_schematic = MCSchematic(shape=farm_sch[0][new_index], filename=filename)
            rotation = randint(0, 3)
            for i in xrange(rotation):
                new_schematic.rotateLeft()

        elif cord_spawn in res:
            print("in residential area !!!!!!!")
            new_index = 0  #random.randint(0, 1)
            filename = "./stock-filters/GDMC_Submission_Files/Schematics/" + res_sch[1][new_index] + ".schematic"
            new_schematic = MCSchematic(shape=res_sch[0][new_index], filename=filename)
            rotation = randint(0, 3)
            for i in xrange(rotation):
                new_schematic.rotateLeft()

        elif cord_spawn in market:
            print("in market area !!!!!!!!!")
            new_index = random.randint(0, 2)
            filename = "./stock-filters/GDMC_Submission_Files/Schematics/" + market_sch[1][new_index] + ".schematic"
            new_schematic = MCSchematic(shape=market_sch[0][new_index], filename=filename)
            rotation = randint(0, 3)
            for i in xrange(rotation):
                new_schematic.rotateLeft()

        entrance = plot.entrance
        spawn_y = hmap.getHeight(entrance[0] + spawn_x, entrance[1] + spawn_z, False)
        placeSchematic(level, Vector(spawn_x, spawn_y, spawn_z), new_schematic)  #plot.schematic


def scanForPlot(schematic, restrictions, heightmap, variance=1, buffer=1):
    w = schematic.Width
    d = schematic.Length
    variance_buffer_reduction = buffer // 2

    # Check each grid position
    x_max = heightmap.width - w - buffer
    x = buffer
    while x < x_max:
        z_max = heightmap.maxz - heightmap.minz - d - buffer
        z = buffer
        x_skip_count = 0
        while z < z_max:
            invalid = False
            lowest_y = highest_y = heightmap.getHeight(x, z, True)

            # Scan the size of the plot for restrictions and suitable variance
            for x1 in range(x - buffer, w + x + buffer):
                z_skip_count = 0
                for z1 in range(z - buffer, d + z + buffer):

                    # If restricted, don't consider this plot
                    invalid = bool(restrictions[x1][z1])

                    if invalid:

                        # Optimization: skip ahead based on coordinates of invalid block
                        z += z_skip_count
                        x_skip_count = max(x_skip_count, x1 - x + buffer)

                        break
                    z_skip_count += 1

                    try:
                        height = heightmap.getHeight(x1, z1, True)
                    except TypeError as ex:
                        print("hmap width: " + str(heightmap.maxx - heightmap.minx))
                        print("hmap depth: " + str(heightmap.maxz - heightmap.minz))
                        print("x: " + str(x))
                        print("z: " + str(z))
                        print("x1: " + str(x1))
                        print("z1: " + str(z1))
                        raise ex

                    lowest_y = min(lowest_y, height)
                    highest_y = max(highest_y, height)

                    # If ground is too uneven, don't spawn
                    if x - variance_buffer_reduction < x1 < w + x + variance_buffer_reduction\
                            and z - variance_buffer_reduction < z1 < d + z + variance_buffer_reduction:
                        variance_check = (abs(highest_y - lowest_y) > variance)
                    else:
                        variance_check = False
                    if variance_check:
                        invalid = True
                        break

                if invalid:
                    break

            if not invalid:
                plot = Plot(w, d, x=x, z=z, schematic=schematic)
                return plot
            z += 1
        x += 1 + x_skip_count
    return None


def rotateEntrance(entrance, structure_width, structure_depth, rotation = 1):
    try:
        rot = rotation % 4
    except TypeError:
        raise TypeError("Rotation must be an integer. Given rotation: " + str(rotation))
    w, d = structure_width, structure_depth
    x, z = entrance[0], entrance[1]
    new_entrance = [x, z]
    if rot == 0:
        return new_entrance
    while rot >= 1:
        new_entrance = [z, w-x-1]
        x, z = new_entrance[0], new_entrance[1]
        w, d = d, w
        rot -= 1
    return new_entrance


def combineArrays(a1, a2):
    a3 = np.zeros_like(a1)
    for xi in xrange(len(a3)):
        for zi in xrange(len(a3[0])):
            a3[xi][zi] = a1[xi][zi] or a2[xi][zi]
    return a3


def placeSchematic(level, destination, schematic, offset=Vector(0, -2, 0)):
    # NOTE: All schematics for this program are expected to go 2 blocks below ground level
    print(schematic)
    print(schematic.bounds)
    level.copyBlocksFrom(schematic, schematic.bounds, destination + offset)

def move_check(list, used_lst, boxmaxx, boxmaxz, boxminx, boxminz):

 possible_moves = []
 up = copy.deepcopy(list)
 down = copy.deepcopy(list)
 left_lst = copy.deepcopy(list)
 right_lst = copy.deepcopy(list)
 for ele in xrange(len(list)):

    # up
    up[ele][0] = up[ele][0] - 1
    if growth_app(up[ele], used_lst, boxmaxx, boxmaxz, boxminx, boxminz):
        possible_moves.append(up[ele])
    # down
    down[ele][0] = down[ele][0] + 1
    if growth_app(down[ele], used_lst, boxmaxx, boxmaxz, boxminx, boxminz):
        possible_moves.append((down[ele]))
    # left
    left_lst[ele][1] = left_lst[ele][1] - 1
    if growth_app(left_lst[ele], used_lst, boxmaxx, boxmaxz, boxminx, boxminz):
        possible_moves.append((left_lst[ele]))
    # right
    right_lst[ele][1] = right_lst[ele][1] + 1
    if growth_app(right_lst[ele], used_lst, boxmaxx, boxmaxz, boxminx, boxminz):
        possible_moves.append((right_lst[ele]))
 return possible_moves


def growth_app(lst, used_lst, boxmaxx, boxmaxz, boxminx, boxminz):

 if lst[0] < boxminx or lst[0] > boxmaxx or lst in used_lst:
    return False

 elif lst[1] < boxminz or lst[1] > boxmaxz or lst in used_lst:
    return False

 else:
    return True


def grow(clean_origin, list, boxmaxx, boxmaxz, boxminx, boxminz):
 print(abs(boxmaxx), abs(boxminx), abs(boxmaxz), abs(boxminz))
 poss_moves = (abs(abs(boxmaxx) - abs(boxminx)) + 1) * (abs(abs(boxmaxz) - abs(boxminz)) + 1)
 used_lst = clean_origin
 no_grow=[]
 print("list",list)
 while poss_moves > len(used_lst):
    for s in xrange(len(list)):

      if not s in no_grow:
        possible_moves = move_check(list[s], used_lst, boxmaxx, boxmaxz, boxminx, boxminz)
        if possible_moves != []:
            clean_moves = []
            for v in possible_moves:
                if v not in clean_moves:
                    clean_moves.append(v)
            move = clean_moves

            list[s].extend(move)
            used_lst.extend(move)

        else:
             no_grow.append(s)
        print("poss_moves", poss_moves)
        print("used list number",len(used_lst))


 print("list 1", len(list[0]))
 print("list 2", len(list[1]))
 print("list 3", len(list[2]))
 return list

def class_dis(result, level):

 farm = []
 market = []
 res = []
 disopt=[1,2,3]

 print('row number :', len(result))

 for k in range(0, len(result)):
    w = 0
    f = 0
    y = 250
    r = 0
    max = []
    while f < len(result[k]) and w == 0: # w < 3
        f = f+1
        while y > 0 and w == 0: # w < 3
            y = y-1
            if level.blockAt(result[k][f][0], y, result[k][f][1]) in [8, 9]:
                w = 1  # w + 1
            elif level.blockAt(result[k][f][0], y, result[k][f][1]) in [1, 2, 3, 12, 13]:
                max.append(y)

    max = sorted(max)[-10:]
    r = sum(max)/10
    if w == 1:  # w >= 3
      print("water")
      distype = np.random.choice(disopt, 1, True, [0.5, 0.25, 0.25])
      if distype == 1:
        farm.extend(result[k])
      elif distype == 2:
        market.extend(result[k])
      elif distype == 3:
        res.extend(result[k])
    elif r > 68:
      print("hill")
      distype = np.random.choice(disopt, 1, True, [0.25, 0.25, 0.5])
      if distype == 1:
        farm.extend(result[k])
      elif distype == 2:
        market.extend(result[k])
      elif distype == 3:
        res.extend(result[k])
    else:
      print("plateau")
      distype = random.choice(disopt)
      if distype == 1:
        farm.extend(result[k])
      elif distype == 2:
        market.extend(result[k])
      elif distype == 3:
        res.extend(result[k])

 print("farm",farm)
 print("market",market)
 print("res",res)

 return (farm,market,res)