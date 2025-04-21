import pygame
import pytmx
import copy
import sys
import json

# 9 Nearby tiles
NEIGHBORS_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]

# Physics tile types
PHYSICS_TILE_TYPES = {
    'torch',
    'walls', 
    'bush',
    'rock',
    'light', 
    'tree',
    'bonfire',
    'water',
    'lava',
    'bronze_chest',
    'silver_chest',
    'gold_chest',
    }

# Hitboxes for physics objects
PHYSICS_TILE_HITBOXES = {
    'walls': {
        0: (16, 16),
        1: (16, 16),
        2: (16, 16),
        3: (16, 16),
        4: (16, 16),
        5: (16, 16),
    },
    'bush': {
        0: (12, 12),
    },
    'rock': {
        0: (12, 12),
    },
    'light': {
        0: (12, 14),
    },
    'tree': {
        0: (0, 0),
        1: (0, 0),
        2: (4, 16),
        3: (4, 16),
    },
    'bonfire': {
        0: (0, 0),
        1: (0, 0),
        2: (8, 14),
        3: (8, 14),
    },
    'water': {
        0: (14, 20),
    },
    'lava': {
        0: (14, 20),
    },
    'bronze_chest': {
        0: (16, 16),
    },
    'silver_chest': {
        0: (16, 16),
    },
    'gold_chest': {
        0: (16, 16),
    },
    'torch' : {
        0: (16, 16),
    }
}

# If over a physics layer tile will negate the physcis
NEGATE_PHYSICS_LAYERS = {
    'bridge'
}

# Non-animated
NON_ORDER_TILES = {
    'ground',
    'bridge',
    }

# INTRERACTABLE_TILE_TYPES = {'ladder'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.tile_size = tile_size
        self.game = game
        self.tilemap = {}
        self.tilemap_layer_data_values = {}
        # Dict used for drawable objects, animated objects, and large objects (larger than 16x16) rendered in y-sort order
        self.object_layers = {
            # Functional Objects
            'player' : {'positions': [], 'variants': []},
            'skeleton' : {'positions': [], 'variants': []},
            'bonfire' : {'positions': [], 'variants': []},
            'bronze_chest' : {'positions': [], 'variants': []},
            'silver_chest' : {'positions': [], 'variants': []},
            'gold_chest' : {'positions': [], 'variants': []},
            # Animation Physics Objects
            # 'bush' : {'positions': [], 'variants': []},
            'tree' : {'positions': [], 'variants': []},
        }

        # Always rendered under the player, non y-sorted animated tiles
        self.animated_layers = {
            'water' : {'positions': [], 'variants': []},
            'lava' : {'positions': [], 'variants': []},
            'red_flower': {'positions': [], 'variants': []},
            'purple_flower': {'positions': [], 'variants': []},
            'torch' : {'positions': [], 'variants': []},
        }

        self.offgrid_tiles = []
        self.player_position = (0, 0)
        self.enemy_positions = []
        self.boss_positions = []
        self.trees = []
        self.current_level = None

    def load(self):
        # Load the map tilemap
        self.tmx_data = pytmx.load_pygame('./levels/test_level_3/test_level_3.tmx')
        self.current_level = 'test_level_3'

        # create dictionary with key = layer names and values an array on integers in the data
        for layer_index, layer in enumerate(self.tmx_data.visible_layers):
            self.tilemap_layer_data_values.update({layer.name:[]})

        # Add integer values of each layer into corresponding layer       
        for layer_index, layer in enumerate(self.tmx_data.visible_layers):
            for x, y , surf in layer.tiles():
                if layer.data[y][x] not in self.tilemap_layer_data_values[layer.name]:
                    self.tilemap_layer_data_values[layer.name].append(layer.data[y][x])

        for layer_index, layer in enumerate(self.tmx_data.visible_layers):
            for x, y , surf in layer.tiles():
                if layer.data[y][x] not in self.tilemap_layer_data_values[layer.name]:
                    self.tilemap_layer_data_values[layer.name].append(layer.data[y][x])

        self.temp_object_layers = copy.deepcopy(self.object_layers)
        self.temp_animated_layers = copy.deepcopy(self.animated_layers)
        
        # Match value within the layer to the variant that is the corresponding index of the layer
        for layer_index, layer in enumerate(self.tmx_data.visible_layers):
            for x, y, surf in layer.tiles():
                key = str(x) + ';' + str(y)
                if key not in self.tilemap:
                    self.tilemap[key] = []
                if layer.data[y][x] != 0:
                    if layer.data[y][x] in self.tilemap_layer_data_values[layer.name]:
                        self.tilemap[key].append({'type': layer.name, 'variant': self.tilemap_layer_data_values[layer.name].index(layer.data[y][x]), 'pos': (x, y), 'layer': layer_index})
                    for k in self.temp_object_layers:
                        if layer.name == k:
                            self.temp_object_layers[k]['positions'].append((x,y))
                            self.temp_object_layers[k]['variants'].append(self.tilemap_layer_data_values[layer.name].index(layer.data[y][x]))
                    for k in self.temp_animated_layers:
                        if layer.name == k:
                            self.temp_animated_layers[k]['positions'].append((x,y))
                            self.temp_animated_layers[k]['variants'].append(self.tilemap_layer_data_values[layer.name].index(layer.data[y][x]))


        # 2D array of physics tiles for the purpose of using a maze solving algo for pathfinding enemies to player
        self.physics_tilemap = [[0 for x in range(self.tmx_data.width)] for y in range(self.tmx_data.height)]
        for tile in self.tilemap:
            negate_physics = None
            for tile_types in self.tilemap[tile]:
                if tile_types['type'] in NEGATE_PHYSICS_LAYERS:
                    negate_physics = True
            index = tile.find(';')
            x = int(tile[:index])
            y = int(tile[index+1:])
            if tile_types['type'] in PHYSICS_TILE_TYPES and not negate_physics:
                self.physics_tilemap[y][x] = 1
            else:
                self.physics_tilemap[y][x] = 0
            
        physics_variants = self.get_top_left_most_variants(self.temp_object_layers)
        # TODO animation objects that are non-physics need to be rendered under player always
        animated_variants = self.get_top_left_most_variants(self.temp_animated_layers)
        
        for k1 in self.temp_object_layers:
            if physics_variants is not None:
                for k2 in physics_variants:
                    if k1 == k2:
                        for i in range(0, len(self.temp_object_layers[k1]['variants'])):
                            if physics_variants[k2][0] == self.temp_object_layers[k1]['variants'][i]:
                                self.object_layers[k1]['positions'].append(self.temp_object_layers[k1]['positions'][i])
        
        for k1 in self.temp_animated_layers:
            if animated_variants is not None:
                for k2 in animated_variants:
                    if k1 == k2:
                        for i in range(0, len(self.temp_animated_layers[k1]['variants'])):
                            if animated_variants[k2][0] == self.temp_animated_layers[k1]['variants'][i]:
                                self.animated_layers[k1]['positions'].append(self.temp_animated_layers[k1]['positions'][i])
            
    def get_top_left_most_variants(self, dict):
        top_left_positions = {}
        top_left_variants = {}
        for k in dict:
            top_left_pos = None
            for v in dict[k]:
                if len(dict[k][v]) == 0:
                    continue
                if v != 'variants':
                        for i in dict[k][v]:
                            if top_left_pos == None:
                                top_left_pos = i
                            elif top_left_pos[1] > i[1]:
                                top_left_pos = i
                            elif top_left_pos[0] > i[0]:
                                top_left_pos = i
                        top_left_positions[k] = []
                        top_left_positions[k].append(top_left_pos)
                        top_left_index = dict[k][v].index(top_left_positions[k][0])
                        top_left_variants[k] = []
                        y = dict[k]['variants'][top_left_index]
                        top_left_variants[k] = []
                        top_left_variants[k].append(y)
                                  
        return top_left_variants

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in list(self.tilemap.keys()):
            for tile in self.tilemap[loc]:
                if (tile['type'], tile['variant']) in id_pairs:
                    match = tile.copy()
                    match['pos'] = list(match['pos'])
                    match['pos'][0] *= self.tile_size
                    match['pos'][1] *= self.tile_size
                    matches.append(match)
                    if not keep:
                        self.tilemap[loc].remove(tile)
                        if not self.tilemap[loc]:  # Remove the key if the list is empty
                            del self.tilemap[loc]

        return matches

    def get_all_ordered_tiles(self):
        """
        Get all tiles and their locations from the tilemap.

        :return: List of dictionaries containing tile information, including location and type.
        """
        all_tiles = []
        for key, tiles in self.tilemap.items():
            for tile in tiles:
                if tile['type'] not in NON_ORDER_TILES:
                    # Each tile entry contains its location, type, and other attributes
                    tile_info = {
                        'type': tile['type'],
                        'variant': tile['variant'],
                        'pos': tile['pos'],
                        'layer': tile['layer']
                    }
                    all_tiles.append(tile_info)
        return all_tiles    

    def get_all_non_ordered_tiles(self):
        """
        Get all tiles and their locations from the tilemap.

        :return: List of dictionaries containing tile information, including location and type.
        """
        all_tiles = []
        for key, tiles in self.tilemap.items():
            for tile in tiles:
                if tile['type'] in NON_ORDER_TILES:
                    # Each tile entry contains its location, type, and other attributes
                    tile_info = {
                        'type': tile['type'],
                        'variant': tile['variant'],
                        'pos': tile['pos'],
                        'layer': tile['layer']
                    }
                    all_tiles.append(tile_info)
        return all_tiles       

    def get_animated_tiles(self):
        """
        Find and return all animated tiles such as bonfires.
        """
        all_tiles = []
        for key, tiles in self.tilemap.items():
            for tile in tiles:
                if tile['type'] in self.animated_tiles:
                    tile_info = {
                        'type': tile['type'],
                        'variant': tile['variant'],
                        'pos': tile['pos'],
                        'layer': tile['layer'],
                        'animation': self.game.assets[tile['type'] + '/animation'].copy()  # Add animation for bonfire
                    }
                    all_tiles.append(tile_info)
        return all_tiles

    def tiles_arounds(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBORS_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.extend(self.tilemap[check_loc])
        return tiles
    
    def physics_rects_around(self, pos, entity_size, obj_type):
        """
        Find all physics-related rectangles around the given position
        considering the size of the entity.

        :param pos: Position of the entity (x, y).
        :param entity_size: Size of the entity (width, height).
        :return: List of pygame.Rect representing the physics collision boxes.
        """
        rects = []
        ignore_physics_rects = []
        # Calculate the number of tiles the entity covers
        start_tile_x = int(pos[0] // self.tile_size) - 2
        end_tile_x = int((pos[0] + entity_size[0]) // self.tile_size) + 2
        start_tile_y = int(pos[1] // self.tile_size) - 2
        end_tile_y = int((pos[1] + entity_size[1]) // self.tile_size) + 2

        for x in range(start_tile_x, end_tile_x):
            for y in range(start_tile_y, end_tile_y):
                check_loc = f"{x};{y}"
                if check_loc in self.tilemap:
                    for tile in self.tilemap[check_loc]:
                        if tile['type'] in NEGATE_PHYSICS_LAYERS:
                            ignore_physics_rects.append((x, y))

        for x in range(start_tile_x, end_tile_x):
            for y in range(start_tile_y, end_tile_y):
                check_loc = f"{x};{y}"
                if check_loc in self.tilemap:
                    for tile in self.tilemap[check_loc]:
                        if  (tile['type'] == 'water' or tile['type'] == 'lava') and obj_type == 'projectile': 
                            continue
                        if tile['type'] in PHYSICS_TILE_TYPES and (x, y) not in ignore_physics_rects:
                            width, height = PHYSICS_TILE_HITBOXES.get(tile['type'], {}).get(tile['variant'], (self.tile_size, self.tile_size))
                            if (tile['type'] == 'water' or tile['type'] == 'lava'): 
                                rect = pygame.Rect(
                                    tile['pos'][0] * self.tile_size + ((self.tile_size - width) / 2),
                                    tile['pos'][1] * self.tile_size + ((self.tile_size - height) / 2) - 4,
                                    width,
                                    height
                                )
                            else:
                                rect = pygame.Rect(
                                    tile['pos'][0] * self.tile_size + ((self.tile_size - width) / 2),
                                    tile['pos'][1] * self.tile_size + ((self.tile_size - height) / 2),
                                    width,
                                    height
                                )
                            rects.append(rect)
        return rects
    

    def bonfires_around(self, pos, player_size):
        nearby_bonfires = []

        # Calculate the number of tiles the entity covers
        start_tile_x = int(pos[0] // self.tile_size) - 2
        end_tile_x = int((pos[0] + player_size[0]) // self.tile_size) + 2
        start_tile_y = int(pos[1] // self.tile_size) - 2
        end_tile_y = int((pos[1] + player_size[1]) // self.tile_size) + 2

        for x in range(start_tile_x, end_tile_x):
            for y in range(start_tile_y, end_tile_y):
                check_loc = f"{x};{y}"
                if check_loc in self.tilemap:
                    for tile in self.tilemap[check_loc]:
                       # Check for bonfire object positions
                        if tile['type'] == 'bonfire':
                            if ((x,y)) in self.object_layers['bonfire']['positions']:
                                nearby_bonfires.append((x * self.tile_size,y * self.tile_size))

        return nearby_bonfires
    
    def chests_around(self, pos, player_size):
        nearby_chests = []

        # Calculate the number of tiles the entity covers
        start_tile_x = int(pos[0] // self.tile_size) - 1
        end_tile_x = int((pos[0] + player_size[0]) // self.tile_size) + 1
        start_tile_y = int(pos[1] // self.tile_size) - 1
        end_tile_y = int((pos[1] + player_size[1]) // self.tile_size) + 1

        for x in range(start_tile_x, end_tile_x):
            for y in range(start_tile_y, end_tile_y):
                check_loc = f"{x};{y}"
                if check_loc in self.tilemap:
                    for tile in self.tilemap[check_loc]:
                       # Check for bonfire object positions
                        if tile['type'] == 'bronze_chest' or tile['type'] == 'silver_chest' or tile['type'] == 'gold_chest':
                            if ((x,y)) in self.object_layers['bronze_chest']['positions'] or ((x,y)) in self.object_layers['silver_chest']['positions'] or ((x,y)) in self.object_layers['gold_chest']['positions']:
                                nearby_chests.append((x * self.tile_size,y * self.tile_size))
        
        return nearby_chests

    def insert_entity_into_physics_tilemap(self, pos, entity_type):
        for i in range(0, len(self.physics_tilemap) - 1):
            for j in range (0, len(self.physics_tilemap[i]) - 1):
                if self.physics_tilemap[i][j] == 2 and entity_type == 'player':
                    self.physics_tilemap[i][j] = 0
                if self.physics_tilemap[i][j] == 3 and entity_type == 'enemy':
                    self.physics_tilemap[i][j] = 0
        if entity_type == 'enemy':
            entity_x = int((pos[0] + 7) // self.tile_size)
            entity_y = int((pos[1] + 4) // self.tile_size)
        else:
            entity_x = int((pos[0] + 7) // self.tile_size)
            entity_y = int((pos[1] + 4) // self.tile_size)
        # Handling for when player leaves tilemap
        if entity_y > len(self.physics_tilemap) - 1:
            return
        if entity_x > len(self.physics_tilemap[entity_y]) - 1:
            return
        if entity_type == 'player':
            self.physics_tilemap[entity_y][entity_x] = 2
        else:
            self.physics_tilemap[entity_y][entity_x] = 3
        return self.physics_tilemap
                
                
    # def render(self, surf, offset=(0, 0)):
    #         """
    #         Render the tilemap to the given surface.

    #         :param surf: The surface to render the tiles on.
    #         :param offset: The offset to apply to the rendering position.
    #         """
    #         # Render off-grid tiles
    #         for tile in self.offgrid_tiles:
    #             self.render_tile(surf, tile, offset)

    #         # Render tiles on the grid within the visible area
    #         for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
    #             for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
    #                 loc = str(x) + ';' + str(y)
    #                 if loc in self.tilemap:
    #                     for tile in sorted(self.tilemap[loc], key=lambda t: t['layer']):
    #                         self.render_tile(surf, tile, offset)

    def render_tile(self, surf, tile, offset):
        """
        Render a single tile on the given surface.

        :param surf: The surface to render the tile on.
        :param tile: The tile data dictionary.
        :param offset: The offset to apply to the tile's position.
        """
        tile_type = tile['type']
        variant = tile['variant']
        pos = tile['pos']
        x_pos = pos[0] * self.tile_size - offset[0]
        y_pos = pos[1] * self.tile_size - offset[1]

        # Tiles and variants to render over the plyer
        deferred_tiles = None # tile_type == 'tree' and variant in [0, 1]
        
        # Render all non-deferred tiles
        if not deferred_tiles and tile_type not in self.object_layers and tile_type not in self.animated_layers:
            # Only render tiles within the screen bounds
            if (-16 <= x_pos < surf.get_width() + 16) and (-16 <= y_pos < surf.get_height() + 16):
                surf.blit(
                    self.game.assets[tile_type][variant], 
                    (x_pos, y_pos)
                )

    

            

