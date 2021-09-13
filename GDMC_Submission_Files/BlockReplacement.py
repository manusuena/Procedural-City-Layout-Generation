
def replaceBlocks(level, box, from_dict, to_dict):
    IGNORE = ["PATH_START", "PATH_BLOCKS"]
    for x in xrange(box.minx, box.maxx):
        for y in xrange(box.miny, box.maxy):
            for z in xrange(box.minz, box.maxz):
                block = level.blockAt(x,y,z)
                data = level.blockDataAt(x,y,z)
                if block == 204:
                    level.setBlockAt(x, y, z, to_dict["PATH_BLOCKS"][0][0])
                    level.setBlockDataAt(x, y, z, to_dict["PATH_BLOCKS"][0][1])
                for key in from_dict:
                    if key in IGNORE:
                        continue
                    if to_dict.get(key) == None:
                        print("Error, key " + key + " not found in to_dict")
                    elif "STAIR" in key or "DOOR" in key:
                        if block == from_dict[key] and block != to_dict[key]:
                            level.setBlockAt(x, y, z, to_dict[key])
                    else:
                        from_match = block == from_dict[key][0] and data == from_dict[key][1]
                        to_match = block == to_dict[key][0] and data == to_dict[key][1]
                        if from_match and not to_match:
                            level.setBlockAt(x, y, z, to_dict[key][0])
                            level.setBlockDataAt(x, y, z, to_dict[key][1])


stair_list = [53, 67, 108, 109, 114, 128, 134, 135, 136, 156, 163, 164, 180, 203]
door_list = [64, 71, 193, 194, 195, 196, 197]
ground_list = [12, ]

spruce_dict = {
    "PILLAR": (1,6),                   # Polished Andesite
    "MATERIAL1": (5,1),                # Spruce Wood Planks
    "FARM_TRIM": (17,1),               # Spruce Log (Upright)
    "WINDOW": (20,0),                  # Glass
    "FLOOR": (43,0),                   # Stone Double Slab
    "MATERIAL2": (98,0),               # Stone Brick
    "MATERIAL2_STAIR": 109,            # Stone Brick Stairs (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 134,            # Spruce Wood Stairs (GET DATA FOR ORIENTATION)
    "CROP1": (59,7),                   # Wheat
    "CROP2": (141,7),                  # Carrots
    "CROP3": (142,7),                  # Potatoes
    "LIGHT_FANCY": (124,0),            # Redstone Lamp
    "CARPET": (171,14),                # Red Carpet
    "FENCE_IN": (188,0),               # Spruce Fence
    "FENCE_OUT": (139,0),              # Cobble Wall
    "DOOR": 193,                       # Spruce Door (GET DATA)
    "GROUND1": (2, 0),                 # Grass
    "GROUND2": (3, 0),                 # Dirt
    "PATH_START": (98, 0),             # Stone Brick
    "PATH_BLOCKS": [(13, 0), (4,0), (1, 5)] # Gravel, Cobble, Andesite
}

oak_dict = {
    "PILLAR": (17,0),              # Oak Log (Upright)
    "MATERIAL1": (5,0),            # Oak Wood Planks
    "FARM_TRIM": (17,0),           # Oak Log (Upright)
    "WINDOW": (20,0),              # Glass
    "FLOOR": (43,0),               # Stone Double Slab
    "MATERIAL2": (98,0),           # Stone Brick
    "MATERIAL2_STAIR": 109,        # Stone Brick Stairs (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 53,         # Oak Wood Stairs (GET DATA FOR ORIENTATION)
    "CROP1": (59,7),               # Wheat
    "CROP2": (141,7),              # Carrots
    "CROP3": (142,7),              # Potatoes
    "LIGHT_FANCY": (124,0),        # Redstone Lamp
    "CARPET": (171,9),             # Cyan Carpet
    "FENCE_IN": (85,0),            # Oak Fence
    "FENCE_OUT": (139,0),          # Cobble Wall
    "DOOR": 64,                    # Oak Door (GET DATA)
    "GROUND1": (2, 0),                 # Grass
    "GROUND2": (3, 0),                 # Dirt
    "PATH_START": (98, 0),         # Stone Brick
    "PATH_BLOCKS": ([(208, 0)])         # Path
}

birch_dict = {
    "PILLAR": (43, 8),             # Stone double slabs
    "MATERIAL1": (5,2),            # Birch Wood Planks
    "FARM_TRIM": (17,2),           # Birch Log (Upright)
    "WINDOW": (20,0),              # Glass
    "FLOOR": (43,0),               # Stone Double Slab
    "MATERIAL2": (98,0),           # Stone Brick
    "MATERIAL2_STAIR": 109,        # Stone Brick Stairs (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 135,        # Birch Wood Stairs (GET DATA FOR ORIENTATION)
    "CROP1": (59,7),               # Wheat
    "CROP2": (141,7),              # Carrots
    "CROP3": (142,7),              # Potatoes
    "LIGHT_FANCY": (124,0),        # Redstone Lamp
    "CARPET": (171,0),             # White Carpet
    "FENCE_IN": (189,0),           # Birch Fence
    "FENCE_OUT": (139,0),          # Cobble Wall
    "DOOR": 194,                   # Birch Door (GET DATA)
    "GROUND1": (2, 0),                 # Grass
    "GROUND2": (3, 0),                 # Dirt
    "PATH_START": (98, 0),         # Stone Brick
    "PATH_BLOCKS": ([(208, 0)])         # Path
}

dark_oak_dict = {
    "PILLAR": (162,1),             # Dark Oak Log (Upright)
    "MATERIAL1": (5,5),            # Dark Oak Wood Planks
    "FARM_TRIM": (162,1),          # Dark Oak Log (Upright)
    "WINDOW": (20,0),              # Glass
    "FLOOR": (43,0),               # Stone Double Slab
    "MATERIAL2": (98,0),           # Stone Brick
    "MATERIAL2_STAIR": 109,        # Stone Brick Stairs (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 164,        # Dark Oak Wood Stairs (GET DATA FOR ORIENTATION)
    "CROP1": (59,7),               # Wheat
    "CROP2": (141,7),              # Carrots
    "CROP3": (142,7),              # Potatoes
    "LIGHT_FANCY": (124,0),        # Redstone Lamp
    "CARPET": (171,15),            # Black Carpet
    "FENCE_IN": (191,0),           # Dark Oak Fence
    "FENCE_OUT": (139,0),          # Cobble Wall
    "DOOR": 197,                   # Dark Oak Door (GET DATA)
    "GROUND1": (2, 0),                 # Grass
    "GROUND2": (3, 0),                 # Dirt
    "PATH_START": (98, 0),         # Stone Brick
    "PATH_BLOCKS": ([(208, 0)])         # Path
}

acacia_dict = {
    "PILLAR": (162,0),             # Acacia Log (Upright)
    "MATERIAL1": (5,4),            # Acacia Wood Planks
    "FARM_TRIM": (162,0),          # Acacia Log (Upright)
    "WINDOW": (20,0),              # Glass
    "FLOOR": (43,0),               # Stone Double Slab
    "MATERIAL2": (98,0),           # Stone Brick
    "MATERIAL2_STAIR": 109,        # Stone Brick Stairs (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 163,        # Acacia Wood Stairs (GET DATA FOR ORIENTATION)
    "CROP1": (59,7),               # Wheat
    "CROP2": (141,7),              # Carrots
    "CROP3": (142,7),              # Potatoes
    "LIGHT_FANCY": (124,0),        # Redstone Lamp
    "CARPET": (171,9),             # Cyan Carpet
    "FENCE_IN": (192,0),           # Acacia Fence
    "FENCE_OUT": (139,0),          # Cobble Wall
    "DOOR": 196,                   # Acacia Door (GET DATA)
    "GROUND1": (2, 0),                 # Grass
    "GROUND2": (3, 0),                 # Dirt
    "PATH_START": (98, 0),         # Stone Brick
    "PATH_BLOCKS": ([(208,0)])          # Path
}

desert_dict = {
    "PILLAR": (98,0),              # Stone Brick
    "MATERIAL1": (24,0),           # Sandstone
    "FARM_TRIM": (1,4),            # Polished Diorite
    "WINDOW": (20,0),              # Glass
    "FLOOR": (43,0),               # Stone Double Slab
    "MATERIAL2": (24,2),           # Smooth Sandstone
    "MATERIAL2_STAIR": 128,        # Sandstone Stairs (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 128,        # Sandstone Stairs (GET DATA FOR ORIENTATION)
    "CROP1": (59,7),               # Wheat
    "CROP2": (141,7),              # Carrots
    "CROP3": (142,7),              # Potatoes
    "LIGHT_FANCY": (124,0),        # Redstone Lamp
    "CARPET": (171,13),            # Green Carpet
    "FENCE_IN": (139,0),           # Cobble Wall
    "FENCE_OUT": (139,0),          # Cobble Wall
    "DOOR": 194,                   # Birch Door (GET DATA)
    "GROUND1": (12, 0),            # Sand
    "GROUND2": (12, 0),            # Sand
    "PATH_START": (24,0),          # Stone Brick
    "PATH_BLOCKS": ([(1, 0)])
}

blank_dict = {
    "PILLAR": (0,0),
    "MATERIAL1": (0,0),
    "FARM_TRIM": (0,0),
    "WINDOW": (0,0),
    "FLOOR": (0,0),
    "MATERIAL2": (0,0),
    "MATERIAL2_STAIR": 0,         # (GET DATA FOR ORIENTATION)
    "MATERIAL1_STAIR": 0,         # (GET DATA FOR ORIENTATION)
    "CROP1": (0,0),
    "CROP2": (0,0),
    "CROP3": (0,0),
    "LIGHT_FANCY": (0,0),
    "CARPET": (0,0),
    "FENCE_IN": (0,0),
    "FENCE_OUT": (0,0),
    "DOOR": 0,                    # (GET DATA)
    "GROUND1": (0, 0),
    "GROUND2": (0, 0),
    "PATH_START": (0, 0),
    "PATH_BLOCKS": ([])
}

replacement_dictionaries = {
    "oak": oak_dict,
    "spruce": spruce_dict,
    "birch": birch_dict,
    "acacia": acacia_dict,
    "dark oak": dark_oak_dict,
    "desert": desert_dict
}

